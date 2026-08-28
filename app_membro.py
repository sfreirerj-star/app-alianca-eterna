import streamlit as st
import json
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Aliança Eterna",
    page_icon="💍",
    layout="centered",
    initial_sidebar_state="collapsed"
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

# --- GERENCIAMENTO DE DADOS (JSON) ---
ARQUIVO_DADOS = "dados_app.json"

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Dados padrão caso o arquivo não exista
    return {
        "recado_pastoral": "Igreja amada, é uma alegria estarmos juntos em mais uma semana de vitórias. Acompanhem nossa programação!",
        "devocional_titulo": "Aliança Inquebrável",
        "devocional_texto": "'Melhor serem dois do que um...' - Eclesiastes 4:9",
        "link_formulario": "https://forms.gle/Y5kCJh5KnVpChy8J7"
    }

dados = carregar_dados()

# --- CABEÇALHO DO APLICATIVO ---
st.markdown("<h1 style='text-align: center; color: #1e3d59;'>Aliança Eterna</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555;'>Aplicativo Oficial da Família e do Ministério de Casais</p>", unsafe_allow_html=True)
st.divider()

# --- SEÇÃO: RECADO DA PASTORAL ---
st.markdown("### 📢 Recado da Pastoral")
st.info(dados.get("recado_pastoral", "Seja bem-vindo ao nosso aplicativo!"))

# --- SEÇÃO: INSTAGRAM / TRANSMISSÕES ---
st.markdown("### 🎥 Transmissões e Cultos Ao Vivo")
st.markdown("Acompanhe nossos cultos, avisos e a programação oficial no Instagram da igreja:")

st.link_button(
    "📸 Acessar Instagram @admucuripe",
    "https://www.instagram.com/admucuripe/",
    type="primary",
    use_container_width=True
)

st.divider()

# --- SEÇÃO: DEVOCIONAL DE CASAIS ---
st.markdown("### 📖 Devocional de Casais")
titulo_devocional = dados.get("devocional_titulo", "Mensagem da Semana")
texto_devocional = dados.get("devocional_texto", "Acompanhe nossas reflexões semanais.")

st.success(f"**Tema da Semana: {titulo_devocional}**\n\n{texto_devocional}")

st.divider()

# --- SEÇÃO: PARTICIPAÇÃO E CADASTROS ---
st.markdown("### 📝 Participação e Cadastros")
st.write("Deseja atualizar seus dados ou participar ativamente da nossa rede de casais? Clique no botão abaixo:")

link_form = dados.get("link_formulario", "https://forms.gle/Y5kCJh5KnVpChy8J7")

st.link_button(
    "👉 Preencher Formulário / Cadastro",
    link_form,
    type="primary",
    use_container_width=True
)

# --- RODAPÉ DISCRETO ---
st.markdown("---")
st.markdown("<p style='text-align: center; font-size: 12px; color: gray;'>Ministério Aliança Eterna • Todos os direitos reservados</p>", unsafe_allow_html=True)