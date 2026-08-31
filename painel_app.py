import base64
from datetime import datetime
import json
import os
import requests
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Painel de Controle Oficial", page_icon="📖", layout="wide"
)

ARQUIVO_DADOS = "dados_painel.json"

# --- CONFIGURAÇÕES DE AUTOMACAO DO GITHUB ---
# Certifique-se de que este é o seu token NOVO (sem expiração e com escopo repo)
GITHUB_TOKEN = "ghp_n52oYjwq2j4ngp7d8nuFgGf1nkYG3nVXM"
REPO_OWNER = "sfreirerj-star"
REPO_NAME = "app-alianca-eterna"
BRANCH = "main"

# --- SENHAS DE ACESSO ---
SENHA_PASTORAL = "pastor123"  # Altere para a senha desejada da pastoral
SENHA_CASAIS = "casais123"  # Altere para a senha desejada da liderança de casais


def salvar_no_github(caminho_arquivo):
  """Envia o arquivo atualizado automaticamente para o GitHub via API"""
  try:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{caminho_arquivo}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    # Pega o SHA atual do arquivo no GitHub (obrigatório para atualizar arquivos existentes)
    response = requests.get(url, headers=headers)
    sha = None
    if response.status_code == 200:
      sha = response.json().get("sha")

    # Lê o arquivo local e codifica em base64
    with open(caminho_arquivo, "rb") as f:
      conteudo_bytes = f.read()
      conteudo_base64 = base64.b64encode(conteudo_bytes).decode("utf-8")

    # Prepara o payload para o commit via API
    payload = {
        "message": f"Atualização automática de dados via Painel - {caminho_arquivo}",
        "content": conteudo_base64,
        "branch": BRANCH,
    }
    if sha:
      payload["sha"] = sha

    res = requests.put(url, headers=headers, json=payload)
    if res.status_code in [200, 201]:
      st.success("✅ Salvo localmente e sincronizado com o GitHub com sucesso!")
      return True
    else:
      st.error(f"❌ Erro ao enviar para o GitHub ({res.status_code}): {res.text}")
      return False
  except Exception as e:
    st.error(f"❌ Erro de conexão com o GitHub: {e}")
    return False


def buscar_devocional_automatico():
  """Seleciona o devocional do dia com base na data do sistema"""
  try:
    dia_do_ano = datetime.now().timetuple().tm_yday
    devocionais = [
        {
            "titulo": "O Que Você Faz Quando NINGUÉM ESTÁ VENDO?",
            "versiculo": (
                '"Feliz é todo aquele que teme ao Senhor que anda nos seus'
                ' caminhos" — Salmo 128:1'
            ),
            "texto": (
                "A fé verdadeira é testada muito mais dentro de casa na"
                " convivência diária do que no culto de domingo. A integridade"
                " silenciosa e as decisões sem plateia definem o verdadeiro"
                " alicerce do lar."
            ),
            "link_video": "https://youtu.be/0Ev_B5S04YA",
        },
        {
            "titulo": "Construindo uma Aliança Inabalável",
            "versiculo": (
                '"Acima de tudo, porém, revistam-se do amor, que é o elo da'
                ' perfeita união." — Colossenses 3:14'
            ),
            "texto": (
                "Fortalecendo a aliança conjugal através do perdão, do diálogo"
                " constante e dos princípios inegociáveis da Palavra de Deus"
                " em família."
            ),
            "link_video": "https://youtu.be/0Ev_B5S04YA",
        },
    ]

    dev_atual = devocionais[dia_do_ano % len(devocionais)]
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    return {
        "data": data_hoje,
        "titulo": dev_atual["titulo"],
        "versiculo": dev_atual["versiculo"],
        "texto": dev_atual["texto"],
        "link_video": dev_atual["link_video"],
    }
  except Exception:
    return {
        "data": datetime.now().strftime("%d/%m/%Y"),
        "titulo": "Devocional Diário da Família",
        "versiculo": '"Melhor serem dois do que um..." — Eclesiastes 4:9',
        "texto": "Reflexão diária para fortalecimento do lar e da vida conjugal.",
        "link_video": "https://youtu.be/0Ev_B5S04YA",
    }


# Carrega dados atuais ou gera o padrão do dia
if os.path.exists(ARQUIVO_DADOS):
  with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
    dados = json.load(f)
else:
  dados = {
      "estudo": {"destino": "Toda a Igreja", "texto": "Teste inicial."},
      "recado": {"destino": "Toda a Igreja", "texto": "Teste inicial."},
      "casais_msg": {"texto": "Bem-vindos ao Ministério de Casais Aliança Eterna!"},
      "devocional": buscar_devocional_automatico(),
  }

# --- INTERFACE DO PAINEL ---
st.title("Painel de Controle: App Oficial")
st.write("Área de gestão restrita para a liderança e pastoral da igreja.")

