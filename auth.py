import streamlit as st

USUARIO_CORRETO = "admin"
SENHA_CORRETA = "12345"


def verificar_autenticacao():
  if "logado_agora" not in st.session_state:
    st.session_state["logado_agora"] = False

  if not st.session_state["logado_agora"]:
    st.markdown(
        """<style>.stApp { background-color: #f0f2f6 !important; }</style>""",
        unsafe_allow_html=True,
    )
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
      st.subheader("🔒 Acesso Restrito - Sistema Pastoral")
      st.markdown("Por favor, digite suas credenciais para acessar o painel.")

      with st.form("form_login_unico"):
        usuario_input = st.text_input("Usuário")
        senha_input = st.text_input("Senha", type="password")
        botao_entrar = st.form_submit_button(
            "Entrar no Sistema", use_container_width=True
        )

        if botao_entrar:
          if (
              usuario_input == USUARIO_CORRETO
              and senha_input == SENHA_CORRETA
          ):
            st.session_state["logado_agora"] = True
            st.session_state["acao_gestao"] = "listar"
            st.rerun()
          else:
            st.error("❌ Usuário ou senha incorretos.")
    st.stop()
