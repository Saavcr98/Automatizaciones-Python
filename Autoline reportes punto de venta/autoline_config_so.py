"""
CONFIGURACION: REPORTE SO (Servicios Realizados) -- PUNTO DE VENTA
====================================================================
Archivo de configuracion INDEPENDIENTE del autoline_config.py
principal. El reporte "SO" (Servicios Realizados / cuadro "MKT
Reporte de Dest") vive en una rama del arbol completamente distinta
("Punto de Venta") con su PROPIO catalogo de nombres de agencia -- NO
son los mismos nombres que usan los reportes de Vehiculos/CRM en
autoline_config.py, aunque sean la misma instancia/empresa.

Ruta completa en el arbol (para todas las instancias EXCEPTO
Mercedes):
    Punto de Venta > <agencia> > Informes y consultas >
    Reportes Kasa Servicio SO > Servicios Realizados

Mercedes usa una ruta distinta (con "Seleccion de informe", codigo
"MKB") -- ver REPORTE_SO_MERCEDES y obtener_reporte_so() mas abajo.

El cuadro de parametros que abre ("MKT Reporte de Dest (SO)") tiene:
    Desde, Hasta, Mecanico, Departamento
No tiene "Sucursal" -- este reporte se corre UNA sola vez por agencia
(Mecanico y Departamento se dejan en blanco para traer todo).

Usa el MISMO motor (autoline_core.py) que el proyecto principal --
este archivo es solo el catalogo de instancias/agencias y la
definicion del reporte, igual que hace autoline_config.py.

IMPORTANTE: verifica los nombres de agencia contra el arbol real,
igual que en autoline_config.py -- estos se escribieron tal cual se
compartieron, y pueden tener alguna diferencia de acento o abreviatura
frente al arbol real de Autoline.
"""

# ==================== INSTANCIAS (Punto de Venta) ====================
# "agencias" aqui es solo una LISTA de nombres (no hay codigos que
# variar, a diferencia de autoline_config.py).

INSTANCIAS = {
    "Kasa Mitsubishi": {
        "titulo_ventana": "Kasa Mitsubishi",
        "raices": {},
        "agencias": [
            "03. AutoMitsu Satelite",
            "A3. AutoMitsu Santa Clara",
            "3C. AutoMitsu Juriquilla",
            "B3. AutoMitsu Queretaro",
        ],
    },

    "Kasa BYD": {
        "titulo_ventana": "Kasa BYD",
        "raices": {},
        "agencias": [
            "C2. AKV BYD Tlalnepantla",
            "C3. AKV  BYD Coacalco",
            "C4. AKV BYD Lomas Verdes",
        ],
    },

    "Kasa - GKAHO Honda - Acura": {
        "titulo_ventana": "GKAHO",
        "raices": {},
        "agencias": [
            "10. Automoviles Lomas Verdes S.A d",
            "30. Satélite Vehículos S.A de C.V",
            "31. Honda Lomas Verdes",
            "32. Honda Angelópolis",
            "34. Honda Tlanepantla",
            "36. Honda Santa Clara",
        ],
    },

    "Kasa Stellantis": {
        "titulo_ventana": "Kasa Stellantis",
        "raices": {},
        "agencias": [
            "01. Kasa Automotriz, SA de CV",
            "02. Automóviles Kasa Viaducto SA",
            "08. Kasa Naucalpan, SA de CV",
            "2B. Kasa Automotriz",
            "2C. Kasa Naucalpan",
            "2D. Kasa Coacalco",
            "8A. Kasa Coacalco",
        ],
    },

    "Kasa GM": {
        "titulo_ventana": "Kasa GM",
        "raices": {},
        "agencias": [
            "40. Automóviles Vallejo",
            "41. Toyota Coacalco",
            "42. Toyota Ecatepec",
            "60. Sol Valle Dorado",
            "61. Sol Coacalco",
            "62. Chevrolet Tlalnepantla",
            "70. Hyundai Satélite",
            "71. Hyundai Iztapalapa",
            "72. Hyundai Zaragoza",
            "80. Kia Coacalco",
            "81. Kia Ecatepec",
            "90. Autos Premier GK",
            "D1. Geely Santa Clara",
            "DD. Geely Lomas Verdes",
            "E1. GWM Santa Clara",
            "EE. GWM Coacalco",
        ],
    },

    "Kasa - GKAMB Mercedes Benz": {
        "titulo_ventana": "GKAMB",
        "raices": {},
        "agencias": [
            "50. Autosat",
            "51. Autosat Insurgentes",
            "53. Autosat Vallejo",
        ],
    },
}


# ==================== REPORTE ====================
# Mercedes usa un patron DISTINTO al resto: si pasa por el cuadro de
# "Seleccion de informe" (como ENV) con su propio codigo, y una ruta
# extra distinta ("Generador de informes" > "Ejecutar generador de
# informes", en vez de "Reportes Kasa Servicio SO" > "Servicios
# Realizados"). El cuadro de parametros final es el MISMO para todos
# (Desde/Hasta, sin Sucursal).

REPORTE_SO_DEFAULT = {
    "descripcion": "SO Servicio Realizados",
    "raiz_generica": "Punto de Venta",
    "ruta_extra": ["Informes y consultas", "Reportes Kasa Servicio SO", "Servicio Realizados"],
    "usa_seleccion_informe": False,
    "codigo_seleccion": None,
    "campo_fecha_desde": "Desde",
    "campo_fecha_hasta": "Hasta",
    "campo_variable": None,  # no hay campo que varie -- se corre una vez por agencia
}

REPORTE_SO_MERCEDES = {
    "descripcion": "SO Servicio Realizados (Mercedes)",
    "raiz_generica": "Punto de Venta",
    "ruta_extra": ["Informes y consultas", "Generador de informes", "Ejecutar generador de informes"],
    "usa_seleccion_informe": True,
    "codigo_seleccion": "MKB",
    "campo_fecha_desde": "Desde",
    "campo_fecha_hasta": "Hasta",
    "campo_variable": None,  # no hay campo que varie -- se corre una vez por agencia
}

_NOMBRE_INSTANCIA_MERCEDES = "Kasa - GKAMB Mercedes Benz"


def obtener_reporte_so(nombre_instancia):
    """Regresa la definicion del reporte SO que le corresponde a esta
    instancia -- Mercedes tiene su propia variante, todas las demas
    usan la default."""
    if nombre_instancia == _NOMBRE_INSTANCIA_MERCEDES:
        return REPORTE_SO_MERCEDES
    return REPORTE_SO_DEFAULT


# ==================== FUNCIONES AYUDANTES ====================

def obtener_agencias(nombre_instancia):
    """Regresa la lista de nombres de agencia (Punto de Venta) para
    una instancia."""
    instancia = INSTANCIAS.get(nombre_instancia, {})
    return list(instancia.get("agencias", []))


def construir_ruta_arbol(nombre_instancia, nombre_agencia):
    """Arma la ruta COMPLETA del arbol para el reporte SO: raiz
    ('Punto de Venta', o su nombre alternativo si esa instancia tiene
    uno configurado en 'raices') + la agencia + la ruta fija del
    reporte (que puede variar segun la instancia -- ver
    obtener_reporte_so)."""
    instancia = INSTANCIAS.get(nombre_instancia, {})
    reporte = obtener_reporte_so(nombre_instancia)
    raiz_generica = reporte["raiz_generica"]
    raices_override = instancia.get("raices", {})
    raiz_real = raices_override.get(raiz_generica, raiz_generica)

    ruta = [raiz_real, nombre_agencia]
    ruta.extend(reporte["ruta_extra"])
    return ruta
