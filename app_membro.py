from datetime import datetime, timedelta, timezone
import json
import os
import tomllib
from bs4 import BeautifulSoup
import psycopg2
import requests
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Casamento com Propósito - Aliança Eterna",
    page_icon="icone.png",  # ou "icone.ico"
    layout="wide",
)

# --- MODO MANUTENCAO / ATUALIZACAO ---
# Mude para True enquanto estiver mexendo/atualizando o app no GitHub.
# Quando terminar, volte para False para liberar o acesso da liderança e membros.
MODO_MANUTENCAO = False

if MODO_MANUTENCAO:
  st.warning("🚧 **Sistema em Atualização**")
  st.info(
      "Estamos aprimorando o aplicativo da nossa igreja para trazer novidades"
      " para vocês. Por favor, aguarde alguns instantes. O sistema voltará a"
      " funcionar em breve!"
  )
  st.stop()  # Interrompe a execução para que ninguém veja o app incompleto

ARQUIVO_DADOS = "dados_painel.json"


# --- FUNÇÕES DE LIGAÇÃO AO NEON (POSTGRESQL) ---
def _obter_database_url():
  """Obtém a DATABASE_URL a partir do st.secrets, variáveis de ambiente ou .streamlit/secrets.toml."""
  try:
    if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
      return str(st.secrets["DATABASE_URL"]).strip()
  except Exception:
    pass

  url_env = os.environ.get("DATABASE_URL")
  if url_env and url_env.strip():
    return url_env.strip()

  caminho_secrets = os.path.join(".streamlit", "secrets.toml")
  if os.path.exists(caminho_secrets):
    try:
      with open(caminho_secrets, "rb") as f:
        data = tomllib.load(f)
        if "DATABASE_URL" in data and str(data["DATABASE_URL"]).strip():
          return str(data["DATABASE_URL"]).strip()
    except Exception:
      pass

  return None


def _conectar_neon():
  """Abre uma ligação ao PostgreSQL do Neon."""
  url = _obter_database_url()
  if not url:
    return None

  url_limpa = url.replace("&channel_binding=require", "").replace(
      "?channel_binding=require&", "?"
  )
  return psycopg2.connect(url_limpa)


@st.cache_data(ttl=120)
def carregar_dados_neon_e_local():
  """Carrega os conteúdos do painel (conteudo_painel) do Neon, com fallback para o JSON local."""
  dados_local = {}
  try:
    if os.path.exists(ARQUIVO_DADOS):
      with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        dados_local = json.load(f)
  except Exception:
    dados_local = {}

  dados_neon = {}
  conn = None
  try:
    conn = _conectar_neon()
    if conn is not None:
      with conn.cursor() as cur:
        cur.execute("SELECT chave, payload FROM conteudo_painel")
        for chave, payload in cur.fetchall():
          if isinstance(payload, dict):
            dados_neon[str(chave)] = payload
  except Exception as e:
    print(f"Aviso ao carregar conteudo_painel do Neon: {e}")
  finally:
    if conn is not None:
      try:
        conn.close()
      except Exception:
        pass

  resultado = dict(dados_local) if isinstance(dados_local, dict) else {}
  resultado.update(dados_neon)
  return resultado


@st.cache_data(ttl=300)
def carregar_planejamento_2027_membro():
  """Carrega o Planeamento Estratégico 2027 a partir do Neon."""
  conn = None
  try:
    conn = _conectar_neon()
    if conn is not None:
      with conn.cursor() as cur:
        cur.execute("SELECT plano FROM planejamento_2027 WHERE id = 1")
        row = cur.fetchone()
        if row and isinstance(row[0], dict):
          return row[0]
  except Exception as e:
    print(f"Aviso ao carregar planejamento_2027 do Neon: {e}")
  finally:
    if conn is not None:
      try:
        conn.close()
      except Exception:
        pass
  return {}


