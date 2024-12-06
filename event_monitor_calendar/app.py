import time
import requests
from datetime import datetime, timedelta
import pytz  # Para manejar zonas horarias
import firebase_admin
from firebase_admin import credentials, firestore
from dateutil import parser  # Para manejar el formato de tiempo en los eventos

# Configura las credenciales de Firebase
cred = credentials.Certificate("/app/files/serviceAccountKey.json") 
firebase_admin.initialize_app(cred)
db = firestore.client()

# Configura la URL de la API
API_URL = "http://localhost:5000/start-recording"  

# Define la zona horaria local
local_tz = pytz.timezone("America/Santiago")

def fetch_upcoming_events(hours_ahead=24):
    """Consulta Firebase para recuperar reuniones programadas en las próximas horas."""
    now = datetime.now(local_tz)
    future_time = now + timedelta(hours=hours_ahead)

    year = now.year
    month = now.month

    events = []

    # Referencia a la colección del año y mes actuales
    year_ref = db.collection("videocalls").document(str(year))
    month_ref = year_ref.collection(str(month).zfill(2))  # Aseguramos formato de dos dígitos para el mes

    # Consulta documentos dentro del mes
    docs = month_ref.stream()
    for doc in docs:
        event = doc.to_dict()
        event_time = parser.isoparse(event.get("time"))  # Convierte el tiempo a datetime
        if now <= event_time <= future_time:
            event["id"] = doc.id  # Incluye el ID del documento
            events.append(event)

    return events

def send_event_to_api(event):
    """Envía los datos del evento a la API."""
    payload = {
        "link": event.get("link", ""),
        "eventId": event["id"],  # ID del evento
        "participants": ["javierignacio.nunez@gmail.com","emma.ariasbustamante@gmail.com"],
        # "participants": event.get("participants", []),  # Lista de participantes
        "summary": event.get("summary", ""),
        "time": event["time"]  # Hora del evento
  # Resumen del evento
    }
    print(payload)
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        print(f"Evento enviado con éxito: {payload}")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar evento: {e}")

def monitor_events(events):
    """Monitorea eventos cargados y envía notificaciones a la API si están por comenzar."""
    now = datetime.now(local_tz)
    for event in events[:]:  # Iteramos sobre una copia para modificar la lista original
        event_time = parser.isoparse(event["time"])
        # Si el evento comienza en los próximos 10 minutos, envíalo y elimínalo de la lista
        if now <= event_time <= now + timedelta(minutes=10):
            send_event_to_api(event)
            events.remove(event)  # Remover evento procesado para evitar duplicados

def main():
    """Bucle principal que consulta Firebase y monitorea reuniones."""
    events = fetch_upcoming_events()
    print(f"Inicialmente cargados {len(events)} eventos.")
    for event in events:
        print(event)

    while True:
        monitor_events(events)  # Monitorea eventos cargados en memoria
        now = datetime.now(local_tz)
        
        # Cada 30 minutos, actualizamos la lista de eventos (ajusta según tu preferencia)
        if now.minute % 30 == 0:
            print("Actualizando lista de eventos...")
            events = fetch_upcoming_events()
            print(f"Se han cargado {len(events)} eventos actualizados.")
        
        time.sleep(60)  # Monitorea cada minuto

if __name__ == "__main__":
    main()
