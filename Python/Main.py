from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import random
import time
import traceback

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI()


# ============================================================
# CONFIGURACIÓN DE LOS TEXTOS
# ============================================================

class TextoConfig(BaseModel):
    pregunta: str
    respuestas: List[str]


class FormConfig(BaseModel):
    url: str
    iteraciones: int
    requiereLoginGoogle: bool

    textosCortosConfig: List[TextoConfig] = []
    textosLargosConfig: List[TextoConfig] = []


# ============================================================
# UTILIDADES
# ============================================================

def esperar(segundos=0.3):
    time.sleep(segundos)


def click_con_js(driver, element):
    """
    Hace clic sobre un elemento utilizando JavaScript.
    Es más resistente a problemas de elementos parcialmente visibles.
    """
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            element
        )

        esperar(0.15)

        driver.execute_script(
            "arguments[0].click();",
            element
        )

        esperar(0.25)

        return True

    except Exception as e:
        print(f"⚠️ No se pudo hacer click: {e}")
        return False


def obtener_texto_pregunta(pregunta):
    """
    Intenta obtener el título de la pregunta.
    """

    selectores = [
        './/div[@role="heading"]',
        './/div[contains(@class, "M7eMe")]',
        './/span[contains(@class, "M7eMe")]'
    ]

    for xpath in selectores:
        try:
            elementos = pregunta.find_elements(By.XPATH, xpath)

            for elemento in elementos:
                texto = elemento.text.strip()

                if texto:
                    return texto.lower()

        except:
            pass

    return ""


def obtener_texto_config(texto_pregunta, configuraciones, predeterminado):
    """
    Busca una respuesta configurada para la pregunta.
    """

    if not configuraciones:
        return predeterminado

    for cfg in configuraciones:

        pregunta_cfg = cfg.pregunta.strip().lower()

        if pregunta_cfg in texto_pregunta and cfg.respuestas:

            return random.choice(cfg.respuestas)

    # Si no encontró coincidencia exacta,
    # utiliza cualquiera de las respuestas configuradas.

    todas = []

    for cfg in configuraciones:
        todas.extend(cfg.respuestas)

    if todas:
        return random.choice(todas)

    return predeterminado


def escribir_input(input_element, texto):
    """
    Escribe en un input intentando evitar problemas con
    valores anteriores.
    """

    try:
        input_element.click()

        input_element.send_keys(Keys.CONTROL, "a")
        input_element.send_keys(Keys.BACKSPACE)

        input_element.send_keys(str(texto))

        return True

    except Exception as e:

        print(f"⚠️ Error escribiendo input: {e}")

        try:
            input_element.clear()
            input_element.send_keys(str(texto))
            return True

        except:
            return False


# ============================================================
# MATRIZ DE UNA OPCIÓN
# ============================================================

def procesar_matriz_radio(driver, pregunta):
    """
    Procesa una matriz de opción múltiple.

    Google Forms normalmente representa cada fila de la matriz
    mediante un radiogroup que contiene varios elementos role=radio.
    """

    try:

        # Primero buscamos radiogroups.
        grupos = pregunta.find_elements(
            By.XPATH,
            './/*[@role="radiogroup"]'
        )

        grupos_validos = []

        for grupo in grupos:

            radios = grupo.find_elements(
                By.XPATH,
                './/*[@role="radio"]'
            )

            if radios:
                grupos_validos.append(grupo)

        # Una pregunta normal de opción múltiple
        # suele tener UN solo radiogroup.
        #
        # Una matriz tiene normalmente varios.
        if len(grupos_validos) < 2:
            return False

        print(
            f"   📊 Matriz detectada: "
            f"{len(grupos_validos)} filas"
        )

        for indice, grupo in enumerate(grupos_validos):

            radios = grupo.find_elements(
                By.XPATH,
                './/*[@role="radio"]'
            )

            if not radios:
                continue

            # Seleccionar una opción aleatoria de esta fila.
            radio = random.choice(radios)

            if click_con_js(driver, radio):

                print(
                    f"      ✓ Fila {indice + 1}: "
                    f"opción seleccionada"
                )

            esperar(0.15)

        return True

    except Exception as e:

        print(f"❌ Error procesando matriz: {e}")
        traceback.print_exc()

        return False


