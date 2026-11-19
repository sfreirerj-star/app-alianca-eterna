from PIL import Image

# Abre a imagem atual
img = Image.open("icone.png")

# Salva no formato de ícone do Windows com vários tamanhos padrão
img.save(
    "icone.ico",
    format="ICO",
    sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)],
)

print("Conversão concluída com sucesso! O arquivo icone.ico foi criado.")
