from datetime import datetime
import os
import pandas as pd
import sqlite3

LINK_PLANILHA_GOOGLE = "https://docs.google.com/spreadsheets/d/1Zy2qTGHHqzLhim_ebHsCFgNrHBzPB1AxSscoQZXh3Vc/export?format=csv"

CASAIS_LIDERES = [
    ("marcelo", "gilmara"),
    ("tony", "jessica"),
    ("bruno", "marluce"),
    ("jessica", "arlindo"),
    ("thiago", "amanda"),
]

# Lista padrão de categorias/problemas para acompanhamento direcionado
CATEGORIAS_DESAFIOS = [
    "Infidelidade",
    "Violência Doméstica",
    "Vícios",
    "Processo de Separação",
    "Brigas Conjugais / Conflitos",
    "Outros / Geral",
]


def carregar_acompanhamentos():
  if not os.path.exists("acompanhamento.db"):
    return pd.DataFrame(
        columns=[
            "id",
            "casal_alvo",
            "casal_lider",
            "tipo",
            "motivo",  # Novo campo para a categoria do problema
            "data_atendimento",
            "descricao",
        ]
    )
  conn = sqlite3.connect("acompanhamento.db")
  try:
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    # Garante compatibilidade caso a coluna 'motivo' ainda não exista em bancos antigos
    if "motivo" not in df.columns:
      df["motivo"] = "Outros / Geral"
  except Exception:
    df = pd.DataFrame(
        columns=[
            "id",
            "casal_alvo",
            "casal_lider",
            "tipo",
            "motivo",
            "data_atendimento",
            "descricao",
        ]
    )
  conn.close()
  return df


def calcular_anos_casamento(data_casamento_str):
  try:
    if pd.isna(data_casamento_str) or not str(data_casamento_str).strip():
      return 0
    dt = pd.to_datetime(data_casamento_str, errors="coerce", dayfirst=True)
    if pd.isna(dt):
      return 0
    hoje = datetime.now()
    anos = (
        hoje.year
        - dt.year
        - ((hoje.month, hoje.day) < (dt.month, dt.day))
    )
    return max(0, anos)
  except Exception:
    return 0


def e_lider(nome1, nome2):
  n1 = str(nome1).strip().lower()
  n2 = str(nome2).strip().lower()
  for l1, l2 in CASAIS_LIDERES:
    if (l1 in n1 and l2 in n2) or (l1 in n2 and l2 in n1):
      return True
  return False


