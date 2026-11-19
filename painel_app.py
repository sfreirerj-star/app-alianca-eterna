import base64
from datetime import datetime, timedelta, timezone
import calendar
import json
import os
import tomllib
from bs4 import BeautifulSoup
import database as db
import gestao_lideres
import pandas as pd
import psycopg2
from psycopg2.extras import Json
import requests
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Painel de Controle Oficial", page_icon="📖", layout="wide"
)

ARQUIVO_DADOS = "dados_painel.json"

# --- CONFIGURAÇÃO DA PLANILHA DO GOOGLE FORMS ---
LINK_PLANILHA_GOOGLE = (
    "https://docs.google.com/spreadsheets/d/1Zy2qTGHHqzLhim_ebHsCFgNrHBzPB1AxSscoQZXh3Vc/export?format=csv"
)


def _obter_segredo(chave, padrao=""):
  """Obtém um segredo a partir do st.secrets, variáveis de ambiente ou .streamlit/secrets.toml."""
  try:
    if hasattr(st, "secrets") and chave in st.secrets:
      val = str(st.secrets[chave]).strip()
      if val:
        return val
  except Exception:
    pass

  env_val = os.environ.get(chave)
  if env_val and env_val.strip():
    return env_val.strip()

  caminho_secrets = os.path.join(".streamlit", "secrets.toml")
  if os.path.exists(caminho_secrets):
    try:
      with open(caminho_secrets, "rb") as f:
        data = tomllib.load(f)
        if chave in data and str(data[chave]).strip():
          return str(data[chave]).strip()
    except Exception:
      pass

  return padrao


# --- CONFIGURAÇÕES DE AUTOMAÇÃO DO GITHUB (VIA SECRETS) ---
GITHUB_TOKEN = _obter_segredo("GITHUB_TOKEN", "")
REPO_OWNER = "sfreirerj-star"
REPO_NAME = "app-alianca-eterna"
BRANCH = "main"

# --- SENHAS DE ACESSO (APENAS LIDERANÇA, VIA SECRETS) ---
SENHA_PASTORAL = _obter_segredo("SENHA_PASTORAL", "pastor123")
SENHA_CASAIS = _obter_segredo("SENHA_CASAIS", "casais123")

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "senha_pastoral_ok" not in st.session_state:
  st.session_state["senha_pastoral_ok"] = False

if "senha_casais_ok" not in st.session_state:
  st.session_state["senha_casais_ok"] = False


def _obter_database_url():
  """Obtém a DATABASE_URL a partir do st.secrets, variáveis de ambiente ou .streamlit/secrets.toml."""
  url = _obter_segredo("DATABASE_URL", "")
  return url if url else None


