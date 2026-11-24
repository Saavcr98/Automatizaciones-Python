import gspread
import json
import os
from google.oauth2.service_account import Credentials
from config import SPREADSHEET_ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def conectar() -> gspread.Spreadsheet:
    """Autentica y abre el spreadsheet desde variable de entorno o archivo."""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    
    if creds_json:
        # En Railway: leer desde variable de entorno
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        # Local: leer desde archivo credentials.json
        creds = Credentials.from_service_account_file(
            "credentials.json", scopes=SCOPES
        )
    
    cliente = gspread.authorize(creds)
    return cliente.open_by_key(SPREADSHEET_ID)


def escribir_hoja(sheet: gspread.Spreadsheet, nombre_hoja: str,
                  encabezados: list, filas: list) -> None:
    try:
        ws = sheet.worksheet(nombre_hoja)
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=nombre_hoja, rows=5000, cols=50)

    datos = [encabezados] + filas
    num_filas = len(datos)
    num_cols = len(encabezados)

    # Convertir numero de columna a letra (1=A, 2=B, ... 34=AH)
    def col_a_letra(n):
        resultado = ""
        while n > 0:
            n, resto = divmod(n - 1, 26)
            resultado = chr(65 + resto) + resultado
        return resultado

    col_fin = col_a_letra(num_cols)
    rango = f"A1:{col_fin}{num_filas}"

    # Limpiar solo el rango de datos, no toda la hoja
    ws.batch_clear([f"A1:{col_fin}10000"])

    # Escribir datos solo en ese rango
    ws.update(rango, datos, value_input_option="USER_ENTERED")

    print(f"  '{nombre_hoja}' actualizada: {len(filas)} filas + encabezado.")
