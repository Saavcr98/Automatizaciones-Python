"""
Automatizacion Seekop -> Google Sheets
========================================
Flujo:
  1) Llama al Apps Script Web App -> accion "limpiar" (Limpiar columnas.gs)
  2) Abre Chrome, hace login en rk.sicopweb.com
  3) Entra a "Analisis Diario 2.0" y captura el bi_token desde el trafico de red
  4) Abre el bot (Render), pega el token y da click en "Actualizar reportes"
  5) Espera a que el bot termine
  6) Llama al Apps Script Web App -> accion "actualizar" (Actualizar formulas.gs)

Requisitos (instalar una sola vez):
    pip install selenium webdriver-manager requests python-dotenv

Configura tus datos en el archivo .env (mismo folder), NUNCA los dejes
escritos directamente aqui en el codigo.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ----------------------------------------------------------------------
# Configuracion
# ----------------------------------------------------------------------
# Se usa la ruta absoluta del propio script (no la carpeta de trabajo
# actual) para encontrar el .env. Esto es clave para que funcione igual
# corriendo a mano desde la terminal, o disparado por el Programador de
# tareas de Windows -- donde el campo "Iniciar en" puede fallar por el
# espacio en "Base de Datos" y dejar la carpeta de trabajo en otro lado.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

SEEKOP_URL = "https://rk.sicopweb.com/#/login-screen"
SEEKOP_USER = os.getenv("SEEKOP_USER")
SEEKOP_PASS = os.getenv("SEEKOP_PASS")

BOT_URL = os.getenv("BOT_URL", "https://seekop-bot-3.onrender.com/")

# URL del Web App que creaste en Apps Script (paso 1 de las instrucciones)
APPSCRIPT_WEBAPP_URL = os.getenv("APPSCRIPT_WEBAPP_URL")

# Texto (o parte del texto, SIN acentos para evitar problemas de codificacion
# en el .env) del reporte a abrir para generar el trafico con el token
REPORTE_NOMBRE = os.getenv("REPORTE_NOMBRE", "Diario 2.0")

# Carpeta donde Chrome guarda la sesion (cookies) entre ejecuciones.
# Gracias a esto, despues de iniciar sesion UNA vez en tu cuenta de Google
# (necesario porque tu dominio @grupokasa.com.mx no permite acceso publico
# a los Web Apps de Apps Script), las siguientes corridas ya no piden login.
PERFIL_CHROME_DIR = os.path.join(SCRIPT_DIR, "chrome_profile")

LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(LOG_DIR, f"run_{datetime.now():%Y%m%d_%H%M%S}.log"),
            encoding="utf-8",
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def llamar_appscript(driver: webdriver.Chrome, accion: str, timeout: int = 180) -> None:
    """Dispara una funcion de Apps Script via el Web App (doGet), navegando
    con el propio Chrome (no con requests) porque tu dominio de Google
    Workspace exige una sesion de Google valida para llamar la URL.
    """
    if not APPSCRIPT_WEBAPP_URL:
        raise RuntimeError(
            "Falta APPSCRIPT_WEBAPP_URL en el .env. "
            "Sigue el paso 1 (implementar como Aplicacion web) antes de correr esto."
        )
    url = f"{APPSCRIPT_WEBAPP_URL}?action={accion}"
    log.info("Llamando Apps Script -> accion=%s", accion)
    driver.get(url)

    wait = WebDriverWait(driver, timeout)

    # Si no hay sesion de Google guardada todavia (primera vez que se corre
    # el script, o el perfil de Chrome es nuevo), aparecera la pantalla de
    # login de Google. Le damos tiempo de sobra para que la persona la
    # complete a mano UNA sola vez; de ahi en adelante queda guardada.
    if "accounts.google.com" in driver.current_url or "Sign in" in driver.title:
        log.warning(
            "Se requiere iniciar sesion de Google manualmente en la ventana "
            "de Chrome (solo la primera vez). Esperando hasta %s segundos...",
            timeout,
        )

    wait.until(lambda d: "OK" in d.find_element(By.TAG_NAME, "body").text)
    texto = driver.find_element(By.TAG_NAME, "body").text.strip()
    log.info("Respuesta Apps Script: %s", texto)
    if not texto.startswith("OK"):
        raise RuntimeError(f"Apps Script no confirmo exito: {texto}")


def crear_driver() -> webdriver.Chrome:
    """Crea el driver de Chrome con logging de red habilitado
    (necesario para poder leer las URLs de las llamadas XHR y sacar bi_token)
    y con un perfil persistente (para no tener que loguearse en Google
    en cada ejecucion).
    """
    os.makedirs(PERFIL_CHROME_DIR, exist_ok=True)

    options = Options()
    # Comenta la siguiente linea si quieres VER el navegador mientras corre
    # options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument(f"--user-data-dir={PERFIL_CHROME_DIR}")
    options.add_argument("--profile-directory=Default")
    options.set_capability(
        "goog:loggingPrefs", {"performance": "ALL"}
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Network.enable", {})

    # Por default, Selenium corta la conexion HTTP interna (Python <-> Chrome)
    # a los 120 segundos si una pagina no responde. Eso es lo que trunco a
    # "consolidar", que puede tardar varios minutos en terminar. Lo subimos
    # a 10 minutos para darle margen a las funciones de Apps Script mas
    # pesadas.
    driver.command_executor.set_timeout(600)
    driver.set_page_load_timeout(600)

    return driver


def habilitar_semantics_flutter(driver: webdriver.Chrome, espera: int = 15) -> None:
    """Seekop esta hecho en Flutter Web (renderer CanvasKit): toda la
    interfaz se dibuja dentro de un <canvas>, por lo que normalmente NO
    existen <input>/<button> reales en el DOM y Selenium no puede
    encontrar nada.

    Flutter trae un boton oculto pensado para lectores de pantalla que,
    al darle click, activa un "arbol de accesibilidad" (semantics) y ahi
    si genera elementos reales con atributo aria-label que coincide con
    el texto visible. Hay que activarlo despues de cada carga de pagina
    completa (login-screen). La navegacion interna despues del login es
    dentro de la misma SPA, por lo que se mantiene activo.
    """
    try:
        placeholder = WebDriverWait(driver, espera).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "flt-semantics-placeholder"))
        )
        driver.execute_script("arguments[0].click();", placeholder)
        time.sleep(2)
        log.info("Accesibilidad de Flutter activada (semantics tree).")
    except Exception:
        log.warning(
            "No se encontro el boton de accesibilidad de Flutter "
            "(flt-semantics-placeholder). Puede que ya este activo o "
            "que la app haya cambiado."
        )


def _guardar_diagnostico(driver: webdriver.Chrome, etiqueta: str) -> None:
    """Guarda HTML + screenshot para poder ver exactamente que habia en
    pantalla cuando algo fallo, sin tener que repetir la corrida a ciegas.
    """
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = os.path.join(LOG_DIR, f"{etiqueta}_{marca}.html")
    png_path = os.path.join(LOG_DIR, f"{etiqueta}_{marca}.png")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    driver.save_screenshot(png_path)
    log.error(
        "Diagnostico guardado. URL: %s | Titulo: %s | HTML: %s | PNG: %s",
        driver.current_url, driver.title, html_path, png_path,
    )


def login_seekop(driver: webdriver.Chrome) -> None:
    log.info("Abriendo login de Seekop...")
    driver.get(SEEKOP_URL)
    # Deja que la SPA resuelva si ya hay una sesion activa (redirect
    # automatico a board-list) antes de decidir que hacer.
    time.sleep(3)

    habilitar_semantics_flutter(driver)

    # Si ya hay una sesion activa, la SPA redirige fuera de /login
    # (por ejemplo a /dashboard, /board-list o /report...). En ese caso
    # se omite el llenado del formulario.
    try:
        WebDriverWait(driver, 8).until(
            lambda d: "/login" not in d.current_url.lower()
        )
        log.info(
            "Ya habia una sesion activa en Seekop (redirigido a %s); "
            "se omite el llenado del formulario de login.",
            driver.current_url,
        )
        return
    except Exception:
        pass  # sigue en /login: hay que iniciar sesion

    wait = WebDriverWait(driver, 45)

    def _buscar_campos():
        # 1) Flutter con semantics activo (aria-label)
        try:
            usr = driver.find_element(
                By.XPATH, "//*[contains(translate(@aria-label,'USARIOU','usariou'),'suario')]"
            )
            pwd = driver.find_element(
                By.XPATH, "//*[contains(translate(@aria-label,'ONTRASE','ontrase'),'ontrase')]"
            )
            return usr, pwd
        except Exception:
            pass
        # 2) Pagina web normal con <input> reales
        try:
            pwd = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            candidatos = [
                e for e in driver.find_elements(By.CSS_SELECTOR, "input")
                if (e.get_attribute("type") or "text").lower() in ("text", "email", "")
                and e.is_displayed()
            ]
            if candidatos:
                return candidatos[0], pwd
        except Exception:
            pass
        return None

    try:
        campo_usuario, campo_clave = wait.until(lambda d: _buscar_campos())
    except Exception:
        _guardar_diagnostico(driver, "login_page")
        raise

    campo_usuario.click()
    campo_usuario.send_keys(SEEKOP_USER)
    campo_clave.click()
    campo_clave.send_keys(SEEKOP_PASS)

    try:
        try:
            boton_login = driver.find_element(
                By.XPATH,
                "//body//*[self::button or @role='button']"
                "[contains(translate(normalize-space(.),'INICAR','inicar'),'iniciar') "
                "or contains(translate(@aria-label,'INICAR','inicar'),'iniciar')]",
            )
        except Exception:
            boton_login = driver.find_element(
                By.XPATH,
                "//body//*[contains(translate(@aria-label,'INICAR','inicar'),'iniciar') or contains(translate(text(),'INICAR','inicar'),'iniciar')]",
            )
        driver.execute_script("arguments[0].click();", boton_login)
    except Exception:
        _guardar_diagnostico(driver, "login_boton")
        raise

    # Espera a que cargue el listado de reportes (columna izquierda)
    try:
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(@aria-label,'GRUPOKASA') or contains(text(),'GRUPOKASA')]")
        ))
    except Exception:
        _guardar_diagnostico(driver, "post_login")
        raise
    log.info("Login exitoso.")


def extraer_bi_token(driver: webdriver.Chrome) -> str:
    """Abre el reporte 'Analisis Diario 2.0' y saca el bi_token
    de las llamadas de red (getIndicadoresReload / getDimensiones / aplicaciones/...).
    """
    wait = WebDriverWait(driver, 30)

    # Si el reporte ya estaba abierto de una sesion anterior (sesion activa
    # detectada en login_seekop), darle click de nuevo NO genera trafico
    # nuevo porque ya es el estado actual. Forzamos un refresh completo de
    # la pagina para garantizar que siempre se disparen las llamadas de
    # red frescas con el bi_token, tal como sugieren las instrucciones del
    # propio bot ("Recarga la pagina o navega a cualquier reporte").
    log.info("Recargando la pagina para asegurar trafico de red fresco...")
    driver.refresh()
    time.sleep(3)
    habilitar_semantics_flutter(driver)

    log.info("Abriendo reporte '%s'...", REPORTE_NOMBRE)
    try:
        reporte = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//*[contains(@aria-label,\"{REPORTE_NOMBRE}\") or contains(text(),\"{REPORTE_NOMBRE}\")]")
            )
        )
        driver.execute_script("arguments[0].click();", reporte)
    except Exception:
        _guardar_diagnostico(driver, "reporte_no_encontrado")
        raise

    # Dale tiempo a que la SPA dispare todas sus llamadas XHR
    time.sleep(6)

    token = None
    logs_red = driver.get_log("performance")
    for entrada in logs_red:
        try:
            mensaje = json.loads(entrada["message"])["message"]
        except (KeyError, json.JSONDecodeError):
            continue

        if mensaje.get("method") != "Network.requestWillBeSent":
            continue

        url = mensaje.get("params", {}).get("request", {}).get("url", "")
        if "bi_token=" in url:
            # El token viene como query param en la URL de la llamada
            token = url.split("bi_token=")[1].split("&")[0]
            break

    if not token:
        raise RuntimeError(
            "No se pudo capturar el bi_token del trafico de red. "
            "Puede que el nombre del reporte o el endpoint hayan cambiado."
        )

    log.info("bi_token capturado (%d caracteres).", len(token))
    return token


def actualizar_bot(driver: webdriver.Chrome, token: str, timeout: int = 600) -> None:
    log.info("Abriendo bot en Render...")
    driver.get(BOT_URL)
    wait = WebDriverWait(driver, 30)

    # TODO: verifica el selector real del textarea si esto falla
    textarea = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//textarea[contains(@placeholder,'bi_token') or contains(@placeholder,'token')]")
        )
    )
    textarea.clear()
    textarea.send_keys(token)

    boton = driver.find_element(
        By.XPATH, "//button[contains(., 'Actualizar reportes')]"
    )

    # "MITSUBISHICORP" ya aparece en la pagina DESDE ANTES de dar click
    # (es una de las etiquetas de corporativos que se puede seleccionar).
    # Por eso contamos cuantas veces aparece ANTES de arrancar, y esperamos
    # a que aparezca una vez MAS (la del renglon en RESULTADO) para saber
    # que en verdad termino, y no solo que la etiqueta sigue ahi.
    ULTIMO_CORPORATIVO = "MITSUBISHICORP"
    texto_antes = driver.find_element(By.TAG_NAME, "body").text
    conteo_antes = texto_antes.count(ULTIMO_CORPORATIVO)

    boton.click()
    log.info("Se dio click en 'Actualizar reportes', esperando a que termine...")

    wait_largo = WebDriverWait(driver, timeout)
    wait_largo.until(
        lambda d: d.find_element(By.TAG_NAME, "body").text.count(ULTIMO_CORPORATIVO) > conteo_antes
    )
    # Margen extra generoso por si el bot sigue escribiendo en el Sheet
    # justo despues de mostrar la ultima fila en pantalla (esto es
    # justamente lo que causo que la corrida anterior copiara datos a medias).
    time.sleep(20)
    log.info("Bot termino la actualizacion (se encontro '%s' un total de %d veces).",
              ULTIMO_CORPORATIVO, conteo_antes + 1)


# ----------------------------------------------------------------------
# Orquestacion
# ----------------------------------------------------------------------
def main() -> None:
    driver = None
    try:
        log.info("=== INICIO DEL PROCESO AUTOMATICO ===")

        driver = crear_driver()

        # 1) Limpiar columnas (Hoja Sheets 1)
        llamar_appscript(driver, "limpiar")

        # 2) y 3) Login + extraccion de token
        login_seekop(driver)
        token = extraer_bi_token(driver)

        # 4) y 5) Bot
        actualizar_bot(driver, token)

        # 6) Actualizar formulas (Hoja Sheets 2) -- DEBE ir antes de "consolidar"
        llamar_appscript(driver, "actualizar")

        # 7) Consolidar base completa (Chorizo.gs) -- SIEMPRE al final
        llamar_appscript(driver, "consolidar")

        log.info("=== PROCESO COMPLETADO CON EXITO (orden respetado) ===")

    except Exception:
        log.exception("El proceso fallo.")
        if driver:
            captura = os.path.join(LOG_DIR, f"error_{datetime.now():%Y%m%d_%H%M%S}.png")
            driver.save_screenshot(captura)
            log.info("Captura de pantalla del error guardada en: %s", captura)
        raise
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
