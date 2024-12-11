from flask import Flask, request, jsonify
import os
import json 

app = Flask(__name__)

@app.route('/start-recording', methods=['POST'])
def start_recording():
    data = request.get_json()
    enventId = data.get("eventId") 
    link = data.get("link")
    summary = data.get("summary")
    participants = data.get("participants", [])
    time = data.get("time")

    if not link or not enventId or not participants or not time or not summary:
        return jsonify({"error": "Falta datos de la videollamada"}), 400

    participants_json = json.dumps(participants)
    # Ejecutar el script gmeet.py con los parámetros recibidos
    os.system(f'python3 gmeet.py "{link}" "{enventId}" "{summary}" \'{participants_json}\' "{time}"')
    
    return jsonify({"message": "Recording started"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)