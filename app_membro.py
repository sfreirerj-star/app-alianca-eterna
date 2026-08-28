import streamlit as st
import json
import os

ARQUIVO_DADOS = "dados_app.json"
LINK_FORMULARIO_FIXO = "https://forms.gle/Y5kCJh5KnVPGhy8j7"

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "recado_pastor": "Igreja amada, é uma alegria estarmos juntos em mais uma semana de vitórias. Acompanhem nossa programação!",
            "devocional_casais": "Tema da Semana: Aliança Inquebrável. 'Melhor serem dois do que um...' - Eclesiastes 4:9"
        }

# Configuração da página do aplicativo
st.set_page_config(
    page_title="Aliança Eterna - Oficial", 
    page_icon="💍", 
    layout="centered"
)

# Estilização visual limpa
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Carrega os dados atualizados em tempo real
dados = carregar_dados()

# Cabeçalho Visual do App
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>💍 Aliança Eterna</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280;'>Aplicativo Oficial da Família e do Ministério de Casais</p>", unsafe_allow_html=True)
st.markdown("---")

# Seção 1: Recado do Pastor
st.markdown("### 📢 Mensagem da Pastoreio")
st.info(dados["recado_pastor"])

st.markdown("")

# Seção 2: Devocional / Aliança Eterna
st.markdown("### 🕊️ Ministério de Casais")
st.success(dados["devocional_casais"])

st.markdown("---")

# Seção 3: Botão de Ação / Cadastro com Aviso Gentil
st.markdown("### 📝 Participação e Cadastros")

st.info(
    "💍 **Quer fazer parte do Ministério de Casais?**\n\n"
    "Este espaço de cadastro é dedicado exclusivamente aos casais (namorados com propósito, noivos e casados) que desejam fortalecer os laços da família segundo os princípios de Deus. "
    "Se este é o seu caso, preencha o formulário abaixo para caminharmos juntos!"
)

# Apenas um único botão limpo e direto para o Google Forms
st.link_button("💍 Participar do Ministério Aliança Eterna", LINK_FORMULARIO_FIXO, use_container_width=True)

# Rodapé discreto do app
st.markdown("---")
st.markdown("<p style='text-align: center; color: #9CA3AF; font-size: 12px;'>Desenvolvido para a Igreja • Todos os direitos reservados</p>", unsafe_allow_html=True)