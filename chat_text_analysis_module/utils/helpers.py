from datetime import datetime as dt
import calendar
import locale
import os
import streamlit as st
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(model="gpt-4o", 
                 temperature=0, 
                 api_key= os.getenv("API_KEY_CHATGPT")
)

def fix_encoding(text):
    """
    Corrige problemas de codificación en el texto. 
    Intenta convertir el texto de latin1 a utf-8.

    Args:
        text (str): Texto a corregir.

    Returns:
        str: Texto corregido.
    """
    try:
        return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text  # Devuelve el texto original si falla


def format_iso_date(iso_date):
    """
    Convierte una fecha en formato ISO a "dd/mm/aaaa".

    Args:
        iso_date (str): Fecha en formato ISO.

    Returns:
        str: Fecha formateada en "dd/mm/aaaa".
    """
    try:
        date = dt.fromisoformat(iso_date)
        return date.strftime("%d/%m/%Y")
    except ValueError:
        return "Formato de fecha inválido"  # Mensaje de error si el formato es inválido


# Configurar la localización para nombres de meses en español
# locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')


def get_month_name(month_number):
    """
    Convierte un número de mes (1-12) al nombre en español.

    Args:
        month_number (int): Número del mes.

    Returns:
        str: Nombre del mes en español.
    """
    return calendar.month_name[month_number].capitalize()


def load_transcription(file_path):
    """
    Carga el contenido de un archivo de transcripción.

    Args:
        file_path (str): Ruta del archivo.

    Returns:
        str: Contenido del archivo o mensaje de error si no se puede leer.
    """
    try:
        print(f"Intentando leer el archivo desde el path: {file_path}")
        if not os.path.exists(file_path):
            return f"Error: El archivo {file_path} no se encuentra."
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"Archivo {file_path} no encontrado."
    except Exception as e:
        return f"Error al cargar la transcripción: {e}"


def generate_summary(transcription):
    """
    Genera un resumen de compromisos basado en la transcripción.

    Args:
        transcription (str): Texto de la transcripción.

    Returns:
        tuple: Resumen generado y el modelo LLM utilizado.
    """
    prompt_summary = (
        f"Resumen de compromisos:\n{transcription}\n\n"
        "Tu resumen debe tener la siguiente estructura: Titulo de reunión, fecha, Resumen general, "
        "Lista de compromisos (Tareas o compromisos, Responsables, Fechas limites, entre otros), "
        "Puntos abiertos (temas que quedaron pendientes para futuras reuniones o que requieren más análisis)."
    )
    summary = llm.invoke([("system", prompt_summary)]).content
    return summary, llm



