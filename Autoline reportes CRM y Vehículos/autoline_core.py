"""
MOTOR DE AUTOMATIZACION DE AUTOLINE
=====================================
Toda la logica de automatizacion vive aqui, separada de la interfaz.
Tanto un script de terminal como la interfaz grafica (gui_autoline.py)
usan esta misma clase.

Requisitos:
    pip install pywinauto pywin32
"""

import ctypes
import os
import re
import time

import win32api
import win32con
import win32gui
import win32process
from pywinauto import Application, Desktop


def forzar_ventana_al_frente(hwnd):
    """Trae una ventana al frente de forma confiable, incluso cuando NO
    ha habido ninguna interaccion real del usuario en un buen rato (el
    caso de una corrida 100% automatica). El truco simple de simular
    una tecla Alt no basta en ese escenario -- Windows bloquea el robo
    de foco ('foreground lock') mas agresivamente cuando no detecta
    actividad reciente de un usuario real.

    La tecnica correcta es "adjuntar" temporalmente la cola de entrada
    de nuestro hilo a la del hilo que actualmente tiene el foco (y a la
    del hilo dueño de la ventana destino), pedir el foco, y luego
    desadjuntar. Esto imita lo que pasa cuando un usuario real hace
    clic (que sí tiene permiso de cambiar el foco), en vez de pedirlo
    desde un proceso sin ninguna actividad de por medio."""
    hwnd_actual = win32gui.GetForegroundWindow()
    hilo_actual = win32api.GetCurrentThreadId()

    hilo_destino = 0
    hilo_frente = 0
    try:
        hilo_destino, _ = win32process.GetWindowThreadProcessId(hwnd)
        if hwnd_actual:
            hilo_frente, _ = win32process.GetWindowThreadProcessId(hwnd_actual)
    except Exception:
        pass

    adjuntado_destino = False
    adjuntado_frente = False
    try:
        if hilo_destino and hilo_destino != hilo_actual:
            adjuntado_destino = win32process.AttachThreadInput(hilo_actual, hilo_destino, True)
        if hilo_frente and hilo_frente != hilo_actual:
            adjuntado_frente = win32process.AttachThreadInput(hilo_actual, hilo_frente, True)

        try:
            win32gui.BringWindowToTop(hwnd)
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
    except Exception:
        # Respaldo: el truco simple de Alt, por si AttachThreadInput
        # fallo por algun motivo (ej. permisos, ventana ya cerrada).
        ALT = 0x12
        ctypes.windll.user32.keybd_event(ALT, 0, 0, 0)
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
        ctypes.windll.user32.keybd_event(ALT, 0, 2, 0)
    finally:
        try:
            if adjuntado_destino:
                win32process.AttachThreadInput(hilo_actual, hilo_destino, False)
            if adjuntado_frente:
                win32process.AttachThreadInput(hilo_actual, hilo_frente, False)
        except Exception:
            pass


class ReporteCancelado(Exception):
    """Se lanza cuando el usuario cancela una corrida en curso."""
    pass