@st.cache_resource(show_spinner=False)
def _obter_conexao_cacheada(url_limpa):
  """Reutiliza uma conexão aberta com o PostgreSQL do Neon e garante as tabelas uma única vez por sessão do servidor."""
  conn = psycopg2.connect(url_limpa, connect_timeout=5)
  with conn.cursor() as cur:
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
    cur.execute("""
            CREATE TABLE IF NOT EXISTS conteudo_painel (
                chave TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    cur.execute("""
            CREATE TABLE IF NOT EXISTS planejamento_2027 (
                id INTEGER PRIMARY KEY DEFAULT 1,
                plano JSONB NOT NULL,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT linha_unica_plano CHECK (id = 1)
            );
        """)
  conn.commit()
  return conn


def _conectar_neon():
  """Retorna uma conexão ativa com o PostgreSQL do Neon, reconectando automaticamente se caiu."""
  url = _obter_database_url()
  if not url:
    return None

  url_limpa = url.replace("&channel_binding=require", "").replace(
      "?channel_binding=require&", "?"
  )
  try:
    conn = _obter_conexao_cacheada(url_limpa)
    if conn.closed != 0:
      _obter_conexao_cacheada.clear()
      conn = _obter_conexao_cacheada(url_limpa)
    else:
      try:
        with conn.cursor() as cur:
          cur.execute("SELECT 1")
      except Exception:
        conn.rollback()
        _obter_conexao_cacheada.clear()
        conn = _obter_conexao_cacheada(url_limpa)
    return conn
  except Exception as e:
    print(f"Aviso ao conectar ao Neon: {e}")
    return None


@st.cache_data(ttl=300, show_spinner=False)
def _feriados_nacionais_por_ano(ano):
  """Retorna dicionário { 'YYYY-MM-DD': 'Nome do Feriado' } incluindo Páscoa/Sexta-feira Santa/Corpus Christi."""
  a = ano % 19
  b = ano // 100
  c = ano % 100
  d = b // 4
  e = b % 4
  f = (b + 8) // 25
  g = (b - f + 1) // 3
  h = (19 * a + b - d - g + 15) % 30
  i = c // 4
  k = c % 4
  l = (32 + 2 * e + 2 * i - h - k) % 7
  m = (a + 11 * h + 22 * l) // 451
  mes_pascoa = (h + l - 7 * m + 114) // 31
  dia_pascoa = ((h + l - 7 * m + 114) % 31) + 1
  pascoa = datetime(ano, mes_pascoa, dia_pascoa).date()

  sexta_santa = pascoa - timedelta(days=2)
  corpus_christi = pascoa + timedelta(days=60)

  return {
      f"{ano:04d}-01-01": "Confraternização Universal",
      sexta_santa.strftime("%Y-%m-%d"): "Paixão de Cristo",
      f"{ano:04d}-04-21": "Tiradentes",
      f"{ano:04d}-05-01": "Dia do Trabalhador",
      corpus_christi.strftime("%Y-%m-%d"): "Corpus Christi",
      f"{ano:04d}-09-07": "Independência do Brasil",
      f"{ano:04d}-10-12": "Nossa Senhora Aparecida",
      f"{ano:04d}-11-02": "Finados",
      f"{ano:04d}-11-15": "Proclamação da República",
      f"{ano:04d}-12-25": "Natal",
  }


def _compromissos_padrao():
  """Compromissos de liderança e eventos do ministério."""
  return [
      {
          "data": "2026-12-12",
          "sigla": "EVT",
          "titulo": "Planejamento / Encontro de Encerramento — Dezembro",
          "tipo": "Evento",
          "cor": "#16a34a",
          "observacao": "Janela disponível em dezembro de 2026 para planejar e realizar programação/encontro do ministério.",
      },
      {
          "data": "2027-01-16",
          "sigla": "LDD",
          "titulo": "Alinhamento da Liderança — 1º Bimestre",
          "tipo": "Liderança",
          "cor": "#2563eb",
          "observacao": "Definição de metas e cronograma do 1º Bimestre (Fundamentos e Tudo sobre Casamento).",
      },
      {
          "data": "2027-02-20",
          "sigla": "EVT",
          "titulo": "Encontro de Casais — Fundamentos da Aliança",
          "tipo": "Evento",
          "cor": "#16a34a",
          "observacao": "Programação do 1º Bimestre para os casais da igreja.",
      },
      {
          "data": "2027-03-20",
          "sigla": "LDD",
          "titulo": "Reunião de Líderes — Comunicação no Casamento",
          "tipo": "Liderança",
          "cor": "#2563eb",
          "observacao": "Preparação e divisão de visitas/aconselhamento do 2º Bimestre.",
      },
      {
          "data": "2027-04-17",
          "sigla": "EVT",
          "titulo": "Noite de Casais — Comunicação e Perdão",
          "tipo": "Evento",
          "cor": "#16a34a",
          "observacao": "Encontro temático do 2º Bimestre.",
      },
      {
          "data": "2027-05-15",
          "sigla": "LDD",
          "titulo": "Alinhamento da Liderança — Papel da Mulher",
          "tipo": "Liderança",
          "cor": "#2563eb",
          "observacao": "Organização da programação de Maio/Junho.",
      },
      {
          "data": "2027-06-12",
          "sigla": "EVT",
          "titulo": "Encontro Especial de Casais — Junho",
          "tipo": "Evento",
          "cor": "#16a34a",
          "observacao": "Encontro ou programação especial para casais em junho de 2027.",
      },
      {
          "data": "2027-07-17",
          "sigla": "LDD",
          "titulo": "Reunião de Líderes — Papel do Homem",
          "tipo": "Liderança",
          "cor": "#2563eb",
          "observacao": "Alinhamento do 4º Bimestre (liderança servicial e cuidado espiritual).",
      },
      {
          "data": "2027-08-21",
          "sigla": "EVT",
          "titulo": "Encontro de Casais — Aliança e Família",
          "tipo": "Evento",
          "cor": "#16a34a",
          "observacao": "Programação do 4º Bimestre.",
      },
      {
          "data": "2027-09-18",
          "sigla": "LDD",
          "titulo": "Reunião de Líderes — Economia Doméstica",
          "tipo": "Liderança",
          "cor": "#2563eb",
          "observacao": "Preparação do tema de finanças a dois e mordomia (5º Bimestre).",
      },
      {
          "data": "2027-10-16",
          "sigla": "EVT",
          "titulo": "Workshop / Encontro — Economia Doméstica",
          "tipo": "Evento",
          "cor": "#16a34a",
          "observacao": "Encontro prático sobre orçamento familiar e prevenção de dívidas.",
      },
      {
          "data": "2027-11-20",
          "sigla": "LDD",
          "titulo": "Alinhamento Final — Pais e Filhos",
          "tipo": "Liderança",
          "cor": "#2563eb",
          "observacao": "Avaliação anual e organização do 6º Bimestre.",
      },
      {
          "data": "2027-12-11",
          "sigla": "EVT",
          "titulo": "Confraternização de Encerramento — Família e Aliança",
          "tipo": "Evento",
          "cor": "#16a34a",
          "observacao": "Encerramento do calendário 2027 com as famílias.",
      },
  ]


def _plano_2027_padrao():
  fuso_brasil = timezone(timedelta(hours=-3))
  return {
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
              "foco": (
                  "Adaptação à nova vida a dois, rotinas e construção da"
                  " aliança."
              ),
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
              "foco": (
                  "Liderança servicial, responsabilidade, cuidado e cobertura"
                  " espiritual."
              ),
          },
          {
              "modulo": 5,
              "bimestre": "5º Bimestre (Set / Out)",
              "tema": "Economia Doméstica",
              "foco": (
                  "Finanças a dois, orçamento familiar, mordomia e prevenção de"
                  " dívidas."
              ),
          },
          {
              "modulo": 6,
              "bimestre": "6º Bimestre (Nov / Dez)",
              "tema": "Relacionamento entre Pais e Filhos",
              "foco": (
                  "Educação, limites, presença e transmissão de valores na"
                  " família."
              ),
          },
      ],
      "ciclo_prazos": [
          (
              "1. Preparação: alinhamento da liderança, estudo do tema e"
              " definição de datas/estrutura."
          ),
          (
              "2. Promoção: divulgação nos cultos, grupos e convites aos casais"
              " e líderes."
          ),
          (
              "3. Execução: realização do encontro/ministração conforme"
              " disponibilidade da igreja."
          ),
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
      "compromissos_calendario": _compromissos_padrao(),
  }


def carregar_planejamento_2027():
  """Carrega o Planeamento Estratégico 2027 a partir do Neon (com cache em sessão)."""
  if "plano_2027_cache" in st.session_state and isinstance(
      st.session_state["plano_2027_cache"], dict
  ):
    return st.session_state["plano_2027_cache"]

  conn = _conectar_neon()
  if conn is not None:
    try:
      with conn.cursor() as cur:
        cur.execute("SELECT plano FROM planejamento_2027 WHERE id = 1")
        row = cur.fetchone()
        if row and isinstance(row[0], dict):
          plano_carregado = dict(row[0])
          if not plano_carregado.get("compromissos_calendario"):
            plano_carregado["compromissos_calendario"] = _compromissos_padrao()
          st.session_state["plano_2027_cache"] = plano_carregado
          return plano_carregado
        plano_inicial = _plano_2027_padrao()
        cur.execute(
            """
                        INSERT INTO planejamento_2027 (id, plano, atualizado_em)
                        VALUES (1, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (id) DO NOTHING
                    """,
            (Json(plano_inicial),),
        )
      conn.commit()
      st.session_state["plano_2027_cache"] = plano_inicial
      return plano_inicial
    except Exception as e:
      try:
        conn.rollback()
      except Exception:
        pass
      print(f"Aviso ao carregar Planejamento 2027 do Neon: {e}")

  plano_padrao = _plano_2027_padrao()
  st.session_state["plano_2027_cache"] = plano_padrao
  return plano_padrao


def salvar_planejamento_2027(plano_dict):
  """Guarda o Planeamento Estratégico 2027 no Neon e atualiza o cache."""
  conn = _conectar_neon()
  if conn is not None:
    try:
      with conn.cursor() as cur:
        cur.execute(
            """
                        INSERT INTO planejamento_2027 (id, plano, atualizado_em)
                        VALUES (1, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (id) DO UPDATE
                        SET plano = EXCLUDED.plano, atualizado_em = CURRENT_TIMESTAMP
                    """,
            (Json(plano_dict),),
        )
      conn.commit()
      st.session_state["plano_2027_cache"] = dict(plano_dict)
      return True
    except Exception as e:
      try:
        conn.rollback()
      except Exception:
        pass
      st.error(f"❌ Erro ao salvar Planejamento 2027 no Neon: {e}")
      return False
  return False


def _renderizar_grade_mensal_html(ano, mes, itens_por_data, feriados_ano=None, destaque_mes=True, dia_hoje_iso=None):
  """Renderiza uma grade mensal nos moldes da imagem: mês/ano no topo, DOM..SÁB, badges e rótulo de feriado abaixo do dia."""
  meses_pt = {
      1: "Jan",
      2: "Fev",
      3: "Mar",
      4: "Abr",
      5: "Mai",
      6: "Jun",
      7: "Jul",
      8: "Ago",
      9: "Set",
      10: "Out",
      11: "Nov",
      12: "Dez",
  }
  dias_semana = ["DOM", "SEG", "TER", "QUA", "QUI", "SEX", "SÁB"]
  if feriados_ano is None:
    feriados_ano = _feriados_nacionais_por_ano(ano)

  cal = calendar.Calendar(firstweekday=6)
  semanas = cal.monthdayscalendar(ano, mes)

  linhas_html = ""
  for semana in semanas:
    celulas_html = ""
    for dia in semana:
      if dia == 0:
        celulas_html += (
            '<td style="border:1px solid #eef0f3; background:#fafafa; height:96px; vertical-align:top; padding:8px; border-radius:8px;"></td>'
        )
      else:
        data_iso = f"{ano:04d}-{mes:02d}-{dia:02d}"
        eventos_dia = itens_por_data.get(data_iso, [])
        nome_feriado = feriados_ano.get(data_iso)
        eh_hoje = (dia_hoje_iso == data_iso)

        badges_html = ""
        for ev in eventos_dia:
          sigla = str(ev.get("sigla", "EVT")).strip()[:4].upper()
          cor = str(ev.get("cor", "#22c55e")).strip()
          titulo_ev = str(ev.get("titulo", "")).replace('"', "&quot;")
          badges_html += (
              f'<div title="{titulo_ev}" style="margin-top:5px; display:inline-block; '
              f'background:{cor}; color:#ffffff; font-weight:700; font-size:11px; '
              f'padding:2px 8px; border-radius:6px; letter-spacing:0.3px;">{sigla}</div> '
          )

        feriado_html = ""
        if nome_feriado:
          feriado_html = (
              f'<div style="margin-top:6px; font-size:11px; font-weight:600; color:#ea580c; '
              f'white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="{nome_feriado}">'
              f"{nome_feriado}</div>"
          )

        if eh_hoje:
          borda_celula = "border:2px solid #2563eb; background:#ffffff;"
          numero_html = (
              f'<span style="display:inline-flex; align-items:center; justify-content:center; '
              f'width:28px; height:28px; border-radius:999px; background:#2563eb; color:#ffffff; '
              f'font-size:15px; font-weight:700;">{dia}</span>'
          )
        else:
          borda_celula = "border:1px solid #eef0f3; background:#ffffff;"
          cor_num = "#ea580c" if nome_feriado else "#111827"
          numero_html = f'<span style="font-size:16px; font-weight:700; color:{cor_num};">{dia}</span>'

        celulas_html += (
            f'<td style="{borda_celula} height:96px; width:14.28%; vertical-align:top; padding:8px; border-radius:8px;">'
            f"<div>{numero_html}</div>"
            f'<div style="margin-top:2px;">{badges_html}</div>'
            f"{feriado_html}"
            f"</td>"
        )
    linhas_html += f"<tr>{celulas_html}</tr>"

  cabecalho_dias = "".join(
      f'<th style="text-align:center; font-size:12px; color:#6b7280; padding:10px 4px; font-weight:700; letter-spacing:0.4px;">{d}</th>'
      for d in dias_semana
  )

  if destaque_mes:
    titulo_mes = (
        f'<div style="display:flex; align-items:baseline; gap:8px; margin-bottom:12px; padding-left:4px;">'
        f'<span style="font-size:26px; font-weight:800; color:#111827;">{meses_pt[mes]}</span>'
        f'<span style="font-size:20px; font-weight:500; color:#6b7280;">{ano}</span>'
        f"</div>"
    )
  else:
    titulo_mes = (
        f'<div style="display:flex; align-items:baseline; gap:6px; margin-bottom:8px; padding-left:2px;">'
        f'<span style="font-size:16px; font-weight:800; color:#111827;">{meses_pt[mes]}</span>'
        f'<span style="font-size:14px; font-weight:500; color:#6b7280;">{ano}</span>'
        f"</div>"
    )

  return (
      f'<div style="background:#ffffff; border:1px solid #e5e7eb; border-radius:16px; padding:16px; margin-bottom:14px;">'
      f"{titulo_mes}"
      f'<table style="width:100%; border-collapse:separate; border-spacing:5px; table-layout:fixed;">'
      f"<thead><tr>{cabecalho_dias}</tr></thead>"
      f"<tbody>{linhas_html}</tbody>"
      f"</table>"
      f"</div>"
  )


def renderizar_calendario_planejamento_2027(plano_2027):
  """Exibe o calendário mensal ou anual iniciando no mês vigente, com feriados marcados e compromissos/eventos."""
  st.subheader("📅 Calendário de Compromissos da Liderança, Eventos e Feriados")

  fuso_brasil = timezone(timedelta(hours=-3))
  hoje_br = datetime.now(fuso_brasil).date()
  dia_hoje_iso = hoje_br.strftime("%Y-%m-%d")

  compromissos = plano_2027.get("compromissos_calendario", [])
  itens_por_data = {}
  for item in compromissos:
    dt_str = str(item.get("data", "")).strip()
    if dt_str:
      itens_por_data.setdefault(dt_str, []).append(item)

  opcoes_meses = []
  cur_ano, cur_mes = hoje_br.year, hoje_br.month
  for _ in range(14):
    opcoes_meses.append((cur_ano, cur_mes))
    if cur_mes == 12:
      cur_ano += 1
      cur_mes = 1
    else:
      cur_mes += 1

  meses_pt = {
      1: "Jan",
      2: "Fev",
      3: "Mar",
      4: "Abr",
      5: "Mai",
      6: "Jun",
      7: "Jul",
      8: "Ago",
      9: "Set",
      10: "Out",
      11: "Nov",
      12: "Dez",
  }

  col_visao, col_mes, col_filtro = st.columns([1.2, 1.4, 1.4])
  with col_visao:
    modo_calendario = st.radio(
        "Visualização do Calendário:",
        ["Mensal", "Anual"],
        horizontal=True,
        key="modo_cal_2027",
    )
  with col_mes:
    periodo_selecionado = st.selectbox(
        "Mês e Ano (Vigente / Próximos):",
        options=opcoes_meses,
        format_func=lambda ym: f"{meses_pt[ym[1]]} {ym[0]}",
        index=0,
        key="mes_cal_2027",
    )
  with col_filtro:
    filtro_tipo = st.selectbox(
        "Filtrar Compromissos:",
        ["Todos", "Liderança", "Evento"],
        key="filtro_cal_2027",
    )

  itens_filtrados = {}
  for dt_key, lista_ev in itens_por_data.items():
    filtrados = [
        ev
        for ev in lista_ev
        if filtro_tipo == "Todos" or ev.get("tipo") == filtro_tipo
    ]
    if filtrados:
      itens_filtrados[dt_key] = filtrados

  st.caption(
      "Legenda: **LDD** = Compromisso da Liderança | **EVT** = Evento do"
      " Ministério | Texto em laranja = Feriado"
  )

  if modo_calendario == "Mensal":
    ano_sel, mes_sel = periodo_selecionado
    feriados_sel = _feriados_nacionais_por_ano(ano_sel)
    st.markdown(
        _renderizar_grade_mensal_html(
            ano_sel,
            mes_sel,
            itens_filtrados,
            feriados_ano=feriados_sel,
            destaque_mes=True,
            dia_hoje_iso=dia_hoje_iso,
        ),
        unsafe_allow_html=True,
    )
    prefixo_mes = f"{ano_sel:04d}-{mes_sel:02d}-"
    lista_mes = [
        c
        for c in compromissos
        if str(c.get("data", "")).startswith(prefixo_mes)
        and (filtro_tipo == "Todos" or c.get("tipo") == filtro_tipo)
    ]
    feriados_mes = [
        (dt_k, nom_f)
        for dt_k, nom_f in sorted(feriados_sel.items())
        if dt_k.startswith(prefixo_mes)
    ]

    if lista_mes:
      st.markdown(f"**Compromissos e Eventos do Mês ({len(lista_mes)}):**")
      for c in sorted(lista_mes, key=lambda x: str(x.get("data", ""))):
        try:
          data_br = datetime.strptime(c["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
          data_br = c.get("data", "")
        st.markdown(
            f"- **{data_br}** `[{c.get('sigla', 'EVT')}]` — **{c.get('titulo')}** ({c.get('tipo')}): {c.get('observacao', '')}"
        )
    else:
      st.info(
          f"Nenhum compromisso ou evento marcado em {meses_pt[mes_sel]} {ano_sel} —"
          " você pode planejar algo abaixo!"
      )

    if feriados_mes:
      st.markdown("**Feriados Marcados no Mês:**")
      for dt_k, nom_f in feriados_mes:
        data_br = datetime.strptime(dt_k, "%Y-%m-%d").strftime("%d/%m/%Y")
        st.markdown(f"- **{data_br}:** {nom_f}")
  else:
    ano_anual = periodo_selecionado[0]
    feriados_anual = _feriados_nacionais_por_ano(ano_anual)
    for linha_mes in range(0, 12, 3):
      cols_ano = st.columns(3)
      for idx_col in range(3):
        m_num = linha_mes + idx_col + 1
        with cols_ano[idx_col]:
          st.markdown(
              _renderizar_grade_mensal_html(
                  ano_anual,
                  m_num,
                  itens_filtrados,
                  feriados_ano=feriados_anual,
                  destaque_mes=False,
                  dia_hoje_iso=dia_hoje_iso,
              ),
              unsafe_allow_html=True,
          )

    st.markdown(f"**Resumo de Compromissos e Eventos ({ano_anual}):**")
    if compromissos:
      linhas_resumo = []
      for c in sorted(compromissos, key=lambda x: str(x.get("data", ""))):
        if not str(c.get("data", "")).startswith(f"{ano_anual:04d}-"):
          continue
        if filtro_tipo != "Todos" and c.get("tipo") != filtro_tipo:
          continue
        try:
          data_br = datetime.strptime(c["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
          data_br = c.get("data", "")
        linhas_resumo.append({
            "Data": data_br,
            "Sigla": c.get("sigla", "EVT"),
            "Tipo": c.get("tipo", "Evento"),
            "Compromisso / Evento": c.get("titulo", ""),
            "Observação": c.get("observacao", ""),
        })
      if linhas_resumo:
        st.dataframe(pd.DataFrame(linhas_resumo), use_container_width=True, hide_index=True)

  st.markdown("#### ➕ Planejar / Adicionar Compromisso da Liderança ou Evento")
  with st.form("form_novo_compromisso_2027", clear_on_submit=True):
    c1, c2, c3 = st.columns([1.2, 1.2, 1.6])
    with c1:
      data_padrao_form = (
          datetime(hoje_br.year, 12, 12)
          if (hoje_br.year, hoje_br.month) == (2026, 11)
          else datetime(2027, 6, 12)
      )
      data_novo_ev = st.date_input(
          "Data do Compromisso / Evento",
          value=data_padrao_form,
          min_value=datetime(hoje_br.year, hoje_br.month, 1),
          max_value=datetime(2027, 12, 31),
      )
    with c2:
      tipo_novo_ev = st.selectbox(
          "Categoria", ["Liderança", "Evento"], key="tipo_novo_comp_2027"
      )
    with c3:
      sigla_padrao = "LDD" if tipo_novo_ev == "Liderança" else "EVT"
      sigla_novo_ev = st.text_input(
          "Sigla no Calendário (até 4 letras)", value=sigla_padrao, max_chars=4
      )

    titulo_novo_ev = st.text_input(
        "Título do Compromisso da Liderança ou Evento",
        placeholder="Ex.: Encontro de Casais em Dezembro / Reunião de Liderança",
    )
    obs_novo_ev = st.text_input(
        "Observação / Detalhes",
        placeholder="Local, horário, pauta ou observação pastoral",
    )
    enviou_ev = st.form_submit_button("Adicionar ao Calendário e Salvar no Neon")

    if enviou_ev:
      if titulo_novo_ev.strip():
        cor_ev = "#2563eb" if tipo_novo_ev == "Liderança" else "#22c55e"
        novo_item = {
            "data": data_novo_ev.strftime("%Y-%m-%d"),
            "sigla": (sigla_novo_ev.strip().upper() or sigla_padrao)[:4],
            "titulo": titulo_novo_ev.strip(),
            "tipo": tipo_novo_ev,
            "cor": cor_ev,
            "observacao": obs_novo_ev.strip(),
        }
        plano_2027.setdefault("compromissos_calendario", []).append(novo_item)
        plano_2027["atualizado_em"] = datetime.now(fuso_brasil).strftime(
            "%d/%m/%Y %H:%M"
        )
        if salvar_planejamento_2027(plano_2027):
          st.success("✅ Compromisso/evento adicionado e salvo no Neon!")
          st.rerun()
      else:
        st.warning("⚠️ Informe o título do compromisso ou evento.")


def _buscar_json_github(caminho_arquivo):
  """Busca um arquivo JSON direto do GitHub (Raw/API) para sincronizar em outros dispositivos/locais."""
  headers = {"Accept": "application/vnd.github.v3.raw"}
  if GITHUB_TOKEN.strip():
    headers["Authorization"] = f"token {GITHUB_TOKEN.strip()}"
  url_raw = (
      f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{caminho_arquivo}"
  )
  res = requests.get(url_raw, headers=headers, timeout=4)
  if res.status_code == 200:
    return res.json()
  return None


def salvar_no_github(caminho_arquivo):
  """Envia o arquivo atualizado automaticamente para o GitHub via API."""
  if not GITHUB_TOKEN.strip():
    st.warning(
        "⚠️ GITHUB_TOKEN não configurado em .streamlit/secrets.toml ou"
        " st.secrets. Os dados foram salvos no Neon e localmente."
    )
    return False

  try:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{caminho_arquivo}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN.strip()}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers, timeout=5)
    sha = response.json().get("sha") if response.status_code == 200 else None

    with open(caminho_arquivo, "rb") as f:
      conteudo_bytes = f.read()
      conteudo_base64 = base64.b64encode(conteudo_bytes).decode("utf-8")

    payload = {
        "message": (
            f"Atualização automática de dados via Painel - {caminho_arquivo}"
        ),
        "content": conteudo_base64,
        "branch": BRANCH,
    }
    if sha:
      payload["sha"] = sha

    res = requests.put(url, headers=headers, json=payload, timeout=8)
    if res.status_code in [200, 201]:
      st.session_state["dados_painel_cache"] = None
      st.success(
          "✅ Salvo no Neon, localmente e sincronizado com o GitHub com sucesso!"
      )
      return True
    else:
      st.error(f"❌ Erro ao enviar para o GitHub ({res.status_code}): {res.text}")
      return False
  except Exception as e:
    st.error(f"❌ Erro de conexão com o GitHub: {e}")
    return False


@st.cache_data(ttl=600, show_spinner=False)
def _buscar_devocional_cacheado(data_formatada, mes_str, ano_str, dia_num_str):
  """Busca o devocional com cache de 10 minutos para não travar o carregamento da página."""
  meses_pt = {
      "01": "Janeiro",
      "02": "Fevereiro",
      "03": "Março",
      "04": "Abril",
      "05": "Maio",
      "06": "Junho",
      "07": "Julho",
      "08": "Agosto",
      "09": "Setembro",
      "10": "Outubro",
      "11": "Novembro",
      "12": "Dezembro",
  }
  mes_nome = meses_pt.get(mes_str, "")
  string_data_hoje = f"{dia_num_str} de {mes_nome} de {ano_str}"
  url = f"https://www.devocionaldiario.com.br/index.php?mes={mes_str}&ano={ano_str}"

  try:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=2.5)
    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")
      texto_isolado = ""

      for p in soup.find_all(["p", "div", "span", "b", "strong"]):
        if string_data_hoje in p.text:
          bloco = p.find_parent(["div", "article", "section"])
          if bloco:
            texto_isolado = bloco.text.strip()
            for d_ant in [
                "06 de ",
                "6 de ",
                "05 de ",
                "5 de ",
                "Papel de Parede",
                "Download",
            ]:
              if d_ant in texto_isolado:
                texto_isolado = texto_isolado.split(d_ant)[0].strip()
            break

      if not texto_isolado:
        primeiro_p = soup.find("p")
        if primeiro_p:
          texto_isolado = primeiro_p.text.strip()

      return {
          "data": data_formatada,
          "titulo": f"Devocional Diário — {data_formatada}",
          "versiculo": "Palavra de Reflexão para Hoje",
          "texto": (
              texto_isolado
              if texto_isolado
              else "Reflexão diária indisponível no momento."
          ),
          "link_site": url,
      }
  except Exception:
    pass

  return {
      "data": data_formatada,
      "titulo": f"Devocional Diário — {data_formatada}",
      "versiculo": '"Melhor serem dois do que um..." — Eclesiastes 4:9',
      "texto": "Reflexão diária disponível em devocionaldiario.com.br.",
      "link_site": "https://www.devocionaldiario.com.br",
  }


def buscar_devocional_automatico():
  """Busca o devocional da data atual do Brasil com cache."""
  fuso_brasil = timezone(timedelta(hours=-3))
  hoje = datetime.now(fuso_brasil)
  return _buscar_devocional_cacheado(
      hoje.strftime("%d/%m/%Y"),
      hoje.strftime("%m"),
      hoje.strftime("%Y"),
      str(int(hoje.strftime("%d"))),
  )


def carregar_dados_painel(forcar_github=False):
  """Carrega dados combinando local, GitHub (quando solicitado ou sem dado local) e Neon, com cache."""
  if (
      not forcar_github
      and "dados_painel_cache" in st.session_state
      and isinstance(st.session_state["dados_painel_cache"], dict)
  ):
    return st.session_state["dados_painel_cache"]

  dados_local = {}
  if os.path.exists(ARQUIVO_DADOS):
    try:
      with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        dados_local = json.load(f)
    except Exception:
      dados_local = {}

  dados_github = {}
  if forcar_github or not dados_local:
    try:
      remoto = _buscar_json_github(ARQUIVO_DADOS)
      if isinstance(remoto, dict):
        dados_github = remoto
        try:
          with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
            json.dump(dados_github, f, ensure_ascii=False, indent=4)
        except Exception:
          pass
    except Exception:
      pass

  dados_neon = {}
  conn = _conectar_neon()
  if conn is not None:
    try:
      with conn.cursor() as cur:
        cur.execute("SELECT chave, payload FROM conteudo_painel")
        for chave, payload in cur.fetchall():
          if isinstance(payload, dict):
            dados_neon[str(chave)] = payload
    except Exception as e:
      try:
        conn.rollback()
      except Exception:
        pass
      print(f"Aviso ao carregar conteudo_painel do Neon: {e}")

  resultado = dict(dados_local)
  resultado.update(dados_github)
  resultado.update(dados_neon)
  st.session_state["dados_painel_cache"] = resultado
  return resultado


def salvar_dados_painel(dados_dict, sincronizar_github=True):
  """Salva conteúdos no Neon, localmente em JSON e sincroniza com o GitHub."""
  conn = _conectar_neon()
  if conn is not None:
    try:
      with conn.cursor() as cur:
        for chave in ["estudo", "recado", "casais_msg", "devocional"]:
          if chave in dados_dict and isinstance(dados_dict[chave], dict):
            cur.execute(
                """
                                INSERT INTO conteudo_painel (chave, payload, atualizado_em)
                                VALUES (%s, %s, CURRENT_TIMESTAMP)
                                ON CONFLICT (chave) DO UPDATE
                                SET payload = EXCLUDED.payload,
                                    atualizado_em = CURRENT_TIMESTAMP
                            """,
                (chave, Json(dados_dict[chave])),
            )
      conn.commit()
    except Exception as e:
      try:
        conn.rollback()
      except Exception:
        pass
      st.error(f"❌ Erro ao salvar conteúdo no Neon: {e}")

  try:
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
      json.dump(dados_dict, f, ensure_ascii=False, indent=4)
  except Exception as e:
    st.warning(f"⚠️ Aviso ao salvar {ARQUIVO_DADOS} localmente: {e}")

  st.session_state["dados_painel_cache"] = dict(dados_dict)

  if sincronizar_github:
    salvar_no_github(ARQUIVO_DADOS)


# --- CARREGAMENTO DE DADOS ---
dados = carregar_dados_painel()

if "estudo" not in dados:
  dados["estudo"] = {"destino": "Toda a Igreja", "texto": ""}
if "recado" not in dados:
  dados["recado"] = {"destino": "Toda a Igreja", "texto": ""}
if "casais_msg" not in dados:
  dados["casais_msg"] = {"texto": ""}

fuso_brasil = timezone(timedelta(hours=-3))
data_hoje = datetime.now(fuso_brasil).strftime("%d/%m/%Y")

dev_atual = dados.get("devocional", {})
if not isinstance(dev_atual, dict) or dev_atual.get("data") != data_hoje:
  dados["devocional"] = buscar_devocional_automatico()
  salvar_dados_painel(dados, sincronizar_github=False)

# --- INTERFACE DO PAINEL (RESTRITA À LIDERANÇA) ---
col_tit, col_sync = st.columns([3.5, 1.2])
with col_tit:
  st.title("Painel de Controle: App Oficial")
  st.write(
      "Acesso exclusivo para a liderança autorizada (uso via computador ou"
      " celular)."
  )
with col_sync:
  st.write("")
  if st.button("🔄 Atualizar do GitHub", use_container_width=True):
    st.session_state.pop("dados_painel_cache", None)
    st.session_state.pop("plano_2027_cache", None)
    _obter_conexao_cacheada.clear()
    carregar_dados_painel(forcar_github=True)
    st.rerun()

menu_lateral = st.sidebar.selectbox(
    "Selecione o Painel de Gestão:",
    [
        "Área Pastoral",
        "Liderança de Casais",
        "Planejamento Estratégico 2027",
    ],
)

if st.sidebar.button("🔒 Bloquear / Sair do Painel"):
  st.session_state["senha_pastoral_ok"] = False
  st.session_state["senha_casais_ok"] = False
  st.rerun()

# --- CONTROLE DE EXIBIÇÃO DA BARRA LATERAL (Acompanhamento) ---
autorizado_painel = (
    (menu_lateral == "Área Pastoral" and st.session_state["senha_pastoral_ok"])
    or (
        menu_lateral == "Liderança de Casais"
        and st.session_state["senha_casais_ok"]
    )
    or (
        menu_lateral == "Planejamento Estratégico 2027"
        and (
            st.session_state["senha_pastoral_ok"]
            or st.session_state["senha_casais_ok"]
        )
    )
)

if autorizado_painel:
  st.sidebar.markdown("---")
  st.sidebar.header("📝 Registrar Acompanhamento")

  df_lista_casais = db.obter_df_processado()
  lideres_manuais = db.carregar_lideres_json()
  lista_nomes_casais = []
  if not df_lista_casais.empty:
    col_n1 = db.obter_coluna_segura(
        df_lista_casais, ["Nome completo", "Nome"], 1
    )
    col_n2 = db.obter_coluna_segura(
        df_lista_casais, ["cônjuge", "conjuge"], 7
    )
    for _, row in df_lista_casais.iterrows():
      chave_r = db.obter_chave_unica(row)
      eh_lider_manual = lideres_manuais.get(chave_r)
      if eh_lider_manual is not None:
        eh_lider = bool(eh_lider_manual)
      else:
        eh_lider = str(row.get("Perfil", "")).strip() == "⭐ Líder"

      if eh_lider:
        continue

      n1 = str(row.get(col_n1, "")).strip()
      n2 = str(row.get(col_n2, "")).strip()
      if n1 and n2 and n2.lower() != "nan":
        lista_nomes_casais.append(f"{n1} & {n2}")
      elif n1 and n1.lower() != "nan":
        lista_nomes_casais.append(n1)

  casal_selecionado = st.sidebar.selectbox(
      "Casal Sendo Acompanhado",
      lista_nomes_casais
      if lista_nomes_casais
      else ["Nenhum casal disponível para acompanhamento"],
  )

  lideres_disponiveis = [
      "Marcelo & Gilmara",
      "Tony & Jessica",
      "Bruno & Marluce",
      "Jessica & Arlindo",
      "Thiago & Amanda",
  ]
  lider_responsavel = st.sidebar.selectbox(
      "Casal Líder Responsável", lideres_disponiveis
  )
  tipo_atendimento = st.sidebar.selectbox(
      "Tipo de Atendimento", ["Aconselhamento", "Visita no Lar"]
  )
  motivo_atendimento = st.sidebar.selectbox(
      "Foco / Desafio do Atendimento",
      [
          "Brigas Conjugais / Conflitos",
          "Infidelidade",
          "Violência Doméstica",
          "Vícios",
          "Processo de Separação",
          "Outros / Geral",
      ],
  )

  data_atendimento = st.sidebar.text_input(
      "Data do Atendimento (DD/MM/AAAA)",
      value=datetime.now(fuso_brasil).strftime("%d/%m/%Y"),
  )
  descricao_atendimento = st.sidebar.text_area(
      "Detalhes (Oração, orientações, auxílio, etc.)", height=80
  )

  if st.sidebar.button("Salvar Registro de Acompanhamento"):
    if casal_selecionado and casal_selecionado not in [
        "Nenhum casal cadastrado",
        "Nenhum casal disponível para acompanhamento",
    ]:
      conn = _conectar_neon()
      if conn is not None:
        try:
          with conn.cursor() as cursor:
            cursor.execute(
                """
                                INSERT INTO registros_acompanhamento
                                    (casal_alvo, casal_lider, tipo, motivo, data_atendimento, descricao)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                (
                    casal_selecionado,
                    lider_responsavel,
                    tipo_atendimento,
                    motivo_atendimento,
                    data_atendimento,
                    descricao_atendimento,
                ),
            )
          conn.commit()
          st.sidebar.success(
              "✅ Acompanhamento registrado no Neon com sucesso!"
          )
        except Exception as e:
          try:
            conn.rollback()
          except Exception:
            pass
          st.sidebar.error(f"❌ Erro ao salvar no Neon: {e}")
      else:
        st.sidebar.error("❌ Não foi possível conectar ao Neon.")
    else:
      st.sidebar.error("❌ Selecione um casal válido para registrar.")


# --- LÓGICA DAS ABAS DO PAINEL ---

if menu_lateral == "Área Pastoral":
  st.header("🔒 Acesso Restrito - Área Pastoral")
  senha_digitada = st.text_input(
      "Senha Pastoral", type="password", key="input_senha_pastoral"
  )

  if senha_digitada == SENHA_PASTORAL:
    if not st.session_state["senha_pastoral_ok"]:
      st.session_state["senha_pastoral_ok"] = True
      st.rerun()
  elif senha_digitada:
    if st.session_state["senha_pastoral_ok"]:
      st.session_state["senha_pastoral_ok"] = False
      st.rerun()
    st.error("❌ Senha incorreta!")

  if st.session_state["senha_pastoral_ok"]:
    st.success("Acesso autorizado!")

    st.markdown("---")
    st.header("⭐ Gestão de Liderança de Casais")
    df_casais = db.obter_df_processado()
    gestao_lideres.renderizar_painel_lideranca(
        df_casais, "Nome completo", "cônjuge"
    )

    st.markdown("---")
    st.header("Esboço / Estudo da Palavra")
    destino_estudo = st.radio(
        "Destino do estudo:",
        ["Toda a Igreja", "Apenas para os Casais"],
        key="dest_est",
    )
    texto_estudo = st.text_area(
        "Sugestão de Estudo",
        value=dados.get("estudo", {}).get("texto", ""),
        height=100,
    )

    st.header("Recados e Avisos do Pastor")
    destino_recado = st.radio(
        "Destino do recado:",
        ["Toda a Igreja", "Apenas para os Casais"],
        key="dest_rec",
    )
    texto_recado = st.text_area(
        "Mensagem ou Aviso",
        value=dados.get("recado", {}).get("texto", ""),
        height=100,
    )

    if st.button("Salvar Alterações Pastorais"):
      dados["estudo"] = {"destino": destino_estudo, "texto": texto_estudo}
      dados["recado"] = {"destino": destino_recado, "texto": texto_recado}
      salvar_dados_painel(dados, sincronizar_github=True)
  else:
    st.info("Digite a senha pastoral para liberar a edição.")

elif menu_lateral == "Liderança de Casais":
  st.header("🔒 Acesso Restrito - Ministério de Casais")
  senha_digitada_casais = st.text_input(
      "Senha Liderança de Casais", type="password", key="input_senha_casais"
  )

  if senha_digitada_casais == SENHA_CASAIS:
    if not st.session_state["senha_casais_ok"]:
      st.session_state["senha_casais_ok"] = True
      st.rerun()
  elif senha_digitada_casais:
    if st.session_state["senha_casais_ok"]:
      st.session_state["senha_casais_ok"] = False
      st.rerun()
    st.error("❌ Senha incorreta!")

  if st.session_state["senha_casais_ok"]:
    st.success("Acesso autorizado!")

    texto_casais = st.text_area(
        "Recado / Mensagem Exclusiva para o Casal",
        value=dados.get("casais_msg", {}).get("texto", ""),
        height=100,
    )

    st.subheader("Gerenciamento do Devocional Diário (Automático)")
    dev_atual = dados.get("devocional", buscar_devocional_automatico())

    edit_titulo = st.text_input(
        "Título do Devocional", value=dev_atual.get("titulo", "")
    )
    edit_versiculo = st.text_input(
        "Versículo Base", value=dev_atual.get("versiculo", "")
    )
    edit_texto = st.text_area(
        "Reflexão / Mensagem", value=dev_atual.get("texto", ""), height=100
    )
    edit_link = st.text_input(
        "Link do Site Oficial", value=dev_atual.get("link_site", "")
    )

    if st.button("Salvar Alterações de Casais"):
      dados["casais_msg"] = {"texto": texto_casais}
      dados["devocional"] = {
          "data": datetime.now(fuso_brasil).strftime("%d/%m/%Y"),
          "titulo": edit_titulo,
          "versiculo": edit_versiculo,
          "texto": edit_texto,
          "link_site": edit_link,
      }
      salvar_dados_painel(dados, sincronizar_github=True)

    st.markdown("---")
    st.subheader("📋 Relação Geral de Casais Cadastrados")
    df_casais = db.obter_df_processado()
    if not df_casais.empty:

      def destacar_lideranca(val):
        if str(val) == "⭐ Líder":
          return (
              "background-color: #d4edda; color: #155724; font-weight: bold;"
          )
        return ""

      try:
        st.dataframe(
            df_casais.style.map(destacar_lideranca, subset=["Perfil"]),
            use_container_width=True,
        )
      except Exception:
        st.dataframe(df_casais, use_container_width=True)
  else:
    st.info("Digite a senha da liderança de casais para liberar o painel.")

elif menu_lateral == "Planejamento Estratégico 2027":
  st.header("🗓️ Planejamento Estratégico 2027 — Ministério de Casais")
  if not (
      st.session_state["senha_pastoral_ok"]
      or st.session_state["senha_casais_ok"]
  ):
    st.warning(
        "🔒 Acesso restrito à liderança. Autentique-se na **Área Pastoral** ou"
        " **Liderança de Casais** para visualizar e editar o planejamento."
    )
  else:
    plano_2027 = carregar_planejamento_2027()

    renderizar_calendario_planejamento_2027(plano_2027)

    st.markdown("---")
    fundamento = plano_2027.get("fundamento", {})
    st.info(
        f"**{fundamento.get('titulo', 'Amor como Fundamento')}**"
        f" ({fundamento.get('versiculo', '1 Coríntios 13:1-2')}): "
        f"{fundamento.get('texto', '')}"
    )

    st.subheader("👥 4 Grupos-Alvo")
    for grp in plano_2027.get("grupos_alvo", []):
      st.markdown(
          f"- **{grp.get('nome')}** ({grp.get('publico')}): {grp.get('foco')}"
      )

    st.subheader("📚 6 Módulos Bimestrais (2027)")
    df_mod = pd.DataFrame(plano_2027.get("modulos_bimestrais", []))
    if not df_mod.empty:
      st.dataframe(df_mod, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("⏱️ Ciclo de Prazos e Oração")
    for etapa in plano_2027.get("ciclo_prazos", []):
      st.write(etapa)
    st.write(
        f"**Calendário de Oração:** {plano_2027.get('calendario_oracao', '')}"
    )

    st.subheader("🎉 Datas em Destaque — 2027")
    for dt_item in plano_2027.get("datas_comemorativas_2027", []):
      st.markdown(
          f"- **{dt_item.get('data')} — {dt_item.get('evento')}:**"
          f" {dt_item.get('sugestao')}"
      )

    st.markdown("---")
    st.subheader("✏️ Atualizar Calendário de Oração / Observações 2027")
    novo_oracao = st.text_area(
        "Calendário de Oração",
        value=plano_2027.get("calendario_oracao", ""),
        height=80,
    )
    if st.button("Salvar Planejamento 2027 no Neon"):
      plano_2027["calendario_oracao"] = novo_oracao
      plano_2027["atualizado_em"] = datetime.now(fuso_brasil).strftime(
          "%d/%m/%Y %H:%M"
      )
      if salvar_planejamento_2027(plano_2027):
        st.success("✅ Planejamento Estratégico 2027 atualizado no Neon!")