# ============================================================
# MATRIZ DE CASILLAS
# ============================================================

def procesar_matriz_checkbox(driver, pregunta):
    """
    Procesa una matriz de casillas de verificación.
    """

    try:

        grupos = pregunta.find_elements(
            By.XPATH,
            './/*[@role="group"]'
        )

        grupos_validos = []

        for grupo in grupos:

            checkboxes = grupo.find_elements(
                By.XPATH,
                './/*[@role="checkbox"]'
            )

            if checkboxes:
                grupos_validos.append(grupo)

        if len(grupos_validos) < 2:
            return False

        print(
            f"   ☑️ Matriz de casillas detectada: "
            f"{len(grupos_validos)} filas"
        )

        for indice, grupo in enumerate(grupos_validos):

            checkboxes = grupo.find_elements(
                By.XPATH,
                './/*[@role="checkbox"]'
            )

            if not checkboxes:
                continue

            # Seleccionamos una o más opciones.
            cantidad = random.randint(
                1,
                len(checkboxes)
            )

            seleccionadas = random.sample(
                checkboxes,
                cantidad
            )

            for checkbox in seleccionadas:
                click_con_js(driver, checkbox)
                esperar(0.1)

            print(
                f"      ✓ Fila {indice + 1}: "
                f"{cantidad} opción(es)"
            )

        return True

    except Exception as e:

        print(f"❌ Error procesando matriz checkbox: {e}")
        traceback.print_exc()

        return False


# ============================================================
# FECHA
# ============================================================

