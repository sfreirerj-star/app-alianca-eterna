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
      st.session_state["lideres_manuais"] = db.carregar_lideres_json()

    if not col_nome1 or col_nome1 not in df.columns:
      col_nome1 = db.obter_coluna_segura(
          df,
          [
              "Nome completo",
              "Nome",
              "Nome 1",
              "Esposo(a) 1",
              df.columns[1] if len(df.columns) > 1 else df.columns[0],
          ],
          1 if len(df.columns) > 1 else 0,
      )

    if not col_conjuge or col_conjuge not in df.columns:
      col_conjuge = db.obter_coluna_segura(
          df,
          [
              "cônjuge",
              "conjuge",
              "Esposo(a) 2",
              df.columns[7] if len(df.columns) > 7 else df.columns[0],
          ],
          7 if len(df.columns) > 7 else 0,
      )

    opcoes_lideranca = []
    mapa_indices = {}

    for i, r in df.iterrows():
      n1 = str(r.get(col_nome1, "")).strip()
      n2 = str(r.get(col_conjuge, "")).strip()

      if not n1 or n1.lower() == "nan":
        for col in df.columns[:3]:
          val = str(r.get(col, "")).strip()
          if val and val.lower() != "nan" and not val.isdigit():
            n1 = val
            break

      if (not n2 or n2.lower() == "nan") and len(df.columns) > 7:
        val_c = str(r.get(df.columns[7], "")).strip()
        if val_c and val_c.lower() != "nan":
          n2 = val_c

      chave_r = db.obter_chave_unica(r)
      eh_lider_manual = st.session_state["lideres_manuais"].get(chave_r)

      if eh_lider_manual is not None:
        eh_lider = eh_lider_manual
      else:
        eh_lider = str(r.get("Perfil", "")) == "⭐ Líder"

      prefixo = "⭐ [Líder] " if eh_lider else ""

      if n1 and n2 and n2.lower() != "nan":
        nome_fmt = f"{n1} & {n2}"
      elif n1:
        nome_fmt = n1
      else:
        nome_fmt = f"Casal da Linha {i+1}"

      texto_opcao = f"{i}: {prefixo}{nome_fmt}"
      opcoes_lideranca.append(texto_opcao)
      mapa_indices[texto_opcao] = i

    with st.form("form_painel_lideranca"):
      casal_selecionado = st.selectbox(
          "Selecione o Casal:", opcoes_lideranca, key="select_painel_lider"
      )

      col1, col2 = st.columns(2)
      btn_pro = col1.form_submit_button(
          "⭐ Promover a Líder", use_container_width=True
      )
      btn_rem = col2.form_submit_button(
          "❌ Remover da Liderança", use_container_width=True
      )

      if btn_pro or btn_rem:
        if casal_selecionado:
          idx_real = mapa_indices[casal_selecionado]
          registro_selecionado = df.loc[idx_real]
          chave_unica = db.obter_chave_unica(registro_selecionado)

          if btn_pro:
            st.session_state["lideres_manuais"][chave_unica] = True
            if "Perfil" in df.columns:
              df.loc[idx_real, "Perfil"] = "⭐ Líder"
            st.success(
                f"✅ Operação realizada com sucesso! Casal da linha {idx_real}"
                " promovido a Líder."
            )
          elif btn_rem:
            st.session_state["lideres_manuais"][chave_unica] = False
            if "Perfil" in df.columns:
              df.loc[idx_real, "Perfil"] = "Casal"
            st.success(
                f"✅ Operação realizada com sucesso! Status de liderança"
                f" removido da linha {idx_real}."
            )

          # SALVA IMEDIATAMENTE NO ARQUIVO JSON LOCAL
          db.salvar_lideres_json(st.session_state["lideres_manuais"])

          st.cache_data.clear()
          st.rerun()