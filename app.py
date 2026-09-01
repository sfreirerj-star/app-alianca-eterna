import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import re
import relatorios  
import agenda         # <--- Módulo de Agenda importado
import streamlit.components.v1 as components  

# --- CONFIGURAÇÃO DA PLANILHA DO GOOGLE FORMS ---
LINK_PLANILHA_GOOGLE = "https://docs.google.com/spreadsheets/d/1Zy2qTGHHqzLhim_ebHsCFgNrHBzPB1AxSscoQZXh3Vc/export?format=csv"

# 1. Configuração da Página (DEVE SER A PRIMEIRA COISA)
st.set_page_config(page_title="Gestão Pastoral - Ministério de Casais", page_icon="💒", layout="wide")

# Estilização CSS dos Botões e Cores Fixas
st.markdown("""
<style>
    div.stButton > button {
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15) !important;
        width: 100% !important;
    }

    /* Cores personalizadas para cada um dos 6 botões */
    div.stHorizontalBlock > div:nth-child(1) div.stButton > button { background-color: #2563eb !important; } /* Consultar - Azul */
    div.stHorizontalBlock > div:nth-child(2) div.stButton > button { background-color: #16a34a !important; } /* Novo Casal - Verde */
    div.stHorizontalBlock > div:nth-child(3) div.stButton > button { background-color: #ca8a04 !important; } /* Editar - Amarelo/Laranja */
    div.stHorizontalBlock > div:nth-child(4) div.stButton > button { background-color: #dc2626 !important; } /* Excluir - Vermelho */
    div.stHorizontalBlock > div:nth-child(5) div.stButton > button { background-color: #7c3aed !important; } /* Relatórios - Roxo */
    div.stHorizontalBlock > div:nth-child(6) div.stButton > button { background-color: #0284c7 !important; } /* Agenda - Azul Claro */

    div.stFormSubmitButton button, 
    div.stButton > button:nth-last-child(1) {
        background-color: #4A4A4A !important;
        color: white !important;
    }
    
    div.stButton > button[kind="secondary"] {
        background-color: #4A4A4A !important;
        color: white !important;
        border: 1px solid #333333 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. CONTROLE DE LOGIN BLINDADO
# ==========================================
USUARIO_CORRETO = "admin"
SENHA_CORRETA = "12345"

if "logado_agora" not in st.session_state:
    st.session_state["logado_agora"] = False

if "acao_gestao" not in st.session_state:
    st.session_state["acao_gestao"] = ""

if not st.session_state["logado_agora"]:
    st.markdown("""<style>.stApp { background-color: #f0f2f6 !important; }</style>""", unsafe_allow_html=True)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        st.subheader("🔒 Acesso Restrito - Sistema Pastoral")
        st.markdown("Por favor, digite suas credenciais para acessar o painel.")
        
        with st.form("form_login_unico"):
            usuario_input = st.text_input("Usuário")
            senha_input = st.text_input("Senha", type="password")
            botao_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if botao_entrar:
                if usuario_input == USUARIO_CORRETO and senha_input == SENHA_CORRETA:
                    st.session_state["logado_agora"] = True
                    st.session_state["acao_gestao"] = ""
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")
    st.stop()

# ==========================================
# 2. CARREGAMENTO DE DADOS (CASAIS)
# ==========================================

@st.cache_data(ttl=300)
def carregar_dados():
  """Carrega os dados diretamente da planilha online do Google Forms em tempo real"""
  try:
    if "COLOQUE_SEU_LINK" in LINK_PLANILHA_GOOGLE:
      return pd.DataFrame()

    df = pd.read_csv(LINK_PLANILHA_GOOGLE)

    # Limpeza padrão dos nomes de colunas e dados nulos
    df.columns = df.columns.str.strip()
    if any(df.columns.str.contains("Unnamed")):
      df = df.loc[:, ~df.columns.str.contains("Unnamed")]

    for col in df.columns:
      df[col] = df[col].astype(str).replace("nan", "")

    return df
  except Exception as e:
    st.error(f"Erro ao carregar dados da planilha do Google: {e}")
    return pd.DataFrame()


df = carregar_dados()

if not df.empty:
    def formatar_data_para_br(val):
        if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
            return ""
        if isinstance(val, (pd.Timestamp, datetime)):
            return val.strftime('%d/%m/%Y')
        
        val_str = str(val).strip()
        try:
            if '-' in val_str and len(val_str.split('-')[0]) == 4:
                dt = datetime.strptime(val_str[:10], '%Y-%m-%d')
                return dt.strftime('%d/%m/%Y')
        except:
            pass
        return val_str

    def formatar_exibicao_filhos(texto_filhos):
        if pd.isna(texto_filhos) or not str(texto_filhos).strip() or str(texto_filhos).lower() in ['nan', 'não', 'nao', '0', 'sem filhos', 'não temos']:
            return "Nenhum cadastrado."
        
        linhas = str(texto_filhos).split('\n')
        resultado_formatado = []
        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue
            match_data = re.search(r'(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})', linha)
            if match_data:
                data_encontrada = formatar_data_para_br(match_data.group(1))
                nome_encontrado = linha.replace(match_data.group(1), '').strip()
                nome_encontrado = re.sub(r'[\-\–\—\:]\s*$', '', nome_encontrado).strip()
                resultado_formatado.append(f"• **Nome Completo:** {nome_encontrado}  |  **Data de Nascimento:** {data_encontrada}")
            else:
                resultado_formatado.append(f"• {linha}")
        return "\n\n".join(resultado_formatado)

    def obter_coluna_segura(nomes_possiveis, indice_fallback):
        for nome in nomes_possiveis:
            for col in df.columns:
                if nome.lower() in col.lower():
                    return col
        if len(df.columns) > indice_fallback:
            return df.columns[indice_fallback]
        return df.columns[0]

    # Identificação blindada das colunas de casais
    col_nome1 = obter_coluna_segura(["Nome completo", "Nome"], 1 if len(df.columns) > 1 else 0)
    col_conjuge = obter_coluna_segura(["cônjuge", "conjuge"], 7 if len(df.columns) > 7 else 0)
    col_nasc1 = obter_coluna_segura(["Nascimento", "Data de Nascimento"], 2 if len(df.columns) > 2 else 0)
    col_endereco = obter_coluna_segura(["Endereço", "Endereco"], 3 if len(df.columns) > 3 else 0)
    col_tel = obter_coluna_segura(["Telefone", "Celular", "Contato"], 4 if len(df.columns) > 4 else 0)
    col_nasc2 = obter_coluna_segura(["Nascimento: 2", "Data de Nascimento: 2", "Nascimento 2"], 8 if len(df.columns) > 8 else 0)
    col_casamento = obter_coluna_segura(["casamento", "união estável"], 10 if len(df.columns) > 10 else 0)
    
    col_filhos = obter_coluna_segura(["filhos do casal", "filhos"], len(df.columns) - 1)
    col_filhos_fora = obter_coluna_segura(["filhos fora do casamento", "fora do casamento"], len(df.columns) - 1)

    # Cálculo correto e robusto dos Anos de Casamento
    df_calc = df.copy()
    datas_casamento_str = df_calc[col_casamento].astype(str).str.strip()
    
    # Tenta extrair anos ou converter datas para calcular a média corretamente
    anos_casados_lista = []
    ano_atual = datetime.now().year
    
    for val in datas_casamento_str:
        ano_encontrado = None
        # Tenta extrair 4 dígitos de ano (ex: 2010, 15/05/2012)
        match_ano = re.search(r'(19\d{2}|20\d{2})', val)
        if match_ano:
            ano_casamento = int(match_ano.group(1))
            ano_encontrado = ano_atual - ano_casamento
        else:
            try:
                dt = pd.to_datetime(val, dayfirst=True, errors='coerce')
                if not pd.isna(dt):
                    ano_encontrado = ano_atual - dt.year
            except:
                pass
        anos_casados_lista.append(ano_encontrado if (ano_encontrado is not None and 0 <= ano_encontrado <= 80) else None)

    df_calc['Anos_Casados'] = anos_casados_lista

    st.title("👩‍❤️‍👨 Sistema de Gestão Pastoral - Casais")
    st.markdown("---")

    st.subheader("Painel de Gestão de Cadastros")
    st.markdown("Selecione a ação desejada nos botões abaixo:")

    # ==========================================
    # OS 6 BOTÕES DO PAINEL PRINCIPAL
    # ==========================================
    b_col1, b_col2, b_col3, b_col4, b_col5, b_col6 = st.columns(6)
    
    with b_col1:
        if st.button("📋 Consultar", use_container_width=True, key="btn_consultar"):
            st.session_state["acao_gestao"] = "listar"
            st.rerun()
            
    with b_col2:
        if st.button("➕ Novo Casal", use_container_width=True, key="btn_novo"):
            st.session_state["acao_gestao"] = "incluir"
            st.rerun()
            
    with b_col3:
        if st.button("✏️ Editar", use_container_width=True, key="btn_editar"):
            st.session_state["acao_gestao"] = "editar"
            st.rerun()
            
    with b_col4:
        if st.button("🗑️ Excluir", use_container_width=True, key="btn_excluir"):
            st.session_state["acao_gestao"] = "excluir"
            st.rerun()

    with b_col5:
        if st.button("📊 Relatórios", use_container_width=True, key="btn_relatorios"):
            st.session_state["acao_gestao"] = "relatorios"
            st.rerun()

    with b_col6:
        if st.button("📅 Agenda", use_container_width=True, key="btn_agenda"):
            st.session_state["acao_gestao"] = "agenda"
            st.rerun()

    st.markdown("---")

    acao = st.session_state["acao_gestao"]

    if acao == "":
        st.info("👆 Por favor, clique em um dos botões acima para selecionar a operação desejada.")

    # ==========================================
    # 4. TELA DE CONSULTA
    # ==========================================
    elif acao == "listar":
        st.markdown("#### 📑 Registros Atuais na Base de Dados")
        termo_busca = st.text_input("🔍 Busca Rápida (Digite o nome do cônjuge, telefone ou e-mail):", "")
        
        df_filtrado = df.copy()
        if termo_busca.strip():
            filtro = df_filtrado.astype(str).apply(lambda x: x.str.contains(termo_busca, case=False, na=False)).any(axis=1)
            df_filtrado = df_filtrado[filtro]

        st.dataframe(df_filtrado, use_container_width=True, hide_index=True, height=220)

        with st.expander("📊 Abrir Painéis, Estatísticas e Busca Avançada do Ministério"):
            st.markdown("### Resumo Estatístico do Ministério")
            col_est1, col_est2, col_est3 = st.columns(3)
            col_est1.metric("Total de Casais Cadastrados", len(df))
            
            if 'Anos_Casados' in df_calc.columns and not df_calc['Anos_Casados'].dropna().empty:
                media_anos = df_calc['Anos_Casados'].mean()
                col_est2.metric("Média de Anos de Casamento", f"{media_anos:.1f} anos")
            else:
                col_est2.metric("Média de Anos de Casamento", "N/D")
            
            total_filhos_registrados = df[col_filhos].apply(lambda x: len(str(x).split('\n')) if str(x).strip() else 0).sum()
            col_est3.metric("Total de Filhos Registrados", int(total_filhos_registrados))

            st.markdown("---")
            st.markdown("### 📈 Gráficos e Distribuições (Tempo de Casamento)")
            if 'Anos_Casados' in df_calc.columns and not df_calc['Anos_Casados'].dropna().empty:
                def faixa_tempo(anos):
                    if pd.isna(anos) or anos < 0: return "Não Informado"
                    elif anos < 5: return "Menos de 5 anos"
                    elif anos < 10: return "5 a 9 anos"
                    elif anos < 20: return "10 a 19 anos"
                    else: return "20 anos ou mais"

                df_calc['Faixa_Casamento'] = df_calc['Anos_Casados'].apply(faixa_tempo)
                df_contagem = df_calc['Faixa_Casamento'].value_counts().reset_index()
                df_contagem.columns = ['Faixa', 'Quantidade']

                fig = px.pie(df_contagem, names='Faixa', values='Quantidade', title="Distribuição Percentual do Tempo de Casamento", hole=0.4)
                fig.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ Insira datas de casamento válidas nos registros para visualizar o gráfico de distribuição.")

    # ==========================================
    # 5. OPÇÃO "INCLUIR NOVO CASAL"
    # ==========================================
    elif acao == "incluir":
        with st.form("form_novo"):
            st.markdown("### ➕ Cadastrar Novo Casal na Base Local")
            c1, c2 = st.columns(2)
            n1 = c1.text_input("Nome Esposo(a) 1")
            n2 = c2.text_input("Nome Esposo(a) 2")
            
            c3, c4, c5 = st.columns(3)
            tel = c3.text_input("Telefone")
            email = c4.text_input("E-mail")
            end = c5.text_input("Endereço")
            
            c6, c7, c8 = st.columns(3)
            dt_n1 = c6.text_input("Nascimento 1 (DD/MM/AAAA)")
            dt_n2 = c7.text_input("Nascimento 2 (DD/MM/AAAA)")
            dt_cas = c8.text_input("Data Casamento (DD/MM/AAAA)")
            
            c9, c10 = st.columns(2)
            est_civil = c9.text_input("Estado civil atual do casal")
            igreja_origem = c10.text_input("Qual a igreja de origem do casal?")

            c11, c12, c13 = st.columns(3)
            tempo_cong = c11.text_input("Quanto tempo congregam na igreja atual?")
            possui_filhos = c12.text_input("Possuem filhos?")
            filhos_moram = c13.text_input("Os filhos moram com o casal?")

            st.markdown("#### 👶 Dados dos Filhos")
            f1_col1, f1_col2 = st.columns([3, 1])
            filho_nome_1 = f1_col1.text_input("Nome Completo do Filho 1")
            filho_nasc_1 = f1_col2.text_input("Data Nasc. Filho 1 (DD/MM/AAAA)")

            f2_col1, f2_col2 = st.columns([3, 1])
            filho_nome_2 = f2_col1.text_input("Nome Completo do Filho 2")
            filho_nasc_2 = f2_col2.text_input("Data Nasc. Filho 2 (DD/MM/AAAA)")

            st.markdown("#### 👶 Filhos Fora do Casamento")
            ff1_col1, ff1_col2 = st.columns([3, 1])
            filho_fora_nome_1 = ff1_col1.text_input("Nome Completo (Fora do Casamento)")
            filho_fora_nasc_1 = ff1_col2.text_input("Data Nasc. (DD/MM/AAAA)")

            c14, c15, c16, c17 = st.columns(4)
            batizado = c14.text_input("Você é batizado(a)?")
            membros = c15.text_input("Membros oficiais da igreja?")
            celula = c16.text_input("Participam de célula/grupo pequeno?")
            ministerio = c17.text_input("Servem a algum ministério? Qual?")

            cadastrar = st.form_submit_button("➕ Salvar Novo Casal")
            
            if cadastrar:
                lista_f = []
                if filho_nome_1.strip(): lista_f.append(f"{filho_nome_1.strip()} {filho_nasc_1.strip()}")
                if filho_nome_2.strip(): lista_f.append(f"{filho_nome_2.strip()} {filho_nasc_2.strip()}")
                str_filhos_final = "\n".join(lista_f)

                lista_ff = []
                if filho_fora_nome_1.strip(): lista_ff.append(f"{filho_fora_nome_1.strip()} {filho_fora_nasc_1.strip()}")
                str_filhos_fora_final = "\n".join(lista_ff)

                novo_registro = {col: "" for col in df.columns}
                if 'Carimbo de data/hora' in df.columns:
                    novo_registro['Carimbo de data/hora'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                novo_registro[col_nome1] = n1
                novo_registro[col_conjuge] = n2
                novo_registro[col_tel] = tel
                if 'E-mail:' in df.columns:
                    novo_registro['E-mail:'] = email
                novo_registro[col_endereco] = end
                novo_registro[col_nasc1] = dt_n1
                novo_registro[col_nasc2] = dt_n2
                novo_registro[col_casamento] = dt_cas
                
                df_novo = pd.DataFrame([novo_registro])
                df_final = pd.concat([df, df_novo], ignore_index=True)
                df_final.to_excel(NOME_ARQUIVO, index=False)
                st.success("✅ Novo casal incluído com sucesso no banco de dados!")
                st.cache_data.clear()
                st.rerun()

    # ==========================================
    # 6. OPÇÃO "EDITAR"
    # ==========================================
    elif acao == "editar":
        opcoes_casais = [f"{i}: {r[col_nome1]} & {r[col_conjuge]}" for i, r in df.iterrows()]
        selecionado = st.selectbox("Selecione o Casal para editar:", opcoes_casais, key="select_edicao_casal")
        
        if selecionado:
            idx = int(selecionado.split(":")[0])
            registro = df.loc[idx].to_dict()
            
            with st.form("form_edicao"):
                st.markdown("### ✏️ Editando Dados Completos do Casal")
                c1, c2 = st.columns(2)
                n1 = c1.text_input("Nome do Esposo(a) 1", value=str(registro.get(col_nome1, '')))
                n2 = c2.text_input("Nome do Esposo(a) 2", value=str(registro.get(col_conjuge, '')))
                
                c3, c4, c5 = st.columns(3)
                tel = c3.text_input("Telefone", value=str(registro.get(col_tel, '')))
                email = c4.text_input("E-mail", value=str(registro.get('E-mail:', '')))
                end = c5.text_input("Endereço", value=str(registro.get(col_endereco, '')))
                
                c6, c7, c8 = st.columns(3)
                dt_n1 = c6.text_input("Nascimento 1 (DD/MM/AAAA)", value=formatar_data_para_br(registro.get(col_nasc1, '')))
                dt_n2 = c7.text_input("Nascimento 2 (DD/MM/AAAA)", value=formatar_data_para_br(registro.get(col_nasc2, '')))
                dt_cas = c8.text_input("Data de Casamento (DD/MM/AAAA)", value=formatar_data_para_br(registro.get(col_casamento, '')))
                
                filhos_atual_texto = str(registro.get(col_filhos, ''))
                st.markdown("#### 👶 Filhos do Casal (Formatados)")
                st.markdown(formatar_exibicao_filhos(filhos_atual_texto))
                
                filhos_fora_texto = str(registro.get(col_filhos_fora, ''))
                st.markdown("#### 👶 Filhos Fora do Casamento (Formatados)")
                st.markdown(formatar_exibicao_filhos(filhos_fora_texto))

                salvar = st.form_submit_button("💾 Salvar Alterações")
                
                if salvar:
                    df[col_nome1] = df[col_nome1].astype(str)
                    df[col_conjuge] = df[col_conjuge].astype(str)

                    df.at[idx, col_nome1] = n1
                    df.at[idx, col_conjuge] = n2
                    df.at[idx, col_tel] = tel
                    if 'E-mail:' in df.columns:
                        df.at[idx, 'E-mail:'] = email
                    df.at[idx, col_endereco] = end
                    df.at[idx, col_nasc1] = dt_n1
                    df.at[idx, col_nasc2] = dt_n2
                    df.at[idx, col_casamento] = dt_cas
                    
                    df.to_excel(NOME_ARQUIVO, index=False)
                    st.success("Cadastro atualizado com sucesso!")
                    st.cache_data.clear()
                    st.rerun()

    # ==========================================
    # 7. OPÇÃO "EXCLUIR"
    # ==========================================
    elif acao == "excluir":
        st.warning("⚠️ Atenção: A exclusão de um registro é permanente na base de dados local.")
        opcoes_excluir = [f"{i}: {r[col_nome1]} & {r[col_conjuge]}" for i, r in df.iterrows()]
        selecionado_excluir = st.selectbox("Selecione o Casal que deseja remover:", opcoes_excluir, key="select_excluir_casal")
        
        if selecionado_excluir:
            idx_exc = int(selecionado_excluir.split(":")[0])
            casal_nome = f"{df.loc[idx_exc, col_nome1]} & {df.loc[idx_exc, col_conjuge]}"
            
            col_btn1, col_btn2 = st.columns([1, 4])
            confirmar = col_btn1.button("🗑️ Confirmar Exclusão", key="btn_confirma_exclusao")
            
            if confirmar:
                df = df.drop(idx_exc).reset_index(drop=True)
                df.to_excel(NOME_ARQUIVO, index=False)
                st.success(f"✅ O cadastro de '{casal_nome}' foi removido com sucesso!")
                st.cache_data.clear()
                st.rerun()

    # ==========================================
    # 8. OPÇÃO "RELATÓRIOS POR CICLOS"
    # ==========================================
    elif acao == "relatorios":
        st.markdown("### 📊 Relatórios Pastorais por Ciclos de Casamento")
        st.write("Gere o relatório completo com a distribuição dos casais baseada nas fases do casamento.")

        if st.button("📊 Gerar Relatório por Ciclos", key="btn_gerar_relatorio_ciclos"):
            st.session_state['html_relatorio'] = relatorios.gerar_html_relatorio()
            st.success("Relatório gerado com sucesso! Veja a visualização e a opção de impressão abaixo.")

        if 'html_relatorio' in st.session_state:
            st.markdown("---")
            st.subheader("Visualização para Impressão")
            components.html(st.session_state['html_relatorio'], height=600, scrolling=True)
            
            botao_imprimir = """
            <script>
            function imprimirRelatorio() {
                var janela = window.open('', '', 'height=700,width=900');
                janela.document.write(document.querySelector('iframe').contentDocument.documentElement.innerHTML);
                janela.document.close();
                janela.focus();
                setTimeout(() => { janela.print(); }, 500);
            }
            </script>
            <button onclick="imprimirRelatorio()" style="background-color: #2e75b6; color: white; padding: 10px 20px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin-top: 15px;">
                🖨️ Imprimir / Salvar PDF do Relatório
            </button>
            """
            components.html(botao_imprimir, height=80)

    # ==========================================
    # 9. OPÇÃO "AGENDA DO MINISTÉRIO"
    # ==========================================
    elif acao == "agenda":
        agenda.modulo_agenda()

    st.markdown("<br><br>", unsafe_allow_html=True)
    cols_centro = st.columns([2, 1, 2])
    with cols_centro[1]:
        if st.button("🚪 Sair do Sistema", use_container_width=True, key="btn_sair_sistema"):
            st.session_state["logado_agora"] = False
            st.session_state["acao_gestao"] = ""
            st.rerun()
# ... (todo o restante do seu código anterior do app.py continua aqui em cima) ...

# --- REGISTRO DE ACOMPANHAMENTO NA BARRA LATERAL ---
st.sidebar.markdown("---")
st.sidebar.subheader("📝 Registrar Acompanhamento")

# Carrega os casais da planilha do Google para preencher os selects
try:
  df_google = pd.read_csv(LINK_PLANILHA_GOOGLE)
  # Cria lista de nomes dos casais (Esposo & Cônjuge)
  lista_casais = (
      df_google.iloc[:, 2].astype(str) + " & " + df_google.iloc[:, 5].astype(str)
  ).tolist()
except Exception:
  lista_casais = []

casal_escolhido = st.sidebar.selectbox(
    "Casal Sendo Acompanhado", lista_casais
)
casal_lider_resp = st.sidebar.selectbox(
    "Casal Líder Responsável",
    [
        "Marcelo & Gilmara",
        "Tony & Jessica",
        "Bruno & Marluce",
        "Jessica & Arlindo",
        "Thiago & Amanda",
    ],
)
tipo_acao = st.sidebar.selectbox(
    "Tipo de Atendimento", ["Aconselhamento", "Visita no Lar"]
)
data_atendimento = st.sidebar.date_input("Data do Atendimento")
descricao_detalhes = st.sidebar.text_area(
    "Detalhes (Oração, orientações, auxílio, etc.)"
)

if st.sidebar.button("Salvar Registro de Acompanhamento"):
  if casal_escolhido and descricao_detalhes:
    ba.salvar_registro(
        casal_escolhido,
        casal_lider_resp,
        tipo_acao,
        data_atendimento.strftime("%d/%m/%Y"),
        descricao_detalhes,
    )
    st.sidebar.success("Acompanhamento salvo com sucesso!")
  else:
    st.sidebar.error("Preencha todos os campos corretamente.")