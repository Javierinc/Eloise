import datetime as dt
import os.path
import firebase_admin
from firebase_admin import credentials, firestore
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timezone

firebase_cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "serviceAccountKey.json")

cred = credentials.Certificate(firebase_cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

#Función para guardar nuevas reuniones o actualizar reuniones en Firestore
def save_or_update_meeting(event_id, summary, time, participants, link):
    #aquí se parsea la fecha para obtener el año y el mes
    date = dt.datetime.fromisoformat(time)
    year = str(date.year)
    month = str(date.month).zfill(2) 

    #Estos son los datos de la reunión que se guardaran eventualmente
    meeting_data = {
        "evendId": event_id,
        "summary": summary,
        "time": time,
        "participants": participants,
        "link": link
    }

    #Esta es la referencia al documento en firestore utilizando el event_id de la reunión como identificador
    doc_ref = db.collection("videocalls").document(year).collection(month).document(event_id)
    
    try:
        existing_doc = doc_ref.get()

        # Si la reunión ya existe, se verificar si hay cambios en ella
        if existing_doc.exists:
            existing_data = existing_doc.to_dict()

            # Elimina la reunión si ya no tiene enlace de Meet
            if not link:
                doc_ref.delete()
                print(f"Reunión con eventId {event_id} eliminada debido a la falta de enlace de Meet.")
                return

            # Detecta cambios en los datos de la reunión
            if (existing_data.get("time") != time or
                existing_data.get("summary") != summary or
                existing_data.get("participants") != participants or
                existing_data.get("link") != link):
                # Actualiza la reunión si hay cambios
                doc_ref.update(meeting_data)
                print(f"Reunión con eventId {event_id} actualizada en Firestore.")
            else:
                print(f"La reunión con eventId {event_id} ya está actualizada.")
        else:
            # Crea un nuevo documento si no existe
            if link:  # Solo guardar si hay enlace de Meet
                doc_ref.set(meeting_data)
                print(f"Reunión con eventId {event_id} guardada en Firestore.")
    except Exception as e:
        print(f"Error al guardar o actualizar la reunión: {e}")
 
#Función que elimina de firestore reuniones que no existen en el calendario
def remove_nonexistent_meetings(event_ids, year, month):
    meetings_ref = db.collection("videocalls").document(year).collection(month)

    try:
        #Obtiene todas las reuniones que están en Firestore
        stored_meetings = {doc.id: doc.to_dict() for doc in meetings_ref.stream()}

        #Elimina de Firestore las reuniones que no están en el calendario
        for stored_event_id in stored_meetings.keys():
            if stored_event_id not in event_ids:
                meetings_ref.document(stored_event_id).delete()
                print(f"Reunión con eventId {stored_event_id} eliminada de Firestore (ya no estaba en el calendario)")
    except Exception as e:
        print(f"Error al eliminar reuniones no existentes: {e}")


#Función principal encargada de sicronizar reuniones con Firestore
def main():
    creds = None
    credentials_path = os.getenv("GOOGLE_CREDENTIALS", "credentials.json")
    token_path = os.getenv("GOOGLE_TOKEN", "token.json")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
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
            if 'conferenceData' in event:
                conference = event['conferenceData'].get('entryPoints', [])
                for entry in conference:
                    if entry.get('entryPointType') == 'video':
                        start = event["start"].get("dateTime", event["start"].get("date"))
                        end = event["end"].get("dateTime", event["end"].get("date"))
                        event_time = dt.datetime.fromisoformat(start).strftime("%Y-%m-%d %H:%M:%S")
                        print(f"Evento {event["summary"]} inicia a las: {event_time} y termina a las {end}")
                        print(f"Google Meet URL: {entry.get('uri')}" )

                        start_time = dt.datetime.fromisoformat(start)
                        end_time = dt.datetime.fromisoformat(end)

                        duration = (end_time - start_time).total_seconds() / 60
                        print(f"La duración es de {duration}")
                        print("***************************")

                        attendees = event.get('attendees', [])
                        participants = []

                        if attendees:
                            print("Participantes de la videollamada")
                            for attendee in attendees:
                                email = attendee.get('email')
                                response_status = attendee.get('responseStatus')
                                print(f" - {email}: {response_status}")
                                participants.append({
                                    "email": email,
                                    "status": response_status
                                })
                        else:
                            print("no hay participantes listados")
                        
                        event_id = event['id']
                        summary = event['summary']
                        link = entry.get('uri')
                
                        event_ids.add(event_id)
                        save_or_update_meeting(event_id, summary, start, participants, link)
                    
        remove_nonexistent_meetings(event_ids, year, month)                
        print("todas las videollamadas fueron almacenadas en Firestore.")
                        

    except HttpError as error:
        print("Ups ha ocurrido un error: ", error)


if __name__ == "__main__":
    main()