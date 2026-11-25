# ============================================================
# main.py  Orquestador principal del bot Seekop -> Sheets
# ============================================================

from seekop_api import descargar_reporte
from sheets import conectar, escribir_hoja
from config import REPORTES, FECHA_INICIO, FECHA_FIN
import sys


def main():
    print("=" * 55)
    print("  BOT SEEKOP -> GOOGLE SHEETS")
    print(f"  Período: {FECHA_INICIO}  ->  {FECHA_FIN}")
    print("=" * 55)

    # 1. Conectar a Google Sheets
    print("\n Conectando a Google Sheets...")
    try:
        spreadsheet = conectar()
        print(f"   Conectado a: {spreadsheet.title}")
    except Exception as e:
        print(f"   Error de conexión con Sheets: {e}")
        sys.exit(1)

    # 2. Procesar cada reporte
    errores = []
    for nombre_hoja, cfg in REPORTES.items():
        try:
            encabezados, filas = descargar_reporte(nombre_hoja, cfg)
            escribir_hoja(spreadsheet, nombre_hoja, encabezados, filas)
        except Exception as e:
            print(f"   Error en '{nombre_hoja}': {e}")
            errores.append(nombre_hoja)

    # 3. Resumen final
    print("\n" + "=" * 55)
    exitosos = len(REPORTES) - len(errores)
    print(f"   {exitosos}/{len(REPORTES)} reportes actualizados.")
    if errores:
        print(f"    Con errores: {', '.join(errores)}")
    print("=" * 55)


if __name__ == "__main__":
    main()
