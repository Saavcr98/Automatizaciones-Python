"""
EJECUTOR DE TRABAJOS (proceso independiente)
===============================================
Corre la cola de trabajos de Autoline como un proceso APARTE del
proceso de la interfaz grafica. Esto es clave: los clics y teclas
simuladas (pywinauto/SendInput) resultaron poco confiables cuando se
ejecutaban desde un hilo dentro del MISMO proceso que la ventana de
tkinter -- como proceso independiente, no hay ninguna interferencia
posible con el bucle de mensajes de la interfaz.

USO (normalmente lo invoca gui_autoline.py automaticamente, pero
tambien se puede correr a mano):
    python ejecutar_trabajos.py ruta_al_archivo_de_trabajos.json

El archivo JSON debe contener una lista de trabajos, cada uno con:
    {
        "etiqueta": "...",
        "titulo_parcial": "...",
        "ruta_arbol": [...],
        "usa_seleccion_informe": true/false,
        "codigo_seleccion": "..." o null,
        "campos_fijos": {...},
        "nombre_campo_variable": "...",
        "valores_variable": [...],
        "carpeta_destino": "..."
    }

Imprime cada linea de progreso a stdout INMEDIATAMENTE (flush=True)
para que quien lo invoque (la interfaz) lo pueda leer en vivo, linea
por linea, a medida que avanza.
"""

import json
import sys

from autoline_core import AutolineRunner, ReporteCancelado


def log_inmediato(mensaje):
    print(mensaje, flush=True)


def main():
    if len(sys.argv) < 2:
        print("Uso: python ejecutar_trabajos.py archivo_trabajos.json", flush=True)
        sys.exit(1)

    ruta_json = sys.argv[1]
    with open(ruta_json, encoding="utf-8") as f:
        datos = json.load(f)

    trabajos = datos["trabajos"]
    carpeta_destino = datos.get("carpeta_destino")

    runner = AutolineRunner(
        carpeta_destino=carpeta_destino,
        log=log_inmediato,
    )

    try:
        runner.ejecutar_lote(trabajos)
        print("__FIN_OK__", flush=True)
    except ReporteCancelado:
        print("__FIN_CANCELADO__", flush=True)
    except Exception as e:
        print(f"[ERROR FATAL] {e}", flush=True)
        print("__FIN_ERROR__", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
