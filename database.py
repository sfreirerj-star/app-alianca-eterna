from datetime import datetime
import re
import unicodedata
import pandas as pd
import streamlit as st

LINK_PLANILHA_GOOGLE = "https://docs.google.com/spreadsheets/d/1Zy2qTGHHqzLhim_ebHsCFgNrHBzPB1AxSscoQZXh3Vc/export?format=csv"

LIDERES_OFICIAIS = [
    "marcelo",
    "gilmara",
    "bruno",
    "marluce",
    "thiago",
    "amanda",
    "tony",
    "jessica",
    "arlindo",
]


def remover_acentos(texto):
  return "".join(
      c
      for c in unicodedata.normalize("NFD", str(texto))
      if unicodedata.category(c) != "Mn"
  ).lower()


# Removido o cache estático puro e adicionado controle baseado na versão do session_state
def carregar_dados_brutos():
  try:
    if "COLOQUE_SEU_LINK" in LINK_PLANILHA_GOOGLE:
      return pd.DataFrame()

    # Força a leitura direta da planilha sem cache rígido para evitar dessincronização
    df = pd.read_csv(LINK_PLANILHA_GOOGLE)
    return df
  except Exception:
    return pd.DataFrame()


def obter_chave_unica(row):
  n1 = (
      str(row.get("Nome completo:", row.iloc[1] if len(row) > 1 else ""))
      .strip()
      .upper()
  )
  n2 = (
      str(row.get("Nome do cônjuge:", row.iloc[7] if len(row) > 7 else ""))
      .strip()
      .upper()
  )
  tel = str(row.get("Telefone:", row.iloc[4] if len(row) > 4 else "")).strip()
  return f"{n1}__{n2}__{tel}"


def obter_df_processado():
  df = carregar_dados_brutos().copy()
  if df.empty:
    return df

  perfis = []
  
  # Garante inicialização segura do session_state de líderes manuais
  if "lideres_manuais" not in st.session_state:
    st.session_state["lideres_manuais"] = {}

  lideres_manuais = st.session_state["lideres_manuais"]

  for idx, row in df.iterrows():
    chave = obter_chave_unica(row)

    # 1. A alteração manual tem prioridade absoluta
    if chave in lideres_manuais:
      eh_lider = bool(lideres_manuais[chave])
    else:
      # 2. Regra padrão oficial
      linha_texto = " ".join(str(val).lower() for val in row.values)
      linha_texto_limpa = remover_acentos(linha_texto)
      eh_lider = any(
          remover_acentos(lider) in linha_texto_limpa for lider in LIDERES_OFICIAIS
      )

    perfis.append("⭐ Líder" if eh_lider else "Casal")

  if "Perfil" not in df.columns:
    df.insert(0, "Perfil", perfis)
  else:
    df["Perfil"] = perfis

  df.index = range(1, len(df) + 1)
  return df


def formatar_data_para_br(val):
  if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
    return ""
  if isinstance(val, (pd.Timestamp, datetime)):
    return val.strftime("%d/%m/%Y")

  val_str = str(val).strip()
  try:
    if "-" in val_str and len(val_str.split("-")[0]) == 4:
      dt = datetime.strptime(val_str[:10], "%Y-%m-%d")
      return dt.strftime("%d/%m/%Y")
  except:
    pass
  return val_str


def formatar_exibicao_filhos(texto_filhos):
  if (
      pd.isna(texto_filhos)
      or not str(texto_filhos).strip()
      or str(texto_filhos).lower()
      in ["nan", "não", "nao", "0", "sem filhos", "não temos"]
  ):
    return "Nenhum cadastrado."

  linhas = str(texto_filhos).split("\n")
  resultado_formatado = []
  for linha in linhas:
    linha = linha.strip()
    if not linha:
      continue
    match_data = re.search(r"(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})", linha)
    if match_data:
      data_encontrada = formatar_data_para_br(match_data.group(1))
      nome_encontrado = linha.replace(match_data.group(1), "").strip()
      nome_encontrado = re.sub(r"[\-\–\—\:]\s*$", "", nome_encontrado).strip()
      resultado_formatado.append(
          f"• **Nome Completo:** {nome_encontrado}  |  **Data de"
          f" Nascimento:** {data_encontrada}"
      )
    else:
      resultado_formatado.append(f"• {linha}")
  return "\n\n".join(resultado_formatado)


def obter_coluna_segura(df, nomes_possiveis, indice_fallback):
  for nome in nomes_possiveis:
    for col in df.columns:
      if nome.lower() in col.lower():
        return col
  if len(df.columns) > indice_fallback:
    return df.columns[indice_fallback]
  return df.columns[0]