def procesar_fecha(driver, pregunta):

    """
    Google Forms puede mostrar:

        DD / MM / AAAA

    pero internamente utilizar:

        <input type="date">

    En ese caso el valor debe enviarse como:

        YYYY-MM-DD
    """

    try:

        print(
            "   📅 Buscando campo fecha..."
        )

        # ====================================================
        # BUSCAR INPUT TYPE=DATE
        # ====================================================

        date_inputs = pregunta.find_elements(
            By.XPATH,
            './/input[@type="date"]'
        )

        visibles = []

        for inp in date_inputs:

            try:

                if inp.is_displayed():

                    visibles.append(inp)

            except:
                pass

        print(
            f"   🔎 Inputs date encontrados: "
            f"{len(visibles)}"
        )

        # ====================================================
        # SI ENCONTRAMOS INPUT DATE
        # ====================================================

        if visibles:

            fecha = random.choice([
                "2024-01-15",
                "2024-02-20",
                "2024-03-10",
                "2024-04-18",
                "2024-05-22",
                "2024-06-12",
                "2024-07-25",
                "2024-08-17",
                "2024-09-14",
                "2024-10-21",
                "2024-11-09",
                "2024-12-16"
            ])

            inp = visibles[0]

            print(
                f"   ✏️ Fecha ISO: {fecha}"
            )

            # ------------------------------------------------
            # MÉTODO 1:
            # JavaScript
            # ------------------------------------------------

            try:

                driver.execute_script(
                    """
                    const input = arguments[0];
                    const value = arguments[1];

                    input.value = value;

                    input.dispatchEvent(
                        new Event('input', {
                            bubbles: true
                        })
                    );

                    input.dispatchEvent(
                        new Event('change', {
                            bubbles: true
                        })
                    );
                    """,
                    inp,
                    fecha
                )

                esperar(0.4)

                valor_actual = inp.get_attribute(
                    "value"
                )

                print(
                    f"   🔎 Valor después de JS: "
                    f"{valor_actual}"
                )

                if valor_actual == fecha:

                    try:
                        inp.send_keys(Keys.TAB)
                    except:
                        pass

                    esperar(0.4)

                    # Mostrar formato legible
                    partes = fecha.split("-")

                    print(
                        "   ✅ Fecha completada: "
                        f"{partes[2]}/"
                        f"{partes[1]}/"
                        f"{partes[0]}"
                    )

                    return True

            except Exception as e:

                print(
                    f"   ⚠️ Falló método JS: {e}"
                )

            # ------------------------------------------------
            # MÉTODO 2:
            # send_keys
            # ------------------------------------------------

            try:

                print(
                    "   🔧 Intentando "
                    "send_keys..."
                )

                inp.click()

                inp.send_keys(
                    Keys.CONTROL,
                    "a"
                )

                inp.send_keys(
                    Keys.BACKSPACE
                )

                # Para input=date, Selenium/Chrome/Edge
                # acepta normalmente la fecha en partes.
                partes = fecha.split("-")

                inp.send_keys(
                    partes[1]
                )

                inp.send_keys(
                    partes[2]
                )

                inp.send_keys(
                    partes[0]
                )

                inp.send_keys(
                    Keys.TAB
                )

                esperar(0.5)

                valor_actual = (
                    inp.get_attribute("value")
                )

                print(
                    f"   🔎 Valor final: "
                    f"{valor_actual}"
                )

                if valor_actual:

                    print(
                        f"   ✅ Fecha completada: "
                        f"{valor_actual}"
                    )

                    return True

            except Exception as e:

                print(
                    f"   ⚠️ send_keys también falló: "
                    f"{e}"
                )

        # ====================================================
        # FALLBACK
        # POR SI ALGÚN DÍA GOOGLE FORMS CAMBIA EL CONTROL
        # Y VUELVE A UTILIZAR 3 INPUTS.
        # ====================================================

        print(
            "   🔧 No se encontró input[type=date]."
        )

        inputs = obtener_inputs_visibles(
            pregunta
        )

        print(
            f"   🔎 Inputs normales visibles: "
            f"{len(inputs)}"
        )

        if len(inputs) >= 3:

            dia_input = inputs[0]
            mes_input = inputs[1]
            anio_input = inputs[2]

            dia = random.randint(
                1,
                28
            )

            mes = random.randint(
                1,
                12
            )

            anio = random.randint(
                2020,
                2026
            )

            print(
                f"   ✏️ Día: {dia:02d}"
            )

            escribir_input(
                dia_input,
                f"{dia:02d}"
            )

            esperar(0.2)

            print(
                f"   ✏️ Mes: {mes:02d}"
            )

            escribir_input(
                mes_input,
                f"{mes:02d}"
            )

            esperar(0.2)

            print(
                f"   ✏️ Año: {anio}"
            )

            escribir_input(
                anio_input,
                str(anio)
            )

            try:
                anio_input.send_keys(
                    Keys.TAB
                )
            except:
                pass

            esperar(0.5)

            print(
                "   ✅ Fecha completada."
            )

            return True

        print(
            "   ❌ No se pudo encontrar "
            "el campo fecha."
        )

        return False

    except Exception as e:

        print(
            f"❌ Error procesando fecha: {e}"
        )

        traceback.print_exc()

        return False

# ============================================================
# HORA
# ============================================================

def procesar_hora(driver, pregunta):
    """
    Procesa una pregunta de tipo hora.
    """

    try:

        inputs = pregunta.find_elements(
            By.XPATH,
            './/input'
        )

        visibles = [
            i for i in inputs
            if i.is_displayed()
        ]

        if len(visibles) < 2:
            return False

        hora = random.randint(1, 12)

        minuto = random.choice([
            0,
            15,
            30,
            45
        ])

        escribir_input(
            visibles[0],
            hora
        )

        escribir_input(
            visibles[1],
            minuto
        )

        print(
            f"   🕐 Hora: "
            f"{hora}:{minuto:02d}"
        )

        esperar(0.2)

        return True

    except Exception as e:

        print(f"❌ Error procesando hora: {e}")
        traceback.print_exc()

        return False


# ============================================================
# LISTA DESPLEGABLE
# ============================================================

