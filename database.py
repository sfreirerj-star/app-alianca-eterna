import base64
import json
import os
import re
import tomllib
import pandas as pd
import psycopg2
import requests
import streamlit as st

# URL pública da planilha do Google Sheets exportada em CSV
URL_GOOGLE_SHEETS = (
    "https://docs.google.com/spreadsheets/d/1Zy2qTGHHqzLhim_ebHsCFgNrHBzPB1AxSscoQZXh3Vc/export?format=csv"
)

ARQUIVO_LIDERES = "lideres_config.json"


def _obter_segredo_db(chave, padrao=None):
  try:
    if hasattr(st, "secrets") and chave in st.secrets:
      val = str(st.secrets[chave]).strip()
      if val:
        return val
  except Exception:
    pass

  url_env = os.environ.get(chave)
  if url_env and url_env.strip():
    return url_env.strip()

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


# --- LIGAÇÃO AO NEON (POSTGRESQL) ---
def _obter_database_url():
  """Obtém a DATABASE_URL a partir do st.secrets, variáveis de ambiente ou .streamlit/secrets.toml."""
  return _obter_segredo_db("DATABASE_URL", None)


@st.cache_resource(show_spinner=False)
def _obter_conexao_neon_cacheada(url_limpa):
  """Reutiliza uma conexão aberta ao PostgreSQL do Neon e garante a tabela lideres_config."""
  conn = psycopg2.connect(url_limpa, connect_timeout=5)
  with conn.cursor() as cur:
    cur.execute("""
            CREATE TABLE IF NOT EXISTS lideres_config (
                chave_casal TEXT PRIMARY KEY,
                eh_lider BOOLEAN NOT NULL DEFAULT FALSE,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
  conn.commit()
  return conn


def _conectar_neon():
  """Retorna uma ligação ativa ao PostgreSQL do Neon, reconectando se necessário."""
  url = _obter_database_url()
  if not url:
    return None

  url_limpa = url.replace("&channel_binding=require", "").replace(
      "?channel_binding=require&", "?"
  )
  try:
    conn = _obter_conexao_neon_cacheada(url_limpa)
    if conn.closed != 0:
      _obter_conexao_neon_cacheada.clear()
      conn = _obter_conexao_neon_cacheada(url_limpa)
    else:
      try:
        with conn.cursor() as cur:
          cur.execute("SELECT 1")
      except Exception:
        conn.rollback()
        _obter_conexao_neon_cacheada.clear()
        conn = _obter_conexao_neon_cacheada(url_limpa)
    return conn
  except Exception as e:
    print(f"Aviso ao conectar ao Neon em database.py: {e}")
    return None


def _buscar_lideres_github():
  """Busca lideres_config.json diretamente do GitHub para sincronizar em outros locais."""
  repo_owner = _obter_segredo_db("REPO_OWNER", "sfreirerj-star")
  repo_name = _obter_segredo_db("REPO_NAME", "app-alianca-eterna")
  branch = _obter_segredo_db("BRANCH", "main")
  token = _obter_segredo_db("GITHUB_TOKEN", "")

  headers = {"Accept": "application/vnd.github.v3.raw"}
  if token:
    headers["Authorization"] = f"token {token}"

  url_raw = (
      f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/{ARQUIVO_LIDERES}"
  )
  try:
    res = requests.get(url_raw, headers=headers, timeout=4)
    if res.status_code == 200:
      dados = res.json()
      if isinstance(dados, dict):
        return {
            str(k): bool(v) for k, v in dados.items() if isinstance(v, bool)
        }
  except Exception:
    pass
  return {}


def _enviar_lideres_github(dados_limpos):
  """Envia o arquivo lideres_config.json atualizado para o GitHub via API."""
  token = _obter_segredo_db("GITHUB_TOKEN", "")
  if not token:
    return False

  repo_owner = _obter_segredo_db("REPO_OWNER", "sfreirerj-star")
  repo_name = _obter_segredo_db("REPO_NAME", "app-alianca-eterna")
  branch = _obter_segredo_db("BRANCH", "main")

  try:
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{ARQUIVO_LIDERES}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(url, headers=headers, timeout=5)
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    conteudo_base64 = base64.b64encode(
        json.dumps(dados_limpos, ensure_ascii=False, indent=4).encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": f"Atualização automática de liderança - {ARQUIVO_LIDERES}",
        "content": conteudo_base64,
        "branch": branch,
    }
    if sha:
      payload["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=payload, timeout=8)
    return put_resp.status_code in [200, 201]
  except Exception:
    return False


# --- FUNÇÕES DE GERENCIAMENTO DE LÍDERES (NEON + GITHUB + FALLBACK JSON) ---
def _carregar_lideres_json_local():
  """Fallback local caso não exista ligação ativa ao Neon."""
  caminhos = [ARQUIVO_LIDERES, "dados_app.json"]
  for caminho in caminhos:
    if os.path.exists(caminho):
      try:
        with open(caminho, "r", encoding="utf-8") as f:
          dados = json.load(f)
          if isinstance(dados, dict):
            return {
                str(k): bool(v) for k, v in dados.items() if isinstance(v, bool)
            }
      except Exception:
        pass
  return {}


@st.cache_data(ttl=120, show_spinner=False)
def _carregar_lideres_com_cache():
  """Carrega o estado de liderança do Neon, com fallback para GitHub e JSON local."""
  conn = _conectar_neon()
  if conn is not None:
    try:
      with conn.cursor() as cur:
        cur.execute("SELECT chave_casal, eh_lider FROM lideres_config")
        linhas = cur.fetchall()
      if linhas:
        return {str(chave): bool(eh_lider) for chave, eh_lider in linhas}
    except Exception as e:
      try:
        conn.rollback()
      except Exception:
        pass
      print(f"Aviso ao carregar líderes do Neon: {e}")

  dados_local = _carregar_lideres_json_local()
  if dados_local:
    return dados_local

  dados_github = _buscar_lideres_github()
  if dados_github:
    try:
      with open(ARQUIVO_LIDERES, "w", encoding="utf-8") as f:
        json.dump(dados_github, f, ensure_ascii=False, indent=4)
    except Exception:
      pass
    return dados_github

  return {}


def carregar_lideres_json():
  """Retorna o dicionário de liderança atualizado (com cache de 2 minutos)."""
  return dict(_carregar_lideres_com_cache())


def salvar_lideres_json(dados, sincronizar_github=True):
  """Guarda o dicionário de liderança no Neon, localmente em JSON e sincroniza no GitHub."""
  if not isinstance(dados, dict):
    return False

  dados_limpos = {
      str(k): bool(v) for k, v in dados.items() if isinstance(v, bool)
  }

  conn = _conectar_neon()
  if conn is not None:
    try:
      with conn.cursor() as cur:
        for chave, eh_lider in dados_limpos.items():
          cur.execute(
              """
                            INSERT INTO lideres_config (chave_casal, eh_lider, atualizado_em)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (chave_casal) DO UPDATE
                            SET eh_lider = EXCLUDED.eh_lider,
                                atualizado_em = CURRENT_TIMESTAMP
                        """,
              (chave, eh_lider),
          )
      conn.commit()
    except Exception as e:
      try:
        conn.rollback()
      except Exception:
        pass
      print(f"Erro ao salvar líderes no Neon: {e}")

  try:
    with open(ARQUIVO_LIDERES, "w", encoding="utf-8") as f:
      json.dump(dados_limpos, f, ensure_ascii=False, indent=4)
  except Exception as e:
    print(f"Erro ao salvar líderes localmente: {e}")

  _carregar_lideres_com_cache.clear()
  st.session_state["lideres_manuais"] = dict(dados_limpos)

  if sincronizar_github:
    return _enviar_lideres_github(dados_limpos)
  return True


def obter_chave_unica(row):
  """Gera uma chave única compatível com o formato do sistema e do Neon/JSON."""
  try:
    n1 = str(row.get("Nome completo", row.get("Nome", ""))).strip().upper()
    tel = str(row.get("Telefone", row.get("Celular", ""))).strip()
    email = str(row.get("Endereço de e-mail", row.get("E-mail:", ""))).strip()
    return f"{n1}__{tel}__{tel if tel else email}"
  except Exception:
    return str(row.name)


# --- FUNÇÕES DE SEGURANÇA E TRATAMENTO DE COLUNAS ---
def obter_coluna_segura(df, nomes_possiveis, indice_fallback):
  """Busca uma coluna no DataFrame de forma flexível ou recorre ao índice."""
  for nome in nomes_possiveis:
    for col in df.columns:
      if nome.lower() in str(col).lower():
        return col
  if len(df.columns) > indice_fallback:
    return df.columns[indice_fallback]
  return df.columns[0] if not df.empty else None


def formatar_data_para_br(data_str):
  """Padroniza datas para o formato brasileiro DD/MM/AAAA se possível."""
  if pd.isna(data_str) or not str(data_str).strip():
    return ""
  val = str(data_str).strip()
  if "T" in val:
    val = val.split("T")[0]
  match_iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", val)
  if match_iso:
    ano, mes, dia = match_iso.groups()
    return f"{dia}/{mes}/{ano}"
  return val


def formatar_exibicao_filhos(texto_filhos):
  """Formata a exibição dos filhos para o painel de edição/visualização."""
  if not texto_filhos or str(texto_filhos).lower() == "nan":
    return "Nenhum filho registrado."
  return str(texto_filhos).replace("\n", " | ")


# --- FUNÇÃO PRINCIPAL DE PROCESSAMENTO DO DATAFRAME ---
@st.cache_data(ttl=120, show_spinner=False)
def carregar_dados_web():
  try:
    df = pd.read_csv(URL_GOOGLE_SHEETS)
    return df
  except Exception as e:
    st.error(f"Erro ao carregar dados do Google Sheets: {e}")
    return pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def _processar_dataframe_cacheado(lideres_tupla):
  """Processa o DataFrame uma única vez por janela de cache, evitando loop linha a linha em toda interação."""
  lideres_dict = dict(lideres_tupla)
  df = carregar_dados_web().copy()

  if df.empty:
    if os.path.exists("respostas_forms.csv.xlsx"):
      try:
        df = pd.read_excel("respostas_forms.csv.xlsx")
      except Exception:
        pass

  if df.empty:
    return pd.DataFrame()

  if "Perfil" not in df.columns:
    df.insert(0, "Perfil", "Casal")

  perfis = []
  for _, row in df.iterrows():
    chave = obter_chave_unica(row)
    eh_lider = None
    if chave in lideres_dict:
      eh_lider = lideres_dict[chave]
    else:
      for k, v in lideres_dict.items():
        if any(part in k for part in chave.split("__") if len(part) > 3):
          eh_lider = v
          break

    if eh_lider is not None:
      perfis.append("⭐ Líder" if eh_lider else "Casal")
    else:
      val_atual = str(row.get("Perfil", ""))
      if "líder" in val_atual.lower() or "⭐" in val_atual:
        perfis.append("⭐ Líder")
      else:
        perfis.append("Casal")

  df["Perfil"] = perfis
  return df


def obter_df_processado():
  """Puxa os dados atualizados direto do Google Sheets e aplica o status de liderança do Neon/JSON."""
  lideres_dict = carregar_lideres_json()
  st.session_state["lideres_manuais"] = lideres_dict
  lideres_tupla = tuple(sorted(lideres_dict.items()))
  return _processar_dataframe_cacheado(lideres_tupla).copy()