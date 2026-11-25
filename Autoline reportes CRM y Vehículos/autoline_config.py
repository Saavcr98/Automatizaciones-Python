"""
CONFIGURACION: INSTANCIAS Y REPORTES DE AUTOLINE
====================================================
Dos mapas separados:

1. INSTANCIAS: cada ventana/instancia de Autoline, sus agencias (si
   aplica) con sus codigos, y sus "raices" alternativas (cuando el
   mismo nivel del arbol se llama distinto segun la instancia, ej.
   "CRM (30)" en Honda en vez de solo "CRM").

2. REPORTES: cada tipo de reporte (ENV, ENE, NFF, CVH, ZS1...), con
   su propia ruta despues de la agencia, si usa el cuadro de
   "Seleccion de informe" o lo salta, y los nombres EXACTOS de sus
   campos de fecha.

Edita este archivo cuando agreguen/quiten una agencia, codigo, o
reporte -- no hace falta tocar el motor ni la interfaz.

IMPORTANTE: los nombres de agencia deben coincidir EXACTAMENTE con lo
que aparece en el arbol de Autoline, incluyendo acentos (ej.
"Automóviles", "Satélite") -- si un acento no coincide, no lo va a
encontrar. Verifica contra el arbol real si algo falla.
"""

# ==================== INSTANCIAS ====================

INSTANCIAS = {
    "Kasa BYD": {
        "titulo_ventana": "Kasa BYD",
        "raices": {},
        "agencias": {
            "C2. Automoviles AKV BYD": ["BDT", "BDL", "BDC"],
        },
    },

    "Kasa Stellantis": {
        "titulo_ventana": "Kasa Stellantis",
        "raices": {},
        "agencias": {
            "01. Kasa Automotriz, SA de CV": ["CHR"],
            "02. Automóviles Kasa Viaducto SA": ["CH", "STA", "STC", "STN", "LMC", "LMN", "LMV", "LMS", "LME"],
            "08. Kasa Naucalpan, SA de CV": ["CHN", "CHC"],
        },
    },

    "Kasa GM": {
        "titulo_ventana": "Kasa GM",
        "raices": {},
        "agencias": {
            "40. Automóviles Vallejo": ["TOY", "TOC", "TOE"],
            "60. Sol Valle Dorado": ["DOR", "COA", "MAC"],
            "70. Hyundai Satélite": ["HYU", "HYC", "HYZ"],
            "80. Kia Motors": ["KCO", "KEC"],
            "90. Autos Premier GK": ["GMC"],
            "DD. Geely Lomas Verdes": ["GLV", "GSC", "GST"],
            "EE. GWM": ["GWM", "GWE"],
        },
    },

    "Kasa - GKAMB Mercedes Benz": {
        "titulo_ventana": "GKAMB",
        # En esta instancia el nivel "Vehiculos" se llama "Vehículos (50)"
        "raices": {"Vehículos": "Vehículos (50)"},
        "agencias": None,  # sin nivel de agencia -- va directo a Informes y consultas
        "codigos_directos": ["MB", "MBI", "MBV"],
    },

    "Kasa Mitsubishi": {
        "titulo_ventana": "Kasa Mitsubishi",
        "raices": {"Vehículos": "Vehículos (03)"},
        "agencias": None,
        "codigos_directos": ["MIS", "MIC", "MSC", "MIQ"],
    },

    "Kasa - GKAHO Honda - Acura": {
        "titulo_ventana": "GKAHO",
        # En esta instancia el nivel "CRM" se llama "CRM (30)"
        "raices": {"CRM": "CRM (30)"},
        # CONFIRMADO con captura del arbol real: en esta instancia,
        # "CRM (30)" NO tiene subcarpetas de agencia (a diferencia de
        # "Vehículos", que si las tiene) -- va directo de "CRM (30)" a
        # "Informes y consultas"/"Informes Grupo Kasa". Reportes con
        # raiz_generica "CRM" (CVH, ZS1) deben saltarse el nivel de
        # agencia para esta instancia especifica.
        "raices_sin_agencia": ["CRM"],
        # OJO: verifica estos nombres contra el arbol real -- los
        # acentos y abreviaturas (S.A de C.V, etc.) deben coincidir
        # exactamente. Los ajuste con los acentos que mencionaste,
        # pero si alguno no encuentra, compara contra el arbol.
        "agencias": {
            "10. Automoviles Lomas Verdes S.A d": ["ACU"],
            "30. Satélite Vehículos S.A de C.V": ["HOS"],
            "31. Honda Lomas Verdes": ["HOL"],
            "32. Honda Angelópolis": ["HOA"],
            "34. Honda Tlanepantla": ["HOT", "HSC", "HST"],
            "36. Honda Santa Clara": ["HST"],
        },
    },
}


# ==================== REPORTES ====================
# ruta_extra: los renglones del arbol DESPUES de la agencia (o del
#   nivel raiz si no hay agencia), incluyendo el ULTIMO que se activa
#   con doble clic.
# usa_seleccion_informe: True si despues del doble clic aparece el
#   cuadro para escribir un codigo (ej. ENV) antes de llegar a
#   Desde/Hasta/Sucursal. False si va directo a ese cuadro.
# raiz_generica: "Vehículos" o "CRM" -- el motor la traduce sola si
#   esa instancia tiene una "raiz" alternativa configurada arriba.

