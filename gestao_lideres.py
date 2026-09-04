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

    if df.empty:
      st.warning("⚠️ Nenhum registro carregado da planilha.")
      return

    # Nome exato da coluna identificado na sua tabela: "Nome completo:"
    c_nome = "Nome completo:" if "Nome completo:" in df.columns else "Nome completo"
    if c_nome not in df.columns:
      c_nome = df.columns[3] if len(df.columns) > 3 else df.columns[0]

    # Procura coluna de cônjuge se houver
    c_conj = next((c for c in df.columns if "cônjuge" in c.lower() or "conjuge" in c.lower() or "espos" in c.lower()), None)

    if "lideres_manuais" not in st.session_state:
      st.session_state["lideres_manuais"] = {}

    opcoes_lideranca = []
    mapa_indices = {}

    for i, r in df.iterrows():
      n1 = str(r.get(c_nome, "")) if c_nome else ""
      n2 = str(r.get(c_conj, "")) if c_conj else ""

      if not n1.strip() and len(r) > 0:
        n1 = str(r.iloc[0])

      eh_lider = str(r.get("Perfil", "")) == "⭐ Líder"
      prefixo = "⭐ [Líder] " if eh_lider else ""
      nome_fmt = f"{n1} & {n2}" if n2 and n2 != "nan" and n2.strip() else n1
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