def procesar_dropdown(driver, pregunta):

    try:

        print(
            "   🔽 Buscando lista desplegable..."
        )

        # ====================================================
        # BUSCAR EL CONTROL DEL DROPDOWN
        # ====================================================

        controles = pregunta.find_elements(
            By.XPATH,
            './/*[@role="listbox"]'
            ' | .//*[@role="combobox"]'
        )

        controles_visibles = []

        for control in controles:

            try:

                if control.is_displayed():
                    controles_visibles.append(control)

            except:
                pass

        if not controles_visibles:

            print(
                "   ❌ No se encontró el dropdown."
            )

            return False

        dropdown = controles_visibles[0]

        print(
            "   ✓ Dropdown encontrado."
        )

        # ====================================================
        # ABRIR DROPDOWN
        # ====================================================

        if not click_con_js(
            driver,
            dropdown
        ):

            return False

        esperar(0.6)

        # ====================================================
        # BUSCAR TODAS LAS OPCIONES
        # ====================================================

        opciones = driver.find_elements(
            By.XPATH,
            '//*[@role="option"]'
            ' | //*[@role="menuitem"]'
        )

        opciones_validas = []

        # Textos que NO son respuestas reales
        textos_ignorados = {
            "",
            "elegir",
            "elige",
            "seleccionar",
            "seleccione",
            "selecciona",
            "selecciona una opción",
            "seleccione una opción",
            "choose",
            "select",
            "select an option",
            "select one",
            "seleccionar una opción"
        }

        # ====================================================
        # FILTRAR OPCIONES
        # ====================================================

        for opcion in opciones:

            try:

                if not opcion.is_displayed():
                    continue

                texto = (
                    opcion.text
                    .strip()
                )

                texto_normalizado = (
                    texto
                    .lower()
                    .strip()
                )

                print(
                    f"      🔎 Opción detectada: "
                    f"'{texto}'"
                )

                # ------------------------------------------------
                # IGNORAR VACÍAS
                # ------------------------------------------------

                if not texto_normalizado:
                    continue

                # ------------------------------------------------
                # IGNORAR "ELEGIR"
                # ------------------------------------------------

                if texto_normalizado in textos_ignorados:

                    print(
                        f"      ⏭️ Ignorada: "
                        f"'{texto}'"
                    )

                    continue

                # ------------------------------------------------
                # IGNORAR DESHABILITADAS
                # ------------------------------------------------

                if (
                    opcion.get_attribute(
                        "aria-disabled"
                    )
                    == "true"
                ):

                    print(
                        f"      ⏭️ Deshabilitada: "
                        f"'{texto}'"
                    )

                    continue

                # ------------------------------------------------
                # IGNORAR SI ES EL VALOR ACTUAL
                # ------------------------------------------------

                aria_selected = (
                    opcion.get_attribute(
                        "aria-selected"
                    )
                )

                # Una opción puede estar seleccionada,
                # pero NO necesariamente debemos excluirla.
                #
                # Por eso aquí solamente mostramos información.

                if aria_selected == "true":

                    print(
                        f"      ℹ️ Actualmente seleccionada: "
                        f"'{texto}'"
                    )

                # ------------------------------------------------
                # AGREGAR COMO OPCIÓN REAL
                # ------------------------------------------------

                opciones_validas.append(
                    opcion
                )

            except Exception as e:

                print(
                    f"      ⚠️ Error leyendo opción: "
                    f"{e}"
                )

        # ====================================================
        # MOSTRAR RESULTADO
        # ====================================================

        print(
            f"   🔎 Opciones reales encontradas: "
            f"{len(opciones_validas)}"
        )

        # ====================================================
        # NO HAY OPCIONES
        # ====================================================

        if not opciones_validas:

            print(
                "   ❌ No se encontraron "
                "opciones reales."
            )

            try:

                driver.find_element(
                    By.TAG_NAME,
                    "body"
                ).send_keys(
                    Keys.ESCAPE
                )

            except:
                pass

            return False

        # ====================================================
        # SELECCIONAR OPCIÓN REAL
        # ====================================================

        opcion = random.choice(
            opciones_validas
        )

        texto = (
            opcion.text
            .strip()
        )

        print(
            f"   🎯 Seleccionando: "
            f"'{texto}'"
        )

        # ====================================================
        # CLICK
        # ====================================================

        if click_con_js(
            driver,
            opcion
        ):

            esperar(0.5)

            # ------------------------------------------------
            # COMPROBAR EL VALOR DEL DROPDOWN
            # ------------------------------------------------

            try:

                valor_despues = (
                    dropdown.text
                    .strip()
                )

                print(
                    f"   🔎 Dropdown después "
                    f"del click: "
                    f"'{valor_despues}'"
                )

            except:
                pass

            print(
                f"   ✅ Dropdown seleccionado: "
                f"'{texto}'"
            )

            return True

        print(
            "   ❌ No se pudo hacer click "
            "en la opción."
        )

        return False

    except Exception as e:

        print(
            f"❌ Error procesando dropdown: {e}"
        )

        traceback.print_exc()

        return False

