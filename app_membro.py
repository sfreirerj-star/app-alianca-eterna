from datetime import datetime
import json
import os
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Aliança Eterna", page_icon="📖", layout="centered"
)

ARQUIVO_DADOS = "dados_painel.json"


# --- CARREGAMENTO DE DADOS COM SEGURANÇA ---
try:
  if os.path.exists(ARQUIVO_DADOS):
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
      dados = json.load(f)
  else:
    dados = {}
except Exception:
  dados = {}

# Recupera os blocos com fallback seguro
estudo = dados.get("estudo", {})
if not isinstance(estudo, dict):
  estudo = {}

recado = dados.get("recado", {})
if not isinstance(recado, dict):
  recado = {}

casais_msg = dados.get("casais_msg", {})
if not isinstance(casais_msg, dict):
  casais_msg = {}

dev_salvo = dados.get("devocional", {})
if not isinstance(dev_salvo, dict) or not dev_salvo.get("titulo"):
  dev = {
      "data": datetime.now().strftime("%d/%m/%Y"),
      "titulo": "Construindo uma Aliança Inabalável",
      "versiculo": (
          '"Acima de tudo, porém, revistam-se do amor, que é o elo da perfeita'
          ' união." — Colossenses 3:14'
      ),
      "texto": (
          "Fortalecendo a aliança conjugal através do perdão, do diálogo"
          " constante e dos princípios inegociáveis da Palavra de Deus em"
          " família."
      ),
      "link_video": "https://youtu.be/0Ev_B5S04YA",
  }
else:
  dev = dev_salvo


# --- INTERFACE DO APLICATIVO DOS MEMBROS ---
st.title("Aliança Eterna")
st.markdown("*Aplicativo Oficial da Família e do Ministério de Casais*")
st.markdown("---")

# 1. Estudo da Palavra
texto_estudo = estudo.get("texto") or estudo.get("sugestao")
if texto_estudo:
  st.markdown("### 📖 Estudo da Palavra")
  destino_estudo = estudo.get("destino", "Toda a Igreja")
  st.markdown(f"📌 **Destino:** `{destino_estudo}`")
  st.info(texto_estudo)
  st.markdown("---")

# 2. Recados e Avisos Pastorais
texto_recado = recado.get("texto") or recado.get("mensagem")
if texto_recado:
  st.markdown("### 📢 Recados e Avisos do Pastor")
  destino_recado = recado.get("destino", "Toda a Igreja")
  st.markdown(f"📌 **Destino:** `{destino_recado}`")
  st.success(texto_recado)
  st.markdown("---")

# 3. Recado Direto aos Casais (Ministério de Casais)
texto_casais = casais_msg.get("texto") or casais_msg.get("mensagem")
if texto_casais:
  st.markdown("### 💍 Recado do Ministério para os Casais")
  st.markdown("📌 **Destino:** `Apenas para os Casais`")
  st.warning(texto_casais)
  st.markdown("---")

# 4. Devocional Diário / Casais
st.markdown("### 📅 Devocional de Casais")
st.write(
    f"**Data:** {dev.get('data', datetime.now().strftime('%d/%m/%Y'))}"
)
st.markdown(f"#### {dev.get('titulo')}")
st.markdown(f"*{dev.get('versiculo')}*")
st.write(dev.get("texto"))

if dev.get("link_video"):
  st.markdown("---")
  st.markdown(
      f"""
    <div style="text-align: center; margin: 20px 0;">
        <a href="{dev.get('link_video')}" target="_blank" style="display:inline-block; padding:12px 24px; font-size:16px; font-weight:bold; color:white; background-color:#FF0000; text-align:center; text-decoration:none; border-radius:8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
            ▶ Assistir ao Vídeo do Devocional no YouTube
        </a>
    </div>
    """,
      unsafe_allow_html=True,
  )

# 5. Participação e Cadastros
st.markdown("---")
st.markdown("### 📝 Participação e Cadastros")
st.write(
    "Deseja atualizar seus dados ou participar ativamente da nosso ministério de"
    " casais? Basta apenas um dos cônjuges fazer o preenchimento. Clique no botão abaixo:"
)
st.markdown(
    """
<div style="margin: 15px 0;">
    <a href="https://docs.google.com/forms/d/e/1FAIpQLScOhLmBiUcKmM6hYTGO9NExTeNGgLSyj-HaeT6QgAWsUilhcg/viewform?usp=header" target="_blank" style="display:inline-block; padding:12px 24px; font-size:16px; font-weight:bold; color:white; background-color:#007BFF; text-align:center; text-decoration:none; border-radius:8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
        📋 Preencher Formulário / Cadastro
    </a>
</div>
""",
    unsafe_allow_html=True,
)

# 6. Rodapé de Redes Sociais / Contato
st.markdown("---")
st.markdown("### 🌐 Redes Sociais e Contato")
st.markdown(
    "Acompanhe nossos cultos, avisos e a programação oficial no Instagram da"
    " igreja:"
)
st.markdown(
    """
<div style="margin: 15px 0;">
    <a href="https://instagram.com/admucuripe" target="_blank" style="display:inline-block; padding:12px 24px; font-size:16px; font-weight:bold; color:white; background-color:#E1306C; text-align:center; text-decoration:none; border-radius:8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
        📸 Acessar Instagram @admucuripe
    </a>
</div>
""",
    unsafe_allow_html=True,
)