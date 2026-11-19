from datetime import datetime, timedelta, timezone
import json
import os
import sqlite3
import tomllib
import psycopg2
from psycopg2.extras import Json


def obter_database_url():
  # 1. Tenta variável de ambiente
  url = os.environ.get("DATABASE_URL")
  if url:
    return url

  # 2. Tenta ler do .streamlit/secrets.toml local
  caminho_secrets = os.path.join(".streamlit", "secrets.toml")
  if os.path.exists(caminho_secrets):
    with open(caminho_secrets, "rb") as f:
      data = tomllib.load(f)
      if "DATABASE_URL" in data:
        return data["DATABASE_URL"]

  raise RuntimeError(
      "DATABASE_URL não encontrada. Configure em .streamlit/secrets.toml ou nas"
      " variáveis de ambiente."
  )


def conectar_neon():
  url = obter_database_url()
  # Remove channel_binding caso cause incompatibilidade em versões específicas do libpq
  url_limpa = url.replace("&channel_binding=require", "").replace(
      "?channel_binding=require&", "?"
  )
  return psycopg2.connect(url_limpa)


def criar_tabelas(conn):
  with conn.cursor() as cur:
    # 1. Acompanhamentos pastorais e de casais
    cur.execute("""
            CREATE TABLE IF NOT EXISTS registros_acompanhamento (
                id SERIAL PRIMARY KEY,
                casal_alvo TEXT NOT NULL,
                casal_lider TEXT NOT NULL,
                tipo TEXT NOT NULL,
                motivo TEXT DEFAULT 'Outros / Geral',
                data_atendimento TEXT NOT NULL,
                descricao TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # 2. Configuração de líderes
    cur.execute("""
            CREATE TABLE IF NOT EXISTS lideres_config (
                chave_casal TEXT PRIMARY KEY,
                eh_lider BOOLEAN NOT NULL DEFAULT FALSE,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # 3. Conteúdo dinâmico do painel (estudo, recado, casais_msg, devocional)
    cur.execute("""
            CREATE TABLE IF NOT EXISTS conteudo_painel (
                chave TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # 4. Planejamento Estratégico 2027
    cur.execute("""
            CREATE TABLE IF NOT EXISTS planejamento_2027 (
                id INTEGER PRIMARY KEY DEFAULT 1,
                plano JSONB NOT NULL,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT linha_unica_plano CHECK (id = 1)
            );
        """)
  conn.commit()


def migrar_acompanhamento_sqlite(conn):
  caminho_db = "acompanhamento.db"
  if not os.path.exists(caminho_db):
    print("ℹ️ acompanhamento.db local não encontrado; pulando migração de atendimentos.")
    return

  sqlite_conn = sqlite3.connect(caminho_db)
  sqlite_conn.row_factory = sqlite3.Row
  cur_sqlite = sqlite_conn.cursor()

  try:
    cur_sqlite.execute("PRAGMA table_info(registros)")
    colunas_existentes = {col["name"] for col in cur_sqlite.fetchall()}
    if not colunas_existentes:
      print("ℹ️ Tabela 'registros' vazia ou inexistente no SQLite.")
      return

    tem_motivo = "motivo" in colunas_existentes
    query = (
        "SELECT casal_alvo, casal_lider, tipo, motivo, data_atendimento,"
        " descricao FROM registros"
        if tem_motivo
        else (
            "SELECT casal_alvo, casal_lider, tipo, data_atendimento,"
            " descricao FROM registros"
        )
    )
    cur_sqlite.execute(query)
    linhas = cur_sqlite.fetchall()

    with conn.cursor() as cur_pg:
      # Evita duplicar se rodar o script mais de uma vez
      cur_pg.execute("SELECT COUNT(*) FROM registros_acompanhamento")
      total_pg = cur_pg.fetchone()[0]

      if total_pg == 0 and linhas:
        for r in linhas:
          motivo_val = (
              r["motivo"]
              if tem_motivo and r["motivo"]
              else "Outros / Geral"
          )
          cur_pg.execute(
              """
                            INSERT INTO registros_acompanhamento
                                (casal_alvo, casal_lider, tipo, motivo, data_atendimento, descricao)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """,
              (
                  str(r["casal_alvo"] or ""),
                  str(r["casal_lider"] or ""),
                  str(r["tipo"] or ""),
                  str(motivo_val),
                  str(r["data_atendimento"] or ""),
                  str(r["descricao"] or ""),
              ),
          )
        conn.commit()
        print(f"✅ Migrados {len(linhas)} registros do acompanhamento.db para o Neon.")
      else:
        print(
            f"ℹ️ Tabela registros_acompanhamento já possui {total_pg} registro(s); nenhuma duplicação feita."
        )
  finally:
    sqlite_conn.close()


def migrar_lideres_e_conteudo(conn):
  # Migra lideres_config.json se existir
  for arq_lideres in ["lideres_config.json", "dados_app.json"]:
    if os.path.exists(arq_lideres):
      try:
        with open(arq_lideres, "r", encoding="utf-8") as f:
          dados_lid = json.load(f)
        if isinstance(dados_lid, dict) and dados_lid:
          with conn.cursor() as cur:
            for k, v in dados_lid.items():
              if isinstance(v, bool):
                cur.execute(
                    """
                                        INSERT INTO lideres_config (chave_casal, eh_lider, atualizado_em)
                                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                                        ON CONFLICT (chave_casal) DO UPDATE
                                        SET eh_lider = EXCLUDED.eh_lider, atualizado_em = CURRENT_TIMESTAMP
                                    """,
                    (str(k), v),
                )
          conn.commit()
          print(f"✅ Lideranças sincronizadas a partir de {arq_lideres}.")
          break
      except Exception as e:
        print(f"⚠️ Aviso ao ler {arq_lideres}: {e}")

  # Migra dados_painel.json se existir
  if os.path.exists("dados_painel.json"):
    try:
      with open("dados_painel.json", "r", encoding="utf-8") as f:
        dados_painel = json.load(f)
      if isinstance(dados_painel, dict):
        with conn.cursor() as cur:
          for chave in ["estudo", "recado", "casais_msg", "devocional"]:
            if chave in dados_painel and isinstance(dados_painel[chave], dict):
              cur.execute(
                  """
                                    INSERT INTO conteudo_painel (chave, payload, atualizado_em)
                                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                                    ON CONFLICT (chave) DO UPDATE
                                    SET payload = EXCLUDED.payload, atualizado_em = CURRENT_TIMESTAMP
                                """,
                  (chave, Json(dados_painel[chave])),
              )
        conn.commit()
        print("✅ Conteúdos do dados_painel.json enviados para o Neon.")
    except Exception as e:
      print(f"⚠️ Aviso ao ler dados_painel.json: {e}")


def popular_planejamento_2027(conn):
  fuso_brasil = timezone(timedelta(hours=-3))
  plano_2027 = {
      "ano": 2027,
      "atualizado_em": datetime.now(fuso_brasil).strftime("%d/%m/%Y %H:%M"),
      "fundamento": {
          "titulo": "Amor como Fundamento",
          "versiculo": "1 Coríntios 13:1-2",
          "texto": (
              "O amor não é sentimento superficial nem complemento: é decisão"
              " constante, base e estrutura do ministério e do lar."
              " Planejamos com organização e prazos para não improvisar e para"
              " respeitar a agenda geral da igreja."
          ),
      },
      "grupos_alvo": [
          {
              "nome": "Preparação para o Casamento",
              "publico": "Noivos e casais se preparando para o casamento",
              "foco": "Aconselhamento pré-matrimonial e alinhamento de princípios.",
          },
          {
              "nome": "Recém-Casados",
              "publico": "Casais recém-casados",
              "foco": "Adaptação à nova vida a dois, rotinas e construção da aliança.",
          },
          {
              "nome": "Enriquecimento Conjugal",
              "publico": "Todos os casais da igreja (abrangente)",
              "foco": (
                  "Fortalecimento contínuo de todos os casais da igreja, com"
                  " alguns anos de casados ou em qualquer etapa."
              ),
          },
          {
              "nome": "Restauração de Casamentos",
              "publico": "Casais que precisam de restauração",
              "foco": (
                  "Acolhimento, cura, aconselhamento e reconstrução em"
                  " momentos de crise."
              ),
          },
      ],
      "modulos_bimestrais": [
          {
              "modulo": 1,
              "bimestre": "1º Bimestre (Jan / Fev)",
              "tema": "Fundamentos e Tudo sobre Casamento",
              "foco": "Visão bíblica da aliança, propósito e amor como base.",
          },
          {
              "modulo": 2,
              "bimestre": "2º Bimestre (Mar / Abr)",
              "tema": "Comunicação no Casamento",
              "foco": "Diálogo franco, escuta ativa, resolução de conflitos e perdão.",
          },
          {
              "modulo": 3,
              "bimestre": "3º Bimestre (Mai / Jun)",
              "tema": "O Papel da Mulher no Casamento",
              "foco": "Identidade, sabedoria, dignidade e edificação do lar.",
          },
          {
              "modulo": 4,
              "bimestre": "4º Bimestre (Jul / Ago)",
              "tema": "O Papel do Homem no Casamento",
              "foco": "Liderança servicial, responsabilidade, cuidado e cobertura espiritual.",
          },
          {
              "modulo": 5,
              "bimestre": "5º Bimestre (Set / Out)",
              "tema": "Economia Doméstica",
              "foco": "Finanças a dois, orçamento familiar, mordomia e prevenção de dívidas.",
          },
          {
              "modulo": 6,
              "bimestre": "6º Bimestre (Nov / Dez)",
              "tema": "Relacionamento entre Pais e Filhos",
              "foco": "Educação, limites, presença e transmissão de valores na família.",
          },
      ],
      "ciclo_prazos": [
          "1. Preparação: alinhamento da liderança, estudo do tema e definição de datas/estrutura.",
          "2. Promoção: divulgação nos cultos, grupos e convites aos casais e líderes.",
          "3. Execução: realização do encontro/ministração conforme disponibilidade da igreja.",
      ],
      "calendario_oracao": (
          "Intercessão contínua da liderança e convite à igreja para orar"
          " antes de cada decisão, escolha de equipe e encontro (baseado no"
          " exemplo de oração de Jesus)."
      ),
      "datas_comemorativas_2027": [
          {
              "data": "12/06/2027",
              "evento": "Dia dos Namorados (Sábado)",
              "sugestao": "Encontro / jantar ou programação especial para casais.",
          },
          {
              "data": "Feriados e Datas de 2027",
              "evento": "Janela de Feriados e Finais de Semana de 2027",
              "sugestao": (
                  "Avaliar datas livres no calendário oficial da igreja para"
                  " retiros, cafés de casais ou encontros temáticos sem"
                  " conflito com outros ministérios."
              ),
          },
      ],
  }

  with conn.cursor() as cur:
    cur.execute(
        """
            INSERT INTO planejamento_2027 (id, plano, atualizado_em)
            VALUES (1, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE
            SET plano = EXCLUDED.plano, atualizado_em = CURRENT_TIMESTAMP
        """,
        (Json(plano_2027),),
    )
  conn.commit()
  print("✅ Planejamento Estratégico 2027 gravado no Neon.")


def main():
  conn = conectar_neon()
  try:
    criar_tabelas(conn)
    migrar_acompanhamento_sqlite(conn)
    migrar_lideres_e_conteudo(conn)
    popular_planejamento_2027(conn)
    print("\n🎉 Estruturação e migração inicial para o Neon concluídas com sucesso!")
  finally:
    conn.close()


if __name__ == "__main__":
  main()
