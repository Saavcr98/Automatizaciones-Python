from flask import Flask, render_template, request, jsonify
from seekop_api import descargar_reporte
from sheets import conectar, escribir_hoja
from config import REPORTES
import traceback

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", reportes=list(REPORTES.keys()))

@app.route("/ejecutar", methods=["POST"])
def ejecutar():
    data = request.json
    fecha_inicio = data.get("fecha_inicio")
    fecha_fin = data.get("fecha_fin")

    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Fechas incompletas"}), 400

    # Sobreescribir fechas en tiempo de ejecucion
    import config
    config.FECHA_INICIO = fecha_inicio
    config.FECHA_FIN = fecha_fin

    resultados = []

    try:
        spreadsheet = conectar()
    except Exception as e:
        return jsonify({"error": f"Error al conectar con Google Sheets: {str(e)}"}), 500

    for nombre, cfg in REPORTES.items():
        try:
            encabezados, filas = descargar_reporte(nombre, cfg, fecha_inicio, fecha_fin)
            escribir_hoja(spreadsheet, nombre, encabezados, filas)
            resultados.append({
                "nombre": nombre,
                "registros": len(filas),
                "ok": True
            })
        except Exception as e:
            resultados.append({
                "nombre": nombre,
                "error": str(e),
                "ok": False
            })

    return jsonify({"resultados": resultados})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
