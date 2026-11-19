import webview

def rodar_app():
    # Cria a janela nativa apontando para o servidor local do Streamlit
    window = webview.create_window(
        "Sistema de Gestão Pastoral - Casais", 
        "http://localhost:8501", 
        width=1280, 
        height=800
    )
    webview.start()

if __name__ == '__main__':
    rodar_app()