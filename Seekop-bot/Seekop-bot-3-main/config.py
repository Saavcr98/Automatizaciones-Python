# ============================================================
# config.py — Parametros centrales del bot Seekop -> Sheets
# ============================================================

import os

# -- Google Sheets --------------------------------------------
SPREADSHEET_ID = "1hO72iGjfxzuGNl6eq4gbzHHS5elIE6pCwCA4uAPjh3M"

# -- API ------------------------------------------------------
API_BASE_URL = "https://www.sicopweb.com/SeekopAPI/adbdc/getListaProspectos"
PAGE_SIZE    = 500
BI_ORIGEN    = "grupokasa"  # fijo para este grupo

# -- Parametros fijos de consulta -----------------------------
PARAMS_FIJOS = {
    "tipoConsulta":     "R",
    "idIndicador":      "ADBDC001",
    "idDimension":      "100",
    "idDimensionValue": "",
}

# -- Reportes -------------------------------------------------
REPORTES = {
    "GRUPOKASA": {
        "idUsuario":            "1920000000",
        "idDistribuidor":       "192000",
        "idDistribuidorOrigen": "096000",
    },
   "GM DEMO CORP": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "096000"},
"HONDA CORPORATIVO": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "101000"},
"ACURA CORPORATIVO": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "103000"},
"TOYOTA CORPORATIVO": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "104000"},
"CHRYSLER": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "129000"},
"HYUNDAI CORP": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "204000"},
"BYD CORP": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "230000"},
"GEELY CORPORATIVO": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "444000"},
"HONDAKASA CORPORATIVO": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "593000"},
"GWM CORPORATIVO": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "841000"},
    "BUICK CORPORATIVO": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "158000"},
"KIA CORPORATIVO": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "233000"},
"MITSUBISHICORP CORPORATIVO": {"idUsuario": "1920000000", "idDistribuidor": "192000", "idDistribuidorOrigen": "186000"}
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
