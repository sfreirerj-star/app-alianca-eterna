from datetime import datetime
import json
import os
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Aliança Eterna", page_icon="📖", layout="centered"
)

ARQUIVO_DADOS = "dados_painel.json"


def buscar_devocional_automatico():
  """Garante um padrão caso o JSON esteja vazio"""
  return {
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


# --- CARREGAMENTO DE DADOS ---
if os.path.exists(ARQUIVO_DADOS):
  with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
    dados = json.load(f)
else:
  dados = {}

# Recupera os blocos salvos no painel
estudo = dados.get("estudo", {})
recado = dados.get("recado", {})
casais_msg = dados.get("casais_msg", {})

# Puxa o devocional do JSON ou gera o do dia atual
dev_salvo = dados.get("devocional", {})
if isinstance(dev_salvo, dict) and dev_salvo.get("titulo"):
  dev = dev_salvo
else:
  dev = buscar_devocional_automatico()


# --- INTERFACE DO APLICATIVO DOS MEMBROS ---
st.title("Aliança Eterna")
st.markdown("*Aplicativo Oficial da Família e do Ministério de Casais*")
st.markdown("---")

# 1. Estudo da Palavra
if estudo.get("texto"):
  st.markdown("### 📖 Estudo da Palavra")
  destino_estudo = estudo.get("destino", "Toda a Igreja")
  st.caption(f"📌 **Destino:** {destino_estudo}")
  st.info(estudo.get("texto"))
  st.markdown("---")

# 2. Recados e Avisos Pastorais
if recado.get("texto"):
  st.markdown("### 📢 Recados e Avisos Pastorais")
  destino_recado = recado.get("destino", "Toda a Igreja")
  st.caption(f"📌 **Destino:** {destino_recado}")
  st.success(recado.get("texto"))
  st.markdown("---")

# 3. Recado Direto aos Casais (Ministério de Casais)
if casais_msg.get("texto"):
  st.markdown("### 💍 Recado Direto aos Casais")
  st.caption("📌 **Destino:** Apenas para os Casais")
  st.warning(casais_msg.get("texto"))
  st.markdown("---")

# 4. Devocional Diário / Casais (Sincronizado com Vídeo do YouTube)
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
      f"👉 **[Assistir ao Vídeo do Devocional no"
      f" YouTube]({dev.get('link_video')})**"
  )

# 5. Participação e Cadastros (Ministério de Casais)
st.markdown("---")
st.markdown("### 📝 Participação e Cadastros")
st.write(
    "Deseja atualizar seus dados ou participar ativamente da nossa rede de"
    " casais? Clique no botão abaixo:"
)
st.link_button(
    "Preencher Formulário / Cadastro",
    "https://forms.gle/exemplo_formulario",
)  # Substitua pelo link real do seu formulário se necessário

# 6. Rodapé de Redes Sociais / Contato
st.markdown("---")
st.markdown("### 🌐 Redes Sociais e Contato")
st.markdown(
    "Acompanhe nossos cultos, avisos e a programação oficial no Instagram da"
    " igreja:"
)
st.link_button(
    "Acessar Instagram @admucuripe", "https://instagram.com/admucuripe"
)