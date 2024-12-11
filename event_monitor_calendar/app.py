from flask import Flask, request, jsonify
import firebase_admin
import datetime as dt
from firebase_admin import credentials, firestore
import requests

app = Flask(__name__)

# Inicializar Firebase
cred = credentials.Certificate("/app/files/serviceAccountKey.json")
# cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Endpoint del servicio de grabación
RECORDING_SERVICE_ENDPOINT = "http://meet-bot:5000/start-recording"

@app.route('/')
def home():
    return '<h1>Contenedor Activo ✌️</h1>'

@app.route('/event', methods=['POST'])
def handle_event():
    
    try:
        # Recuperar el eventId del request
        data = request.json
        event_id = data.get('eventId')

        if not event_id:
            return jsonify({"error": "El eventId es obligatorio"}), 400
        print(event_id)
        # buscar los metadatos del evento en Firebase
        event_metadata = get_event_metadata(event_id)

        if not event_metadata:
            return jsonify({"error": f"Evento con ID {event_id} no encontrado"}), 404

        # Enviar los metadatos al servicio de grabación
        send_to_recording_service(event_metadata)

        return jsonify({"status": "success", "message": "Evento procesado correctamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_event_metadata(event_id):
    """Recupera los metadatos del evento desde Firebase y los estructura."""
    # Construir la referencia al documento en Firebase
    now = dt.datetime.now()
    year = str(now.year)
    month = str(now.month).zfill(2)

    doc_ref = db.collection("videocalls").document(year).collection(month).document(event_id)
    doc = doc_ref.get()

    if doc.exists:
        # estructurar los datos en el formato especificado
        event = doc.to_dict()
        payload = {
            "link": event.get("link", ""),
            "eventId": event_id,  # ID del evento
            "participants": event.get("participants") or ["user@user.com", "user2@user.com"],
            "summary": event.get("summary", ""),
            "time": event.get("time")  # Hora del evento
        }
        print(payload)
        return payload
    return None


def send_to_recording_service(metadata):
    """Envía los metadatos al servicio de grabación."""
    try:
        response = requests.post(RECORDING_SERVICE_ENDPOINT, json=metadata)
        response.raise_for_status()
        print(f"Metadatos enviados al servicio de grabación: {metadata}")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar los metadatos al servicio de grabación: {e}")
        raise


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
