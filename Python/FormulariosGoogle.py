
import random
import time
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# --- FUNCIONES DE AUTOMATIZACIÓN ---
def click_con_js(driver, element):
    """Ejecuta un clic directo en el DOM saltando validaciones de superposición."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", element)
    time.sleep(0.5)

def responder_pagina(driver):
    """Detecta todos los grupos de opciones (combobox/radios) y selecciona uno aleatorio."""
    time.sleep(1.5)  # Breve pausa para asegurar que el DOM cargue
    preguntas = driver.find_elements(By.XPATH, '//div[@role="radiogroup"]')
    
    for pregunta in preguntas:
        opciones = pregunta.find_elements(By.XPATH, './/div[@role="radio"]')
        if opciones:
            eleccion = random.choice(opciones)
            click_con_js(driver, eleccion)

# --- FUNCIÓN PRINCIPAL DE SELENIUM ---
def iniciar_automatizacion(form_url, num_formularios):
    opciones_edge = Options()
    opciones_edge.add_experimental_option("detach", True)
    
    try:
        driver = webdriver.Edge(options=opciones_edge)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar Edge. Asegúrate de tenerlo instalado.\n{e}")
        return

    try:
        for i in range(num_formularios):
            print(f"Iniciando llenado del formulario {i + 1} de {num_formularios}...")
            driver.get(form_url)
            time.sleep(2)

            while True:
                # Seleccionar respuestas aleatorias
                responder_pagina(driver)

                # Buscar botones de navegación
                btn_siguiente = driver.find_elements(By.XPATH, '//div[@role="button"]//span[text()="Siguiente"]')
                btn_enviar = driver.find_elements(By.XPATH, '//div[@role="button"]//span[text()="Enviar"]')

                if btn_siguiente:
                    click_con_js(driver, btn_siguiente[0])
                elif btn_enviar:
                    click_con_js(driver, btn_enviar[0])
                    print(f"✅ Formulario {i + 1} completado y enviado.")
                    break
                else:
                    print("⚠️ No se encontró botón de Siguiente ni Enviar.")
                    break
                    
            time.sleep(3)  # Pausa antes del siguiente
            
        messagebox.showinfo("Proceso Terminado", f"Se han enviado con éxito {num_formularios} formularios.")
        
    except Exception as e:
        messagebox.showerror("Error de Ejecución", f"Ocurrió un error:\n{e}")
    finally:
        print("Finalizado.")

# --- INTERFAZ GRÁFICA (TKINTER) ---
def procesar_datos():
    url = entry_url.get().strip()
    cantidad_txt = entry_cantidad.get().strip()
    
    if not url:
        messagebox.showwarning("Datos incompletos", "Por favor ingresa el link del formulario.")
        return
        
    if not cantidad_txt.isdigit() or int(cantidad_txt) <= 0:
        messagebox.showwarning("Datos inválidos", "La cantidad debe ser un número entero mayor a 0.")
        return
        
    cantidad = int(cantidad_txt)
    
    # Ocultar la ventana de configuración mientras trabaja
    ventana.withdraw()
    
    # Ejecutar el bot de Selenium
    iniciar_automatizacion(url, cantidad)
    
    # Cerrar el programa al terminar
    ventana.destroy()

# Configuración de la ventana principal
ventana = tk.Tk()
ventana.title("AutoLlenado de Formularios")
ventana.geometry("500x250")
ventana.resizable(False, False)

# Etiqueta y campo para el URL
tk.Label(ventana, text="Link del Formulario de Google:", font=("Arial", 10, "bold")).pack(pady=(20, 5))
entry_url = tk.Entry(ventana, width=65)
entry_url.pack(pady=5)

# Etiqueta y campo para la cantidad
tk.Label(ventana, text="¿Cuántos formularios deseas enviar?:", font=("Arial", 10, "bold")).pack(pady=(15, 5))
entry_cantidad = tk.Entry(ventana, width=10, justify="center")
entry_cantidad.insert(0, "5")  # Valor por defecto
entry_cantidad.pack(pady=5)

# Botón de inicio
btn_iniciar = tk.Button(ventana, text="Iniciar Automatización", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=procesar_datos)
btn_iniciar.pack(pady=20)

# Mantener la ventana abierta
ventana.mainloop()