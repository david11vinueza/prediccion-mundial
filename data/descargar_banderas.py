import requests
import os
from banderas import BANDERAS   # correcto porque el script está dentro de /data

# Crear carpeta si no existe
os.makedirs("static/img/banderas", exist_ok=True)

for pais, codigo in BANDERAS.items():
    url = f"https://flagcdn.com/w80/{codigo}.png"
    ruta = f"static/img/banderas/{codigo}.png"

    print(f"Descargando {pais}...")

    img = requests.get(url)
    with open(ruta, "wb") as f:
        f.write(img.content)

print("Listo. Todas las banderas descargadas.")