REPORTES = {
    "ENV": {
        "descripcion": "ENV Ventas",
        "raiz_generica": "Vehículos",
        "ruta_extra": ["Informes y consultas", "Generador de informes", "Ejecutar generador de informes"],
        "usa_seleccion_informe": True,
        "codigo_seleccion": "ENV",
        "campo_fecha_desde": "Desde",
        "campo_fecha_hasta": "Hasta",
        "campo_variable": "Sucursal",
    },

    "ENE": {
        "descripcion": "ENE Entregas",
        "raiz_generica": "Vehículos",
        "ruta_extra": ["Informes y consultas", "Generador de informes", "Ejecutar generador de informes"],
        "usa_seleccion_informe": True,
        "codigo_seleccion": "ENE",
        "campo_fecha_desde": "Desde Fecha de Entrega",
        "campo_fecha_hasta": "Hasta Fecha de Entega",
        "campo_variable": "Sucursal",
    },

    "NFF": {
        "descripcion": "NFF Vencimiento Financiamiento",
        "raiz_generica": "Vehículos",
        "ruta_extra": ["Informes y consultas", "NFF Vencimiento Financiamiento"],
        "usa_seleccion_informe": False,
        "codigo_seleccion": None,
        "campo_fecha_desde": "Desde",
        "campo_fecha_hasta": "Hasta",
        "campo_variable": "Sucursal",
    },

    "CVH": {
        "descripcion": "CVH (CRM)",
        "raiz_generica": "CRM",
        "ruta_extra": ["Informes y consultas", "Generador de informes", "Ejecutar generador de informes"],
        "usa_seleccion_informe": True,
        "codigo_seleccion": "CVH",
        # Nota: en CVH el orden visual es Sucursal primero y luego las
        # fechas, pero como llenamos por NOMBRE de campo (no por
        # posicion), el orden no afecta -- el motor busca cada campo
        # por su nombre sin importar donde este.
        "campo_fecha_desde": "Desde",
        "campo_fecha_hasta": "Hasta",
        "campo_variable": "Sucursal",
    },

    "ZS1": {
        "descripcion": "ZS1 Seguros por Vencer",
        "raiz_generica": "CRM",
        "ruta_extra": ["Informes Grupo Kasa", "Seguros", "ZS1 Seguros por Vencer"],
        "usa_seleccion_informe": False,
        "codigo_seleccion": None,
        "campo_fecha_desde": "Fecha d Vencimiento Desde",
        "campo_fecha_hasta": "Fecha de Vencimiento Hasta",
        "campo_variable": "Sucursal",
    },
    "NNP": {
        # Misma ruta y mismo cuadro de parametros que ENV -- solo
        # cambia el codigo que se escribe en "Seleccion de informe".
        "descripcion": "NNP (mismo cuadro que ENV)",
        "raiz_generica": "Vehículos",
        "ruta_extra": ["Informes y consultas", "Generador de informes", "Ejecutar generador de informes"],
        "usa_seleccion_informe": True,
        "codigo_seleccion": "NNP",
        "campo_fecha_desde": "Desde",
        "campo_fecha_hasta": "Hasta",
        "campo_variable": "Sucursal",
    },

    "NUP": {
        # Misma ruta que ENV (mismo renglon "Ejecutar generador de
        # informes"), pero abre un cuadro de parametros DISTINTO:
        # "VENTAS USADOS PROMOCIONES MKT" -- ahi el campo se llama
        # "SUCURSAL" en mayusculas (confirmado con captura), no
        # "Sucursal" como en ENV.
        "descripcion": "NUP Ventas Usados Promociones MKT",
        "raiz_generica": "Vehículos",
        "ruta_extra": ["Informes y consultas", "Generador de informes", "Ejecutar generador de informes"],
        "usa_seleccion_informe": True,
        "codigo_seleccion": "NUP",
        "campo_fecha_desde": "Desde",
        "campo_fecha_hasta": "Hasta",
        "campo_variable": "SUCURSAL",
    },

}


# ==================== FUNCIONES AYUDANTES ====================

def obtener_agencias(nombre_instancia):
    """Regresa la lista de nombres de agencia para una instancia, o
    una lista vacia si esa instancia no tiene nivel de agencia."""
    instancia = INSTANCIAS.get(nombre_instancia, {})
    agencias = instancia.get("agencias")
    if agencias is None:
        return []
    return list(agencias.keys())


def obtener_codigos(nombre_instancia, nombre_agencia=None):
    """Regresa la lista de codigos para una agencia especifica, o los
    codigos directos si la instancia no tiene nivel de agencia."""
    instancia = INSTANCIAS.get(nombre_instancia, {})
    agencias = instancia.get("agencias")
    if agencias is None:
        return list(instancia.get("codigos_directos", []))
    return list(agencias.get(nombre_agencia, []))


def construir_ruta_arbol(nombre_instancia, nombre_agencia, codigo_reporte):
    """Arma la ruta COMPLETA del arbol (incluyendo el ultimo renglon
    que se activa con doble clic), combinando la raiz correcta para
    esa instancia + la agencia (si aplica) + la ruta extra del
    reporte elegido."""
    instancia = INSTANCIAS.get(nombre_instancia, {})
    reporte = REPORTES.get(codigo_reporte, {})

    raiz_generica = reporte.get("raiz_generica", "Vehículos")
    raices_override = instancia.get("raices", {})
    raiz_real = raices_override.get(raiz_generica, raiz_generica)

    ruta = [raiz_real]
    raices_sin_agencia = instancia.get("raices_sin_agencia", [])
    tiene_agencia_aqui = raiz_generica not in raices_sin_agencia
    if instancia.get("agencias") is not None and nombre_agencia and tiene_agencia_aqui:
        ruta.append(nombre_agencia)
    ruta.extend(reporte.get("ruta_extra", []))
    return ruta
