# ============================================================
# config.py — Parametros centrales del bot Seekop -> Sheets
# ============================================================

import os

# -- Google Sheets --------------------------------------------
SPREADSHEET_ID = "ID DE SHEETS"

# -- API ------------------------------------------------------
API_BASE_URL = "https://www.sicopweb.com/SeekopAPI/adbdc/getListaProspectos"
PAGE_SIZE    = 500
BI_ORIGEN    = "ORIGEN"  # fijo para este grupo

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
        "idUsuario":            "0000",
        "idDistribuidor":       "0000",
        "idDistribuidorOrigen": "096000",
    },
   "GM DEMO CORP": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "6000"},
"HONDA CORPORATIVO": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "1000"},
"ACURA CORPORATIVO": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "3000"},
"TOYOTA CORPORATIVO": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "1000"},
"CHRYSLER": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "9000"},
"HYUNDAI CORP": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "4000"},
"BYD CORP": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "0000"},
"GEELY CORPORATIVO": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "4000"},
"HONDAKASA CORPORATIVO": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "3000"},
"GWM CORPORATIVO": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "1000"},
    "BUICK CORPORATIVO": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "8000"},
"KIA CORPORATIVO": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "3000"},
"MITSUBISHICORP CORPORATIVO": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "6000"},
 "LEAP MOTOR CORP": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "8000"},
   "ZEEKR CORP": {"idUsuario": "0000", "idDistribuidor": "0000", "idDistribuidorOrigen": "4000"}   
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
