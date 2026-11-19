import os
import tomllib
import pandas as pd
import psycopg2
import streamlit as st

ARQUIVO_AGENDA = "agenda_ministerio.xlsx"
ARQUIVO_MENSAGENS = "mensagens_palavra.xlsx"
ARQUIVO_DINAMICAS = "dinamicas_casais.xlsx"


def _obter_database_url():
  """Obtém a DATABASE_URL a partir do st.secrets, variáveis de ambiente ou .streamlit/secrets.toml."""
  try:
    if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
      return str(st.secrets["DATABASE_URL"]).strip()
  except Exception:
    pass

  url_env = os.environ.get("DATABASE_URL")
  if url_env and url_env.strip():
    return url_env.strip()

  caminho_secrets = os.path.join(".streamlit", "secrets.toml")
  if os.path.exists(caminho_secrets):
    try:
      with open(caminho_secrets, "rb") as f:
        data = tomllib.load(f)
        if "DATABASE_URL" in data and str(data["DATABASE_URL"]).strip():
          return str(data["DATABASE_URL"]).strip()
    except Exception:
      pass

  return None


def _conectar_neon():
  """Abre uma ligação ao PostgreSQL do Neon e garante as tabelas da agenda ministerial."""
  url = _obter_database_url()
  if not url:
    raise RuntimeError(
        "DATABASE_URL não configurada em st.secrets, ambiente ou"
        " .streamlit/secrets.toml."
    )

  url_limpa = url.replace("&channel_binding=require", "").replace(
      "?channel_binding=require&", "?"
  )
  conn = psycopg2.connect(url_limpa)
  with conn.cursor() as cur:
    cur.execute("""
            CREATE TABLE IF NOT EXISTS agenda_eventos (
                id SERIAL PRIMARY KEY,
                data_evento TEXT NOT NULL,
                evento TEXT NOT NULL,
                foco_pastoral TEXT DEFAULT '',
                status TEXT DEFAULT 'Planejado'
            );
        """)
    cur.execute("""
            CREATE TABLE IF NOT EXISTS agenda_mensagens (
                id SERIAL PRIMARY KEY,
                tema TEXT NOT NULL,
                referencia TEXT NOT NULL,
                texto TEXT NOT NULL,
                aplicacao TEXT DEFAULT ''
            );
        """)
    cur.execute("""
            CREATE TABLE IF NOT EXISTS agenda_dinamicas (
                id SERIAL PRIMARY KEY,
                titulo TEXT NOT NULL,
                objetivo TEXT DEFAULT '',
                inspiracao TEXT DEFAULT '',
                como_fazer TEXT NOT NULL
            );
        """)
  conn.commit()
  return conn


def carregar_agenda():
  dados_iniciais = [
      {
          "Data": "12/06/2026",
          "Evento": "Jantar dos Namorados / Casais",
          "Foco Pastoral": (
              "Resgate do Romantismo e Aliança (Pr. Josué Gonçalves)"
          ),
          "Status": "Planejado",
      },
      {
          "Data": "10/05/2026",
          "Evento": "Homenagem ao Dia das Mães",
          "Foco Pastoral": "Valorização do papel da mulher e mãe no lar",
          "Status": "Planejado",
      },
      {
          "Data": "09/08/2026",
          "Evento": "Café com os Pais",
          "Foco Pastoral": (
              "A responsabilidade do homem como sacerdote do lar"
          ),
          "Status": "Planejado",
      },
      {
          "Data": "15/10/2026",
          "Evento": "Encontro de Casais (Retiro)",
          "Foco Pastoral": (
              "Trabalhando as Fases e Quebrando Ciclos de Conflito"
          ),
          "Status": "Planejado",
      },
  ]
  conn = None
  try:
    conn = _conectar_neon()
    with conn.cursor() as cur:
      cur.execute("SELECT COUNT(*) FROM agenda_eventos")
      total = cur.fetchone()[0]
      if total == 0:
        for item in dados_iniciais:
          cur.execute(
              """
                            INSERT INTO agenda_eventos (data_evento, evento, foco_pastoral, status)
                            VALUES (%s, %s, %s, %s)
                        """,
              (
                  item["Data"],
                  item["Evento"],
                  item["Foco Pastoral"],
                  item["Status"],
              ),
          )
        conn.commit()

      cur.execute(
          """
                SELECT id, data_evento, evento, foco_pastoral, status
                FROM agenda_eventos
                ORDER BY id ASC
            """
      )
      rows = cur.fetchall()
    return pd.DataFrame(
        rows,
        columns=["id", "Data", "Evento", "Foco Pastoral", "Status"],
    )
  except Exception as e:
    st.error(f"❌ Erro ao carregar agenda do Neon: {e}")
    return pd.DataFrame(
        columns=["id", "Data", "Evento", "Foco Pastoral", "Status"]
    )
  finally:
    if conn is not None:
      try:
        conn.close()
      except Exception:
        pass


