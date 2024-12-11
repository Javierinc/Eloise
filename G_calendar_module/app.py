import datetime as dt
import os.path
import time 
import requests
import threading
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timezone

FILES_PATH = "/app/files"

SERVICE_MONITOR_ENDPOINT = "http://calendar-monitor:3000/event"

SERVICE_ACCOUNT_FILE = os.path.join(FILES_PATH, "serviceAccountKey.json")
CREDENTIALS_FILE = os.path.join(FILES_PATH, "credentials.json")
TOKEN_FILE = os.path.join(FILES_PATH, "token.json")
# SERVICE_ACCOUNT_FILE = "serviceAccountKey.json"
# CREDENTIALS_FILE = "credentials.json"
# TOKEN_FILE = "token.json"

cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
firebase_admin.initialize_app(cred)
db = firestore.client()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Función para guardar nuevas reuniones o actualizar reuniones en Firestore
def save_or_update_meeting(event_id, summary, time, participants, link):
    date = dt.datetime.fromisoformat(time)
    year = str(date.year)
    month = str(date.month).zfill(2)

    meeting_data = {
        "evendId": event_id,
        "summary": summary,
        "time": time,
        "participants": participants,
        "link": link,
    }

    doc_ref = db.collection("videocalls").document(year).collection(month).document(event_id)

    try:
        existing_doc = doc_ref.get()
        if existing_doc.exists:
            existing_data = existing_doc.to_dict()

            if not link:
                doc_ref.delete()
                print(f"Reunión con eventId {event_id} eliminada debido a la falta de enlace de Meet.")
                return

            if (
                existing_data.get("time") != time
                or existing_data.get("summary") != summary
                or existing_data.get("participants") != participants
                or existing_data.get("link") != link
            ):
                doc_ref.update(meeting_data)
                print(f"Reunión con eventId {event_id} actualizada en Firestore.")
            else:
                print(f"La reunión con eventId {event_id} ya está actualizada.")
        else:
            if link:
                doc_ref.set(meeting_data)
                print(f"Reunión con eventId {event_id} guardada en Firestore.")
    except Exception as e:
        print(f"Error al guardar o actualizar la reunión: {e}")

# Función que elimina de Firestore reuniones que no existen en el calendario
def remove_nonexistent_meetings(event_ids, year, month):
    meetings_ref = db.collection("videocalls").document(year).collection(month)
    try:
        stored_meetings = {doc.id: doc.to_dict() for doc in meetings_ref.stream()}
        for stored_event_id in stored_meetings.keys():
            if stored_event_id not in event_ids:
                meetings_ref.document(stored_event_id).delete()
                print(f"Reunión con eventId {stored_event_id} eliminada de Firestore (ya no estaba en el calendario).")
    except Exception as e:
        print(f"Error al eliminar reuniones no existentes: {e}")

#Función para notificar al módulo monitor calendario
def notify_monitor(event_id, retries=3, delay=5):
    payload = {"eventId": event_id}
    for attempt in range(retries):
        try:
            response = requests.post(SERVICE_MONITOR_ENDPOINT, json=payload)
            response.raise_for_status()
            logging.info(f"Notificación enviada para eventId {event_id}")
            return
        except requests.exceptions.RequestException as e:
            logging.error(f"Error al notificar al servicio monitor: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logging.error(f"No se pudo notificar al monitor despues de {retries} intentos")




# Función principal para conectar con el calendario
def sync_calendar():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        now = dt.datetime.now().isoformat() + "Z"

        event_result = service.events().list(calendarId="primary", timeMin=now, maxResults=10, singleEvents=True, orderBy="startTime").execute()
        events = event_result.get("items", [])

        if not events:
            print("No se encontraron eventos próximos")
            return

        year = str(datetime.now(timezone.utc).year)
        month = str(datetime.now(timezone.utc).month).zfill(2)

        event_ids = set()

        for event in events:
            if "conferenceData" in event:
                conference = event["conferenceData"].get("entryPoints", [])
                for entry in conference:
                    if entry.get("entryPointType") == "video":
                        start = event["start"].get("dateTime", event["start"].get("date"))
                        # event_time = dt.datetime.fromisoformat(start).strftime("%Y-%m-%d %H:%M:%S")
                
                        start_datetime = dt.datetime.fromisoformat(start)
                        

                        start_datetime_naive = start_datetime.replace(tzinfo=None)
                        nw = dt.datetime.now()
                        now_naive = nw.replace(tzinfo=None)


                        attendees = event.get("attendees", [])
                        participants = [
                            {"email": attendee.get("email"), "status": attendee.get("responseStatus")}
                            for attendee in attendees
                        ]

                        event_id = event["id"]
                        summary = event["summary"]
                        link = entry.get("uri")

                        event_ids.add(event_id)
                        save_or_update_meeting(event_id, summary, start, participants, link)

                        if now_naive <= start_datetime_naive <= now_naive + dt.timedelta(minutes=5):
                            notify_monitor(event_id)

        remove_nonexistent_meetings(event_ids, year, month)
        print("Sincronización completada con Firestore.")
    except HttpError as error:
        print(f"Ups ha ocurrido un error: {error}")

# Bucle principal para sincronizar cada 10 minutos
def main():
    while True:
        print(f"Iniciando sincronización: {datetime.now()}")
        sync_calendar()
        print(f"Sincronización completada. Esperando 1 minuto...")
        time.sleep(60)  # Espera de 1 minuto

if __name__ == "__main__":
    main()
