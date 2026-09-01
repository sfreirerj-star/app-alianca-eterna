import sqlite3
from datetime import datetime
import os
import pandas as pd

LINK_PLANILHA_GOOGLE = "https://docs.google.com/spreadsheets/d/1Zy2qTGHHqzLhim_ebHsCFgNrHBzPB1AxSscoQZXh3Vc/export?format=csv"

CASAIS_LIDERES = [
    ("marcelo", "gilmara"),
    ("tony", "jessica"),
    ("bruno", "marluce"),
    ("jessica", "arlindo"),
    ("thiago", "amanda"),
]


def carregar_acompanhamentos():
  if not os.path.exists("acompanhamento.db"):
    return pd.DataFrame(
        columns=[
            "id",
            "casal_alvo",
            "casal_lider",
            "tipo",
            "data_atendimento",
            "descricao",
        ]
    )
  conn = sqlite3.connect("acompanhamento.db")
  df = pd.read_sql_query("SELECT * FROM registros", conn)
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
    col_email = (
        next((c for c in cols if "email" in c.lower()), cols[1])
        if len(cols) > 1
        else cols[0]
    )
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
            (
                c
                for c in cols
                if "cônjuge" in c.lower() and "nome" in c.lower()
            ),
            cols[5],
        )
        if len(cols) > 5
        else cols[1]
    )
    col_data_casamento = (
        next(
            (
                c
                for c in cols
                if "casamento" in c.lower() or "união" in c.lower()
            ),
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

    ciclos = {
        "1º Ciclo: Primeiros Anos (0 a 4 anos)": [],
        "2º Ciclo: Consolidação (5 a 9 anos)": [],
        "3º Ciclo: Maturidade (10 a 19 anos)": [],
        "4º Ciclo: Aliança Sólida (20 anos ou mais)": [],
    }

    for _, row in df.iterrows():
      d_casamento = row.get(col_data_casamento, "")
      anos = calcular_anos_casamento(d_casamento)
      n1 = str(row.get(col_nome1, ""))
      n2 = str(row.get(col_nome2, ""))
      is_lider = e_lider(n1, n2)
      nome_formatado = f"{n1} & {n2}"

      # Filtra os acompanhamentos deste casal específico
      historico_casal = ""
      if not df_acomp.empty:
        match_acomp = df_acomp[
            df_acomp["casal_alvo"].str.strip().str.lower()
            == nome_formatado.strip().lower()
        ]
        for _, ac in match_acomp.iterrows():
          historico_casal += f"""
                    <div class="alert alert-secondary py-1 px-2 my-1 small">
                        <b>[{ac['tipo']}] Data:</b> {ac['data_atendimento']} | <b>Líder:</b> {ac['casal_lider']}<br>
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

      if anos <= 4:
        ciclos["1º Ciclo: Primeiros Anos (0 a 4 anos)"].append(dados_casal)
      elif anos <= 9:
        ciclos["2º Ciclo: Consolidação (5 a 9 anos)"].append(dados_casal)
      elif anos <= 19:
        ciclos["3º Ciclo: Maturidade (10 a 19 anos)"].append(dados_casal)
      else:
        ciclos["4º Ciclo: Aliança Sólida (20 anos ou mais)"].append(dados_casal)

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
                            <tbody>
                                {linhas_tabela}
                            </tbody>
                        </table>
                    </div>
                </div>
                """

    html_completo = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Relatório de Acompanhamento Pastoral</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        </head>
        <body class="container py-4">
            <h2 class="mb-2 text-primary">Relatório Pastoral - Histórico de Acompanhamento</h2>
            <p class="text-muted"><b>Data de Emissão:</b> {data_emissao} | <b>Total geral de casais cadastrados:</b> {total_casais}</p>
            <hr class="mb-4">
            {html_ciclos}
        </body>
        </html>
        """
    return html_completo

  except Exception as e:
    return f"<h3>Erro ao gerar relatório com histórico: {e}</h3>"