def adicionar_evento_neon(data_evento, evento, foco_pastoral, status):
  conn = None
  try:
    conn = _conectar_neon()
    with conn.cursor() as cur:
      cur.execute(
          """
                INSERT INTO agenda_eventos (data_evento, evento, foco_pastoral, status)
                VALUES (%s, %s, %s, %s)
            """,
          (data_evento, evento, foco_pastoral, status),
      )
    conn.commit()
    return True
  except Exception as e:
    st.error(f"❌ Erro ao salvar evento no Neon: {e}")
    return False
  finally:
    if conn is not None:
      try:
        conn.close()
      except Exception:
        pass


def remover_evento_neon(evento_id):
  conn = None
  try:
    conn = _conectar_neon()
    with conn.cursor() as cur:
      cur.execute("DELETE FROM agenda_eventos WHERE id = %s", (int(evento_id),))
    conn.commit()
    return True
  except Exception as e:
    st.error(f"❌ Erro ao remover evento do Neon: {e}")
    return False
  finally:
    if conn is not None:
      try:
        conn.close()
      except Exception:
        pass


def carregar_mensagens():
  mensagens_iniciais = [
      {
          "Tema": "Aliança e Companheirismo",
          "Referencia": "Eclesiastes 4:9-12",
          "Texto": (
              "É melhor serem dois do que um, porque têm melhor paga do seu"
              " trabalho. Porque se caírem, um levanta o companheiro..."
          ),
          "Aplicacao": (
              "O casamento é uma sociedade divina onde o apoio mútuo protege o"
              " casal contra as intempéries da vida."
          ),
      },
      {
          "Tema": "Amor e Perdão",
          "Referencia": "Colossenses 3:13-14",
          "Texto": (
              "Suportai-vos uns aos outros, e perdoai-vos uns aos outros, se"
              " alguém tiver queixa contra outro..."
          ),
          "Aplicacao": (
              "O perdão diário e o amor incondicional são os pilares que"
              " sustentam os ciclos de maturidade do casal."
          ),
      },
      {
          "Tema": "O Lar Fundado na Rocha",
          "Referencia": "Josué 24:15",
          "Texto": (
              "Porém, se vos parece mal servir ao Senhor, escolhei hoje a quem"
              " sirvais... Eu e a minha casa serviremos ao Senhor."
          ),
          "Aplicacao": (
              "A liderança espiritual do lar posiciona a família sob a proteção"
              " e a direção de Deus."
          ),
      },
  ]
  conn = None
  try:
    conn = _conectar_neon()
    with conn.cursor() as cur:
      cur.execute("SELECT COUNT(*) FROM agenda_mensagens")
      total = cur.fetchone()[0]
      if total == 0:
        for item in mensagens_iniciais:
          cur.execute(
              """
                            INSERT INTO agenda_mensagens (tema, referencia, texto, aplicacao)
                            VALUES (%s, %s, %s, %s)
                        """,
              (
                  item["Tema"],
                  item["Referencia"],
                  item["Texto"],
                  item["Aplicacao"],
              ),
          )
        conn.commit()

      cur.execute(
          """
                SELECT id, tema, referencia, texto, aplicacao
                FROM agenda_mensagens
                ORDER BY id ASC
            """
      )
      rows = cur.fetchall()
    return pd.DataFrame(
        rows,
        columns=["id", "Tema", "Referencia", "Texto", "Aplicacao"],
    )
  except Exception as e:
    st.error(f"❌ Erro ao carregar mensagens do Neon: {e}")
    return pd.DataFrame(
        columns=["id", "Tema", "Referencia", "Texto", "Aplicacao"]
    )
  finally:
    if conn is not None:
      try:
        conn.close()
      except Exception:
        pass


