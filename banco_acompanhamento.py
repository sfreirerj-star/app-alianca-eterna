import sqlite3


def inicializar_banco():
  conn = sqlite3.connect("acompanhamento.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            casal_alvo TEXT,
            casal_lider TEXT,
            tipo TEXT,
            data_atendimento TEXT,
            descricao TEXT
        )
    """)
  conn.commit()
  conn.close()


def salvar_registro(casal_alvo, casal_lider, tipo, data_atendimento, descricao):
  inicializar_banco()
  conn = sqlite3.connect("acompanhamento.db")
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO registros (casal_alvo, casal_lider, tipo, data_atendimento, descricao)
        VALUES (?, ?, ?, ?, ?)
    """,
      (casal_alvo, casal_lider, tipo, data_atendimento, descricao),
  )
  conn.commit()
  conn.close()


def carregar_registros():
  inicializar_banco()
  conn = sqlite3.connect("acompanhamento.db")
  import pandas as pd

  df = pd.read_sql_query("SELECT * FROM registros", conn)
  conn.close()
  return df
