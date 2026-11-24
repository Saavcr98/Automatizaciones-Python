# ============================================================
# seekop_api.py — Descarga datos de Seekop con paginacion
# ============================================================
# ============================================================
# seekop_api.py — Descarga datos de Seekop con paginacion
# ============================================================

import requests
import time
from config import API_BASE_URL, PAGE_SIZE, COLUMNAS_OCULTAS, PARAMS_FIJOS


def _construir_params(cfg, from_value, fecha_inicio, fecha_fin, bi_token, bi_origen):
    params = {}
    params.update(PARAMS_FIJOS)
    params.update(cfg)
    params["fechaInicio"] = fecha_inicio
    params["fechaFin"]    = fecha_fin
    params["bi_token"]    = bi_token
    params["bi_origen"]   = bi_origen
    params["fromValue"]   = from_value
    params["totalValues"] = PAGE_SIZE
    return params


def obtener_columnas_visibles(columns):
    return [
        col for col, label in columns.items()
        if col not in COLUMNAS_OCULTAS and label != "hidden"
    ]


def descargar_reporte(nombre, cfg, fecha_inicio, fecha_fin, bi_token, bi_origen):
    print(f"Descargando reporte: {nombre}")

    all_rows     = []
    encabezados  = None
    columnas_vis = None
    from_value   = 0

    while True:
        params   = _construir_params(cfg, from_value, fecha_inicio, fecha_fin, bi_token, bi_origen)
        response = requests.get(API_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            print(f"  API error: {data.get('message')}")
            break

        if encabezados is None:
            columns_map  = data["response"]["columns"]
            columnas_vis = obtener_columnas_visibles(columns_map)
            encabezados  = [columns_map[c] for c in columnas_vis]

        registros = data["response"].get("data", [])

        if not registros:
            break

        for reg in registros:
            fila = [reg.get(col, "") for col in columnas_vis]
            all_rows.append(fila)

        print(f"  {len(all_rows)} registros acumulados (pagina desde {from_value})...")

        # Si trajo menos de PAGE_SIZE es la ultima pagina
        if len(registros) < PAGE_SIZE:
            break

        from_value += PAGE_SIZE
        time.sleep(0.5)

    print(f"  {nombre}: {len(all_rows)} registros totales.")
    return encabezados, all_rows
