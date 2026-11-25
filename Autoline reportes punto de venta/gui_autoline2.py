"""
INTERFAZ GRAFICA -- REPORTE SO (Servicios Realizados)
=========================================================
Version simplificada de gui_autoline.py, especifica para el reporte
"SO" (Servicios Realizados / cuadro "MKT Reporte de Dest"), que vive
en la rama "Punto de Venta" con su propio catalogo de agencias (ver
autoline_config_so.py) y NO tiene campo de "Sucursal" -- se corre UNA
sola vez por agencia (Mecanico y Departamento se dejan en blanco para
traer todo).

Por eso esta version es mas simple que gui_autoline.py:
- No hay combo de "Reporte" (solo existe SO aqui).
- No hay campo de "Codigos" (no hay nada que varie por corrida).

Comparte el MISMO motor y el MISMO ejecutor de procesos que el
proyecto principal:
    - autoline_core.py (SIN CAMBIOS de logica, solo se le agrego la
      capacidad de saltarse el campo variable cuando es None)
    - ejecutar_trabajos.py (SIN NINGUN CAMBIO -- ese script no sabe
      nada de autoline_config ni autoline_config_so, solo recibe una
      lista de trabajos ya armados en JSON)

Como este archivo lanza ejecutar_trabajos.py como proceso APARTE (no
un hilo dentro de esta ventana), puede correr AL MISMO TIEMPO que
gui_autoline.py sin ningun riesgo de que se crucen -- son procesos de
automatizacion completamente independientes. Eso si: cada uno necesita
su PROPIA ventana de Autoline abierta para la instancia que este
procesando en ese momento (si ambos intentan usar la MISMA instancia
de Autoline al mismo tiempo, ahi si se estorbarian entre si, igual que
pasaria si un mismo humano intentara usarla dos veces a la vez).

Requisitos: los mismos que gui_autoline.py (pywinauto, pywin32).

COMO USARLO:
1. Deja este archivo junto con 'autoline_core.py',
   'autoline_config_so.py' y 'ejecutar_trabajos.py' en la misma
   carpeta (puede ser la misma carpeta del proyecto principal).
2. Corre: python gui_autoline2.py
3. Elige instancia y agencia. La ruta del arbol se autollena --
   ajusta las FECHAS antes de agregar a la cola.
4. Dale "Agregar a la cola". Repite para cada agencia que quieras
   procesar en esta corrida.
5. Dale "Ejecutar cola completa".
6. Ten la ventana de Autoline correspondiente ya abierta, y evita
   tocar el mouse/teclado mientras corre.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import queue

from autoline_config_so import INSTANCIAS, obtener_agencias, obtener_reporte_so, construir_ruta_arbol


class AutolineSOGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Automatización Autoline -- Reporte SO (Servicios Realizados)")
        self.geometry("800x680")
        self.resizable(True, True)

        self.cola_log = queue.Queue()
        self.proceso = None  # subprocess.Popen del proceso de automatizacion
        self.hilo_lector = None  # hilo que SOLO lee texto del proceso (sin tocar Windows/UI)
        self.carpeta_resultados = None
        self.trabajos = []

        self._construir_widgets()
        self._procesar_cola_log()

    def _construir_widgets(self):
        marco_principal = ttk.Frame(self, padding=15)
        marco_principal.pack(fill="both", expand=True)

        # ---------- Selectores ----------
        marco_form = ttk.LabelFrame(marco_principal, text="Agregar agencia a la cola (reporte SO)", padding=10)
        marco_form.pack(fill="x", pady=(0, 10))

        ttk.Label(marco_form, text="Instancia:").grid(row=0, column=0, sticky="w", pady=4)
        self.combo_instancia = ttk.Combobox(marco_form, values=list(INSTANCIAS.keys()), state="readonly", width=45)
        self.combo_instancia.grid(row=0, column=1, sticky="ew", pady=4, padx=(8, 0))
        self.combo_instancia.bind("<<ComboboxSelected>>", self._al_cambiar_instancia)

        ttk.Label(marco_form, text="Agencia:").grid(row=1, column=0, sticky="w", pady=4)
        self.combo_agencia = ttk.Combobox(marco_form, values=[], state="readonly", width=45)
        self.combo_agencia.grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 0))
        self.combo_agencia.bind("<<ComboboxSelected>>", self._al_cambiar_seleccion)

        ttk.Label(marco_form, text="Fecha Desde:").grid(row=2, column=0, sticky="w", pady=4)
        self.entry_fecha_desde = ttk.Entry(marco_form, width=47)
        self.entry_fecha_desde.insert(0, "01/01/2026")
        self.entry_fecha_desde.grid(row=2, column=1, sticky="ew", pady=4, padx=(8, 0))

        ttk.Label(marco_form, text="Fecha Hasta:").grid(row=3, column=0, sticky="w", pady=4)
        self.entry_fecha_hasta = ttk.Entry(marco_form, width=47)
        self.entry_fecha_hasta.insert(0, "20/07/2026")
        self.entry_fecha_hasta.grid(row=3, column=1, sticky="ew", pady=4, padx=(8, 0))

        ttk.Label(marco_form, text="Ruta en el árbol (auto, editable):").grid(row=4, column=0, sticky="w", pady=4)
        self.entry_ruta = ttk.Entry(marco_form, width=47)
        self.entry_ruta.grid(row=4, column=1, sticky="ew", pady=4, padx=(8, 0))

        ttk.Label(
            marco_form,
            text="(Mecánico y Departamento se dejan en blanco -- trae todo)",
            foreground="#666",
        ).grid(row=5, column=1, sticky="w", pady=(0, 4), padx=(8, 0))

        marco_form.columnconfigure(1, weight=1)

        ttk.Button(marco_principal, text="➕ Agregar a la cola", command=self._agregar_a_cola).pack(anchor="w", pady=(0, 10))

        # ---------- Cola de trabajos ----------
        marco_cola = ttk.LabelFrame(marco_principal, text="Cola de trabajos", padding=10)
        marco_cola.pack(fill="both", expand=False, pady=(0, 10))

        self.lista_cola = tk.Listbox(marco_cola, height=5)
        self.lista_cola.pack(side="left", fill="both", expand=True)

        marco_botones_cola = ttk.Frame(marco_cola)
        marco_botones_cola.pack(side="left", padx=(8, 0))
        ttk.Button(marco_botones_cola, text="Quitar seleccionado", command=self._quitar_de_cola).pack(fill="x", pady=2)
        ttk.Button(marco_botones_cola, text="Vaciar cola", command=self._vaciar_cola).pack(fill="x", pady=2)

        # ---------- Carpeta destino ----------
        marco_carpeta = ttk.Frame(marco_principal)
        marco_carpeta.pack(fill="x", pady=(0, 10))
        ttk.Label(marco_carpeta, text="Carpeta de destino:").pack(side="left")
        self.entry_carpeta = ttk.Entry(marco_carpeta)
        self.entry_carpeta.insert(0, os.path.join(os.path.expanduser("~"), "Downloads", "ReportesAutolineSO"))
        self.entry_carpeta.pack(side="left", fill="x", expand=True, padx=(8, 4))
        ttk.Button(marco_carpeta, text="...", width=3, command=self._elegir_carpeta).pack(side="left")

        # ---------- Botones de ejecucion ----------
        marco_botones = ttk.Frame(marco_principal)
        marco_botones.pack(fill="x", pady=(0, 10))

        self.boton_ejecutar = ttk.Button(marco_botones, text="▶ Ejecutar cola completa", command=self._iniciar_ejecucion)
        self.boton_ejecutar.pack(side="left")

        self.boton_cancelar = ttk.Button(marco_botones, text="■ Cancelar", command=self._cancelar, state="disabled")
        self.boton_cancelar.pack(side="left", padx=(8, 0))

        self.boton_abrir_carpeta = ttk.Button(
            marco_botones, text="📂 Abrir carpeta de resultados",
            command=self._abrir_carpeta, state="disabled"
        )
        self.boton_abrir_carpeta.pack(side="left", padx=(8, 0))

        # ---------- Barra de progreso ----------
        self.barra_progreso = ttk.Progressbar(marco_principal, mode="indeterminate")
        self.barra_progreso.pack(fill="x", pady=(0, 10))

        # ---------- Log ----------
        marco_log = ttk.LabelFrame(marco_principal, text="Progreso", padding=5)
        marco_log.pack(fill="both", expand=True)

        self.texto_log = scrolledtext.ScrolledText(marco_log, wrap="word", state="disabled", font=("Consolas", 9))
        self.texto_log.pack(fill="both", expand=True)

    # ---------------- Cascada instancia -> agencia ----------------

    def _al_cambiar_instancia(self, event=None):
        instancia = self.combo_instancia.get()
        agencias = obtener_agencias(instancia)
        self.combo_agencia.configure(values=agencias, state="readonly")
        self.combo_agencia.set("")
        self._al_cambiar_seleccion()

    def _al_cambiar_seleccion(self, event=None):
        instancia = self.combo_instancia.get()
        agencia = self.combo_agencia.get()

        if not instancia or not agencia:
            return

        ruta = construir_ruta_arbol(instancia, agencia)
        self.entry_ruta.delete(0, "end")
        self.entry_ruta.insert(0, " > ".join(ruta))

    # ---------------- Cola de trabajos ----------------

    def _agregar_a_cola(self):
        instancia = self.combo_instancia.get()
        agencia = self.combo_agencia.get()

        if not instancia:
            messagebox.showerror("Falta información", "Elige una instancia.")
            return
        if not agencia:
            messagebox.showerror("Falta información", "Elige una agencia.")
            return
        if not self.entry_ruta.get().strip():
            messagebox.showerror("Falta información", "La ruta del árbol está vacía.")
            return

        ruta_arbol = [p.strip() for p in self.entry_ruta.get().split(">") if p.strip()]

        reporte = obtener_reporte_so(instancia)
        campos_fijos = {
            reporte["campo_fecha_desde"]: self.entry_fecha_desde.get().strip(),
            reporte["campo_fecha_hasta"]: self.entry_fecha_hasta.get().strip(),
        }
        titulo_parcial = INSTANCIAS[instancia]["titulo_ventana"]

        etiqueta = f"{instancia} / {agencia} / SO"

        trabajo = {
            "etiqueta": etiqueta,
            "titulo_parcial": titulo_parcial,
            "ruta_arbol": ruta_arbol,
            "usa_seleccion_informe": reporte["usa_seleccion_informe"],
            "codigo_seleccion": reporte["codigo_seleccion"],
            "campos_fijos": campos_fijos,
            "nombre_campo_variable": None,
            # Se corre UNA sola vez (este reporte no tiene un campo
            # que varie, como si fuera "Sucursal" en los demas) -- un
            # solo valor placeholder en la lista para que el motor
            # ejecute exactamente una corrida.
            "valores_variable": [None],
        }
        self.trabajos.append(trabajo)
        self.lista_cola.insert("end", etiqueta)

    def _quitar_de_cola(self):
        seleccion = self.lista_cola.curselection()
        if not seleccion:
            return
        idx = seleccion[0]
        self.lista_cola.delete(idx)
        del self.trabajos[idx]

    def _vaciar_cola(self):
        self.lista_cola.delete(0, "end")
        self.trabajos = []

    # ---------------- Carpeta destino ----------------

    def _elegir_carpeta(self):
        carpeta = filedialog.askdirectory(initialdir=self.entry_carpeta.get())
        if carpeta:
            self.entry_carpeta.delete(0, "end")
            self.entry_carpeta.insert(0, carpeta)

    def _abrir_carpeta(self):
        if self.carpeta_resultados and os.path.exists(self.carpeta_resultados):
            os.startfile(self.carpeta_resultados)

    # ---------------- Log ----------------

    def _escribir_log(self, mensaje):
        self.cola_log.put(mensaje)

    def _procesar_cola_log(self):
        try:
            while True:
                mensaje = self.cola_log.get_nowait()
                self.texto_log.configure(state="normal")
                self.texto_log.insert("end", mensaje + "\n")
                self.texto_log.see("end")
                self.texto_log.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(150, self._procesar_cola_log)

    # ---------------- Ejecucion ----------------

    def _iniciar_ejecucion(self):
        if not self.trabajos:
            messagebox.showerror("Cola vacía", "Agrega al menos una agencia a la cola antes de ejecutar.")
            return

        carpeta = self.entry_carpeta.get().strip()
        self.carpeta_resultados = carpeta

        self.texto_log.configure(state="normal")
        self.texto_log.delete("1.0", "end")
        self.texto_log.configure(state="disabled")

        self.boton_ejecutar.configure(state="disabled")
        self.boton_cancelar.configure(state="normal")
        self.boton_abrir_carpeta.configure(state="disabled")
        self.barra_progreso.start(12)

        # Mismo formato de JSON que gui_autoline.py -- ejecutar_trabajos.py
        # no sabe (ni le importa) si los trabajos vinieron de
        # autoline_config.py o de autoline_config_so.py, asi que se
        # reutiliza SIN NINGUN CAMBIO.
        datos = {"trabajos": list(self.trabajos), "carpeta_destino": carpeta}
        archivo_temp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(datos, archivo_temp, ensure_ascii=False)
        archivo_temp.close()
        self._archivo_trabajos_temp = archivo_temp.name

        script_ejecutor = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ejecutar_trabajos.py")

        self.proceso = subprocess.Popen(
            [sys.executable, script_ejecutor, self._archivo_trabajos_temp],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        self.hilo_lector = threading.Thread(
            target=self._leer_salida_proceso,
            daemon=True,
        )
        self.hilo_lector.start()

    def _cancelar(self):
        self._escribir_log("\n[Cancelando... cerrando el proceso de automatizacion]")
        self.boton_cancelar.configure(state="disabled")
        if self.proceso is not None and self.proceso.poll() is None:
            try:
                self.proceso.terminate()
            except Exception:
                pass

    def _leer_salida_proceso(self):
        """Este hilo SOLO lee texto de la salida del proceso -- no
        toca ventanas ni hace ninguna automatizacion, asi que es
        seguro que corra en un hilo aparte (los clics y teclas viven
        en el proceso totalmente distinto lanzado arriba)."""
        try:
            for linea in self.proceso.stdout:
                linea = linea.rstrip("\n")
                if linea in ("__FIN_OK__", "__FIN_CANCELADO__", "__FIN_ERROR__"):
                    continue
                self._escribir_log(linea)
        except Exception as e:
            self._escribir_log(f"\n[ERROR leyendo el proceso] {e}")
        finally:
            self.proceso.wait()
            try:
                os.remove(self._archivo_trabajos_temp)
            except Exception:
                pass
            self.after(0, self._al_terminar)

    def _al_terminar(self):
        self.barra_progreso.stop()
        self.boton_ejecutar.configure(state="normal")
        self.boton_cancelar.configure(state="disabled")
        self.boton_abrir_carpeta.configure(state="normal")


if __name__ == "__main__":
    app = AutolineSOGUI()
    app.mainloop()