def adicionar_mensagem_neon(tema, referencia, texto, aplicacao):
  conn = None
  try:
    conn = _conectar_neon()
    with conn.cursor() as cur:
      cur.execute(
          """
                INSERT INTO agenda_mensagens (tema, referencia, texto, aplicacao)
                VALUES (%s, %s, %s, %s)
            """,
          (tema, referencia, texto, aplicacao),
      )
    conn.commit()
    return True
  except Exception as e:
    st.error(f"❌ Erro ao salvar mensagem no Neon: {e}")
    return False
  finally:
    if conn is not None:
      try:
        conn.close()
      except Exception:
        pass


def remover_mensagem_neon(msg_id):
  conn = None
  try:
    conn = _conectar_neon()
    with conn.cursor() as cur:
      cur.execute("DELETE FROM agenda_mensagens WHERE id = %s", (int(msg_id),))
    conn.commit()
    return True
  except Exception as e:
    st.error(f"❌ Erro ao remover mensagem do Neon: {e}")
    return False
  finally:
    if conn is not None:
      try:
        conn.close()
      except Exception:
        pass


def carregar_dinamicas():
  dinamicas_iniciais = [
      {
          "Titulo": "A Aliança Inquebrável",
          "Objetivo": (
              "Conscientizar sobre o compromisso irrevogável do casamento."
          ),
          "Inspiracao": "Pr. Josué Gonçalves (Princípios de Aliança)",
          "ComoFazer": (
              "Entregar um pedaço de barbante ou corda trançada para cada"
              " casal. Pedir que tentem cortar com as mãos ou puxar com força"
              " em direções opostas mostrando que a corda unida resiste."
              " Ensinar que a aliança com Deus e entre o casal não se rompe com"
              " facilidade quando há três dobras (Deus, marido e esposa)."
          ),
      },
      {
          "Titulo": "O Espelho da Comunicação",
          "Objetivo": (
              "Melhorar a escuta ativa e eliminar ruídos no diálogo."
          ),
          "Inspiracao": (
              "Ministério Casados para Sempre / Família debaixo da Graça"
          ),
          "ComoFazer": (
              "Fazer os casais sentarem-se frente a frente. Um fala por 2"
              " minutos sobre um sonho ou necessidade sem ser interrompido; o"
              " outro deve apenas repetir o que entendeu ('O que eu ouvi você"
              " dizer foi...'). Depois invertem os papéis. Ajuda a combater o"
              " hábito de já responder na defensiva."
          ),
      },
      {
          "Titulo": "Limpando as Mágoas (O Memorial do Perdão)",
          "Objetivo": (
              "Estimular o perdão de ofensas passadas que travam o"
              " relacionamento."
          ),
          "Inspiracao": "Pr. Josué Gonçalves (Ciclos de Conflito)",
          "ComoFazer": (
              "Entregar um pequeno papel para cada cônjuge escrever"
              " anonimamente ou para o parceiro uma pequena mágoa ou"
              " desentendimento antigo que ainda machuca. Em seguida, orientar"
              " que rasguem o papel em pedaços miúdos ou coloquem"
              " symbolicamente em uma vasilha (simbolizando a cruz de Cristo"
              " que lança os erros no mar do esquecimento), encerrando com uma"
              " oração de perdão mútuo e abraço."
          ),
      },
  ]
  conn = None
  try:
    conn = _conectar_neon()
    with conn.cursor() as cur:
      cur.execute("SELECT COUNT(*) FROM agenda_dinamicas")
      total = cur.fetchone()[0]
      if total == 0:
        for item in dinamicas_iniciais:
          cur.execute(
              """
                            INSERT INTO agenda_dinamicas (titulo, objetivo, inspiracao, como_fazer)
                            VALUES (%s, %s, %s, %s)
                        """,
              (
                  item["Titulo"],
                  item["Objetivo"],
                  item["Inspiracao"],
                  item["ComoFazer"],
              ),
          )
        conn.commit()

      cur.execute(
          """
                SELECT id, titulo, objetivo, inspiracao, como_fazer
                FROM agenda_dinamicas
                ORDER BY id ASC
            """
      )
      rows = cur.fetchall()
    return pd.DataFrame(
        rows,
        columns=["id", "Titulo", "Objetivo", "Inspiracao", "ComoFazer"],
    )
  except Exception as e:
    st.error(f"❌ Erro ao carregar dinâmicas do Neon: {e}")
    return pd.DataFrame(
        columns=["id", "Titulo", "Objetivo", "Inspiracao", "ComoFazer"]
    )
  finally:
    if conn is not None:
      try:
        conn.close()
      except Exception:
        pass


