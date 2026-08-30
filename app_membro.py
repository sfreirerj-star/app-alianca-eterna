import json
import os
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Aliança Eterna",
    page_icon="💍",
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
ARQUIVO_DADOS = "dados_app.json"


def carregar_dados():
  if os.path.exists(ARQUIVO_DADOS):
    try:
      with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
      pass
  return {}


dados = carregar_dados()

# --- CABEÇALHO DO APLICATIVO ---
st.markdown(
    "<h1 style='text-align: center; color: #1e3d59;'>Aliança Eterna</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #555;'>Aplicativo Oficial da Família"
    " e do Ministério de Casais</p>",
    unsafe_allow_html=True,
)
st.divider()

# --- SEÇÃO: RECADOS E AVISOS DO PASTOR ---
st.markdown("### 📢 Recados e Avisos do Pastor")
recado_pastor = dados.get(
    "recado_pastor",
    "Igreja amada, é uma alegria estarmos juntos em mais uma semana de vitórias.",
)
st.info(recado_pastor)

# --- SEÇÃO: ESBOÇO / ESTUDO DA PALAVRA ---
st.markdown("### 📖 Esboço / Estudo da Palavra")
estudo_palavra = dados.get(
    "estudo_palavra",
    "Acompanhe o estudo bíblico semanal disponibilizado pela pastoral.",
)
st.write(estudo_palavra)

st.divider()

# --- SEÇÃO: INSTAGRAM / TRANSMISSÕES ---
st.markdown("### 🎥 Transmissões e Cultos Ao Vivo")
st.markdown(
    "Acompanhe nossos cultos, avisos e a programação oficial no Instagram da"
    " igreja:"
)
st.link_button(
    "📸 Acessar Instagram @admucuripe",
    "https://www.instagram.com/admucuripe/",
    type="primary",
    use_container_width=True,
)

st.divider()

# --- SEÇÃO: DEVOCIONAL DIÁRIO (CASAIS) ---
st.markdown("### 🕊️ Devocional e Mensagens para os Casais")
devocional_casais = dados.get(
    "devocional_casais",
    "🗓️ **Devocional Diário**\n\nAcompanhe as mensagens diárias preparadas"
    " para edificação do seu lar.",
)
st.success(devocional_casais)

# --- SEÇÃO: RECADO DIRETO AOS CASAIS ---
st.markdown("### 💌 Recado Direto aos Casais")
recado_casais = dados.get(
    "recado_casais",
    "Fique ligado nos próximos encontros e programações da nossa rede.",
)
st.info(recado_casais)

st.divider()

# --- SEÇÃO: PARTICIPAÇÃO E CADASTROS ---
st.markdown("### 📝 Participação e Cadastros")
st.write(
    "Venha fazer parte do ministério de casais da igreja (Aliança Eterna), preencha"
    " o formulário de cadastro aqui:"
)

link_form = dados.get(
    "link_formulario",
    "https://docs.google.com/forms/d/e/1FAIpQLScOhLmBiUcKmM6hYTGO9NExTeNGgLSyj-HaeT6QgAWsUilhcg/viewform?usp=header",
)

st.link_button(
    "👉 Preencher Formulário / Cadastro",
    link_form,
    type="primary",
    use_container_width=True,
)

# --- RODAPÉ DISCRETO ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; font-size: 12px; color: gray;'>Ministério"
    " Aliança Eterna • Todos os direitos reservados</p>",
    unsafe_allow_html=True,
)