from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from data.banderas import BANDERAS
import os

def generar_pdf_prediccion(datos):

    ruta = "static/prediccion.pdf"
    c = canvas.Canvas(ruta, pagesize=letter)
    width, height = letter

    # =========================================================
    # ENCABEZADO
    # =========================================================
    def encabezado(titulo):
        c.setFillColorRGB(0.15, 0.16, 0.45)
        c.rect(0, height - 70, width, 70, fill=1)

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 26)
        c.drawString(40, height - 40, "MUNDIAL 2026")

        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height - 60, titulo)

    # =========================================================
    # DATOS PERSONALES
    # =========================================================
    def datos_personales(y):
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, f"Participante: {datos['nombre']} {datos['apellido']}")
        y -= 18
        c.setFont("Helvetica", 11)
        c.drawString(40, y, f"Edad: {datos['edad']}   Cédula: {datos['cedula']}   Celular: {datos['celular']}")
        return y - 30

    # =========================================================
    # NORMALIZAR LISTA DE PAISES
    # =========================================================
    def normalizar(valor):
        if isinstance(valor, list):
            return valor
        if isinstance(valor, str):
            return [p.strip() for p in valor.split(",") if p.strip()]
        return []

    # =========================================================
    # IMPRIMIR GRUPO (UNA COLUMNA)
    # =========================================================
    def imprimir_grupo(x, y, nombre_grupo, valor_paises):
        lista = normalizar(valor_paises)

        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, f"Grupo {nombre_grupo}")
        y -= 18

        c.setFont("Helvetica", 12)
        for pais in lista:

            if pais in BANDERAS:
                bandera = f"static/img/banderas/{BANDERAS[pais]}.png"
                if os.path.exists(bandera):
                    c.drawImage(bandera, x, y - 5, width=16, height=12)
                c.drawString(x + 25, y, pais)
            else:
                c.drawString(x + 25, y, f"{pais} (sin bandera)")

            y -= 16

        return y - 10

    grupos = datos["grupos"]

    # =========================================================
    # =====================  PÁGINA 1  ========================
    # =========================================================
    encabezado("Predicción Oficial — Página 1")
    y = height - 110
    y = datos_personales(y)

    # Grupos en pares (misma línea)
    pares = [("A", "B"), ("C", "D"), ("E", "F"), ("G", "H"), ("I", "J")]

    for g1, g2 in pares:
        y1 = imprimir_grupo(40, y, g1, grupos[g1])
        y2 = imprimir_grupo(300, y, g2, grupos[g2])
        y = min(y1, y2) - 20

    c.showPage()

    # =========================================================
    # =====================  PÁGINA 2  ========================
    # =========================================================
    encabezado("Predicción Oficial — Página 2")
    y = height - 110
    y = datos_personales(y)

    # Grupos K y L en la misma línea
    y1 = imprimir_grupo(40, y, "K", grupos.get("K", []))
    y2 = imprimir_grupo(300, y, "L", grupos.get("L", []))
    y = min(y1, y2) - 30

    # MEJORES TERCEROS
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Mejores terceros")
    y -= 25

    c.setFont("Helvetica", 12)
    for t in datos["terceros"]:
        pais = datos["terceros_real"][t]

        if pais in BANDERAS:
            bandera = f"static/img/banderas/{BANDERAS[pais]}.png"
            if os.path.exists(bandera):
                c.drawImage(bandera, 40, y - 5, width=16, height=12)

        c.drawString(65, y, f"{pais} (Grupo {t})")
        y -= 16

    y -= 30

    # GOLEADOR
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Goleador")
    y -= 25

    goleador = datos["goleador"]

    # Buscar país del goleador
    pais_goleador = None
    for grupo, lista in grupos.items():
        lista_norm = normalizar(lista)
        if goleador in lista_norm:
            pais_goleador = goleador
            break

    if pais_goleador and pais_goleador in BANDERAS:
        bandera = f"static/img/banderas/{BANDERAS[pais_goleador]}.png"
        if os.path.exists(bandera):
            c.drawImage(bandera, 40, y - 5, width=16, height=12)

    c.setFont("Helvetica", 12)
    c.drawString(65, y, goleador)
    y -= 40

    # PREDICCIONES FINALES
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Predicciones finales")
    y -= 25

    # CAMPEÓN
    campeon = datos["campeon"]
    if campeon in BANDERAS:
        bandera = f"static/img/banderas/{BANDERAS[campeon]}.png"
        if os.path.exists(bandera):
            c.drawImage(bandera, 40, y - 5, width=16, height=12)
    c.setFont("Helvetica", 12)
    c.drawString(65, y, f"Campeón: {campeon}")
    y -= 18

    # VICECAMPEÓN
    vice = datos["vice"]
    if vice in BANDERAS:
        bandera = f"static/img/banderas/{BANDERAS[vice]}.png"
        if os.path.exists(bandera):
            c.drawImage(bandera, 40, y - 5, width=16, height=12)
    c.drawString(65, y, f"Vicecampeón: {vice}")
    y -= 18

    # TERCER LUGAR
    tercero = datos["tercero_final"]
    if tercero in BANDERAS:
        bandera = f"static/img/banderas/{BANDERAS[tercero]}.png"
        if os.path.exists(bandera):
            c.drawImage(bandera, 40, y - 5, width=16, height=12)
    c.drawString(65, y, f"3er lugar: {tercero}")

    c.save()
    return ruta
