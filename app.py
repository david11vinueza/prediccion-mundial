from flask import Flask, render_template, request, redirect, session, send_file
from pdf.generar_pdf import generar_pdf_prediccion
from data.grupos import GRUPOS
from data.goleadores import GOLEADORES
from data.banderas import BANDERAS
from excel.guardar_resultados import (
    guardar_resultados,
    usuario_existe,
    recalcular_todos,
    actualizar_fila2,
    inicializar_encabezados
)

import gspread
from google.oauth2.service_account import Credentials

# Scheduler
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

import os
import shutil
import json

app = Flask(__name__)
app.secret_key = "clave-super-secreta"

SHEET_ID = "1iFC3Lxqz2cTEYMgg_5hWUlUxCw4KjC7S1skWgmAv2dQ"
API_KEY = "4c13ad48e7484c4b9dae8d50fea972fa"


# =========================================================
# GOOGLE SHEETS — CONEXIÓN GLOBAL (MODO RENDER + LOCAL)
# =========================================================
if os.environ.get("GOOGLE_CREDENTIALS"):
    info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
else:
    # Modo local
    creds = Credentials.from_service_account_file(
        "excel/credenciales.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

cliente = gspread.authorize(creds)
ws_global = cliente.open_by_key(SHEET_ID).sheet1


def get_sheet():
    return ws_global


# =========================================================
# SCHEDULER — ACTUALIZACIÓN AUTOMÁTICA DIARIA
# =========================================================
def tarea_actualizar_datos():
    try:
        print("[Scheduler] Actualizando datos reales...")
        ws = get_sheet()

        inicializar_encabezados(ws)
        actualizar_fila2(ws, API_KEY)
        recalcular_todos(ws, API_KEY)

        print("[Scheduler] Actualización completada.")
    except Exception as e:
        print("[Scheduler] ERROR:", e)


scheduler = BackgroundScheduler()
scheduler.add_job(
    func=tarea_actualizar_datos,
    trigger="cron",
    hour=3,
    minute=0
)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


# =========================================================
# INDEX
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "GET":
        session.clear()
        return render_template("index.html")

    if request.method == "POST":
        ws = get_sheet()

        session["nombre"] = request.form["nombre"]
        session["apellido"] = request.form["apellido"]
        session["edad"] = request.form["edad"]
        session["cedula"] = request.form["cedula"]
        session["celular"] = request.form["celular"]

        if usuario_existe(ws, session["nombre"], session["apellido"], session["cedula"]):
            return redirect("/mis_puntos")

        return redirect("/grupos")


# =========================================================
# GRUPOS
# =========================================================
@app.route("/grupos", methods=["GET", "POST"])
def grupos():

    ws = get_sheet()

    if usuario_existe(ws, session.get("nombre"), session.get("apellido"), session.get("cedula")):
        return redirect("/mis_puntos")

    if request.method == "POST":

        session["grupos"] = {}
        session["terceros_real"] = {}

        for g in GRUPOS.keys():
            session["grupos"][g] = request.form.get(f"orden{g}")
            session["terceros_real"][g] = request.form.get(f"tercero{g}")

        return redirect("/puntos")

    return render_template("grupos.html", grupos=GRUPOS, banderas=BANDERAS)


# =========================================================
# PUNTOS ADICIONALES
# =========================================================
@app.route("/puntos")
def puntos():

    ws = get_sheet()

    if usuario_existe(ws, session.get("nombre"), session.get("apellido"), session.get("cedula")):
        return redirect("/mis_puntos")

    return render_template(
        "puntos_adicionales.html",
        terceros=session["terceros_real"],
        banderas=BANDERAS,
        goleadores=GOLEADORES,
        grupos=GRUPOS
    )


# =========================================================
# GENERAR PDF + GUARDAR RESULTADOS + MOSTRAR MENSAJE
# =========================================================
@app.route("/generar_pdf", methods=["POST"])
def generar_pdf():

    ws = get_sheet()

    if usuario_existe(ws, session.get("nombre"), session.get("apellido"), session.get("cedula")):
        return redirect("/mis_puntos")

    seleccionados = request.form.get("tercerosSeleccionados", "")
    terceros = seleccionados.split(",") if seleccionados else []

    datos = {
        "nombre": session.get("nombre"),
        "apellido": session.get("apellido"),
        "edad": session.get("edad"),
        "cedula": session.get("cedula"),
        "celular": session.get("celular"),
        "grupos": session.get("grupos"),
        "terceros_real": session.get("terceros_real"),
        "terceros": terceros,
        "goleador": request.form.get("goleador"),
        "campeon": request.form.get("campeon"),
        "vice": request.form.get("vice"),
        "tercero_final": request.form.get("tercero_final")
    }

    guardar_resultados(datos, SHEET_ID, API_KEY)

    ruta_pdf = generar_pdf_prediccion(datos)
    nombre_pdf = f"Prediccion_2026_{session['apellido']}_{session['nombre']}.pdf"

    # Guardar PDF en static/pdfs
    os.makedirs("static/pdfs", exist_ok=True)
    ruta_destino = os.path.join("static", "pdfs", nombre_pdf)
    shutil.copy(ruta_pdf, ruta_destino)

    # MOSTRAR MENSAJE DE PAGO
    return render_template("mensaje_pago.html", nombre_pdf=nombre_pdf)


# =========================================================
# VER PDF
# =========================================================
@app.route("/ver_pdf/<archivo>")
def ver_pdf(archivo):
    ruta = os.path.join("static", "pdfs", archivo)
    return send_file(ruta, mimetype="application/pdf")


# =========================================================
# MIS PUNTOS
# =========================================================
@app.route("/mis_puntos")
def mis_puntos():

    if "nombre" not in session:
        return redirect("/")

    ws = get_sheet()
    datos = ws.get_all_records()

    participantes = datos[1:]  # fila 2 = resultados reales

    mi_fila = None
    for fila in participantes:
        if (
            fila["Nombre"].strip().lower() == session["nombre"].strip().lower() and
            fila["Apellido"].strip().lower() == session["apellido"].strip().lower() and
            str(fila["Cédula"]) == str(session["cedula"])
        ):
            mi_fila = fila
            break

    return render_template("mis_puntos.html", fila=mi_fila, BANDERAS=BANDERAS)



# =========================================================
# RANKING
# =========================================================
@app.route("/ranking")
def ranking():

    ws = get_sheet()
    datos = ws.get_all_records()

    participantes = datos[1:]

    for fila in participantes:
        try:
            fila["Puntos"] = int(fila.get("Puntos", 0))
        except:
            fila["Puntos"] = 0

    participantes_ordenados = sorted(
        participantes,
        key=lambda x: x["Puntos"],
        reverse=True
    )

    return render_template("ranking.html", participantes=participantes_ordenados)


# =========================================================
# EJECUCIÓN
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