# --- CARREGAMENTO DE DADOS DO PAINEL COM SEGURANÇA ---
dados = carregar_dados_neon_e_local()

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
@st.cache_data(ttl=300)
def buscar_devocional_site():
  # Fuso horário oficial do Brasil (UTC-3)
  fuso_brasil = timezone(timedelta(hours=-3))
  hoje = datetime.now(fuso_brasil)

  dia_atual = hoje.day
  mes_atual = hoje.strftime("%m")
  ano_atual = hoje.strftime("%Y")
  data_formatada = hoje.strftime("%d/%m/%Y")

  # Meses por extenso para achar exato como o site publica ("12 de Setembro de 2026")
  meses_pt = {
      "01": "Janeiro",
      "02": "Fevereiro",
      "03": "Março",
      "04": "Abril",
      "05": "Maio",
      "06": "Junho",
      "07": "Julho",
      "08": "Agosto",
      "09": "Setembro",
      "10": "Outubro",
      "11": "Novembro",
      "12": "Dezembro",
  }
  string_data_site = f"{dia_atual} de {meses_pt.get(mes_atual, '')} de {ano_atual}"

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

      # Procura especificamente pelo título/cabeçalho da data no corpo do site (ex: "12 de Setembro de 2026")
      texto_encontrado = ""
      elementos = soup.find_all(["div", "article", "section", "p", "span", "h3"])

      for el in elementos:
        if string_data_site.lower() in el.text.lower():
          # Pega o elemento pai ou o próprio bloco de conteúdo que contém o texto do devocional
          parent = el.find_parent(["div", "article"])
          if parent:
            texto_encontrado = parent.get_text().strip()
          else:
            texto_encontrado = el.text.strip()
          break

      # Se não achou pelo texto exato, tenta achar o bloco do dia correspondente
      if not texto_encontrado:
        for el in elementos:
          if f"Dia {dia_atual}" in el.text:
            texto_encontrado = el.text.strip()
            break

      if texto_encontrado:
        return {
            "data": data_formatada,
            "titulo": f"Devocional Diário — {data_formatada}",
            "versiculo": "Palavra de Reflexão para Hoje",
            "texto": texto_encontrado[:500] + "...",
            "link_original": url,
        }
  except Exception:
    pass

  # Fallback seguro caso ocorra algum erro na leitura
  return {
      "data": data_formatada,
      "titulo": f"Devocional Diário — {data_formatada}",
      "versiculo": (
          '"Então, me invocareis, passareis a orar a mim, e eu vos ouvirei."'
          " — Jeremias 29:12"
      ),
      "texto": (
          "Buscando ao Senhor de todo o coração com fé e esperança na Sua"
          " Palavra."
      ),
      "link_original": url,
  }


dev = buscar_devocional_site()
plano_2027 = carregar_planejamento_2027_membro()

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

# 4.1 Planejamento Estratégico 2027 (se disponível no Neon)
if plano_2027:
  st.markdown("---")
  with st.expander("🗓️ Planejamento Estratégico 2027 — Ministério de Casais"):
    fundamento = plano_2027.get("fundamento", {})
    if fundamento:
      st.info(
          f"**{fundamento.get('titulo', 'Amor como Fundamento')}**"
          f" ({fundamento.get('versiculo', '1 Coríntios 13:1-2')}): "
          f"{fundamento.get('texto', '')}"
      )

    grupos = plano_2027.get("grupos_alvo", [])
    if grupos:
      st.markdown("#### 👥 Grupos do Ministério")
      for grp in grupos:
        st.markdown(
            f"- **{grp.get('nome')}** ({grp.get('publico')}): {grp.get('foco')}"
        )

    modulos = plano_2027.get("modulos_bimestrais", [])
    if modulos:
      st.markdown("#### 📚 Módulos Bimestrais 2027")
      for mod in modulos:
        st.markdown(
            f"- **{mod.get('bimestre')} — {mod.get('tema')}:** {mod.get('foco')}"
        )

    datas_destaque = plano_2027.get("datas_comemorativas_2027", [])
    if datas_destaque:
      st.markdown("#### 🎉 Datas em Destaque (2027)")
      for dt_item in datas_destaque:
        st.markdown(
            f"- **{dt_item.get('data')} — {dt_item.get('evento')}:**"
            f" {dt_item.get('sugestao')}"
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