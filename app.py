"""
Aplicación web basada en Flask que utiliza el modelo 'gemini-1.5-flash' de Google Gemini para generar respuestas
a partir de entradas del usuario. La aplicación almacena el historial de conversaciones y utiliza Markdown
para formatear las respuestas generadas.

Requisitos:
- Flask y Flask-Session instalados.
- Paquete `google.generativeai` instalado.
- Configurar la variable de entorno `GEMINI_API_KEY` con la clave de acceso a la API de Gemini.

Características:
1. Muestra una página inicial donde el usuario puede interactuar con el modelo.
2. Permite gestionar un historial limitado de interacciones entre usuario y modelo.
3. Formatea las respuestas en Markdown antes de mostrarlas.
"""

import os

import google.generativeai as genai
import markdown
import requests
from flask import Flask, request, render_template, session

from flask_session import Session

# Configuración de la aplicación Flask
app = Flask(__name__)

# Configuración de sesiones
app.secret_key = "clave_secreta_para_sesiones"  # Cambia esto en producción
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuración del modelo Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# Constante para limitar el historial de interacciones
MAX_HISTORY = 4


@app.route("/")
def home():
    """
    Ruta principal de la aplicación. Muestra la interfaz inicial y el historial de interacciones previas,
    si existe alguno.
    """
    if "history" not in session:
        session["history"] = []  # Inicializar el historial si no está presente
    return render_template("index.html", history=session["history"])


@app.route("/predict", methods=["POST"])
def predict():
    """
    Procesa la entrada del usuario, genera una respuesta utilizando el modelo Gemini,
    y actualiza el historial con la interacción actual.

    Returns:
        str: Renderiza la página principal con la nueva respuesta y el historial actualizado.
    """
    # Obtener el texto ingresado por el usuario
    prompt = request.form.get("prompt")

    if not prompt:
        # Manejar el caso de entrada vacía
        return render_template("index.html", error="Por favor, ingresa un texto válido.")

    # Construir el contexto con el historial de interacciones
    history = session.get("history", [])
    context = ""
    for item in history[-MAX_HISTORY:]:
        context += f"Usuario: {item['prompt']}\nModelo: {item['response_raw']}\n"
    context += f"Usuario: {prompt}\n"

    try:
        # Generar la respuesta utilizando el modelo
        response = model.generate_content(context).text

        # Formatear la respuesta en HTML utilizando Markdown
        output_html = markdown.markdown(response)

        # Actualizar el historial con la interacción actual
        history.append({
            "prompt": prompt,
            "response_raw": response,
            "response_html": output_html
        })
        session["history"] = history

        # Renderizar la página con la nueva respuesta
        return render_template("index.html", prompt=prompt, response_html=output_html, history=history)

    except requests.exceptions.RequestException as e:
        # Manejar errores de conexión o solicitudes
        return render_template("index.html", error=f"Error al conectarse a Gemini: {e}")


if __name__ == "__main__":
    app.run(debug=True)