def gerar_html_relatorio():
  try:
    if "COLOQUE_SEU_LINK" in LINK_PLANILHA_GOOGLE:
      return "<h3>Erro: Link da planilha do Google não configurado.</h3>"

    df = pd.read_csv(LINK_PLANILHA_GOOGLE)
    df_acomp = carregar_acompanhamentos()

    if df.empty:
      return "<h3>Nenhum cadastro encontrado na planilha.</h3>"

    df.columns = df.columns.str.strip()
    if any(df.columns.str.contains("Unnamed")):
      df = df.loc[:, ~df.columns.str.contains("Unnamed")]

    total_casais = len(df)
    data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")

    cols = df.columns
    col_nome1 = (
        next(
            (
                c
                for c in cols
                if "nome" in c.lower() and "cônjuge" not in c.lower()
            ),
            cols[2],
        )
        if len(cols) > 2
        else cols[0]
    )
    col_nome2 = (
        next(
            (c for c in cols if "cônjuge" in c.lower() and "nome" in c.lower()),
            cols[5],
        )
        if len(cols) > 5
        else cols[1]
    )
    col_data_casamento = (
        next(
            (c for c in cols if "casamento" in c.lower() or "união" in c.lower()),
            cols[4],
        )
        if len(cols) > 4
        else cols[0]
    )
    col_tel = (
        next(
            (
                c
                for c in cols
                if "telefone" in c.lower() or "celular" in c.lower()
            ),
            cols[6],
        )
        if len(cols) > 6
        else cols[0]
    )

    # 1. Estrutura por Ciclos de Casamento
    ciclos = {
        "1º Ciclo: Primeiros Anos (0 a 4 anos)": [],
        "2º Ciclo: Consolidação (5 a 9 anos)": [],
        "3º Ciclo: Maturidade (10 a 19 anos)": [],
        "4º Ciclo: Aliança Sólida (20 anos ou mais)": [],
    }

    # 2. Estrutura por Blocos de Desafios/Problemas Conjugais
    mapeamento_desafios = {categoria: [] for categoria in CATEGORIAS_DESAFIOS}

    for _, row in df.iterrows():
      d_casamento = row.get(col_data_casamento, "")
      anos = calcular_anos_casamento(d_casamento)
      n1 = str(row.get(col_nome1, ""))
      n2 = str(row.get(col_nome2, ""))
      is_lider = e_lider(n1, n2)
      nome_formatado = f"{n1} & {n2}"

      historico_casal = ""
      categorias_deste_casal = set()

      if not df_acomp.empty:
        match_acomp = df_acomp[
            df_acomp["casal_alvo"].str.strip().str.lower()
            == nome_formatado.strip().lower()
        ]
        for _, ac in match_acomp.iterrows():
          motivo_atendimento = ac.get("motivo", "Outros / Geral")
          if motivo_atendimento not in mapeamento_desafios:
            motivo_atendimento = "Outros / Geral"
          categorias_deste_casal.add(motivo_atendimento)

          badge_motivo = f'<span class="badge bg-danger">{motivo_atendimento}</span>'
          historico_casal += f"""
                    <div class="alert alert-secondary py-1 px-2 my-1 small">
                        <b>[{ac['tipo']}]</b> {badge_motivo} | <b>Data:</b> {ac['data_atendimento']} | <b>Líder:</b> {ac['casal_lider']}<br>
                        <b>Relato:</b> {ac['descricao']}
                    </div>
                    """

      if not historico_casal:
        historico_casal = (
            '<p class="text-muted small mb-0">Nenhum registro ainda.</p>'
        )

      dados_casal = {
          "c1": n1,
          "c2": n2,
          "data": str(d_casamento),
          "tel": str(row.get(col_tel, "")),
          "lider": is_lider,
          "historico": historico_casal,
      }

      # Alimenta os ciclos temporais
      if anos <= 4:
        ciclos["1º Ciclo: Primeiros Anos (0 a 4 anos)"].append(dados_casal)
      elif anos <= 9:
        ciclos["2º Ciclo: Consolidação (5 a 9 anos)"].append(dados_casal)
      elif anos <= 19:
        ciclos["3º Ciclo: Maturidade (10 a 19 anos)"].append(dados_casal)
      else:
        ciclos["4º Ciclo: Aliança Sólida (20 anos ou mais)"].append(dados_casal)

      # Alimenta os blocos de desafios se houver registros vinculados
      for cat in categorias_deste_casal:
        mapeamento_desafios[cat].append(dados_casal)

    # Montagem HTML dos Ciclos
    html_ciclos = ""
    for nome_ciclo, lista in ciclos.items():
      if lista:
        linhas_tabela = ""
        for item in lista:
          estilo_linha = (
              'style="background-color: #e8f5e9; font-weight: bold;"'
              if item["lider"]
              else ""
          )
          badge_lider = (
              ' <span class="badge bg-success">🌟 Líder</span>'
              if item["lider"]
              else ""
          )
          linhas_tabela += f"""
                    <tr {estilo_linha}>
                        <td>{item['c1']} {badge_lider}</td>
                        <td>{item['c2']} {badge_lider}</td>
                        <td>{item['data']}</td>
                        <td>{item['tel']}</td>
                        <td>{item['historico']}</td>
                    </tr>
                    """
        html_ciclos += f"""
                <div class="card mb-4 shadow-sm">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">{nome_ciclo} ({len(lista)} casais)</h5>
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-striped table-bordered mb-0 align-middle">
                            <thead class="table-light">
                                <tr>
                                    <th>Esposo(a) 1</th>
                                    <th>Esposo(a) 2</th>
                                    <th>Data Casamento</th>
                                    <th>Telefone</th>
                                    <th>Histórico de Acompanhamento</th>
                                </tr>
                            </thead>
                            <tbody>{linhas_tabela}</tbody>
                        </table>
                    </div>
                </div>
                """

    # Montagem HTML específica para os Blocos de Desafios/Problemas
    html_desafios = ""
    for nome_desafio, lista_d in mapeamento_desafios.items():
      if lista_d:  # Só exibe se houver casais nessa categoria de atendimento
        linhas_tabela_d = ""
        for item in lista_d:
          linhas_tabela_d += f"""
                    <tr>
                        <td>{item['c1']}</td>
                        <td>{item['c2']}</td>
                        <td>{item['tel']}</td>
                        <td>{item['historico']}</td>
                    </tr>
                    """
        html_desafios += f"""
                <div class="card mb-4 shadow-sm border-warning">
                    <div class="card-header bg-warning text-dark">
                        <h5 class="mb-0">⚠️ Foco / Desafio: {nome_desafio} ({len(lista_d)} casais)</h5>
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-striped table-bordered mb-0 align-middle">
                            <thead class="table-light">
                                <tr>
                                    <th>Esposo(a) 1</th>
                                    <th>Esposo(a) 2</th>
                                    <th>Telefone</th>
                                    <th>Detalhes do Histórico</th>
                                </tr>
                            </thead>
                            <tbody>{linhas_tabela_d}</tbody>
                        </table>
                    </div>
                </div>
                """

    if not html_desafios:
      html_desafios = '<div class="alert alert-info">Nenhum atendimento categorizado por problema específico registrado até o momento.</div>'

    html_completo = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Relatório de Acompanhamento Pastoral</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        </head>
        <body class="container py-4">
            <h2 class="mb-2 text-primary">Relatório Pastoral - Acompanhamento e Mapeamento</h2>
            <p class="text-muted"><b>Data de Emissão:</b> {data_emissao} | <b>Total geral de casais cadastrados:</b> {total_casais}</p>
            <hr class="mb-4">
            
            <ul class="nav nav-tabs mb-4" id="relatorioTab" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="ciclos-tab" data-bs-toggle="tab" data-bs-target="#ciclos" type="button" role="tab">📅 Visão por Ciclos de Casamento</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="desafios-tab" data-bs-toggle="tab" data-bs-target="#desafios" type="button" role="tab">⚠️ Mapeamento por Desafios / Problemas</button>
                </li>
            </ul>

            <div class="tab-content" id="relatorioTabContent">
                <div class="tab-pane fade show active" id="ciclos" role="tabpanel">
                    {html_ciclos}
                </div>
                <div class="tab-pane fade" id="desafios" role="tabpanel">
                    <h4 class="mb-3 text-secondary">Casais Agrupados por Motivo de Acompanhamento</h4>
                    {html_desafios}
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """
    return html_completo

  except Exception as e:
    return f"<h3>Erro ao gerar relatório com histórico: {e}</h3>"