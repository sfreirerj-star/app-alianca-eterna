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
recado_pastor = dados.get("recado_pastor", "")
if recado_pastor:
  st.markdown("### 📢 Recados e Avisos do Pastor")
  st.info(recado_pastor)

# --- SEÇÃO: ESBOÇO / ESTUDO DA PALAVRA ---
estudo_palavra = dados.get("estudo_palavra", "")
if estudo_palavra:
  st.markdown("### 📖 Esboço / Estudo da Palavra")
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
devocional_casais = dados.get("devocional_casais", "")
if devocional_casais:
  st.markdown("### 🕊️ Devocional e Mensagens para os Casais")
  st.success(devocional_casais)

# --- SEÇÃO: RECADO DIRETO AOS CASAIS ---
recado_casais = dados.get("recado_casais", "")
if recado_casais:
  st.markdown("### 💌 Recado Direto aos Casais")
  st.info(recado_casais)

st.divider()

# --- SEÇÃO: PARTICIPAÇÃO E CADASTROS ---
st.markdown("### 📝 Participação e Cadastros")
st.write(
    "Deseja atualizar seus dados ou participar ativamente da nossa rede de"
    " casais? Clique no botão abaixo:"
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