# ============================================================
# CHECKBOXES
# ============================================================

def procesar_checkboxes(driver, pregunta):
    """
    Procesa una pregunta normal de casillas.
    """

    try:

        checkboxes = pregunta.find_elements(
            By.XPATH,
            './/*[@role="checkbox"]'
        )

        if not checkboxes:
            return False

        # Si tiene muchos grupos internos,
        # probablemente sea una matriz.
        grupos = pregunta.find_elements(
            By.XPATH,
            './/*[@role="group"]'
        )

        if len(grupos) > 1:
            return False

        cantidad = random.randint(
            1,
            len(checkboxes)
        )

        seleccionadas = random.sample(
            checkboxes,
            cantidad
        )

        print(
            f"   ☑️ Casillas: "
            f"{cantidad} seleccionada(s)"
        )

        for checkbox in seleccionadas:

            click_con_js(
                driver,
                checkbox
            )

            esperar(0.1)

        return True

    except Exception as e:

        print(
            f"❌ Error procesando checkboxes: {e}"
        )

        traceback.print_exc()

        return False


# ============================================================
# RADIO NORMAL / ESCALA
# ============================================================

def procesar_radio(driver, pregunta):
    """
    Procesa una pregunta normal de opción múltiple
    o una escala lineal.
    """

    try:

        radios = pregunta.find_elements(
            By.XPATH,
            './/*[@role="radio"]'
        )

        if not radios:
            return False

        # Si existen varios radiogroups,
        # no debemos tratarlo como radio normal.
        grupos = pregunta.find_elements(
            By.XPATH,
            './/*[@role="radiogroup"]'
        )

        if len(grupos) > 1:
            return False

        radio = random.choice(radios)

        click_con_js(
            driver,
            radio
        )

        print(
            "   🔘 Opción de radio seleccionada"
        )

        esperar(0.2)

        return True

    except Exception as e:

        print(
            f"❌ Error procesando radio: {e}"
        )

        traceback.print_exc()

        return False


# ============================================================
# TEXTAREA
# ============================================================

def procesar_textarea(
    driver,
    pregunta,
    config
):

    try:

        textareas = pregunta.find_elements(
            By.TAG_NAME,
            "textarea"
        )

        if not textareas:
            return False

        texto_pregunta = obtener_texto_pregunta(
            pregunta
        )

        texto = obtener_texto_config(
            texto_pregunta,
            config.textosLargosConfig,
            "Sin comentarios"
        )

        textareas[0].click()

        textareas[0].send_keys(
            texto
        )

        print(
            f"   📝 Párrafo: {texto}"
        )

        esperar(0.2)

        return True

    except Exception as e:

        print(
            f"❌ Error procesando textarea: {e}"
        )

        traceback.print_exc()

        return False


# ============================================================
# TEXTO CORTO
# ============================================================

def procesar_texto_corto(
    driver,
    pregunta,
    config
):

    try:

        inputs = pregunta.find_elements(
            By.XPATH,
            './/input'
        )

        validos = []

        for inp in inputs:

            try:

                tipo = (
                    inp.get_attribute("type")
                    or "text"
                ).lower()

                if tipo in [
                    "hidden",
                    "checkbox",
                    "radio"
                ]:
                    continue

                if not inp.is_displayed():
                    continue

                validos.append(inp)

            except:
                pass

        if not validos:
            return False

        texto_pregunta = obtener_texto_pregunta(
            pregunta
        )

        texto = obtener_texto_config(
            texto_pregunta,
            config.textosCortosConfig,
            "Respuesta predeterminada"
        )

        escribir_input(
            validos[0],
            texto
        )

        print(
            f"   ✏️ Texto: {texto}"
        )

        esperar(0.2)

        return True

    except Exception as e:

        print(
            f"❌ Error procesando texto: {e}"
        )

        traceback.print_exc()

        return False