class AutolineRunner:
    def __init__(self, titulo_parcial="Kasa BYD", pausa=0.6,
                 carpeta_destino=None, timeout_proceso=600, log=print,
                 debe_cancelar=None):
        self.titulo_parcial = titulo_parcial
        self.pausa = pausa
        self.carpeta_destino = carpeta_destino or os.path.join(
            os.path.expanduser("~"), "Downloads", "ReportesAutoline"
        )
        self.timeout_proceso = timeout_proceso
        self.log = log  # funcion para mandar mensajes (print, o callback de la interfaz)
        # funcion opcional que regresa True si el usuario pidio cancelar
        self.debe_cancelar = debe_cancelar or (lambda: False)

    def _checar_cancelacion(self):
        if self.debe_cancelar():
            raise ReporteCancelado()

    # ---------------- Ventana principal / arbol ----------------

    def esperar_y_traer_al_frente(self, title_re_pattern, timeout=15):
        inicio = time.time()
        ultimo_aviso = 0
        while time.time() - inicio < timeout:
            self._checar_cancelacion()
            try:
                candidatas = Desktop(backend="win32").windows(
                    title_re=title_re_pattern, visible_only=True
                )
                if candidatas:
                    w = candidatas[0]
                    forzar_ventana_al_frente(w.handle)
                    time.sleep(0.3)
                    return w
            except Exception:
                pass
            transcurrido = int(time.time() - inicio)
            if transcurrido - ultimo_aviso >= 5:
                self.log(f"  ... esperando cuadro con titulo '{title_re_pattern}' ({transcurrido}s transcurridos)")
                ultimo_aviso = transcurrido
            time.sleep(0.5)
        return None

    def obtener_arbol_uia(self, reintentos=15, espera=1.0):
        ultimo_error = None
        for _ in range(reintentos):
            self._checar_cancelacion()
            try:
                app = Application(backend="uia").connect(
                    title_re=f".*{self.titulo_parcial}.*"
                )
                ventana = app.top_window()
                forzar_ventana_al_frente(ventana.handle)
                time.sleep(self.pausa)

                # NOTA: antes intentamos "corregir" la posicion de la
                # ventana con MoveWindow cuando GetWindowRect reportaba
                # coordenadas ligeramente negativas (ej. -10,-10). Eso
                # resulto ser una falsa alarma: en Windows 10/11 es
                # NORMAL que una ventana MAXIMIZADA reporte un borde
                # invisible de unos pocos pixeles negativos alrededor
                # (parte del sombreado/marco de DWM), sin que la
                # ventana este realmente fuera de pantalla. "Corregir"
                # eso con MoveWindow terminaba encogiendo o moviendo la
                # ventana de forma innecesaria. Con solo maximize() (lo
                # que ya usaba la version que si funcionaba) basta.
                try:
                    ventana.maximize()
                    time.sleep(0.3)
                except Exception:
                    pass
                arbol = ventana.child_window(control_type="Tree")
                return arbol
            except Exception as e:
                ultimo_error = e
                time.sleep(espera)
        raise RuntimeError(
            f"No pude conectar a la ventana principal de Autoline tras {reintentos} intentos: {ultimo_error}"
        )

    def buscar_item_visible(self, arbol, texto):
        """Buscamos en todo el arbol (no restringido a un padre
        especifico). Se probo restringir la busqueda a los
        descendientes de un padre concreto para evitar confundir el
        mismo texto en ramas distintas, pero eso causo MAS fallas de
        las que evito -- la referencia UIA de un item recien expandido
        no siempre 'refresca' bien para encontrar sus propios hijos, o
        para servir de referencia estable en una verificacion de
        ascendencia. La causa raiz del cruce de ramas (una ruta que
        intentaba pasar por una agencia que no existe bajo CRM en
        Honda) ya se arreglo en autoline_config.py (ver
        'raices_sin_agencia'), asi que aqui ya no hace falta esta
        proteccion extra."""
        candidatos = arbol.descendants(title=texto, control_type="TreeItem")
        for c in candidatos:
            try:
                r = c.rectangle()
                if r.width() > 0 and r.height() > 0:
                    return c
            except Exception:
                continue
        return None

    def resetear_scroll_arbol(self, arbol, ruta_arbol):
        """Busca cualquier renglon de LA RUTA que estamos a punto de
        navegar (sin importar el nivel), y si esta visible en este
        momento lo usamos para regresar el scroll con Home. Antes se
        usaba una lista fija de textos pensada solo para la ruta de
        ENV/Generador de informes ('Informes y consultas', etc.) --
        eso fallaba para rutas distintas como la de ZS1 ('Informes
        Grupo Kasa' > 'Seguros' > ...), donde ninguno de esos textos
        fijos existe: si el arbol quedaba scrolleado mostrando solo
        ese tramo profundo, el reset nunca encontraba nada y no hacia
        nada, dejando el arbol atorado en el ultimo nivel visible."""
        candidatos = list(ruta_arbol) + ["Vehículos", "CRM"]
        for texto in candidatos:
            item = self.buscar_item_visible(arbol, texto)
            if item is not None:
                item.click_input()
                time.sleep(0.2)
                item.type_keys("{HOME}")
                time.sleep(0.5)
                return

    def desplazar_hasta_encontrar(self, arbol, texto, item_referencia=None, texto_padre=None, max_pasos=60):
        """Caso contrario a 'resetear_scroll_arbol' (que regresa el
        scroll HACIA ARRIBA): aqui el renglon que buscamos existe pero
        no se alcanza a ver en pantalla, y no siempre es obvio de que
        lado -- puede estar mas ABAJO (ej. una agencia al final de la
        lista, o un reporte como 'NFF Vencimiento Financiamiento') o
        habernos pasado de largo hacia ABAJO cuando en realidad estaba
        mas ARRIBA. Probamos primero moviendo hacia abajo, y si no
        aparece, probamos hacia arriba desde el mismo punto de
        partida -- cubriendo ambos sentidos antes de rendirnos.

        IMPORTANTE: si nos dieron 'texto_padre', preferimos volver a
        buscar ESE nodo por texto (fresco) en vez de confiar en
        'item_referencia' tal cual -- una referencia guardada de un
        paso anterior puede quedar obsoleta (ej. despues de cerrar una
        ventana de resultados que le robo el foco al arbol), y en ese
        caso ni el clic inicial para pararnos ahi funciona de verdad."""
        item = None
        if texto_padre is not None:
            item = self.buscar_item_visible(arbol, texto_padre)
            if item is None:
                self.log(f"  (La referencia del padre '{texto_padre}' parece obsoleta -- no la encuentro ni buscandola de nuevo.)")

        if item is None:
            item = item_referencia

        if item is None or not self._tiene_rectangulo_visible(item):
            for c in arbol.descendants(control_type="TreeItem"):
                if self._tiene_rectangulo_visible(c):
                    item = c
                    break
        if item is None:
            return None

        try:
            forzar_ventana_al_frente(arbol.handle)
            time.sleep(0.15)
            item.click_input()
            time.sleep(0.15)

            for tecla in ("{DOWN}", "{UP}"):
                for paso in range(max_pasos):
                    encontrado = self.buscar_item_visible(arbol, texto)
                    if encontrado is not None:
                        return encontrado
                    if paso > 0 and paso % 15 == 0:
                        self.log(f"  ...sigo desplazando ({tecla}, paso {paso}/{max_pasos})")
                    item.type_keys(tecla)
                    time.sleep(0.1)
        except Exception as e:
            self.log(f"  (fallo tecnico desplazando el scroll: {e})")
        return self.buscar_item_visible(arbol, texto)

    def _tiene_rectangulo_visible(self, item):
        try:
            r = item.rectangle()
            return r.width() > 0 and r.height() > 0
        except Exception:
            return False

    def _centrar_en_pantalla(self, arbol, item):
        """Si un renglon quedo justo en el borde superior o inferior
        del panel visible, puede reportar un rectangulo 'valido' pero
        no responder bien a clics (renglon parcialmente recortado).
        Lo seleccionamos y damos un par de pasos de flecha abajo+arriba
        para que el arbol lo re-centre un poco antes de interactuar."""
        try:
            forzar_ventana_al_frente(arbol.handle)
            time.sleep(0.1)
            item.click_input()
            time.sleep(0.1)
            item.type_keys("{DOWN}")
            time.sleep(0.15)
            item.type_keys("{UP}")
            time.sleep(0.15)
        except Exception:
            pass

    def asegurar_visible(self, arbol, texto, item_padre=None, texto_padre=None, reintentos=6, espera=0.4):
        item = self.buscar_item_visible(arbol, texto)
        if item is not None:
            return item

        # Si nos dieron el texto del padre, preferimos refrescar su
        # referencia por texto (fresca) antes de usarla para expandir
        # -- una referencia guardada de un paso anterior puede quedar
        # obsoleta (ej. despues de cerrar una ventana de resultados
        # que le robo el foco al arbol), y en ese caso ni el clic para
        # expandir funciona de verdad.
        if texto_padre is not None:
            padre_fresco = self.buscar_item_visible(arbol, texto_padre)
            if padre_fresco is not None:
                item_padre = padre_fresco

        if item_padre is not None:
            try:
                item_padre.click_input()
                time.sleep(0.2)
                item_padre.type_keys("{RIGHT}")
            except Exception as e:
                self.log(f"  (No pude expandir usando el padre guardado: {e})")

        for _ in range(reintentos):
            time.sleep(espera)
            item = self.buscar_item_visible(arbol, texto)
            if item is not None:
                return item

        # Ya no intentamos desplazar el scroll aqui -- confirmado que
        # nunca funciona (siempre agotaba los 120 pasos sin encontrar
        # nada) y solo desperdiciaba ~12 segundos por fallo. En vez de
        # eso, navegar_arbol_con_reintento_total ya se encarga de
        # recuperarse de esto colapsando todo y renavegando desde
        # cero, que si funciona de forma consistente.
        return None

    def obtener_handles_ventanas_autoline(self):
        """Todos los cuadros de Autoline (Seleccion de informe, cuadros
        de parametros, resultados, etc.) comparten la misma clase
        tecnica de ventana (KCMLMasterForm_32), sin importar su
        titulo -- mucho mas confiable para detectar 'aparecio un
        cuadro nuevo' que adivinar el texto del titulo."""
        try:
            return {
                w.handle
                for w in Desktop(backend="win32").windows(
                    class_name="KCMLMasterForm_32", visible_only=True
                )
            }
        except Exception:
            return set()

    def esperar_cuadro_extra_autoline(self, excluir_patrones=None, timeout=30):
        """Busca CUALQUIER cuadro de Autoline (misma clase de ventana
        KCMLMasterForm_32) que no sea la ventana principal ni algo que
        sepamos que hay que ignorar -- SIN comparar contra un set de
        handles 'de antes'. Comparar handles resulto ser poco
        confiable: Windows puede reciclar el mismo numero de HWND para
        una ventana nueva justo despues de que la vieja se cierra, lo
        que hace que 'handle not in handles_previos' falle aunque el
        cuadro nuevo si este ahi (esto explica por que
        'limpiar_dialogos_extra', que NO compara handles y solo filtra
        por titulo, si lo encontraba segundos despues). En cualquier
        momento dado solo deberia existir UN cuadro 'extra' relevante,
        asi que no hace falta diferenciar 'viejo' vs 'nuevo' por
        handle -- basta con que no sea la ventana principal ni algo en
        la lista de exclusion."""
        excluir_patrones = excluir_patrones or []
        inicio = time.time()
        ultimo_aviso = 0
        while time.time() - inicio < timeout:
            self._checar_cancelacion()
            try:
                candidatas = Desktop(backend="win32").windows(
                    class_name="KCMLMasterForm_32", visible_only=True
                )
                for w in candidatas:
                    titulo = w.window_text()
                    if self.titulo_parcial.lower() in titulo.lower():
                        continue
                    if any(re.search(pat, titulo, re.IGNORECASE) for pat in excluir_patrones):
                        continue
                    forzar_ventana_al_frente(w.handle)
                    time.sleep(0.3)
                    return w
            except Exception:
                pass
            transcurrido = int(time.time() - inicio)
            if transcurrido - ultimo_aviso >= 5:
                self.log(f"  ... esperando cuadro extra de Autoline ({transcurrido}s transcurridos)")
                ultimo_aviso = transcurrido
            time.sleep(0.5)
        return None

    def esperar_ventana_autoline_nueva(self, handles_previos, timeout=15):
        inicio = time.time()
        ultimo_aviso = 0
        while time.time() - inicio < timeout:
            self._checar_cancelacion()
            try:
                candidatas = Desktop(backend="win32").windows(
                    class_name="KCMLMasterForm_32", visible_only=True
                )
                for w in candidatas:
                    if w.handle not in handles_previos:
                        forzar_ventana_al_frente(w.handle)
                        time.sleep(0.3)
                        return w
            except Exception:
                pass
            transcurrido = int(time.time() - inicio)
            if transcurrido - ultimo_aviso >= 5:
                self.log(f"  ... esperando cuadro nuevo de Autoline ({transcurrido}s transcurridos)")
                ultimo_aviso = transcurrido
            time.sleep(0.5)
        return None

    def navegar_arbol(self, ruta_arbol, verificar_activacion=None,
                       intentos_activacion=3, timeout_por_intento=12):
        """ruta_arbol: lista COMPLETA de renglones del arbol, en orden,
        incluyendo el ULTIMO que se activa con doble clic (puede ser
        'Ejecutar generador de informes', o el nombre directo de un
        reporte como 'NFF Vencimiento Financiamiento' -- ya no se
        asume nada fijo, el ultimo elemento de la lista es el que se
        activa). Ej:
            ["Vehículos", "C2. Automoviles AKV BYD", "Informes y consultas", "Generador de informes", "Ejecutar generador de informes"]
            ["Vehículos", "01. Kasa Automotriz, SA de CV", "Informes y consultas", "NFF Vencimiento Financiamiento"]

        verificar_activacion: funcion opcional que recibe un timeout
        (segundos) y regresa el resultado esperado (o None si no
        aparecio nada). El doble clic en segundo plano no siempre
        activa al primer intento -- si se pasa esta funcion,
        navegar_arbol reintenta el doble clic (SIN renavegar el
        arbol completo, el item ya esta seleccionado y visible) hasta
        'intentos_activacion' veces, esperando 'timeout_por_intento'
        segundos cada vez, antes de darse por vencido. Si no se pasa
        nada, hace un solo doble clic y regresa sin verificar (modo
        anterior).
        """
        arbol = self.obtener_arbol_uia()
        self.resetear_scroll_arbol(arbol, ruta_arbol)

        item_anterior = None
        texto_anterior = None
        for texto in ruta_arbol[:-1]:
            self._checar_cancelacion()
            item = self.asegurar_visible(arbol, texto, item_anterior, texto_padre=texto_anterior)
            if item is None:
                raise RuntimeError(f"No encontre '{texto}' visible en el arbol.")
            item_anterior = item
            texto_anterior = texto
            time.sleep(self.pausa)

        item_final = self.asegurar_visible(arbol, ruta_arbol[-1], item_anterior, texto_padre=texto_anterior)
        if item_final is None:
            raise RuntimeError(f"No encontre '{ruta_arbol[-1]}' visible en el arbol.")

        # Si el renglon quedo justo en el borde superior o inferior
        # del panel visible, puede reportar un rectangulo 'valido'
        # pero no responder bien a los clics (renglon parcialmente
        # recortado -- confirmado con un caso donde ningun metodo de
        # clic funcionaba en un renglon con coordenadas al borde).
        # Un pequeño paso abajo+arriba re-centra la seleccion antes de
        # intentar interactuar.
        self._centrar_en_pantalla(arbol, item_final)
        item_final = self.buscar_item_visible(arbol, ruta_arbol[-1]) or item_final

        # Diagnostico: registramos las coordenadas del renglon final
        # ANTES de intentar cualquier clic, para poder confirmar en el
        # log si son validas (positivas, dentro del tamano de pantalla)
        # sin tener que pedir otra ronda de pruebas manuales.
        rect_inicial = item_final.rectangle()
        self.log(f"  Renglon a activar: '{ruta_arbol[-1]}' en {rect_inicial}")

        try:
            ventana_hwnd = win32gui.GetAncestor(arbol.handle, 2)  # GA_ROOT
        except Exception:
            ventana_hwnd = arbol.handle

        for intento in range(1, intentos_activacion + 1):
            self._checar_cancelacion()
            metodo = ["doble clic", "clic + Enter", "clic + Espacio"][(intento - 1) % 3]

            try:
                forzar_ventana_al_frente(ventana_hwnd)
                time.sleep(0.3)

                rect_actual = item_final.rectangle()
                self.log(f"  Intento {intento}: clic en {rect_actual}")

                # Alternamos el METODO de activacion en cada intento, no
                # solo repetimos doble clic: ni el doble clic ni la
                # barra espaciadora resultaron 100% confiables por si
                # solos desde un hilo en segundo plano (cada uno fallo
                # en algun reporte distinto) -- probamos varios antes
                # de rendirnos.
                if metodo == "doble clic":
                    item_final.click_input(double=True)
                elif metodo == "clic + Enter":
                    item_final.click_input()
                    time.sleep(0.2)
                    item_final.type_keys("{ENTER}")
                else:
                    item_final.click_input()
                    time.sleep(0.2)
                    item_final.type_keys(" ")
                time.sleep(self.pausa)

                if verificar_activacion is None:
                    return None

                resultado = verificar_activacion(timeout_por_intento)
                if resultado is not None:
                    return resultado
            except Exception as e:
                # Red de seguridad amplia: CUALQUIER falla tecnica en
                # este intento (clic, teclas, o la espera/verificacion
                # posterior -- todas pueden toparse con el mismo
                # bloqueo de foco de Windows en distintos puntos) se
                # registra y pasamos al siguiente metodo, en vez de
                # dejar que tumbe la corrida completa.
                self.log(f"  (fallo tecnico en intento {intento} ('{metodo}'): {e})")
                item_final = self.buscar_item_visible(arbol, ruta_arbol[-1]) or item_final

            if intento < intentos_activacion:
                self.log(f"  '{metodo}' no parecio activar nada (intento {intento}/{intentos_activacion}); probando otro metodo...")

        return None

    # ---------------- Seleccion de informe ----------------

    def esperar_cuadro_seleccion_informe(self, timeout=30):
        """El cuadro de 'Selección de informe' SIEMPRE arranca su
        titulo igual sin importar la instancia/agencia -- solo cambia
        el sufijo entre parentesis, ej. '(VS/C2)', '(VS/30)',
        '(MK/50)'. A diferencia del cuadro de parametros (cuyo titulo
        varia demasiado entre reportes como para confiar en texto
        fijo), aqui SI podemos buscarlo por titulo -- es mas directo y
        confiable que la deteccion generica por 'ventana nueva de la
        misma clase', que no esta detectando bien este cuadro en
        particular (confirmado: el cuadro abre a tiempo pero la
        deteccion por clase no lo ve)."""
        return self.esperar_y_traer_al_frente(".*Selecci.n de informe.*", timeout=timeout)

    def llenar_seleccion_informe_en(self, w, codigo_reporte, intentos=3):
        """Llena el cuadro de 'Seleccion de informe'.

        IMPORTANTE: en cada intento volvemos a buscar el cuadro DESDE
        CERO por titulo (esperar_cuadro_seleccion_informe), en vez de
        reutilizar la misma referencia de ventana/control guardada.
        Confirmado que reutilizar una referencia vieja no es
        confiable: 'dlg.exists()' sobre un handle guardado puede decir
        'si existe' aunque en realidad Windows haya reciclado ese
        mismo numero de HWND para una ventana NUEVA y distinta (el
        mismo problema de reciclaje de HWND que ya vimos en otras
        partes de este proyecto) -- eso dejaba 'campo_definicion'
        apuntando a un control huerfano, de ahi los errores
        ElementNotVisible y [WinError 1400] que no eran el problema
        real. Una busqueda fresca por titulo es la unica forma
        confiable de saber si el cuadro sigue ahi o no."""
        usar_click_fisico = False
        w_actual = w

        for intento in range(1, intentos + 1):
            app = Application(backend="win32").connect(handle=w_actual.handle)
            dlg = app.window(handle=w_actual.handle)

            # No tomamos ciegamente el primer control de esta clase --
            # distintas instancias de Autoline (BYD vs Honda, etc.)
            # pueden tener un orden interno de controles distinto, con
            # campos ocultos o de tamano 0x0 antes del combo real de
            # 'Definicion de informe'. Filtramos por el primero que de
            # verdad tenga un rectangulo visible.
            candidatos = dlg.children(class_name="KCMLDBEdit_32")
            campo_definicion = None
            for c in candidatos:
                try:
                    r = c.rectangle()
                    if r.width() > 0 and r.height() > 0:
                        campo_definicion = c
                        break
                except Exception:
                    continue

            if campo_definicion is None:
                raise RuntimeError(
                    "No encontre un campo visible de 'Definicion de informe' "
                    "en el cuadro de 'Seleccion de informe' (todos los "
                    f"candidatos ({len(candidatos)}) salieron sin rectangulo valido)."
                )

            try:
                self.log(f"  Campo 'Definicion de informe' encontrado en {campo_definicion.rectangle()} (intento {intento}/{intentos})")
            except Exception:
                pass

            try:
                # Usamos .click() (basado en mensajes de Windows) en vez
                # de .click_input() (que simula un clic fisico real y
                # necesita robar el foco/'foreground' del sistema).
                # 'Seleccion de informe' es un cuadro modal hijo de la
                # ventana principal, y Windows parece no dejar pedirle
                # foco directamente a ese tipo de ventana -- de ahi el
                # error consistente. Los metodos basados en mensajes no
                # necesitan foreground para funcionar.
                if usar_click_fisico:
                    campo_definicion.click_input()
                else:
                    campo_definicion.click()
                time.sleep(0.15)
                campo_definicion.type_keys("^a", set_foreground=False)
                time.sleep(0.1)
                campo_definicion.type_keys(codigo_reporte, with_spaces=True, set_foreground=False)
                time.sleep(0.3)
                campo_definicion.type_keys("{ENTER}", set_foreground=False)
                time.sleep(0.6)
            except Exception as e:
                detalle = str(e) or f"{type(e).__name__} sin mensaje"
                self.log(f"  (fallo tecnico al escribir el codigo (intento {intento}/{intentos}): {detalle})")
                if type(e).__name__ == "ElementNotVisible" and not usar_click_fisico:
                    self.log("  (Cambiando a clic fisico real para el resto de los intentos.)")
                    usar_click_fisico = True
                # No regresamos ni tronamos aqui todavia -- caemos a la
                # busqueda fresca de abajo, que es la que realmente
                # decide si esto fue exito (cuadro ya no aparece) o
                # fallo real (cuadro sigue ahi, listo para reintentar).

            # Busqueda FRESCA por titulo -- NO reutilizamos dlg/
            # campo_definicion de este intento. Si ya no aparece, es
            # la señal confiable de que el codigo si se acepto y
            # Autoline avanzo a la siguiente pantalla.
            w_fresca = self.esperar_cuadro_seleccion_informe(timeout=3)
            if w_fresca is None:
                self.log("  El cuadro de 'Selección de informe' ya no aparece -- asumo que el codigo si se acepto.")
                return

            if intento == intentos:
                raise RuntimeError(
                    f"El cuadro de 'Selección de informe' sigue abierto despues "
                    f"de {intentos} intentos con el codigo '{codigo_reporte}'."
                )

            w_actual = w_fresca
            time.sleep(0.5)

    # ---------------- Fechas / sucursal ----------------

    def llenar_fecha(self, control, fecha_ddmmaaaa, intentos=3):
        solo_digitos = re.sub(r"\D", "", fecha_ddmmaaaa)
        for intento in range(1, intentos + 1):
            try:
                try:
                    control.set_focus()
                except Exception:
                    pass
                control.click_input()
                time.sleep(0.15)
                control.type_keys("{HOME}")
                time.sleep(0.1)
                control.type_keys(solo_digitos)
                time.sleep(0.2)
                return
            except Exception as e:
                detalle = str(e) or f"{type(e).__name__} sin mensaje"
                self.log(f"  (fallo tecnico al escribir fecha (intento {intento}/{intentos}): {detalle})")
                if intento == intentos:
                    raise
                time.sleep(1)

    def llenar_texto(self, control, valor, intentos=3):
        for intento in range(1, intentos + 1):
            try:
                try:
                    control.set_focus()
                except Exception:
                    pass
                control.click_input()
                time.sleep(0.15)
                control.type_keys("^a")
                time.sleep(0.1)
                control.type_keys(valor, with_spaces=True)
                time.sleep(0.2)
                return
            except Exception as e:
                detalle = str(e) or f"{type(e).__name__} sin mensaje"
                self.log(f"  (fallo tecnico al escribir texto (intento {intento}/{intentos}): {detalle})")
                if intento == intentos:
                    raise
                time.sleep(1)

    def _encontrar_campo_edit(self, dlg, titulo):
        """Busca un campo de texto por su nombre. Probamos PRIMERO la
        forma anidada (Pane con ese titulo, con un Edit adentro) --
        es la estructura confirmada para campos tipo 'Sucursal',
        'Aseguradora', etc. (los que tienen boton '...' de seleccion).
        Si probamos el Edit directo primero, a veces "encuentra" un
        control Edit distinto que hace match parcial de titulo con el
        backend UIA -- eso NO lanza error (parece que si funciono) pero
        escribe en el campo equivocado y el que se ve en pantalla se
        queda vacio. Como ultimo recurso probamos el Edit directo, que
        si es la forma correcta para campos simples como 'Desde'/
        'Hasta' (sin Pane de por medio).

        Puede haber MAS de un control con el mismo titulo en el arbol
        de accesibilidad -- uno visible en pantalla y otros ocultos o
        con tamano 0x0 (el mismo problema que ya resolvimos con los
        renglones del arbol). Por eso usamos 'descendants' (trae
        TODOS los que coincidan) y nos quedamos con el primero que de
        verdad tenga un rectangulo visible, en vez de confiar en el
        primer match que regrese 'child_window'."""
        def _primero_visible(candidatos):
            for c in candidatos:
                try:
                    r = c.rectangle()
                    if r.width() > 0 and r.height() > 0:
                        return c
                except Exception:
                    continue
            return None

        try:
            panes = dlg.descendants(title=titulo, control_type="Pane")
            for pane in panes:
                campo = _primero_visible(pane.descendants(control_type="Edit"))
                if campo is not None:
                    return campo
        except Exception:
            pass
        try:
            campo = _primero_visible(dlg.descendants(title=titulo, control_type="Edit"))
            if campo is not None:
                return campo
        except Exception:
            pass
        return None

    def llenar_campo_generico(self, dlg, titulo, valor):
        """Llena un campo por nombre, detectando solo si 'parece' fecha
        (dd/mm/aaaa) para usar el metodo de campo enmascarado, o texto
        normal en cualquier otro caso.

        NOTA sobre verificacion: confirmamos en vivo (viendo la
        pantalla mientras se escribia) que el campo 'Sucursal' SI
        recibe el texto correctamente, pero su control no expone ese
        texto de forma legible via window_text() -- regresa cadena
        vacia en vez de fallar o regresar su propia etiqueta. Por eso
        tratamos tanto 'vacio' como 'coincide con la etiqueta' como
        'no puedo verificar, pero seguramente si se escribio bien' --
        no como una falla real."""
        campo = self._encontrar_campo_edit(dlg, titulo)
        if campo is None:
            raise RuntimeError(f"No encontre el campo '{titulo}' en el cuadro de parametros.")

        try:
            self.log(f"  Campo '{titulo}' encontrado en {campo.rectangle()}")
        except Exception:
            pass

        es_fecha = bool(re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", valor.strip()))
        esperado = re.sub(r"\D", "", valor) if es_fecha else valor.strip()

        if es_fecha:
            self.llenar_fecha(campo, valor)
        else:
            self.llenar_texto(campo, valor)

        time.sleep(0.3)
        try:
            texto_actual = campo.window_text()
        except Exception:
            texto_actual = ""

        if not texto_actual.strip() or texto_actual.strip() == titulo.strip():
            self.log(f"  (Nota: no pude verificar '{titulo}' -- este control no expone su valor de forma legible. Sigo de todas formas.)")
            return

        actual_normalizado = re.sub(r"\D", "", texto_actual) if es_fecha else texto_actual.strip()
        if actual_normalizado and esperado in actual_normalizado:
            return

        # Solo llegamos aqui si el campo SI regreso texto legible, y
        # ese texto NO coincide con lo que escribimos -- ahi si vale
        # la pena reintentar, porque sugiere que encontramos el
        # control equivocado (con texto de otro lado adentro).
        self.log(f"  (Campo '{titulo}' muestra un valor distinto al esperado ('{texto_actual}'); reintentando una vez...)")
        campo_actual = self._encontrar_campo_edit(dlg, titulo) or campo
        if es_fecha:
            self.llenar_fecha(campo_actual, valor)
        else:
            self.llenar_texto(campo_actual, valor)
        time.sleep(0.3)

    def limpiar_dialogos_extra(self):
        """Cierra CUALQUIER cuadro de Autoline que haya quedado abierto
        y no sea la ventana principal -- no solo los de 'Cerrar'
        (resultados), sino tambien 'Seleccion de informe' u otros que
        se hayan quedado atorados por un timeout o error anterior.
        Esto es clave: mientras un cuadro modal quede abierto, Windows
        no deja usar la ventana principal detras de el, y todo lo
        demas empieza a fallar en cadena."""
        intentos = 0
        while intentos < 8:
            intentos += 1
            try:
                candidatas = Desktop(backend="win32").windows(
                    class_name="KCMLMasterForm_32", visible_only=True
                )
            except Exception:
                break

            # La ventana principal es la unica cuyo titulo coincide con
            # titulo_parcial -- todo lo demas es un dialogo que hay que
            # cerrar.
            extra = [
                w for w in candidatas
                if self.titulo_parcial.lower() not in w.window_text().lower()
            ]
            if not extra:
                break

            for w in extra:
                try:
                    app = Application(backend="win32").connect(handle=w.handle)
                    spec = app.window(handle=w.handle)
                    cerrado = False
                    for titulo_boton in ("Cerrar", "Cancelar"):
                        try:
                            boton = spec.child_window(title=titulo_boton, class_name="KCMLButton_32")
                            if boton.exists():
                                boton.click_input()
                                cerrado = True
                                self.log(f"Cerre un cuadro atorado: '{w.window_text()}' (boton {titulo_boton}).")
                                break
                        except Exception:
                            continue
                    if not cerrado:
                        # Ultimo recurso: Escape
                        spec.type_keys("{ESC}")
                        self.log(f"Cerre un cuadro atorado con Escape: '{w.window_text()}'.")
                    time.sleep(0.5)
                except Exception:
                    continue

    def _buscar_ventana_con_boton_cerrar(self):
        try:
            candidatas = Desktop(backend="win32").windows(
                class_name="KCMLMasterForm_32", visible_only=True
            )
        except Exception:
            return None
        for w in candidatas:
            try:
                app = Application(backend="win32").connect(handle=w.handle)
                spec = app.window(handle=w.handle)
                boton = spec.child_window(title="Cerrar", class_name="KCMLButton_32")
                if boton.exists():
                    return spec
            except Exception:
                continue
        return None

    def cerrar_resultados_viejos(self):
        cerradas = 0
        while True:
            spec = self._buscar_ventana_con_boton_cerrar()
            if spec is None:
                break
            try:
                spec.child_window(title="Cerrar", class_name="KCMLButton_32").click_input()
                cerradas += 1
                time.sleep(0.5)
            except Exception:
                break
        if cerradas:
            self.log(f"Cerre {cerradas} cuadro(s) de resultados viejo(s).")

    # ---------------- Excel ----------------

    def obtener_handles_excel_actuales(self):
        try:
            return {
                w.handle
                for w in Desktop(backend="win32").windows(title_re=".*Excel.*", visible_only=True)
            }
        except Exception:
            return set()

    def encontrar_excel_nuevo(self, handles_previos, timeout=30):
        inicio = time.time()
        while time.time() - inicio < timeout:
            self._checar_cancelacion()
            try:
                candidatas = Desktop(backend="win32").windows(
                    title_re=".*Excel.*", visible_only=True
                )
                for w in candidatas:
                    if w.handle not in handles_previos:
                        return w
            except Exception:
                pass
            time.sleep(0.5)
        return None

    def guardar_excel_via_gui(self, w_excel, nombre_archivo):
        os.makedirs(self.carpeta_destino, exist_ok=True)
        ruta_completa = os.path.join(self.carpeta_destino, nombre_archivo)

        forzar_ventana_al_frente(w_excel.handle)
        time.sleep(0.5)

        app_excel = Application(backend="win32").connect(handle=w_excel.handle)
        ventana_excel = app_excel.window(handle=w_excel.handle)

        ventana_excel.type_keys("^s")
        time.sleep(1.5)

        candidatas = Desktop(backend="win32").windows(
            title_re=".*Guardar como.*", visible_only=True
        )
        if not candidatas:
            time.sleep(1.5)
            candidatas = Desktop(backend="win32").windows(
                title_re=".*Guardar como.*", visible_only=True
            )

        if not candidatas:
            self.log("[ADVERTENCIA] No aparecio el dialogo 'Guardar como'.")
            return None

        w_guardar = candidatas[0]
        app_guardar = Application(backend="win32").connect(handle=w_guardar.handle)
        dlg_guardar = app_guardar.window(handle=w_guardar.handle)

        campo_nombre = dlg_guardar.child_window(class_name="Edit", found_index=0)
        campo_nombre.set_focus()
        time.sleep(0.2)
        campo_nombre.type_keys("^a")
        time.sleep(0.1)
        campo_nombre.type_keys(ruta_completa, with_spaces=True)
        time.sleep(0.3)
        campo_nombre.type_keys("{ENTER}")
        time.sleep(1)

        try:
            ventana_excel.type_keys("{ENTER}")
        except Exception:
            pass
        time.sleep(1)

        ventana_excel.type_keys("^w")
        time.sleep(0.5)

        return ruta_completa

    # ---------------- Flujo completo ----------------

    def navegar_arbol_con_reintento_total(self, ruta_arbol, intentos_totales=2, **kwargs):
        """Envuelve navegar_arbol con un ultimo recurso: si falla
        porque no encontro algun renglon visible (aunque ya agotamos
        reintentos, scroll hacia arriba y hacia abajo dentro de
        asegurar_visible), colapsamos TODO el arbol de vuelta (igual
        que hacemos entre trabajos al cambiar de agencia) y volvemos a
        navegar desde cero, con expansion fresca en cada nivel -- en
        vez de seguir intentando 'reparar' un estado raro del arbol a
        medias, reiniciamos a un estado conocido y confiable."""
        ultimo_error = None
        for intento in range(1, intentos_totales + 1):
            try:
                return self.navegar_arbol(ruta_arbol, **kwargs)
            except RuntimeError as e:
                ultimo_error = e
                if "No encontre" not in str(e) or intento == intentos_totales:
                    raise
                self.log(f"  ('{e}' -- colapsando todo y reintentando la navegacion desde cero, intento {intento}/{intentos_totales})")
                self.colapsar_todo(ruta_arbol)
                time.sleep(0.5)
        raise ultimo_error

    def ejecutar_para_sucursal(self, ruta_arbol, usa_seleccion_informe, codigo_seleccion,
                                campos_fijos, nombre_campo_variable, valor_variable,
                                nombre_archivo_base):
        etiqueta = ruta_arbol[-1]
        detalle_variable = f" / {nombre_campo_variable} {valor_variable}" if nombre_campo_variable else ""
        self.log(f"\n=== {nombre_archivo_base} / {etiqueta}{detalle_variable} ===")

        handles_excel_previos = self.obtener_handles_excel_actuales()

        # navegar_arbol ahora reintenta el doble clic (sin renavegar
        # todo el arbol) si el cuadro esperado no aparece -- el doble
        # clic en segundo plano no siempre activa al primer intento.
        if usa_seleccion_informe:
            w_seleccion = self.navegar_arbol_con_reintento_total(
                ruta_arbol,
                verificar_activacion=lambda t: self.esperar_cuadro_seleccion_informe(timeout=t),
                intentos_activacion=3, timeout_por_intento=12,
            )
            if w_seleccion is None:
                raise RuntimeError("No aparecio el cuadro de 'Selección de informe'.")
            self.llenar_seleccion_informe_en(w_seleccion, codigo_seleccion)
            # Excluimos el patron de 'Seleccion de informe' por si ese
            # cuadro tarda un poco en cerrarse de verdad y todavia
            # aparece visible en el primer poll.
            w_param = self.esperar_cuadro_extra_autoline(
                excluir_patrones=[r".*Selecci.n de informe.*"], timeout=30
            )
        else:
            w_param = self.navegar_arbol_con_reintento_total(
                ruta_arbol,
                verificar_activacion=lambda t: self.esperar_cuadro_extra_autoline(timeout=t),
                intentos_activacion=3, timeout_por_intento=12,
            )

        if w_param is None:
            raise RuntimeError("No aparecio el cuadro de parametros.")

        titulo_param = w_param.window_text()
        self.log(f"Cuadro de parametros: '{titulo_param}'")

        app = Application(backend="uia").connect(handle=w_param.handle)
        dlg = app.window(handle=w_param.handle)

        # Campos fijos (ej. Desde/Hasta, o los nombres que tenga ese
        # reporte en particular) + el campo que cambia en cada corrida
        # (ej. Sucursal). Si nombre_campo_variable es None (reportes
        # que se corren una sola vez sin nada que varie, ej. "SO"),
        # simplemente no hay nada que llenar aqui.
        for nombre_campo, valor in campos_fijos.items():
            self.llenar_campo_generico(dlg, nombre_campo, valor)
        if nombre_campo_variable:
            self.llenar_campo_generico(dlg, nombre_campo_variable, valor_variable)

        for intento_ok in range(1, 4):
            try:
                dlg.child_window(title="OK", control_type="Button").click_input()
                break
            except Exception as e:
                self.log(f"  (fallo tecnico al dar clic en OK (intento {intento_ok}/3): {e})")
                if intento_ok == 3:
                    raise
                time.sleep(1)
        self.log("Clic en OK. Esperando a que Autoline procese...")

        inicio = time.time()
        ultimo_aviso = 0
        resultado = None
        while time.time() - inicio < self.timeout_proceso:
            self._checar_cancelacion()
            resultado = self._buscar_ventana_con_boton_cerrar()
            if resultado is not None:
                break
            transcurrido = int(time.time() - inicio)
            if transcurrido - ultimo_aviso >= 15:
                self.log(f"  ... sigue procesando ({transcurrido}s transcurridos)")
                ultimo_aviso = transcurrido
            time.sleep(1)

        if resultado is None:
            raise RuntimeError("No aparecio el cuadro de resultados a tiempo.")

        self.log(f"Cuadro de resultados detectado: '{resultado.window_text()}'")

        ruta = None
        w_excel_nuevo = self.encontrar_excel_nuevo(handles_excel_previos)
        if w_excel_nuevo is None:
            self.log("[ADVERTENCIA] No encontre la ventana de Excel nueva.")
        else:
            nombre_archivo = f"{nombre_archivo_base}_{etiqueta}_{valor_variable}.xlsx"
            ruta = self.guardar_excel_via_gui(w_excel_nuevo, nombre_archivo)
            if ruta:
                self.log(f"Excel guardado en: {ruta}")

        for intento_cerrar in range(1, 4):
            try:
                resultado.child_window(title="Cerrar", class_name="KCMLButton_32").click()
                break
            except Exception as e:
                self.log(f"  (fallo tecnico al cerrar el cuadro de resultados (intento {intento_cerrar}/3): {e})")
                if intento_cerrar == 3:
                    raise
                time.sleep(1)
        self.log("Clic en 'Cerrar'.")
        return ruta

    def colapsar_todo(self, ruta_arbol):
        """Colapsa el arbol de vuelta despues de terminar un trabajo,
        para que no quede mas de una rama abierta a la vez cuando se
        pasa a un trabajo distinto (otra agencia u otra instancia).

        En vez de mandar varias flechas izquierda seguidas sobre UNA
        sola referencia guardada (lo que resulto poco confiable -- la
        referencia UIA de un item puede quedar obsoleta justo despues
        de colapsar algo, el mismo problema que ya vimos con la
        navegacion), volvemos a BUSCAR CADA NIVEL POR SU PROPIO TEXTO
        de mas profundo a mas superficial, y colapsamos cada uno con
        una sola flecha izquierda usando una referencia fresca. Basta
        con llegar a colapsar el nivel de la agencia (ruta_arbol[1])
        para ocultar todo lo que estaba abierto debajo -- no hace
        falta seguir subiendo hasta la raiz ('Vehiculos'/'CRM'), esa
        se puede dejar expandida."""
        try:
            arbol = self.obtener_arbol_uia()
        except Exception as e:
            self.log(f"  (No pude reconectar al arbol para colapsar: {e})")
            return

        # Nunca colapsamos el ultimo elemento (es una hoja, no tiene
        # nada que colapsar) ni el primero (la raiz 'Vehiculos'/'CRM',
        # que se puede quedar expandida sin problema).
        niveles_a_colapsar = ruta_arbol[1:-1] if len(ruta_arbol) > 2 else ruta_arbol[:-1]

        algo_colapsado = False
        for texto in reversed(niveles_a_colapsar):
            try:
                item = self.buscar_item_visible(arbol, texto)
                if item is None:
                    # Puede que este nivel (tipicamente la agencia)
                    # haya quedado scrolleado FUERA de la pantalla
                    # despues de colapsar los niveles mas profundos
                    # (colapsar no necesariamente regresa el scroll
                    # hacia arriba). Antes de rendirnos con este nivel,
                    # intentamos regresar el scroll al inicio del arbol
                    # y buscarlo una vez mas.
                    self.resetear_scroll_arbol(arbol, ruta_arbol)
                    item = self.buscar_item_visible(arbol, texto)
                if item is None:
                    continue
                # Igual que en cada interaccion con el arbol desde un
                # proceso en segundo plano: sin forzar el foco real de
                # la ventana, la flecha no siempre le llega de verdad
                # al control.
                forzar_ventana_al_frente(arbol.handle)
                time.sleep(0.15)
                item.click_input()
                time.sleep(0.2)
                item.type_keys("{LEFT}")
                time.sleep(0.3)
                self.log(f"  Colapsado: '{texto}'.")
                algo_colapsado = True
            except Exception as e:
                self.log(f"  (No pude colapsar '{texto}': {e})")

        if not algo_colapsado:
            self.log("  (No encontre ningun nivel de la ruta anterior visible para colapsar -- puede que ya estuviera colapsado.)")

    def ejecutar_lote(self, trabajos):
        """Procesa VARIOS trabajos en secuencia (distintas instancias,
        agencias y/o reportes). Cada trabajo es un diccionario con:
            titulo_parcial: texto que identifica la ventana de esa instancia
            ruta_arbol: lista COMPLETA de niveles del arbol, incluyendo
                el ultimo renglon que se activa con doble clic
            usa_seleccion_informe: True/False
            codigo_seleccion: codigo a escribir en 'Seleccion de informe'
                (solo se usa si usa_seleccion_informe es True)
            campos_fijos: {"Desde": "01/01/2026", "Hasta": "20/07/2026"}
            nombre_campo_variable: ej. "Sucursal"
            valores_variable: lista de codigos, ej. ["BDT", "BDL", "BDC"]
            etiqueta: (opcional) texto descriptivo solo para el log

        Entre un trabajo y otro, colapsa el arbol para que no queden
        varias ramas abiertas a la vez. Regresa la lista de rutas de
        TODOS los archivos Excel generados."""
        todas_las_rutas = []
        for idx_trabajo, trabajo in enumerate(trabajos, start=1):
            self._checar_cancelacion()
            etiqueta = trabajo.get("etiqueta", "")
            self.log(f"\n{'=' * 60}")
            self.log(f"TRABAJO {idx_trabajo}/{len(trabajos)}: {etiqueta}")
            self.log(f"{'=' * 60}")

            self.titulo_parcial = trabajo["titulo_parcial"]

            try:
                rutas = self.ejecutar(
                    trabajo["ruta_arbol"],
                    trabajo["usa_seleccion_informe"],
                    trabajo.get("codigo_seleccion"),
                    trabajo["campos_fijos"],
                    trabajo["nombre_campo_variable"],
                    trabajo["valores_variable"],
                    nombre_archivo_base=trabajo.get("codigo_seleccion") or trabajo["ruta_arbol"][-1],
                )
                todas_las_rutas.extend(rutas)
            except ReporteCancelado:
                raise
            except Exception as e:
                self.log(f"[ERROR] Fallo el trabajo completo '{etiqueta}': {e}")
                self.log("Continuando con el siguiente trabajo de la cola...")

            if idx_trabajo < len(trabajos):
                self.log("Colapsando el árbol antes de continuar con el siguiente trabajo...")
                self.colapsar_todo(trabajo["ruta_arbol"])

        self.log(f"\n¡LOTE COMPLETO! {len(todas_las_rutas)} archivo(s) generado(s) en total.")
        return todas_las_rutas

    def ejecutar(self, ruta_arbol, usa_seleccion_informe, codigo_seleccion, campos_fijos,
                 nombre_campo_variable, valores_variable, nombre_archivo_base=None):
        """Punto de entrada principal para UN reporte/agencia.

        ruta_arbol: lista COMPLETA de renglones del arbol, incluyendo
            el ultimo (el que se activa con doble clic). Ej:
            ["Vehículos", "C2. Automoviles AKV BYD", "Informes y consultas", "Generador de informes", "Ejecutar generador de informes"]
            ["Vehículos", "01. Kasa Automotriz, SA de CV", "Informes y consultas", "NFF Vencimiento Financiamiento"]

        usa_seleccion_informe: True si despues del doble clic aparece
            el cuadro de "Seleccion de informe" donde escribes un
            codigo (ej. ENV, ENE, CVH). False si va directo al cuadro
            de parametros (ej. NFF, ZS1 Seguros).

        codigo_seleccion: el codigo a escribir en "Seleccion de
            informe" (solo aplica si usa_seleccion_informe es True).

        campos_fijos: diccionario {nombre_del_campo: valor} para los
            campos que NO cambian entre corridas (ej. las fechas):
            {"Desde": "01/01/2026", "Hasta": "20/07/2026"}
            (o los nombres que tenga ese reporte, ej. "Desde Fecha de Entrega")

        nombre_campo_variable: nombre del campo que SI cambia en cada
            corrida (ej. "Sucursal")

        valores_variable: lista de valores para ese campo, uno por
            corrida (ej. ["BDT", "BDL", "BDC"])

        Regresa la lista de rutas de los archivos Excel generados."""
        nombre_archivo_base = nombre_archivo_base or codigo_seleccion or ruta_arbol[-1]
        if nombre_campo_variable:
            self.log(f"Valores a procesar ({nombre_campo_variable}): {valores_variable}")
        else:
            self.log("Se corre una sola vez (este reporte no tiene un campo que varie).")
        rutas_generadas = []

        for i, valor in enumerate(valores_variable, start=1):
            self._checar_cancelacion()
            self.log(f"\n{'#' * 50}")
            if nombre_campo_variable:
                self.log(f"# {i}/{len(valores_variable)}: {nombre_campo_variable} = {valor}")
            else:
                self.log(f"# {i}/{len(valores_variable)}")
            self.log(f"{'#' * 50}")

            try:
                self.limpiar_dialogos_extra()
                self.cerrar_resultados_viejos()
                time.sleep(2)
                ruta = self.ejecutar_para_sucursal(
                    ruta_arbol, usa_seleccion_informe, codigo_seleccion,
                    campos_fijos, nombre_campo_variable, valor, nombre_archivo_base
                )
                if ruta:
                    rutas_generadas.append(ruta)
            except ReporteCancelado:
                raise
            except Exception as e:
                etiqueta_error = f"{nombre_campo_variable}={valor}" if nombre_campo_variable else f"intento {i}"
                self.log(f"[ERROR] Fallo en {etiqueta_error}: {e}")
                self.log("Continuando con el siguiente valor...")
                continue

        self.log(f"\n¡Listo! Se procesaron {len(rutas_generadas)}/{len(valores_variable)} corrida(s) exitosamente.")
        return rutas_generadas
