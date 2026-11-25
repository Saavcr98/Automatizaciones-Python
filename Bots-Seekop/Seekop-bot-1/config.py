# ============================================================
# config.py  Parámetros centrales del bot Seekop  Sheets
# ============================================================

from datetime import date

#  Fechas del reporte (modifica estas cada mes) 
FECHA_INICIO = "2026-05-01"
FECHA_FIN    = "2026-05-05"

#  Google Sheets 
SPREADSHEET_ID = "1Jwxnkz0hyea9DUQ3cp5w8g9ybFHhD8qqw_rElaikyaM"

# Mapeo: nombre de hoja en Sheets  configuración del endpoint
REPORTES = {

"MIS":{  "idUsuario": "1295100051",             "idDistribuidor":  "186510",            "idDistribuidorOrigen":  "186510", },
"KASA":{  "idUsuario": "1292740129",             "idDistribuidor":  "129274",            "idDistribuidorOrigen":  "129274", },
"BDT":{  "idUsuario": "2300060001",             "idDistribuidor":  "230006",            "idDistribuidorOrigen":  "230006", },
"BDC":{  "idUsuario": "2300090001",             "idDistribuidor":  "230009",            "idDistribuidorOrigen":  "230009", },
"HOS":{  "idUsuario": "1011880093",             "idDistribuidor":  "101188",            "idDistribuidorOrigen":  "101188", },
"HOT":{  "idUsuario": "1011880093",             "idDistribuidor":  "101188",            "idDistribuidorOrigen":  "101188", },
"KANA":{  "idUsuario": "1292790079",             "idDistribuidor":  "129279",            "idDistribuidorOrigen":  "129279", },
"GEL":{  "idUsuario": "4440870001",             "idDistribuidor":  "444087",            "idDistribuidorOrigen":  "444087", },
"GES":{  "idUsuario": "4440210002",             "idDistribuidor":  "444021",            "idDistribuidorOrigen":  "444021", },
"HOL":{  "idUsuario": "1011890093",             "idDistribuidor":  "593189",            "idDistribuidorOrigen":  "593189", },
"ACU":{  "idUsuario": "1038550046",             "idDistribuidor":  "103855",            "idDistribuidorOrigen":  "103855", },
"TOY":{  "idUsuario": "1044030093",             "idDistribuidor":  "104403",            "idDistribuidorOrigen":  "104403", },
"TOC":{  "idUsuario": "1044250163",             "idDistribuidor":  "104425",            "idDistribuidorOrigen":  "104425", },
"TOS":{  "idUsuario": "1044300001",             "idDistribuidor":  "104430",            "idDistribuidorOrigen":  "104430", },
"GWM":{  "idUsuario": "8410040001",             "idDistribuidor":  "841004",            "idDistribuidorOrigen":  "841004", },
"HYU":{  "idUsuario": "2041180126",             "idDistribuidor":  "204118",            "idDistribuidorOrigen":  "204118", },
"HYI":{  "idUsuario": "2041600014",             "idDistribuidor":  "204160",            "idDistribuidorOrigen":  "204160", },
"HYZ":{  "idUsuario": "2041710001",             "idDistribuidor":  "204171",            "idDistribuidorOrigen":  "204171", },
"HYX":{  "idUsuario": "2041720001",             "idDistribuidor":  "204172",            "idDistribuidorOrigen":  "204172", },
"AKV":{  "idUsuario": "1292800107",             "idDistribuidor":  "129280",            "idDistribuidorOrigen":  "129280", },
"BDL":{  "idUsuario": "2300110001",             "idDistribuidor":  "230011",            "idDistribuidorOrigen":  "230011", },
"GWE":{  "idUsuario": "8410060001",             "idDistribuidor":  "841006",            "idDistribuidorOrigen":  "841006", },
"GMC":{  "idUsuario": "1588120044",             "idDistribuidor":  "158812",            "idDistribuidorOrigen":  "158812", },
"HOA":{  "idUsuario": "1011900070",             "idDistribuidor":  "101190",            "idDistribuidorOrigen":  "101190", },
"KAC":{  "idUsuario": "1295850001",             "idDistribuidor":  "129585",            "idDistribuidorOrigen":  "129585", },
"KIE":{  "idUsuario": "2330150085",             "idDistribuidor":  "233015",            "idDistribuidorOrigen":  "233015", },
"KIC":{  "idUsuario": "2330140080",             "idDistribuidor":  "233014",            "idDistribuidorOrigen":  "233014", },
"MIC":{  "idUsuario": "1866000001",             "idDistribuidor":  "186600",            "idDistribuidorOrigen":  "186600", },
"MIQ":{  "idUsuario": "1866440001",             "idDistribuidor":  "186644",            "idDistribuidorOrigen":  "186644", },
"SOT":{  "idUsuario": "0961240034",             "idDistribuidor":  "096124",            "idDistribuidorOrigen":  "096124", },
"SVD":{  "idUsuario": "0960650148",             "idDistribuidor":  "096065",            "idDistribuidorOrigen":  "096065", },
"SOC":{  "idUsuario": "0960660109",             "idDistribuidor":  "096066",            "idDistribuidorOrigen":  "096066", },   
}


#  Parámetros fijos de la API 
API_BASE_URL   = "https://www.sicopweb.com/SeekopAPI/adbdc/getListaProspectos"
TIPO_CONSULTA  = "R"
ID_INDICADOR   = "ADBDC001"
ID_DIMENSION   = "100"
PAGE_SIZE      = 10000          # registros por llamada (paginación)

#  Columnas visibles que se escribirán en Sheets 
# (las marcadas "hidden" en la API se excluyen automáticamente)
COLUMNAS_OCULTAS = {
    "CampaignId", "HeliosId", "Estado", "Scoring", "TipoDescarte",
    "FechaRechazo", "TipoRechazo", "HintCard", "ConsultaHintCard",
    "Scorebemycar", "FechaUltimoIntento", "EncuestaUltimoIntento",
    "FechaProximoSeg", "ProximoSeg", "PresentacionConfirmada",
    "IntentoActual", "IntentosTotales", "ContactadoMinutos",
    "CAC_Estatus", "CAC_Fuente", "CAC_Subcampana", "CAC_Demos",
    "CAC_Cotizaciones", "CAC_ActCumplidas", "CAC_ActPendientes", "UTM",
}
