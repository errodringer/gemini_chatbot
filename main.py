"""
Este script utiliza la API de Google Gemini para generar contenido basado en un modelo de IA generativa.
El modelo seleccionado es 'gemini-1.5-flash', y la clave de API debe configurarse como una variable de entorno.

Requisitos:
- Instalar el paquete `google.generativeai`.
- Configurar la variable de entorno `GEMINI_API_KEY` con la clave de acceso a la API de Gemini.

Salida:
Imprime en consola el texto generado por el modelo en respuesta a la consulta proporcionada.
"""

import os

import google.generativeai as genai

# Configurar la API utilizando la clave proporcionada en la variable de entorno.
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Opciones de modelos disponibles: 'gemini-1.5-pro' y 'gemini-1.5-flash'.
# Aquí seleccionamos el modelo 'gemini-1.5-flash' por su velocidad.
model = genai.GenerativeModel("gemini-1.5-flash")

# Generar contenido utilizando el modelo. El prompt de entrada es una consulta simple.
response = model.generate_content("Hola, ¿cuánto es 1+1?")

# Imprimir el texto generado por el modelo.
print(response.text)
