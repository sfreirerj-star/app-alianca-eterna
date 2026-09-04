import database as db
import streamlit as st


def renderizar_painel_lideranca(df, col_nome1=None, col_conjuge=None):
  with st.expander(
      "⭐ Painel de Configuração: Substituir / Alterar Casal Líder",
      expanded=True,
  ):
    st.markdown(
        "Utilize esta seção para promover um casal à liderança ou remover o"
        " status de liderança conforme determinação pastoral."
    )

    if df is None or df.empty:
      st.warning("⚠️ Nenhum registro carregado da planilha.")
      return

    if "lideres_manuais" not in st.session_state:
      st.session_state["lideres_manuais"] = {}

    # Define colunas padrão caso não venham preenchidas
    if not col_nome1:
      col_nome1 = db.obter_coluna_segura(
          df, ["Nome completo", "Nome"], 1 if len(df.columns) > 1 else 0
      )
    if not col_conjuge:
      col_conjuge = db.obter_coluna_segura(
          df, ["cônjuge", "conjuge"], 7 if len(df.columns) > 7 else 0
      )

    opcoes_lideranca = []
    mapa_indices = {}

    for i, r in df.iterrows():
      n1 = str(r.get(col_nome1, ""))
      n2 = str(r.get(col_conjuge, ""))

      eh_lider = str(r.get("Perfil", "")) == "⭐ Líder"
      prefixo = "⭐ [Líder] " if eh_lider else ""

      nome_fmt = f"{n1} & {n2}" if n2 and n2.strip() and n2 != "nan" else n1
      if not nome_fmt or nome_fmt == "nan":
        nome_fmt = f"Casal da Linha {i+1}"

      texto_opcao = f"{i}: {prefixo}{nome_fmt}"
      opcoes_lideranca.append(texto_opcao)
      mapa_indices[texto_opcao] = i

    casal_selecionado = st.selectbox(
        "Selecione o Casal:", opcoes_lideranca, key="select_painel_lider"
    )

    if casal_selecionado:
      idx_real = mapa_indices[casal_selecionado]
      registro_selecionado = df.loc[idx_real]
      chave_unica = db.obter_chave_unica(registro_selecionado)

      col1, col2 = st.columns(2)

      with col1:
        if st.button(
            "⭐ Promover a Líder",
            key="btn_promover_lider",
            use_container_width=True,
        ):
          st.session_state["lideres_manuais"][chave_unica] = True
          st.cache_data.clear()
          st.success("✅ Casal promovido a Líder com sucesso!")
          st.rerun()

      with col2:
        if st.button(
            "❌ Remover da Liderança",
            key="btn_remover_lider",
            use_container_width=True,
        ):
          st.session_state["lideres_manuais"][chave_unica] = False
          st.cache_data.clear()
          st.success("✅ Status de liderança removido com sucesso!")
          st.rerun()