# ============================================================
# PROCESAR UNA PREGUNTA
# ============================================================

def procesar_pregunta(
    driver,
    pregunta,
    config
):

    texto_pregunta = (
        obtener_texto_pregunta(
            pregunta
        )
    )

    print()
    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        f"❓ Pregunta: "
        f"{texto_pregunta or '[sin título]'}"
    )

    # ========================================================
    # FECHA
    # ========================================================

    if (
        "fecha" in texto_pregunta
        or "date" in texto_pregunta
        or "día" in texto_pregunta
        or "dia" in texto_pregunta
    ):

        print(
            "   🟢 Tipo detectado: FECHA"
        )

        if procesar_fecha(
            driver,
            pregunta
        ):

            return True

    # ========================================================
    # HORA
    # ========================================================

    if (
        "hora" in texto_pregunta
        or "time" in texto_pregunta
    ):

        print(
            "   🟢 Tipo detectado: HORA"
        )

        if procesar_hora(
            driver,
            pregunta
        ):

            return True

    # ========================================================
    # DROPDOWN
    # ========================================================

    if procesar_dropdown(
        driver,
        pregunta
    ):

        return True

    # ========================================================
    # MATRIZ RADIO
    # ========================================================

    if procesar_matriz_radio(
        driver,
        pregunta
    ):

        return True

    # ========================================================
    # MATRIZ CHECKBOX
    # ========================================================

    if procesar_matriz_checkbox(
        driver,
        pregunta
    ):

        return True

    # ========================================================
    # CHECKBOX NORMAL
    # ========================================================

    if procesar_checkboxes(
        driver,
        pregunta
    ):

        return True

    # ========================================================
    # RADIO NORMAL
    # ========================================================

    if procesar_radio(
        driver,
        pregunta
    ):

        return True

    # ========================================================
    # TEXTAREA
    # ========================================================

    if procesar_textarea(
        driver,
        pregunta,
        config
    ):

        return True

    # ========================================================
    # TEXTO CORTO
    # ========================================================

    if procesar_texto_corto(
        driver,
        pregunta,
        config
    ):

        return True

    print(
        "⚠️ No se pudo determinar "
        "el tipo de pregunta."
    )

    return False

# ============================================================
# LLENAR FORMULARIO
# ============================================================

def llenar_formulario_inteligente(
    driver,
    wait,
    config
):

    print()
    print(
        "🚀 Iniciando procesamiento del formulario..."
    )

    esperar(2)

    procesadas = 0
    no_procesadas = 0

    while True:

        esperar(0.5)

        # ----------------------------------------------------
        # Buscar preguntas actuales
        # ----------------------------------------------------

        preguntas = driver.find_elements(
            By.XPATH,
            '//div[@role="listitem"]'
        )

        print(
            f"🔎 Preguntas encontradas: "
            f"{len(preguntas)}"
        )

        # ----------------------------------------------------
        # Procesar preguntas
        # ----------------------------------------------------

        for pregunta in preguntas:

            try:

                resultado = procesar_pregunta(
                    driver,
                    pregunta,
                    config
                )

                if resultado:
                    procesadas += 1
                else:
                    no_procesadas += 1

            except Exception as e:

                no_procesadas += 1

                print(
                    f"❌ Error general en pregunta: "
                    f"{e}"
                )

                traceback.print_exc()

        # ----------------------------------------------------
        # BOTÓN SIGUIENTE
        # ----------------------------------------------------

        botones_siguiente = driver.find_elements(
            By.XPATH,
            '//div[@role="button"]'
            '[.//span[normalize-space()="Siguiente" '
            'or normalize-space()="Next"]]'
        )

        botones_siguiente_visibles = [
            b for b in botones_siguiente
            if b.is_displayed()
        ]

        if botones_siguiente_visibles:

            print()
            print(
                "➡️ Pasando a la siguiente página..."
            )

            click_con_js(
                driver,
                botones_siguiente_visibles[0]
            )

            esperar(1.5)

            continue

        # ----------------------------------------------------
        # BOTÓN ENVIAR
        # ----------------------------------------------------

        botones_enviar = driver.find_elements(
            By.XPATH,
            '//div[@role="button"]'
            '[.//span[normalize-space()="Enviar" '
            'or normalize-space()="Submit"]]'
        )

        botones_enviar_visibles = [
            b for b in botones_enviar
            if b.is_displayed()
        ]

        if botones_enviar_visibles:

            print()
            print(
                "📤 Enviando formulario..."
            )

            click_con_js(
                driver,
                botones_enviar_visibles[0]
            )

            esperar(2)

            break

        # ----------------------------------------------------
        # NO HAY BOTONES
        # ----------------------------------------------------

        print(
            "⚠️ No se encontró botón "
            "Siguiente ni Enviar."
        )

        break

    print()
    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        f"✓ Preguntas procesadas: "
        f"{procesadas}"
    )

    print(
        f"⚠️ Preguntas no procesadas: "
        f"{no_procesadas}"
    )

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    return True


