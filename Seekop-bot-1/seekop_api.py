# ============================================================
# seekop_api.py  Descarga datos de Seekop con paginación
# ============================================================

import requests
import time
from config import (
    API_BASE_URL, TIPO_CONSULTA, ID_INDICADOR, ID_DIMENSION,
    PAGE_SIZE, COLUMNAS_OCULTAS, FECHA_INICIO, FECHA_FIN
)


def _construir_params(cfg: dict, from_value: int, fecha_inicio: str, fecha_fin: str) -> dict:
    """Arma el diccionario de parámetros para una llamada a la API."""
    return {
        "idUsuario":            cfg["idUsuario"],
        "idDistribuidor":       cfg["idDistribuidor"],
        "idDistribuidorOrigen": cfg["idDistribuidorOrigen"],
        "tipoConsulta":         TIPO_CONSULTA,
        "fechaInicio":          fecha_inicio,
        "fechaFin":             fecha_fin,
        "bi_origen":            "",
        "bi_token":             "",
        "idIndicador":          ID_INDICADOR,
        "idDimension":          ID_DIMENSION,
        "idDimensionValue":     "",
        "fromValue":            from_value,
        "totalValues":          PAGE_SIZE,
    }


def obtener_columnas_visibles(columns: dict) -> list:
    """Devuelve solo las columnas no ocultas, en orden."""
    return [
        col for col, label in columns.items()
        if col not in COLUMNAS_OCULTAS and label != "hidden"
    ]


def descargar_reporte(nombre: str, cfg: dict, fecha_inicio: str, fecha_fin: str) -> tuple[list, list]:
    """
    Descarga todos los registros de un reporte paginando automáticamente.
    Retorna (encabezados, filas)  listo para escribir en Sheets.
    """
    print(f"\n Descargando reporte: {nombre}")

    all_rows   = []
    encabezados = None
    columnas_vis = None
    from_value = 0

    while True:
        params   = _construir_params(cfg, from_value, fecha_inicio, fecha_fin)
        response = requests.get(API_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            print(f"    La API reportó error: {data.get('message')}")
            break

        # Primera página: extraer encabezados
        if encabezados is None:
            columns_map  = data["response"]["columns"]
            columnas_vis = obtener_columnas_visibles(columns_map)
            encabezados  = [columns_map[c] for c in columnas_vis]

        registros = data["response"].get("data", [])
        if not registros:
            break   # No hay más datos

        for reg in registros:
            fila = [reg.get(col, "") for col in columnas_vis]
            all_rows.append(fila)

        total = int(data.get("totalRegistros", 0))
        from_value += PAGE_SIZE
        print(f"   {len(all_rows)}/{total} registros obtenidos...")

        if len(all_rows) >= total:
            break

        time.sleep(0.5)   # Pausa cortés entre páginas

    print(f"   {nombre}: {len(all_rows)} registros totales.")
    return encabezados, all_rows
