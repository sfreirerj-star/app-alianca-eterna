import os
import sys

# Define o diretório base do projeto
base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)

# Verifica se foi passado algum argumento (ex: painel_app.py), senão usa o app.py padrão
if len(sys.argv) > 1:
    app_alvo = sys.argv[1]
else:
    # Se foi chamado pelo iniciar.bat normal, olha o nome do script ou padrão
    app_alvo = "app.py"

# Executa o Streamlit com o alvo correto
os.system(f"python -m streamlit run {app_alvo}")