# ============================================================
# ENDPOINT
# ============================================================

@app.post("/ejecutar-bot")
def ejecutar_bot(config: FormConfig):

    driver = None

    try:

        # ----------------------------------------------------
        # CONFIGURAR EDGE
        # ----------------------------------------------------

        options = Options()

        options.add_argument(
            "--headless=new"
        )

        options.add_argument(
            "--disable-gpu"
        )

        options.add_argument(
            "--no-sandbox"
        )

        options.add_argument(
            "--disable-dev-shm-usage"
        )

        options.add_argument(
            "--window-size=1920,1080"
        )

        options.add_argument(
            "--disable-notifications"
        )

        options.add_argument(
            "--disable-popup-blocking"
        )

        # ----------------------------------------------------
        # DRIVER
        # ----------------------------------------------------

        print(
            "🌐 Iniciando Microsoft Edge..."
        )

        service = Service(
            EdgeChromiumDriverManager().install()
        )

        driver = webdriver.Edge(
            service=service,
            options=options
        )

        wait = WebDriverWait(
            driver,
            15
        )

        # ----------------------------------------------------
        # ITERACIONES
        # ----------------------------------------------------

        exitos = 0

        for i in range(
            config.iteraciones
        ):

            print()
            print(
                "=========================================="
            )

            print(
                f"🔄 ENVÍO "
                f"{i + 1} / "
                f"{config.iteraciones}"
            )

            print(
                "=========================================="
            )

            # ------------------------------------------------
            # Abrir formulario
            # ------------------------------------------------

            driver.get(
                config.url
            )

            esperar(2)

            print(
                f"🌐 URL actual: "
                f"{driver.current_url}"
            )

            # ------------------------------------------------
            # LOGIN
            # ------------------------------------------------

            if config.requiereLoginGoogle:

                print(
                    "🔐 El formulario requiere "
                    "inicio de sesión Google."
                )

                print(
                    "⚠️ El login debe estar "
                    "previamente disponible "
                    "en la sesión del navegador."
                )

            # ------------------------------------------------
            # LLENAR FORMULARIO
            # ------------------------------------------------

            llenar_formulario_inteligente(
                driver,
                wait,
                config
            )

            # ------------------------------------------------
            # Comprobar que el navegador
            # no haya lanzado un error.
            # ------------------------------------------------

            esperar(1)

            print(
                f"📍 URL después del envío: "
                f"{driver.current_url}"
            )

            exitos += 1

            esperar(1)

        # ----------------------------------------------------
        # CERRAR
        # ----------------------------------------------------

        driver.quit()

        print()
        print(
            "=========================================="
        )

        print(
            f"✅ FINALIZADO: "
            f"{exitos} / "
            f"{config.iteraciones}"
        )

        print(
            "=========================================="
        )

        return {
            "status": "success",
            "message": (
                f"Se procesaron "
                f"{exitos} de "
                f"{config.iteraciones} "
                f"iteraciones."
            )
        }

    except Exception as e:

        print()
        print(
            "❌ ERROR DETALLADO EN EL BACKEND"
        )

        traceback.print_exc()

        if driver:

            try:
                driver.quit()
            except:
                pass

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )