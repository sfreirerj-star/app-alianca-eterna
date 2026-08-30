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

    # Verifica se o arquivo já existe no GitHub para capturar o SHA (necessário para update)
    response = requests.get(url, headers=headers)
    sha = None
    if response.status_code == 200:
      sha = response.json().get("sha")

    # Lê o arquivo local codificado em base64
    with open(caminho_arquivo, "rb") as f:
      conteudo_bytes = f.read()
    conteudo_base64 = base64.b64encode(conteudo_bytes).decode("utf-8")

    # Prepara o payload para o commit automático
    payload = {
        "message": "Atualização automática de dados via Painel",
        "content": conteudo_base64,
        "branch": BRANCH,
    }
    if sha:
      payload["sha"] = sha

    # Envia a requisição PUT para o GitHub
    requests.put(url, headers=headers, json=payload)
  except Exception as e:
    print(f"Erro ao sincronizar com o GitHub: {e}")


def buscar_devocional_automatico():
  """Busca um versículo/reflexão diária da internet para casais de forma automática"""
  try:
    dia_do_ano = datetime.now().timetuple().tm_yday
    temas_casais = [
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
            "O amor é paciente, o amor é bondoso. Não inveja, não se vangloria,"
            " não se orgulha.",
        ),
        (
            "Cantares 8:7",
            "As muitas águas não poderiam apagar o amor, nem os rios afogá-lo.",
        ),
        (
            "Provérbios 18:22",
            "Quem acha uma esposa acha uma coisa boa e alcançou a benevolência"
            " do Senhor.",
        ),
    ]
    referencia, texto = temas_casais[dia_do_ano % len(temas_casais)]
    devocional_automatico = (
        f"📅 **Devocional Diário ({datetime.now().strftime('%d/%m/%Y')})**\n\n*\"{texto}\"* —"
        f" **{referencia}**\n\nReflexão da Semana para Edição do Lar:"
        " Fortalecendo a aliança conjugal através do perdão, do diálogo e dos"
        " princípios inegociáveis da Palavra de Deus."
    )
    return devocional_automatico
  except:
    return (
        "Tema da Semana: Aliança Inquebrável. 'Melhor serem dois do que um...'"
        " - Ecclesiastes 4:9"
    )


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


def salvar_dados(dados):
  # 1. Salva localmente no computador
  with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)

  # 2. Envia automaticamente para o GitHub em segundo plano!
  salvar_no_github(ARQUIVO_DADOS)


dados_atuais = carregar_dados()

# Menu lateral de navegação
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
  st.info(
      "Esta é a visão geral dos recados e estudos cadastrados para a"
      " congregação."
  )

  st.subheader("📖 Estudo da Palavra / Sugestão Pastoral")
  st.caption(
      f"Direcionado para: **{dados_atuais.get('destino_estudo', 'Toda a"
      " Igreja')}**"
  )
  st.write(
      dados_atuais.get("estudo_palavra")
      or "Nenhum estudo cadastrado no momento."
  )

  st.subheader("📢 Recado Geral / Pastoral")
  st.caption(
      f"Direcionado para: **{dados_atuais.get('destino_recado_pastor', 'Toda a"
      " Igreja')}**"
  )
  st.write(
      dados_atuais.get("recado_igreja") or "Nenhum recado no momento."
  )

  st.subheader("💍 Mensagem e Direcionamento para os Casais")
  st.write(dados_atuais.get("devocional_casais"))
  st.write(
      dados_atuais.get("recado_casais")
      or "Nenhum recado específico da liderança de casais no momento."
  )

elif tipo_painel == "Área Pastoral":
  st.sidebar.subheader("🔒 Acesso Restrito")
  senha = st.sidebar.text_input("Senha Pastoral", type="password")

  if senha == "igreja123":
    st.success("Acesso Pastoral Liberado!")

    st.header("Esboço / Estudo da Palavra")
    destino_estudo = st.radio(
        "Este estudo é destinado para:",
        ["Toda a Igreja", "Apenas para os Casais"],
        index=0
        if dados_atuais.get("destino_estudo") == "Toda a Igreja"
        else 1,
        key="dest_est",
    )
    novo_estudo = st.text_area(
        "Sugestão de Estudo Bíblico",
        value=dados_atuais.get("estudo_palavra", ""),
        height=150,
    )

    st.markdown("---")
    st.header("Recados e Avisos do Pastor")
    destino_recado = st.radio(
        "Este recado é destinado para:",
        ["Toda a Igreja", "Apenas para os Casais"],
        index=0
        if dados_atuais.get("destino_recado_pastor") == "Toda a Igreja"
        else 1,
        key="dest_rec",
    )
    novo_recado_igreja = st.text_area(
        "Mensagem ou Aviso",
        value=dados_atuais.get("recado_igreja", ""),
        height=120,
    )

    if st.button("Salvar Alterações Pastorais"):
      dados_atuais["estudo_palavra"] = novo_estudo
      dados_atuais["destino_estudo"] = destino_estudo
      dados_atuais["recado_igreja"] = novo_recado_igreja
      dados_atuais["destino_recado_pastor"] = destino_recado
      salvar_dados(dados_atuais)
      st.success("Informações pastorais atualizadas e enviadas com sucesso!")

  elif senha != "":
    st.sidebar.error("Senha incorreta.")
  else:
    st.warning(
        "👈 Por favor, digite a senha de acesso na barra lateral para gerenciar"
        " os conteúdos pastorais."
    )

elif tipo_painel == "Liderança Aliança Eterna":
  st.sidebar.subheader("🔒 Acesso Restrito")
  senha_casais = st.sidebar.text_input("Senha Casais", type="password")

  if senha_casais == "igreja123":
    st.success("Acesso da Liderança de Casais Liberado!")

    st.header("Devocional e Mensagens para os Casais")

    col1, col2 = st.columns([2, 1])
    with col2:
      if st.button("🔄 Atualizar Automático da Internet"):
        dados_atuais["devocional_casais"] = buscar_devocional_automatico()
        salvar_dados(dados_atuais)
        st.success(
            "Devocional atualizado e sincronizado com sucesso para o dia de"
            " hoje!"
        )
        st.rerun()

    novo_devocional = st.text_area(
        "Devocional / Reflexão",
        value=dados_atuais.get("devocional_casais", ""),
        height=140,
    )

    st.markdown("---")
    st.header("Recado Direto aos Casais")
    novo_recado_casais = st.text_area(
        "Aviso Exclusivo da Liderança para os Casais",
        value=dados_atuais.get("recado_casais", ""),
        height=120,
    )

    if st.button("Atualizar Seção de Casais"):
      dados_atuais["devocional_casais"] = novo_devocional
      dados_atuais["recado_casais"] = novo_recado_casais
      salvar_dados(dados_atuais)
      st.success("Conteúdo dos casais atualizado e enviado para o app!")

  elif senha_casais != "":
    st.sidebar.error("Senha incorreta.")
  else:
    st.warning(
        "👈 Por favor, digite a senha de acesso na barra lateral para gerenciar"
        " o painel de casais."
    )