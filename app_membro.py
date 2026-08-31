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

# --- INJEÇÃO DE METADADOS PWA E ESTILOS GERAIS ---
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
.stApp { background-color: #FFFFFF; }
</style>
"""
st.markdown(pwa_code, unsafe_allow_html=True)

# --- ESTILO CSS EXATO PARA OS BOTÕES (COMPACTOS E CENTRALIZADOS) ---
st.markdown(
    """
    <style>
    .stLinkButton > a {
        display: block;
        text-align: center;
        margin: 0 auto;
        width: 35%;                   /* Largura compacta igual ao print */
        background-color: #ff4b4b;
        color: white !important;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        text-decoration: none;
    }
    .stLinkButton > a:hover {
        background-color: #ff2121;
        color: white !important;
        text-decoration: none;
    }
    </style>
""",
    unsafe_allow_html=True,
)

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
st.markdown(
    "<h1 style='text-align: center; color: #1e3d59;'>Aliança Eterna</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; font-size: 1.1em;'>Aplicativo Oficial da Família e do Ministério de Casais</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# Seção: Recado da Pastoral / Geral
st.subheader("📢 Recado da Pastoral")
st.info(
    dados.get("recado_igreja", "Nenhum recado no momento.")
)

st.markdown("---")

# Seção: Transmissões e Cultos Ao Vivo
st.subheader("📺 Transmissões e Cultos Ao Vivo")
st.markdown(
    "Acompanhe nossos cultos, avisos e a programação oficial no Instagram da"
    " igreja:"
)
st.link_button(
    "📸 Acessar Instagram @admucuripe", "https://instagram.com/admucuripe"
)

st.markdown("---")

# Seção: Devocional de Casais
st.subheader("📖 Devocional de Casais")
st.success(dados.get("devocional_casais", "Nenhum devocional cadastrado."))

st.subheader("📢 Recado Direto aos Casais")
st.warning(dados.get("recado_casais", "Nenhum recado específico para os casais."))

st.markdown("---")

# Seção: Participação e Cadastros
st.subheader("📝 Participação e Cadastros")
st.markdown(
    "Deseja atualizar seus dados ou participar ativamente da nossa rede de"
    " casais? Clique no botão abaixo:"
)
st.link_button(
    "📝 Preencher Formulário / Cadastro", "https://forms.gle/exemplo"
)