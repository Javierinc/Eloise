import firebase_admin
from firebase_admin import credentials, firestore
from . import helpers
from collections import defaultdict
from datetime import datetime


if not firebase_admin._apps:
    cred = credentials.Certificate("/app/files/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()


def get_transcriptions_by_email(email):
    """
    Obtiene las transcripciones por correo electrónico
    """
    meetings_by_month = defaultdict(list)
    
    # Referencia a la colección principal
    transcriptions_ref = db.collection("transcriptions")
    
    # Referencia al documento "2024"
    year_ref = transcriptions_ref.document("2024")

    # Obtener las subcolecciones dentro del documento "2024" (los meses, como "11")
    months = year_ref.collections()
    # print("Meses encontrados:")
    for month_ref in months:
        # print(f"- Mes: {month_ref.id}")
        
        # Obtener los documentos dentro de cada mes
        documents = month_ref.stream()
        for doc in documents:
            data = doc.to_dict()
            # print(f"  Documento encontrado: {data}")
            
            # Verificar si el correo está en "participants"
            if email in data.get("participants", []):
                date = datetime.fromisoformat(data.get('time'))
                month_name = helpers.get_month_name(date.month)
                # print(f"  Correo encontrado en documento: {data.get('eventId')}")
                meetings_by_month[month_name].append({
                    "id": data.get("eventId"),
                    "name": f"{data.get('summary')} - {helpers.format_iso_date(data.get('time'))}",
                    "transcription_txt_path": data.get("transcript_txt_path")
                })

    # print("Transcripciones encontradas:", transcripciones)
    return dict(meetings_by_month)  # Transcripciones










# if not firebase_admin._apps:
#     cred = credentials.Certificate("utils/serviceAccountKey.json")
#     firebase_admin.initialize_app(cred)
# db = firestore.client()

# def obtener_transcripciones_por_correo(correo):

    
#     reuniones_por_mes = defaultdict(list)
    
#     # Referencia a la colección principal
#     transcriptions_ref = db.collection("transcriptions")
    
#     # Referencia al documento "2024"
#     años_ref = transcriptions_ref.document("2024")

#     # Obtener las subcolecciones dentro del documento "2024" (los meses, como "11")
#     meses = años_ref.collections()
#     # print("Meses encontrados:")
#     for mes_ref in meses:
#         # print(f"- Mes: {mes_ref.id}")
        
#         # Obtener los documentos dentro de cada mes
#         documentos = mes_ref.stream()
#         for doc in documentos:
#             data = doc.to_dict()
#             # print(f"  Documento encontrado: {data}")
            
#             # Verificar si el correo está en "participants"
#             if correo in data.get("participants", []):
#                 fecha = datetime.fromisoformat(data.get('time'))
#                 mes_nombre = helpers.obtener_nombre_mes(fecha.month)
#                 # print(f"  Correo encontrado en documento: {data.get('eventId')}")
#                 reuniones_por_mes[mes_nombre].append({
#                     "id": data.get("eventId"),
#                     "nombre": f"{data.get('summary')} - {helpers.formatear_fecha_iso(data.get('time'))}",
#                     "transcription_txt_path": data.get("transcript_txt_path")
#                 })

#     # print("Transcripciones encontradas:", transcripciones)
#     return dict(reuniones_por_mes) #transcripcione