menu_lateral = st.sidebar.selectbox(
    "Selecione o Painel de Acesso:",
    ["Membro (Visualização)", "Área Pastoral", "Liderança de Casais"],
)

if menu_lateral == "Área Pastoral":
  st.header("🔒 Acesso Restrito - Área Pastoral")
  senha_digitada = st.text_input("Senha Pastoral", type="password")

  if senha_digitada == SENHA_PASTORAL:
    st.success("Acesso autorizado!")

    st.header("Esboço / Estudo da Palavra")
    destino_estudo = st.radio(
        "Destino do estudo:",
        ["Toda a Igreja", "Apenas para os Casais"],
        key="dest_est",
    )
    texto_estudo = st.text_area(
        "Sugestão de Estudo",
        value=dados.get("estudo", {}).get("texto", ""),
        height=100,
    )

    st.header("Recados e Avisos do Pastor")
    destino_recado = st.radio(
        "Destino do recado:",
        ["Toda a Igreja", "Apenas para os Casais"],
        key="dest_rec",
    )
    texto_recado = st.text_area(
        "Mensagem ou Aviso",
        value=dados.get("recado", {}).get("texto", ""),
        height=100,
    )

    if st.button("Salvar Alterações Pastorais"):
      dados["estudo"] = {"destino": destino_estudo, "texto": texto_estudo}
      dados["recado"] = {"destino": destino_recado, "texto": texto_recado}

      with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

      salvar_no_github(ARQUIVO_DADOS)
  elif senha_digitada:
    st.error("❌ Senha incorreta!")
  else:
    st.info("Digite a senha pastoral para liberar a edição.")

elif menu_lateral == "Liderança de Casais":
  st.header("🔒 Acesso Restrito - Ministério de Casais")
  senha_digitada_casais = st.text_input("Senha Liderança de Casais", type="password")

  if senha_digitada_casais == SENHA_CASAIS:
    st.success("Acesso autorizado!")

    texto_casais = st.text_area(
        "Recado / Mensagem Exclusiva para o Casal",
        value=dados.get("casais_msg", {}).get("texto", ""),
        height=100,
    )

    st.subheader("Gerenciamento do Devocional Diário")
    dev_atual = dados.get("devocional", buscar_devocional_automatico())

    edit_titulo = st.text_input(
        "Título do Devocional", value=dev_atual.get("titulo", "")
    )
    edit_versiculo = st.text_input(
        "Versículo Base", value=dev_atual.get("versiculo", "")
    )
    edit_texto = st.text_area(
        "Reflexão / Mensagem", value=dev_atual.get("texto", ""), height=100
    )
    edit_link = st.text_input(
        "Link do Vídeo (YouTube)", value=dev_atual.get("link_video", "")
    )

    if st.button("Salvar Alterações de Casais"):
      dados["casais_msg"] = {"texto": texto_casais}
      dados["devocional"] = {
          "data": datetime.now().strftime("%d/%m/%Y"),
          "titulo": edit_titulo,
          "versiculo": edit_versiculo,
          "texto": edit_texto,
          "link_video": edit_link,
      }

      with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

      salvar_no_github(ARQUIVO_DADOS)
  elif senha_digitada_casais:
    st.error("❌ Senha incorreta!")
  else:
    st.info("Digite a senha da liderança de casais para liberar a edição.")

else:
  st.subheader("Visão Geral do Aplicativo")

  estudo = dados.get("estudo", {})
  recado = dados.get("recado", {})
  casais_msg = dados.get("casais_msg", {})
  dev = dados.get("devocional", buscar_devocional_automatico())

  st.markdown("---")
  st.markdown("### 📖 Estudo da Palavra / Sugestão Pastoral")
  st.write(f"**Destino:** {estudo.get('destino', 'Toda a Igreja')}")
  st.info(estudo.get("texto") or "Nenhum estudo cadastrado no momento.")

  st.markdown("---")
  st.markdown("### 📢 Recados e Avisos Pastorais")
  st.write(f"**Destino:** {recado.get('destino', 'Toda a Igreja')}")
  st.success(recado.get("texto") or "Nenhum recado cadastrado no momento.")

  st.markdown("---")
  st.markdown("### 💍 Ministério de Casais (Aliança Eterna)")
  st.warning(
      casais_msg.get("texto") or "Nenhum recado para casais cadastrado."
  )

  st.markdown("#### 📅 Devocional Diário")
  st.write(f"**Data:** {dev.get('data')}")
  st.markdown(f"**{dev.get('titulo')}**")
  st.markdown(f"*{dev.get('versiculo')}*")
  st.write(dev.get("texto"))

  if dev.get("link_video"):
    st.markdown(
        f"[▶️ Assistir ao Vídeo do Devocional]({dev.get('link_video')})"
    )