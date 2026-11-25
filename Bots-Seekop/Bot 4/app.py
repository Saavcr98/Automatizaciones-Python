import os
import threading
import uuid
from flask import Flask, render_template, request, jsonify
from seekop_api import descargar_reporte
from sheets import conectar, escribir_hoja
from config import REPORTES, BI_ORIGEN

app = Flask(__name__)

JOBS = {}                      # job_id -> estado
JOBS_LOCK = threading.Lock()
EJECUCION_ACTIVA = threading.Lock()   # evita dos ejecuciones simultáneas


def _procesar(job_id, fecha_inicio, fecha_fin, bi_token):
    job = JOBS[job_id]
    try:
        spreadsheet = conectar()
    except Exception as e:
        job.update(estado="error", error=f"Error al conectar con Google Sheets: {e}")
        EJECUCION_ACTIVA.release()
        return

    for nombre, cfg in REPORTES.items():
        job["actual"] = nombre
        try:
            encabezados, filas = descargar_reporte(
                nombre, cfg, fecha_inicio, fecha_fin, bi_token, BI_ORIGEN
            )
            escribir_hoja(spreadsheet, nombre, encabezados, filas)
            job["resultados"].append({"nombre": nombre, "registros": len(filas), "ok": True})
            del filas, encabezados            # libera memoria entre reportes
        except Exception as e:
            job["resultados"].append({"nombre": nombre, "error": str(e), "ok": False})

    job.update(estado="terminado", actual=None)
    EJECUCION_ACTIVA.release()


@app.route("/")
def index():
    return render_template("index.html", reportes=list(REPORTES.keys()))


@app.route("/ejecutar", methods=["POST"])
def ejecutar():
    data = request.json
    fecha_inicio = data.get("fecha_inicio")
    fecha_fin    = data.get("fecha_fin")
    bi_token     = data.get("bi_token", "").strip()

    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Fechas incompletas"}), 400
    if not bi_token:
        return jsonify({"error": "El bi_token es obligatorio"}), 400

    if not EJECUCION_ACTIVA.acquire(blocking=False):
        return jsonify({"error": "Ya hay una ejecución en curso. Espera a que termine."}), 409

    job_id = uuid.uuid4().hex
    with JOBS_LOCK:
        JOBS[job_id] = {"estado": "corriendo", "actual": None,
                        "total": len(REPORTES), "resultados": []}

    threading.Thread(
        target=_procesar,
        args=(job_id, fecha_inicio, fecha_fin, bi_token),
        daemon=True,
    ).start()

    return jsonify({"job_id": job_id})


@app.route("/estado/<job_id>")
def estado(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Trabajo no encontrado"}), 404
    return jsonify(job)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
