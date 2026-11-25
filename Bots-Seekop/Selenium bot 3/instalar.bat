@echo off
cd /d "%~dp0"
echo Creando entorno virtual...
py -m venv venv
if errorlevel 1 (
  echo ERROR: Python no esta instalado correctamente.
  pause
  exit /b 1
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo Listo. Ahora abre el archivo .env con el Bloc de notas y llena tus datos.
pause