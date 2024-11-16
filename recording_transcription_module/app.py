from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/start-recording', methods=['POST'])
def start_recording():
    data = request.get_json()
    link = data.get("link")
    duration = data.get("duration")

    if not link or not duration:
        return jsonify({"error": "Link or duration missing"}), 400

    # Ejecutar el script main.py con los parámetros recibidos
    os.system(f"python3 main.py {link} {duration}")
    
    return jsonify({"message": "Recording started"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)