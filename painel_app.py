import base64
import json
import os
from datetime import datetime
import requests
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Painel de Controle Oficial", page_icon="📖", layout="wide"
)

ARQUIVO_DADOS = "dados_painel.json"

# --- CONFIGURAÇÕES DE AUTOMAÇÃO DO GITHUB ---
GITHUB_TOKEN = "ghp_BBU2EjN4tZRP8gmYoVPEDNWdHnKAM0l0CNk"
REPO_OWNER = "sfreirerj-star"
REPO_NAME = "app-alianca-eterna"
BRANCH = "main"


def salvar_no_github(caminho_arquivo):
  """Envia o arquivo atualizado automaticamente para o GitHub via API"""
  try:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{caminho_arquivo}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers)
    sha = response.json().get("sha") if response.status_code == 200 else None

    with open(caminho_arquivo, "rb") as f:
      conteudo_base64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "message": "Atualização automática de dados via Painel",
        "content": conteudo_base64,
        "branch": BRANCH,
    }
    if sha:
      payload["sha"] = sha

    res = requests.put(url, headers=headers, json=payload)
    if res.status_code in [200, 201]:
      st.success("Sincronizado com o GitHub automaticamente com sucesso!")
    else:
      st.error(f"Erro na API do GitHub: {res.status_code} - {res.text}")
  except Exception as e:
    st.error(f"Erro ao conectar com o GitHub: {e}")


def salvar_dados(dados):
  with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)
  salvar_no_github(ARQUIVO_DADOS)


def buscar_devocional_automatico():
  try:
    dia = datetime.now().timetuple().tm_yday
    temas = [
        (
            "Eclesiastes 4:9-12",
            "Melhor serem dois do que um... Cordão de três dobras não se"
            " rebenta com facilidade.",
        ),
        (
            "Efésios 5:25",
            "Maridos, amem suas mulheres, como Cristo amou a igreja e se"
            " entregou por ela.",
        ),
        (
            "Colossenses 3:14",
            "Acima de tudo, porém, revistam-se do amor, que é o elo da perfeita"
            " união.",
        ),
        (
            "1 Coríntios 13:4-7",
            "O amor é paciente, o amor é bondoso. Não inveja, não se vangloria.",
        ),
    ]
    ref, texto = temas[dia % len(temas)]
    return (
        f"📅 **Devocional Diário ({datetime.now().strftime('%d/%m/%Y')})**\n\n*\"{texto}\"* —"
        f" **{ref}**\n\nReflexão da Semana: Fortalecendo a aliança com amor e"
        " diálogo."
    )
  except:
    return "Reflexão da Semana: Melhor serem dois do que um."


def carregar_dados():
  if os.path.exists(ARQUIVO_DADOS):
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
      try:
        return json.load(f)
      except:
        pass
  return {
      "estudo_palavra": "",
      "destino_estudo": "Toda a Igreja",
      "recado_igreja": "",
      "destino_recado_pastor": "Toda a Igreja",
      "devocional_casais": buscar_devocional_automatico(),
      "recado_casais": "",
  }


dados_atuais = carregar_dados()

st.sidebar.title("Navegação")
tipo_painel = st.sidebar.selectbox(
    "Selecione o Painel de Acesso:",
    [
        "Membro (Visualização)",
        "Área Pastoral",
        "Liderança Aliança Eterna",
    ],
)

st.title("Painel de Controle: App Oficial")
st.markdown("Área de gestão restrita para a liderança e pastoral da igreja.")
st.markdown("---")

if tipo_painel == "Membro (Visualização)":
  st.info("Visão geral dos recados e estudos cadastrados.")

  st.subheader("📖 Estudo da Palavra / Sugestão Pastoral")
  st.caption(f"Direcionado para: **{dados_atuais.get('destino_estudo')}**")
  st.write(
      dados_atuais.get("estudo_palavra")
      or "Nenhum estudo cadastrado no momento."
  )

  st.subheader("📢 Recado Geral / Pastoral")
  st.caption(
      f"Direcionado para: **{dados_atuais.get('destino_recado_pastor')}**"
  )
  st.write(
      dados_atuais.get("recado_igreja") or "Nenhum recado no momento."
  )

  st.subheader("💍 Mensagem e Direcionamento para os Casais")
  st.write(dados_atuais.get("devocional_casais"))
  st.write(
      dados_atuais.get("recado_casais")
      or "Nenhum recado específico para os casais."
  )

elif tipo_painel == "Área Pastoral":
  st.sidebar.subheader("🔒 Acesso Restrito")
  senha = st.sidebar.text_input("Senha Pastoral", type="password")

  if senha == "igreja123":
    st.success("Acesso Pastoral Liberado!")
    st.header("Esboço / Estudo da Palavra")

    dest_est = st.radio(
        "Destino do estudo:",
        ["Toda a Igreja", "Apenas para os Casais"],
        index=0
        if dados_atuais.get("destino_estudo") == "Toda a Igreja"
        else 1,
    )
    novo_estudo = st.text_area(
        "Sugestão de Estudo", value=dados_atuais.get("estudo_palavra", "")
    )

    st.markdown("---")
    st.header("Recados e Avisos do Pastor")
    dest_rec = st.radio(
        "Destino do recado:",
        ["Toda a Igreja", "Apenas para os Casais"],
        index=0
        if dados_atuais.get("destino_recado_pastor") == "Toda a Igreja"
        else 1,
    )
    novo_recado = st.text_area(
        "Mensagem ou Aviso", value=dados_atuais.get("recado_igreja", "")
    )

    if st.button("Salvar Alterações Pastorais"):
      dados_atuais["estudo_palavra"] = novo_estudo
      dados_atuais["destino_estudo"] = dest_est
      dados_atuais["recado_igreja"] = novo_recado
      dados_atuais["destino_recado_pastor"] = dest_rec
      salvar_dados(dados_atuais)

  elif senha != "":
    st.sidebar.error("Senha incorreta.")

elif tipo_painel == "Liderança Aliança Eterna":
  st.sidebar.subheader("🔒 Acesso Restrito")
  senha_casais = st.sidebar.text_input("Senha Casais", type="password")

  if senha_casais == "igreja123":
    st.success("Acesso da Liderança de Casais Liberado!")
    st.header("Devocional e Mensagens para os Casais")

    if st.button("🔄 Atualizar Automático da Internet"):
      dados_atuais["devocional_casais"] = buscar_devocional_automatico()
      salvar_dados(dados_atuais)
      st.rerun()

    novo_dev = st.text_area(
        "Devocional / Reflexão",
        value=dados_atuais.get("devocional_casais", ""),
    )
    novo_rec_casais = st.text_area(
        "Aviso Exclusivo para os Casais",
        value=dados_atuais.get("recado_casais", ""),
    )

    if st.button("Atualizar Seção de Casais"):
      dados_atuais["devocional_casais"] = novo_dev
      dados_atuais["recado_casais"] = novo_rec_casais
      salvar_dados(dados_atuais)

  elif senha_casais != "":
    st.sidebar.error("Senha incorreta.")