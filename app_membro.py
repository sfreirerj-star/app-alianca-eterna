import json
import os
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Aliança Eterna",
    page_icon="📖",
    layout="centered", # Garante o layout centralizado
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
.stApp { background-color: #FFFFFF; } /* Fundo branco */
</style>
"""
st.markdown(pwa_code, unsafe_allow_html=True)

# --- ESTILO CSS ESPECÍFICO PARA BOTÕES VERMELHOS E CENTRALIZADOS ---
# Este bloco é o segredo para deixar os botões como na sua imagem
st.markdown(
    """
    <style>
    /* Estiliza o container do botão do Streamlit */
    div.stButton > button {
        display: block;               /* Faz o botão ocupar a largura disponível */
        margin: 0 auto;               /* Centraliza o botão horizontalmente */
        width: 50%;                   /* Define a largura do botão (ajuste conforme preferência) */
        background-color: #ff4b4b;    /* Cor de fundo vermelha */
        color: white;                 /* Cor do texto branca */
        border: none;                 /* Remove borda padrão */
        border-radius: 5px;           /* Bordas levemente arredondadas */
        padding: 0.6rem 1.2rem;       /* Espaçamento interno */
        font-weight: bold;            /* Texto em negrito */
        font-size: 1rem;              /* Tamanho da fonte */
        cursor: pointer;              /* Mostra o cursor de mão */
    }
    /* Efeito ao passar o mouse sobre o botão */
    div.stButton > button:hover {
        background-color: #ff2121;    /* Fundo vermelho mais escuro ao passar o mouse */
        color: white;
    }
    
    /* Estiliza o container do LinkButton do Streamlit para seguir o mesmo padrão */
    .stLinkButton > a {
        display: block;
        text-align: center;           /* Centraliza o texto do link */
        margin: 0 auto;
        width: 50%;
        background-color: #ff4b4b;
        color: white !important;      /* !important para garantir a cor branca */
        border-radius: 5px;
        padding: 0.6rem 1.2rem;
        font-weight: bold;
        text-decoration: none;        /* Remove sublinhado do link */
    }
    /* Efeito ao passar o mouse sobre o LinkButton */
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
# Certifique-se de que o arquivo 'dados_painel.json' existe no repositório
ARQUIVO_DADOS = "dados_painel.json"


def carregar_dados():
  if os.path.exists(ARQUIVO_DADOS):
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
      try:
        return json.load(f)
      except:
        pass
  return {
      "recado_pastoral": "Carregando... Seja bem-vindo!",
      "estudo_palavra_titulo": "Carregando...",
      "estudo_palavra_texto": "Carregando...",
      "devocional_casais_titulo": "Carregando...",
      "devocional_casais_texto": "Carregando...",
  }


dados = carregar_dados()

# --- INTERFACE DO APLICATIVO ---
# Título Centralizado
st.markdown(
    "<h1 style='text-align: center; color: #1e3d59;'>Aliança Eterna</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; font-size: 1.1em;'>Aplicativo Oficial da Família e do Ministério de Casais</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# Seção: Recado da Pastoral
st.subheader("📢 Recado da Pastoral")
st.info(
    dados.get("recado_pastoral", "Aguardando mensagem pastoral.")
)  # Usando st.info para a caixa azul

st.markdown("---")

# Seção: Transmissões e Cultos Ao Vivo
st.subheader("📺 Transmissões e Cultos Ao Vivo")
st.markdown(
    "Acompanhe nossos cultos, avisos e a programação oficial no Instagram da"
    " igreja:"
)
# O Streamlit automaticamente centraliza o st.link_button com o CSS acima
st.link_button(
    "📸 Acessar Instagram @admucuripe", "https://instagram.com/admucuripe"
)

st.markdown("---")

# Seção: Devocional de Casais
st.subheader("📖 Devocional de Casais")
st.success(  # Usando st.success para a caixa verde
    f"**{dados.get('devocional_casais_titulo', '')}**\n\n{dados.get('devocional_casais_texto', 'Aguardando devocional da semana.')}"
)

st.markdown("---")

# Seção: Participação e Cadastros
st.subheader("📝 Participação e Cadastros")
st.markdown(
    "Deseja atualizar seus dados ou participar ativamente da nossa rede de casais? Clique no botão abaixo:"
)
# O Streamlit automaticamente centraliza o st.link_button com o CSS acima
st.link_button(
    "📝 Preencher Formulário / Cadastro", "https://forms.gle/exemplo"
)