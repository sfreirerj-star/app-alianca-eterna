from datetime import datetime
import json
import os
from bs4 import BeautifulSoup
import requests
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Aliança Eterna", page_icon="📖", layout="centered"
)

# --- MODO MANUTENCAO / ATUALIZACAO ---
# Mude para True enquanto estiver mexendo/atualizando o app no GitHub.
# Quando terminar, volte para False para liberar o acesso da liderança e membros.
MODO_MANUTENCAO = True

if MODO_MANUTENCAO:
  st.warning("🚧 **Sistema em Atualização**")
  st.info(
      "Estamos aprimorando o aplicativo da nossa igreja para trazer novidades"
      " para vocês. Por favor, aguarde alguns instantes. O sistema voltará a"
      " funcionar em breve!"
  )
  st.stop()  # Interrompe a execução para que ninguém veja o app incompleto

ARQUIVO_DADOS = "dados_painel.json"


# --- CARREGAMENTO DE DADOS DO PAINEL COM SEGURANÇA ---
try:
  if os.path.exists(ARQUIVO_DADOS):
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
      dados = json.load(f)
  else:
    dados = {}
except Exception:
  dados = {}

# Recupera os blocos cadastrados pelo pastor/liderança
estudo = dados.get("estudo", {})
if not isinstance(estudo, dict):
  estudo = {}

recado = dados.get("recado", {})
if not isinstance(recado, dict):
  recado = {}

casais_msg = dados.get("casais_msg", {})
if not isinstance(casais_msg, dict):
  casais_msg = {}


# --- BUSCA AUTOMÁTICA DO DEVOCIONAL DIÁRIO DO SITE ---
@st.cache_data(ttl=3600)  # Atualiza a consulta a cada 1 hora
def buscar_devocional_site():
  hoje = datetime.now()
  dia_atual = hoje.day
  mes_atual = hoje.strftime("%m")
  ano_atual = hoje.strftime("%Y")
  data_formatada = hoje.strftime("%d/%m/%Y")

  url = f"https://www.devocionaldiario.com.br/index.php?nMes={mes_atual}&nAno={ano_atual}"

  try:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=5)
    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")

      # Localiza o bloco correspondente ao dia atual no site
      artigos = soup.find_all(["div", "article", "section", "p"])
      texto_encontrado = ""

      for artigo in artigos:
        if (
            f"Dia {dia_atual}" in artigo.text
            or f"{dia_atual}/{mes_atual}" in artigo.text
        ):
          texto_encontrado = artigo.text.strip()
          break

      if not texto_encontrado:
        primeiro_paragrafo = soup.find("p")
        if primeiro_paragrafo:
          texto_encontrado = primeiro_paragrafo.get_text()

      if texto_encontrado:
        return {
            "data": data_formatada,
            "titulo": f"Devocional Diário — {data_formatada}",
            "versiculo": "Palavra de Reflexão para Hoje",
            "texto": (
                texto_encontrado[:500] + "..."
            ),  # Limita o tamanho para exibição limpa
            "link_original": url,
        }
  except Exception:
    pass

  # Fallback seguro caso o site esteja instável ou fora do ar
  return {
      "data": data_formatada,
      "titulo": "Construindo uma Aliança Inabalável",
      "versiculo": (
          '"Acima de tudo, porém, revistam-se do amor, que é o elo da perfeita'
          ' união." — Colossenses 3:14'
      ),
      "texto": (
          "Fortalecendo a aliança familiar através do perdão, do diálogo"
          " constante e dos princípios inegociáveis da Palavra de Deus."
      ),
      "link_original": url,
  }


dev = buscar_devocional_site()


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

# 4. Devocional Diário Automatizado da Internet
st.markdown("### 📅 Devocional Diário")
st.write(f"**Data:** {dev.get('data')}")
st.markdown(f"#### {dev.get('titulo')}")
st.markdown(f"*{dev.get('versiculo')}*")
st.write(dev.get("texto"))

# Botão para ler completo no site oficial
if dev.get("link_original"):
  st.markdown("---")
  st.markdown(
      f"""
    <div style="text-align: center; margin: 20px 0;">
        <a href="{dev.get('link_original')}" target="_blank" style="display:inline-block; padding:12px 24px; font-size:16px; font-weight:bold; color:white; background-color:#FF0000; text-align:center; text-decoration:none; border-radius:8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
            📖 Ler Devocional Completo no Site Oficial
        </a>
    </div>
    """,
      unsafe_allow_html=True,
  )

# 5. Participação e Cadastros
st.markdown("---")
st.markdown("### 📝 Participação e Cadastros")
st.write(
    "Deseja atualizar seus dados ou participar ativamente do nosso ministério de"
    " casais? Basta apenas um dos cônjuges fazer o preenchimento. Clique no"
    " botão abaixo:"
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