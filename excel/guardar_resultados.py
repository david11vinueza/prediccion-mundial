import gspread
from google.oauth2.service_account import Credentials
import requests
import os
import json

API_COMPETITION = "WC"
API_BASE_URL = "https://api.football-data.org/v4"

# =========================================================
# FUNCIÓN CENTRAL PARA CREDENCIALES (RENDER + LOCAL)
# =========================================================
def obtener_credenciales():
    if os.environ.get("GOOGLE_CREDENTIALS"):
        info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
        return Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
    return Credentials.from_service_account_file(
        "excel/credenciales.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

# =========================================================
# TRADUCCIÓN DE NOMBRES (EN → ES)
# =========================================================
TRAD = {
    "Czechia": "Chequia",
    "Mexico": "México",
    "South Africa": "Sudáfrica",
    "South Korea": "República de Corea",
    "Bosnia-Herzegovina": "Bosnia y Herzegovina",
    "Canada": "Canadá",
    "Qatar": "Catar",
    "Switzerland": "Suiza",
    "Brazil": "Brasil",
    "Morocco": "Marruecos",
    "Haiti": "Haití",
    "Scotland": "Escocia",
    "Turkey": "Turquía",
    "United States": "Estados Unidos",
    "Paraguay": "Paraguay",
    "Australia": "Australia",
    "Germany": "Alemania",
    "Curaçao": "Curazao",
    "Ivory Coast": "Costa de Marfil",
    "Ecuador": "Ecuador",
    "Sweden": "Suecia",
    "Netherlands": "Países Bajos",
    "Japan": "Japón",
    "Tunisia": "Túnez",
    "Belgium": "Bélgica",
    "Egypt": "Egipto",
    "Iran": "Irán",
    "New Zealand": "Nueva Zelanda",
    "Spain": "España",
    "Cape Verde Islands": "Cabo Verde",
    "Saudi Arabia": "Arabia Saudita",
    "Uruguay": "Uruguay",
    "Iraq": "Irak",
    "France": "Francia",
    "Senegal": "Senegal",
    "Norway": "Noruega",
    "Argentina": "Argentina",
    "Algeria": "Argelia",
    "Austria": "Austria",
    "Jordan": "Jordania",
    "Congo DR": "R. D. del Congo",
    "Portugal": "Portugal",
    "Uzbekistan": "Uzbekistán",
    "Colombia": "Colombia",
    "England": "Inglaterra",
    "Croatia": "Croacia",
    "Ghana": "Ghana",
    "Panama": "Panamá"
}

def t(x):
    return TRAD.get(x, x)

# =========================================================
# 1. VERIFICAR SI USUARIO YA EXISTE
# =========================================================
def usuario_existe(ws, nombre, apellido, cedula):
    registros = ws.get_all_records()
    participantes = registros[1:]

    for fila in participantes:
        if (
            fila.get("Nombre", "").strip().lower() == nombre.strip().lower() and
            fila.get("Apellido", "").strip().lower() == apellido.strip().lower() and
            str(fila.get("Cédula", "")).strip() == str(cedula).strip()
        ):
            return True
    return False

# =========================================================
# 2. CREAR ENCABEZADOS (FILA 1)
# =========================================================
def inicializar_encabezados(ws):

    encabezados = ["Nombre", "Apellido", "Edad", "Cédula", "Celular"]

    grupos = ["A","B","C","D","E","F","G","H","I","J","K","L"]
    for g in grupos:
        encabezados += [
            f"{g} - 1°",
            f"{g} - 2°",
            f"{g} - 3°",
            f"{g} - 4°"
        ]

    for i in range(1, 9):
        encabezados.append(f"Mejor Tercero {i}")

    encabezados += [
        "Goleador",
        "Campeón",
        "Vicecampeón",
        "Tercer Lugar",
        "Coincidencia de posiciones",
        "Coincidencias clasificados",
        "Coincidencia de goleador",
        "Puntos"
    ]

    ws.update("A1", [encabezados])

# =========================================================
# 3. OBTENER GOLEADOR ACTUAL
# =========================================================
def obtener_goleador_actual(api_key):
    try:
        url = f"{API_BASE_URL}/competitions/{API_COMPETITION}/scorers"
        headers = {"X-Auth-Token": api_key}
        r = requests.get(url, headers=headers)
        data = r.json()

        if "scorers" not in data or len(data["scorers"]) == 0:
            return ""

        return t(data["scorers"][0]["player"]["name"])
    except:
        return ""

# =========================================================
# 4. OBTENER TERCEROS
# =========================================================
def obtener_terceros_stats(api_key):
    try:
        url = f"{API_BASE_URL}/competitions/{API_COMPETITION}/standings"
        headers = {"X-Auth-Token": api_key}
        r = requests.get(url, headers=headers)
        data = r.json()

        terceros = []

        if "standings" not in data:
            return terceros

        for standing in data["standings"]:
            if standing["type"] != "TOTAL":
                continue

            tabla = standing["table"]
            if len(tabla) < 3:
                continue

            tercero = tabla[2]

            terceros.append({
                "pais": t(tercero["team"]["name"]),
                "puntos": tercero["points"],
                "dg": tercero["goalDifference"],
                "gf": tercero["goalsFor"]
            })

        return terceros
    except:
        return []

# =========================================================
# 5. ORDENAR MEJORES TERCEROS
# =========================================================
def ordenar_mejores_terceros(terceros_stats):
    ordenados = sorted(
        terceros_stats,
        key=lambda x: (x["puntos"], x["dg"], x["gf"]),
        reverse=True
    )
    return [t["pais"] for t in ordenados[:8]]

# =========================================================
# 6. ACTUALIZAR FILA 2 (RESULTADOS REALES)
# =========================================================
def actualizar_fila2(ws, api_key):

    inicializar_encabezados(ws)

    filas = ws.get_all_values()
    if len(filas) < 2:
        ws.append_row([""] * 70)

    fila2 = [""] * 5

    grupos_reales = {}
    grupos = ["A","B","C","D","E","F","G","H","I","J","K","L"]

    try:
        url = f"{API_BASE_URL}/competitions/{API_COMPETITION}/standings"
        headers = {"X-Auth-Token": api_key}
        r = requests.get(url, headers=headers)
        data = r.json()

        if "standings" in data:
            for standing in data["standings"]:
                if standing["type"] != "TOTAL":
                    continue

                group_code = standing.get("group", "")
                if not group_code.lower().startswith("group "):
                    continue

                g = group_code.split(" ")[1]

                tabla = standing["table"]

                if len(tabla) >= 4:
                    grupos_reales[g] = [
                        t(tabla[0]["team"]["name"]),
                        t(tabla[1]["team"]["name"]),
                        t(tabla[2]["team"]["name"]),
                        t(tabla[3]["team"]["name"])
                    ]
    except:
        grupos_reales = {}

    for g in grupos:
        fila2.extend(grupos_reales.get(g, ["", "", "", ""]))

    try:
        terceros_stats = obtener_terceros_stats(api_key)
        mejores_8 = ordenar_mejores_terceros(terceros_stats)
    except:
        mejores_8 = []

    while len(mejores_8) < 8:
        mejores_8.append("")
    fila2.extend(mejores_8)

    fila2.append(obtener_goleador_actual(api_key))

    fila2 += ["", "", ""]

    ws.update("A2", [fila2])

# =========================================================
# 7. CONSTRUIR REALES DESDE FILA 2
# =========================================================
def construir_reales_desde_fila2(fila2):

    reales = {"grupos": {}, "terceros": [], "goleador": "", "campeon": "", "vice": "", "tercero": ""}

    idx = 5
    grupos = ["A","B","C","D","E","F","G","H","I","J","K","L"]

    for g in grupos:
        reales["grupos"][g] = fila2[idx:idx+4]
        idx += 4

    reales["terceros"] = fila2[idx:idx+8]
    idx += 8

    reales["goleador"] = fila2[idx] if idx < len(fila2) else ""
    reales["campeon"] = fila2[idx+1] if idx+1 < len(fila2) else ""
    reales["vice"] = fila2[idx+2] if idx+2 < len(fila2) else ""
    reales["tercero"] = fila2[idx+3] if idx+3 < len(fila2) else ""

    return reales

# =========================================================
# 8. DETALLES DE ACIERTOS
# =========================================================
def generar_detalles_aciertos(reales, usuario):

    detalles_posiciones = []
    detalles_clasificados = []

    paises_posicion = set()

    # A) POSICIONES EXACTAS
    for g in reales["grupos"]:
        real = reales["grupos"][g]
        pred = usuario["grupos"][g]

        for i in range(4):
            if i < len(pred) and i < len(real) and pred[i] == real[i]:
                detalles_posiciones.append(f"{pred[i]} ({i+1}{g})")
                paises_posicion.add(pred[i])

    # B) CLASIFICADOS (SIN REPETIR LOS DE POSICIÓN)
    clasificados_reales = []
    for g in reales["grupos"]:
        clasificados_reales += reales["grupos"][g][:2]
    clasificados_reales += reales["terceros"]

    clasificados_usuario = []
    for g in usuario["grupos"]:
        clasificados_usuario += usuario["grupos"][g][:2]
    clasificados_usuario += usuario["terceros"]

    for pais in clasificados_usuario:
        if pais in clasificados_reales and pais not in paises_posicion:
            detalles_clasificados.append(pais)

    coincide_goleador = "Sí" if usuario["goleador"] == reales["goleador"] else "No"

    texto_pos = ", ".join(detalles_posiciones) + f" | Total: {len(detalles_posiciones)}"
    texto_clas = ", ".join(detalles_clasificados) + f" | Total: {len(detalles_clasificados)}"

    return texto_pos, texto_clas, coincide_goleador

# =========================================================
# 9. CALCULAR PUNTOS
# =========================================================
def calcular_puntos(reales, usuario):

    puntos = 0
    paises_ya_puntuados = set()

    # POSICIONES EXACTAS
    for g in reales["grupos"]:
        real = reales["grupos"][g]
        pred = usuario["grupos"][g]

        for i in range(4):
            if i < len(pred) and i < len(real):
                if pred[i] == real[i]:
                    puntos += 25
                    paises_ya_puntuados.add(pred[i])

    # CLASIFICADOS
    clasificados_reales = []
    for g in reales["grupos"]:
        clasificados_reales += reales["grupos"][g][:2]
    clasificados_reales += reales["terceros"]

    clasificados_usuario = []
    for g in usuario["grupos"]:
        clasificados_usuario += usuario["grupos"][g][:2]
    clasificados_usuario += usuario["terceros"]

    for pais in clasificados_usuario:
        if pais in clasificados_reales and pais not in paises_ya_puntuados:
            puntos += 10
            paises_ya_puntuados.add(pais)

    # GOLEADOR FASE GRUPOS
    if usuario["goleador"] == reales["goleador"]:
        puntos += 100

    # PODIO (predicción inicial)
    if usuario["campeon"] == reales["campeon"]:
        puntos += 500
    if usuario["vice"] == reales["vice"]:
        puntos += 250
    if usuario["tercero"] == reales["tercero"]:
        puntos += 125

    return puntos

# =========================================================
# 10. RECALCULAR TODOS
# =========================================================
def recalcular_todos(ws, api_key):

    registros = ws.get_all_records()
    if len(registros) < 2:
        return

    fila2 = ws.row_values(2)
    reales = construir_reales_desde_fila2(fila2)

    all_rows = ws.get_all_values()
    grupos = ["A","B","C","D","E","F","G","H","I","J","K","L"]

    updates = []

    for i in range(3, len(all_rows)+1):

        fila = ws.row_values(i)

        usuario = {
            "grupos": {},
            "terceros": [],
            "goleador": "",
            "campeon": "",
            "vice": "",
            "tercero": ""
        }

        idx_u = 5
        for g in grupos:
            usuario["grupos"][g] = fila[idx_u:idx_u+4]
            idx_u += 4

        usuario["terceros"] = fila[idx_u:idx_u+8]
        idx_u += 8

        usuario["goleador"] = fila[idx_u] if idx_u < len(fila) else ""
        usuario["campeon"] = fila[idx_u+1] if idx_u+1 < len(fila) else ""
        usuario["vice"] = fila[idx_u+2] if idx_u+2 < len(fila) else ""
        usuario["tercero"] = fila[idx_u+3] if idx_u+3 < len(fila) else ""

        puntos = calcular_puntos(reales, usuario)
        texto_pos, texto_clas, coincide_gol = generar_detalles_aciertos(reales, usuario)

        nueva_fila = fila
        if len(nueva_fila) < 5 + 4*12 + 8 + 4:
            while len(nueva_fila) < 5 + 4*12 + 8 + 4:
                nueva_fila.append("")

        nueva_fila[-4] = texto_pos
        nueva_fila[-3] = texto_clas
        nueva_fila[-2] = coincide_gol
        nueva_fila[-1] = puntos

        updates.append(nueva_fila)

    if updates:
        rango = f"A3"
        ws.update(rango, updates)

# =========================================================
# 11. GUARDAR RESULTADOS (INSCRIPCIÓN)
# =========================================================
def guardar_resultados(datos, SHEET_ID, api_key):

    creds = obtener_credenciales()
    cliente = gspread.authorize(creds)
    ws = cliente.open_by_key(SHEET_ID).sheet1

    fila2 = ws.row_values(2)
    reales = construir_reales_desde_fila2(fila2)

    grupos = ["A","B","C","D","E","F","G","H","I","J","K","L"]

    terceros_paises = []
    for g in datos["terceros"]:
        pais = datos["terceros_real"].get(g, "")
        if pais:
            terceros_paises.append(pais)

    usuario = {
        "grupos": {},
        "terceros": terceros_paises,
        "goleador": datos["goleador"],
        "campeon": datos["campeon"],
        "vice": datos["vice"],
        "tercero": datos["tercero_final"]
    }

    for g in grupos:
        usuario["grupos"][g] = [x.strip() for x in datos["grupos"][g].split(",")]

    puntos = calcular_puntos(reales, usuario)
    texto_pos, texto_clas, coincide_gol = generar_detalles_aciertos(reales, usuario)

    fila = [
        datos["nombre"],
        datos["apellido"],
        datos["edad"],
        datos["cedula"],
        datos["celular"]
    ]

    for g in grupos:
        fila.extend(usuario["grupos"][g])

    fila.extend(usuario["terceros"])

    fila.append(datos["goleador"])
    fila.append(datos["campeon"])
    fila.append(datos["vice"])
    fila.append(datos["tercero_final"])

    fila.append(texto_pos)
    fila.append(texto_clas)
    fila.append(coincide_gol)
    fila.append(puntos)

    # Escribir la fila completa en la siguiente fila disponible
    ultima_fila = len(ws.get_all_values()) + 1
    rango = f"A{ultima_fila}"
    ws.update(rango, [fila])

    return True
