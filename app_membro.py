import json
import os
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Aliança Eterna",
    page_icon="📖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- INJEÇÃO DE METADADOS PWA E ESTILOS ---
pwa_code = """
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#1e3d59">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Aliança Eterna">
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(pwa_code, unsafe_allow_html=True)

# --- GERENCIAMENTO DE DADOS (LENDO DO JSON DO PAINEL) ---
ARQUIVO_DADOS = "dados_painel.json"


def carregar_dados():
  if os.path.exists(ARQUIVO_DADOS):
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
      try:
        return json.load(f)
      except:
        pass
  return {
      "estudo_palavra": "Carregando...",
      "recado_igreja": "Carregando...",
      "devocional_casais": "Carregando...",
      "recado_casais": "Carregando...",
  }


dados = carregar_dados()

# --- INTERFACE DO APLICATIVO ---
st.title("📖 Aliança Eterna")
st.markdown("---")

# Seção de Estudo
st.subheader("📖 Esboço / Estudo da Palavra")
st.write(dados.get("estudo_palavra", "Nenhum estudo cadastrado no momento."))

st.markdown("---")

# Seção de Transmissões
st.subheader("📺 Transmissões e Cultos Ao Vivo")
st.markdown(
    "Acompanhe nossos cultos, avisos e a programação oficial no Instagram da"
    " igreja:"
)
st.link_button(
    "📸 Acessar Instagram @admucuripe", "https://instagram.com/admucuripe"
)

st.markdown("---")

# Seção de Casais
st.subheader("💍 Devocional e Mensagens para os Casais")
st.info(
    dados.get(
        "devocional_casais",
        "Nenhum devocional cadastrado para hoje.",
    )
)

st.subheader("📢 Recado Direto aos Casais")
st.warning(
    dados.get("recado_casais", "Nenhum recado específico no momento.")
)

st.markdown("---")
st.subheader("📝 Participação e Cadastros")
st.markdown(
    "Venha fazer parte do ministério de casais da igreja (Aliança Eterna),"
    " preencha o formulário de cadastro aqui:"
)
st.link_button(
    "📝 Preencher Formulário / Cadastro", "https://forms.gle/exemplo"
)