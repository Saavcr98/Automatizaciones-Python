import gspread
import json
import os
from google.oauth2.service_account import Credentials
from config import SPREADSHEET_ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
COL_INICIO = 3
def conectar():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)

def _col_a_letra(n):
    resultado = ""
    while n > 0:
        n, resto = divmod(n - 1, 26)
        resultado = chr(65 + resto) + resultado
    return resultado

def escribir_hoja(sheet, nombre_hoja, encabezados, filas):
    try:
        ws = sheet.worksheet(nombre_hoja)
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=nombre_hoja, rows=5000, cols=100)

    datos   = [encabezados] + filas
    num_cols  = len(encabezados)
    col_ini   = _col_a_letra(COL_INICIO)
    col_fin = _col_a_letra(COL_INICIO + num_cols - 1)
    ws.batch_clear([f"{col_ini}1:{col_fin}3000"])

    # Escribir datos desde columna B
    rango = f"{col_ini}1:{col_fin}{len(datos)}"
    ws.update(rango, datos, value_input_option="USER_ENTERED")

    print(f"  '{nombre_hoja}' actualizada: {len(filas)} filas desde col {col_ini}.")
