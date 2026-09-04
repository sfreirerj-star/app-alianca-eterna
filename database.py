import json
import os
import re
import pandas as pd
import streamlit as st


# --- FUNÇÕES DE GERENCIAMENTO DE LÍDERES (JSON) ---
def carregar_lideres_json():
  caminho = "lideres_config.json"
  if os.path.exists(caminho):
    try:
      with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def salvar_lideres_json(dados):
  caminho = "lideres_config.json"
  try:
    with open(caminho, "w", encoding="utf-8") as f:
      json.dump(dados, f, ensure_ascii=False, indent=4)
  except Exception as e:
    print(f"Erro ao salvar líderes: {e}")


def obter_chave_unica(row):
  """Gera uma chave única e segura baseada em dados fixos do casal (nome e e-mail/telefone)."""
  try:
    n1 = str(row.get("Nome completo", row.get("Nome", ""))).strip().lower()
    contato = str(
        row.get("Endereço de e-mail", row.get("E-mail:", row.get("Telefone", "")))
    ).strip().lower()
    return f"{n1}_{contato}"
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
def obter_df_processado():
  """Carrega a base de dados (planilha/Excel/CSV) e aplica o status de liderança global atualizado."""
  
  # ATENÇÃO: Substitua 'dados_casais.xlsx' pelo nome real do seu arquivo de dados principal, 
  # ou ajuste caso utilize outra fonte (ex: Google Sheets, CSV, etc.)
  caminho_base = "dados_casais.xlsx"
  
  try:
    if os.path.exists(caminho_base):
      df = pd.read_excel(caminho_base)
    else:
      # Fallback caso a planilha não esteja na raiz, tenta buscar do session_state ou cria um DF de exemplo
      df = st.session_state.get("df_original", pd.DataFrame())
  except Exception:
    df = pd.DataFrame()

  if df.empty:
    # DataFrame de segurança para evitar quebreiras caso a planilha esteja vazia/ausente
    df = pd.DataFrame({
        "Perfil": ["⭐ Líder", "Casal"],
        "Carimbo de data/hora": ["14/07/2025 22:25:41", "31/05/2026 19:35:32"],
        "Endereço de e-mail": ["sfreirerj@hotmail.com", "sinvaladvogado@gmail.com"],
        "Nome completo": ["Marcelo dos Santos Freire", "Sinval Andrade Delfino dos Santos"],
        "Data de Nascimento": ["02/06/1969", "02/09/1972"],
        "Endereço": ["Rua José Affonso Neto, 50 - Recreio", "Estrada do Viegas, 9"],
        "E-mail:": ["sfreirerj@hotmail.com", "sinvaladvogado@gmail.com"],
        "cônjuge": ["Gilmara Pinto Freire", "Renata Brandão"]
    })

  # Garante que a coluna 'Perfil' exista
  if "Perfil" not in df.columns:
    df.insert(0, "Perfil", "Casal")

  # Sincroniza e carrega o dicionário de líderes manuais do JSON / Session State
  if "lideres_manuais" not in st.session_state:
    st.session_state["lideres_manuais"] = carregar_lideres_json()

  lideres_dict = st.session_state["lideres_manuais"]

  # Aplica o status de líder ou casal de forma rigorosa em cada linha
  for idx, row in df.iterrows():
    chave = obter_chave_unica(row)
    
    if chave in lideres_dict:
      eh_lider = lideres_dict[chave]
      df.loc[idx, "Perfil"] = "⭐ Líder" if eh_lider else "Casal"
    else:
      # Se não estiver no JSON customizado, normaliza o valor existente na base
      val_atual = str(row.get("Perfil", ""))
      if "líder" in val_atual.lower() or "⭐" in val_atual:
        df.loc[idx, "Perfil"] = "⭐ Líder"
      else:
        df.loc[idx, "Perfil"] = "Casal"

  return df