def adicionar_dinamica_neon(titulo, objetivo, inspiracao, como_fazer):
  conn = None
  try:
    conn = _conectar_neon()
    with conn.cursor() as cur:
      cur.execute(
          """
                INSERT INTO agenda_dinamicas (titulo, objetivo, inspiracao, como_fazer)
                VALUES (%s, %s, %s, %s)
            """,
          (titulo, objetivo, inspiracao, como_fazer),
      )
    conn.commit()
    return True
  except Exception as e:
    st.error(f"❌ Erro ao salvar dinâmica no Neon: {e}")
    return False
  finally:
    if conn is not None:
      try:
        conn.close()
      except Exception:
        pass


def remover_dinamica_neon(din_id):
  conn = None
  try:
    conn = _conectar_neon()
    with conn.cursor() as cur:
      cur.execute("DELETE FROM agenda_dinamicas WHERE id = %s", (int(din_id),))
    conn.commit()
    return True
  except Exception as e:
    st.error(f"❌ Erro ao remover dinâmica do Neon: {e}")
    return False
  finally:
    if conn is not None:
      try:
        conn.close()
      except Exception:
        pass


def modulo_agenda():
  st.markdown("### ✝️ Agenda Ministerial e Palavra de Deus para os Casais")
  st.write(
      "Gerencie os eventos, alimente o mural com a Palavra e utilize"
      " dinâmicas práticas baseadas em princípios ministeriais."
  )

  # Criando as Três Abas
  aba_agenda, aba_palavra, aba_dinamicas = st.tabs([
      "📅 Agenda Anual de Eventos",
      "📖 Mural da Palavra (Devusionais)",
      "💡 Dinâmicas & Ferramentas (Pr. Josué)",
  ])

  # ==========================================
  # ABA 1: AGENDA DE EVENTOS
  # ==========================================
  with aba_agenda:
    df_agenda = carregar_agenda()

    with st.expander("➕ Adicionar Novo Evento à Agenda"):
      with st.form("form_novo_evento"):
        col1, col2 = st.columns(2)
        data_evento = col1.text_input("Data do Evento (DD/MM/AAAA)")
        nome_evento = col2.text_input(
            "Nome do Evento (Ex: Retiro, Jantar, Palestra)"
        )

        foco_pastoral = st.text_input(
            "Foco Pastoral / Diretriz (Ex: Comunicação, Liderança do Lar)"
        )
        status_evento = st.selectbox(
            "Status",
            ["Planejado", "Em Andamento", "Realizado", "Cancelado"],
        )

        salvar_evento = st.form_submit_button("Salvar na Agenda")

        if salvar_evento:
          if data_evento and nome_evento:
            if adicionar_evento_neon(
                data_evento, nome_evento, foco_pastoral, status_evento
            ):
              st.success("✅ Evento adicionado com sucesso no Neon!")
              st.rerun()
          else:
            st.warning("Preencha pelo menos a Data e o Nome do Evento.")

    st.markdown("---")
    st.subheader("📋 Cronograma de Eventos Cadastrados")

    if not df_agenda.empty:
      cols_exibir = [
          c for c in ["Data", "Evento", "Foco Pastoral", "Status"] if c in df_agenda.columns
      ]
      st.dataframe(df_agenda[cols_exibir], use_container_width=True, hide_index=True)

      st.markdown("### 🗑️ Gerenciar / Remover Evento")
      lista_opcoes = [
          f"{row['id']}: {row['Evento']} ({row['Data']})"
          for _, row in df_agenda.iterrows()
      ]
      selecionado = st.selectbox(
          "Selecione um evento para excluir:", lista_opcoes
      )

      if st.button("Remover Evento Selecionado"):
        evento_id = int(selecionado.split(":")[0])
        if remover_evento_neon(evento_id):
          st.success("Evento removido da agenda!")
          st.rerun()
    else:
      st.info("Nenhum evento cadastrado na agenda no momento.")

  # ==========================================
  # ABA 2: MURAL DA PALAVRA DE DEUS
  # ==========================================
  with aba_palavra:
    st.subheader("📖 Palavra de Deus e Conselhos Pastorais para Casais")
    st.write(
        "Utilize estas bases bíblicas para ministrações ou para enviar nos"
        " grupos de transmissão."
    )

    df_mensagens = carregar_mensagens()

    with st.expander("➕ Adicionar Nova Mensagem / Versículo Bíblico"):
      with st.form("form_nova_mensagem"):
        c_t1, c_t2 = st.columns(2)
        tema_msg = c_t1.text_input(
            "Tema (Ex: Perdão, Aliança, Comunicação, Finanças)"
        )
        ref_msg = c_t2.text_input(
            "Referência Bíblica (Ex: Efésios 4:26-27)"
        )

        texto_biblia = st.text_area("Texto do Versículo / Palavra")
        aplicacao_pastoral = st.text_area(
            "Aplicação Prática para o Casal / Visão Pastoral"
        )

        btn_salvar_msg = st.form_submit_button("Salvar Mensagem no Mural")

        if btn_salvar_msg:
          if tema_msg and ref_msg and texto_biblia:
            if adicionar_mensagem_neon(
                tema_msg, ref_msg, texto_biblia, aplicacao_pastoral
            ):
              st.success("✅ Mensagem bíblica cadastrada com sucesso no Neon!")
              st.rerun()
          else:
            st.warning(
                "Preencha ao menos o Tema, a Referência e o Versículo."
            )

    st.markdown("---")
    st.markdown("### 🕊️ Mural de Reflexões Cadastradas")

    if not df_mensagens.empty:
      for _, row in df_mensagens.iterrows():
        msg_id = int(row["id"])
        with st.container():
          st.markdown(
              f"#### 📌 Tema: {row['Tema']} — *({row['Referencia']})*"
          )
          st.info(f"\"{row['Texto']}\"")
          if pd.notna(row["Aplicacao"]) and str(row["Aplicacao"]).strip():
            st.markdown(f"**💡 Direção Pastoral:** {row['Aplicacao']}")

          if st.button("🗑️ Excluir esta mensagem", key=f"del_msg_{msg_id}"):
            if remover_mensagem_neon(msg_id):
              st.success("Mensagem removida do mural!")
              st.rerun()
          st.markdown("---")
    else:
      st.info("Nenhuma mensagem cadastrada no mural ainda.")

  # ==========================================
  # ABA 3: DINÂMICAS & FERRAMENTAS PRÁTICAS
  # ==========================================
  with aba_dinamicas:
    st.subheader("💡 Banco de Dinâmicas para Encontros de Casais")
    st.write(
        "Sugestões de dinâmicas práticas inspiradas nos princípios de"
        " edificação de lares (Pr. Josué Gonçalves / Casados para Sempre)."
    )

    df_dinamicas = carregar_dinamicas()

    with st.expander("➕ Adicionar Nova Dinâmica ao Banco"):
      with st.form("form_nova_dinamica"):
        d_tit = st.text_input("Título da Dinâmica")
        d_obj = st.text_input("Objetivo Principal")
        d_insp = st.text_input(
            "Inspiração / Referência (Ex: Pr. Josué Gonçalves, Livro X)"
        )
        d_como = st.text_area("Passo a Passo / Como Aplicar na Reunião")

        btn_salvar_din = st.form_submit_button("Salvar Dinâmica")

        if btn_salvar_din:
          if d_tit and d_como:
            if adicionar_dinamica_neon(d_tit, d_obj, d_insp, d_como):
              st.success("✅ Dinâmica cadastrada com sucesso no Neon!")
              st.rerun()
          else:
            st.warning("Preencha o Título e o passo a passo da dinâmica.")

    st.markdown("---")
    st.markdown("### 📋 Dinâmicas Cadastradas para Utilizar nos Encontros")

    if not df_dinamicas.empty:
      for _, row_d in df_dinamicas.iterrows():
        din_id = int(row_d["id"])
        with st.container():
          st.markdown(f"#### 🎯 {row_d['Titulo']}")
          if pd.notna(row_d["Objetivo"]) and str(row_d["Objetivo"]).strip():
            st.markdown(f"**🎯 Objetivo:** {row_d['Objetivo']}")
          if (
              pd.notna(row_d["Inspiracao"])
              and str(row_d["Inspiracao"]).strip()
          ):
            st.markdown(f"**📚 Inspiração:** *{row_d['Inspiracao']}*")

          st.markdown("**🛠️ Como Conduzir:**")
          st.success(row_d["ComoFazer"])

          if st.button(
              "🗑️ Excluir esta dinâmica", key=f"del_din_{din_id}"
          ):
            if remover_dinamica_neon(din_id):
              st.success("Dinâmica removida com sucesso!")
              st.rerun()
          st.markdown("---")
    else:
      st.info("Nenhuma dinâmica cadastrada.")