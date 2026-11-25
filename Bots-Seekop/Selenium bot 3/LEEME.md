# Automatización Seekop → Google Sheets

## 1. Instalación (una sola vez)

Como ya tienes Python instalado y lo usas para otro bot, **no descargues otra
versión** — usaremos un *entorno virtual* (venv), que es justo la herramienta
hecha para esto: crea una carpeta aislada con sus propias librerías, sin
tocar ni pisar las que ya usa tu otro bot. Tu Python 3.13 se queda intacto;
solo aíslas los paquetes de este proyecto (`selenium`, `requests`, etc.).

1. Instala [Google Chrome](https://www.google.com/chrome/) si no lo tienes.
2. Copia esta carpeta a tu PC, por ejemplo en `C:\seekop_automation`.
3. Abre CMD o PowerShell **dentro de esa carpeta** y crea el entorno virtual:
   ```
   python -m venv venv
   ```
4. Actívalo:
   - CMD: `venv\Scripts\activate.bat`
   - PowerShell: `venv\Scripts\Activate.ps1`

   Verás que el inicio de la línea de comandos cambia a `(venv) C:\seekop_automation>`
   — eso confirma que estás dentro del entorno aislado.
5. Con el entorno activado, instala las dependencias (quedan *solo* dentro de `venv`):
   ```
   pip install -r requirements.txt
   ```
6. Renombra `.env.example` a `.env` y llena tus datos reales (usuario, clave, y la URL del Web App de Apps Script — ver paso 2).

Cada vez que quieras correr el script manualmente desde la terminal, primero
activa el entorno (paso 4) y luego corre `python automatizar_seekop.py`. Para
la tarea programada de Windows (paso 4 más abajo) no hace falta "activar"
nada a mano: apuntamos directo al Python de dentro de `venv`, que ya trae
todo instalado — así el Programador de Tareas no toca tu Python global ni el
del otro bot.

## 2. Preparar el Apps Script (una sola vez)

Dentro del editor de Apps Script de tu hoja de cálculo:

1. Agrega un archivo nuevo llamado `WebApp.gs` con este contenido (ya con los
   3 nombres de función reales que me diste, en el orden que debe respetarse):

   ```javascript
   function doGet(e) {
     var accion = e.parameter.action;
     var resultado = "Acción no reconocida";

     if (accion === "limpiar") {
       recorrerLimpiarHojas();               // Limpiar columnas.gs
       resultado = "OK: Limpiar columnas ejecutado";
     } else if (accion === "actualizar") {
       actualizarFormulasCorporativos();     // Actualizar formulas.gs
       resultado = "OK: Actualizar formulas ejecutado";
     } else if (accion === "consolidar") {
       consolidarBaseCompleta();             // Chorizo.gs
       resultado = "OK: Consolidar base completa ejecutado";
     }
     return ContentService.createTextOutput(resultado);
   }
   ```

   > Importante sobre el orden: `doGet` responde al script de Python **hasta
   > que la función de Apps Script termina de correr**. Eso significa que el
   > script de Python, al hacer las llamadas una por una y esperar la
   > respuesta de cada una antes de seguir, garantiza automáticamente la
   > secuencia: `limpiar` → (extracción + bot) → `actualizar` → `consolidar`.
   > Nunca se disparan en paralelo ni se adelanta un paso al otro.

2. Click en **Implementar → Nueva implementación**.
3. Tipo: **Aplicación web**.
4. "Ejecutar como": **Yo (tu correo)**.
5. "Quién tiene acceso": **Cualquiera con el enlace**.
6. Click **Implementar** → autoriza permisos la primera vez.
7. Copia la URL que termina en `/exec` y pégala en tu `.env` como `APPSCRIPT_WEBAPP_URL`.

> Nota: cada vez que edites el código del Web App tendrás que crear una
> **nueva implementación** (o "Gestionar implementaciones → Editar → Nueva versión")
> para que los cambios se reflejen en la URL.

## 3. Probar manualmente

En la terminal, dentro de la carpeta:
```
python automatizar_seekop.py
```
Revisa la ventana de Chrome que se abre y el archivo de log que se genera en `logs/`.
Si algún selector falla (login, textarea del bot, etc.), el log te dirá en qué paso
fue y se guarda una captura de pantalla del error en `logs/` para que ajustes el
`XPATH` correspondiente (están marcados con `# TODO` en el código).

## 4. Programar la ejecución diaria (Windows)

1. Abre **Programador de tareas** (Task Scheduler).
2. **Crear tarea básica** → nómbrala "Seekop Diario".
3. Desencadenador: **Diariamente**, a la hora que te lo pidan.
4. Acción: **Iniciar un programa**.
   - Programa/script: la ruta al Python **de dentro del entorno virtual**, ej.
     `C:\seekop_automation\venv\Scripts\pythonw.exe`
     (usa `pythonw.exe`, no `python.exe`, así no aparece una ventana de consola).
   - Argumentos: `automatizar_seekop.py`
   - Iniciar en: la ruta de la carpeta, ej. `C:\seekop_automation`

   Al apuntar directo a `venv\Scripts\pythonw.exe` te aseguras de que la tarea
   programada use exactamente las librerías de este proyecto, sin importar
   cuál sea tu Python global ni el que usa tu otro bot.
5. En la pestaña **Condiciones**, desmarca "Iniciar la tarea solo si el equipo
   está conectado a la corriente" si usas laptop.
6. En **Configuración**, activa "Ejecutar la tarea lo antes posible si se
   perdió una ejecución programada" — así si prendes la PC tarde, igual corre.

Con esto ya no depende de que tú estés frente a la compu a la hora exacta:
mientras la PC esté encendida (o se encienda después, gracias al punto 6),
el proceso se dispara solo.
