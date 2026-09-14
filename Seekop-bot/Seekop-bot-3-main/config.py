# ============================================================
# config.py — Parametros centrales del bot Seekop -> Sheets
# ============================================================

import os

# -- Google Sheets --------------------------------------------
SPREADSHEET_ID = "Sólo el código link de sheets"

# -- API ------------------------------------------------------
API_BASE_URL = "https://www.sicopweb.com"
PAGE_SIZE    = 500
BI_ORIGEN    = "grupo"  

# -- Parametros fijos de consulta -----------------------------
PARAMS_FIJOS = {
    "tipoConsulta":     "R",
    "idIndicador":      "ADBDC001",
    "idDimension":      "100",
    "idDimensionValue": "",
}

# -- Reportes -------------------------------------------------
REPORTES = {
    "GRUPO": {
        "idUsuario":            "0000000",
        "idDistribuidor":       "000",
        "idDistribuidorOrigen": "00",
 
}

# -- Columnas ocultas -----------------------------------------
COLUMNAS_OCULTAS = {
    "CampaignId", "HeliosId", "Estado", "Scoring", "TipoDescarte",
    "FechaRechazo", "TipoRechazo", "HintCard", "ConsultaHintCard",
    "Scorebemycar", "FechaUltimoIntento", "EncuestaUltimoIntento",
    "FechaProximoSeg", "ProximoSeg", "PresentacionConfirmada",
    "IntentoActual", "IntentosTotales", "ContactadoMinutos",
    "CAC_Estatus", "CAC_Fuente", "CAC_Subcampana", "CAC_Demos",
    "CAC_Cotizaciones", "CAC_ActCumplidas", "CAC_ActPendientes", "UTM",
}
