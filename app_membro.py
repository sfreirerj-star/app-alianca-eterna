import streamlit as st
import json
import os

# Configuração estável com emoji elegante para casais
st.set_page_config(
    page_title="Aliança Eterna",
    page_icon="💍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Tags de PWA atualizadas para o seu app
pwa_code = """
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#1e3d59">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Aliança Eterna">
"""
st.markdown(pwa_code, unsafe_allow_html=True)
# Injeção limpa das tags de PWA para celular e ícone
pwa_code = """
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="icone.png">
<link rel="icon" type="image/png" href="icone.png">
<meta name="theme-color" content="#000000">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Aliança Eterna">
"""
st.markdown(pwa_code, unsafe_allow_html=True)
# Ocultar o menu padrão do Streamlit, rodapé e o perfil/botão do canto inferior direito
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.viewerBadge_container__1QSob {display: none !important;}
div[data-testid="stToolbar"] {display: none !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# Definição dos arquivos e links globais
ARQUIVO_DADOS = "dados_app.json"
LINK_FORMULARIO_FIXO = "https://docs.google.com/forms/d/e/1FAIpQLScOhLmBiUcKmM6hYTGO9NExTeNGgLSyj-HaeT6QgAWsUilhcg/viewform?usp=header"

# Função para carregar os dados de forma segura
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Dados padrão caso o arquivo não exista ou dê erro
    return {
        "recado_pastor": "Igreja amada, é uma alegria estarmos juntos em mais uma semana de vitórias. Acompanhem nossa programação!",
        "devocional_casais": "Tema da Semana: Aliança Inquebrável. 'Melhor serem dois do que um...' - Eclesiastes 4:9"
    }

# Carregando os dados para a sessão
dados = carregar_dados()

# --- INTERFACE DO APLICATIVO ---
st.markdown("<h1 style='text-align: center; color: #1e3d59;'>Aliança Eterna</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Aplicativo Oficial da Família e do Ministério de Casais</p>", unsafe_allow_html=True)

st.divider()

# Seção do Recado
st.subheader("📢 Recado da Pastoral")
st.info(dados.get("recado_pastor", ""))

# Seção do Devocional
st.subheader("📖 Devocional de Casais")
st.success(dados.get("devocional_casais", ""))

st.divider()

# Seção de Participação e Cadastros
st.subheader("📝 Participação e Cadastros")
st.write("Deseja atualizar seus dados ou participar ativamente da nossa rede de casais? Clique no botão abaixo:")

if st.link_button("Acessar Formulário Oficial", LINK_FORMULARIO_FIXO):
    pass