import requests
import json
import ast

LOGIN_URL = "..."
APPS_URL  = "https://api.sicopweb.com/aplicaciones/"


def parsear(texto):
    """Parsea hasta obtener un dict, sin importar cuantas capas tenga."""
    resultado = texto
    for _ in range(4):  # max 4 capas
        if isinstance(resultado, dict) or isinstance(resultado, list):
            return resultado
        try:
            resultado = json.loads(resultado)
            continue
        except Exception:
            pass
        try:
            resultado = ast.literal_eval(resultado)
            continue
        except Exception:
            break
    return resultado


def obtener_token(usuario: str, contrasena: str) -> dict:
    print(f"Iniciando sesion con usuario: {usuario[:3]}***")

    resp_login = requests.post(
        LOGIN_URL,
        json={"Usuario": usuario, "Contrasena": contrasena},
        timeout=30
    )
    resp_login.raise_for_status()

    data_login = parsear(resp_login.text)
    print(f"  Tipo final: {type(data_login)}, valor: {str(data_login)[:100]}")

    if not isinstance(data_login, dict):
        raise ValueError(f"Respuesta inesperada: {type(data_login)} -> {str(data_login)[:200]}")

    usuario_data = data_login.get("usuario", [{}])[0]
    session_id   = usuario_data.get("id")
    bi_origen    = usuario_data.get("base", "").lower()

    if not session_id:
        raise ValueError(f"No se obtuvo session_id. Data: {data_login}")

    print(f"  Sesion iniciada: {usuario_data.get('nombre')}")

    resp_apps = requests.get(
        APPS_URL,
        params={"sessionid": session_id},
        timeout=30
    )
    resp_apps.raise_for_status()

    apps = parsear(resp_apps.text)

    if not isinstance(apps, list):
        raise ValueError(f"Respuesta apps inesperada: {type(apps)}")

    bi_token = None
    for app in apps:
        for param in app.get("params", []):
            if param.get("key") == "bi_token":
                bi_token = param.get("value")
                break
        if bi_token:
            break

    if not bi_token:
        raise ValueError("No se encontro bi_token.")

    print("  Token obtenido correctamente.")
    return {"bi_token": bi_token, "bi_origen": bi_origen}
