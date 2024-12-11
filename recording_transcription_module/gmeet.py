import asyncio
import os
import signal
import subprocess
import click
import datetime as dt
import requests
import json
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

from time import sleep

import undetected_chromedriver as uc

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import firebase_admin
from firebase_admin import credentials, firestore



#Con sys se extraen los datos que llegan al endpoint de start record
meet_link = sys.argv[1]  # El primer argumento es el link de la reunion
event_id = sys.argv[2]  # El segundo argumento es el eventId de la reunión
summary = sys.argv[3] # El tercer argumento es el summary de la reunión
participants_json = sys.argv[4] #el cuarto argumento son los participantes de la reunión
time_meet = sys.argv[5] #es la fecha de la reunión

#Path del volumen que guarda las transcripciones en un txt
volumen_path = "/app/transcription_storage"
FILES_PATH = "/app/files"

SERVICE_ACCOUNT_FILE = os.path.join(FILES_PATH, "serviceAccountKey.json")
#Variables de entorno
USER_GMAIL = os.getenv("USER_GMAIL")
USER_PASSWORD = os.getenv("USER_GMAIL_PASSWORD")
GLADIA_API_KEY = os.getenv("GLADIA_API_KEY")





try:
    participants  = json.loads(participants_json)
except json.JSONDecodeError:
    print("Error: El argumento de participantes no es un JSON válido.")
    participants = []

print(f"Link: {meet_link}")
print(f"eventId: {event_id}")
print(f"summary: {summary}")
print(f"time: {time_meet}")
if participants:
    for participant in participants:
        print(f"participante: {participant}")
else:
    print("no hay participantes en la reunión")

#Iniciar firebase
cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
firebase_admin.initialize_app(cred)
db = firestore.client()

#Función para guardar la transcripción en una colección en firebase
def save_meeting(event_id, summary, time, participants, file_path):
    #Aquí se parsea la fecha para obtener el año y el mes
    date = dt.datetime.fromisoformat(time)
    year = str(date.year)
    month = str(date.month).zfill(2) 

    # Estructura del documento
    transcript_meeting = {
        "eventId": event_id,
        "summary": summary,
        "time": time,
        "participants": participants,
        "transcript_txt_path": file_path
    }

    # Referencia a la subcolección del año y mes
    doc_ref = db.collection("transcriptions").document(str(year)).collection(str(month)).document(event_id)
     # Guardar el documento
    doc_ref.set(transcript_meeting)
    print(f"Transcripción guardada en: transcriptions/{year}/{month}/{event_id}")

#Función que realiza una solicitud HTTP a la URL que se esfecifica en los parámetros
def make_request(url, headers, method="GET", data=None, files=None):
    if method == "POST":
        response = requests.post(url, headers=headers, json=data, files=files)
    else:
        response = requests.get(url, headers=headers)
    return response.json()

#Ejecuta un comando del sistema de forma asincrona con asyncio
async def run_command_async(command):
    #Inicia un proceso shell para ejecutar el comando especificado
    process = await asyncio.create_subprocess_shell(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    #Se captura la salida estandar y los errores del comoando
    try:
        stdout, stderr = await process.communicate()
        print("FFmpeg Output: ",stdout.decode())
        print("FFmpeg error: ", stderr.decode())
        return stdout, stderr
    except asyncio.CancelledError:
        # process.terminate()
        process.send_signal(signal.SIGTERM)
        await process.wait()
        print("Grabación finalizada exitosamente :)")
        raise
    finally:
        process.terminate()
        await process.wait()

async def google_sign_in(email, password, driver):
    # Abre la página de inicio de sesión de google
    driver.get("https://accounts.google.com")

    sleep(1)
    # Buscar el input del correo e ingresar el correo
    email_field = driver.find_element(By.NAME, "identifier")
    email_field.send_keys(email)
    # guarda un pantallazo
    driver.save_screenshot("screenshots/email.png")

    # click en el botón siguiente
    # next_button = driver.find_element_by_id("identifierNext")
    sleep(2)

    driver.find_element(By.ID, "identifierNext").click()

    # espera por un momento a que la pagina siguiente cargue
    sleep(3)

    # guarda pantallazo
    driver.save_screenshot("screenshots/password.png")

    # Encontrar el input de la contraseña e ingresarla
    password_field = driver.find_element(By.NAME, "Passwd")
    password_field.click()
    password_field.send_keys(password)

    # Enter y enviar el formulario 
    password_field.send_keys(Keys.RETURN)

    # espera a que el proceso de login se complete 
    sleep(5)
    # pantallazo
    driver.save_screenshot("screenshots/inicio_sesion.png")


async def join_meet():

    print(f"comienza la grabación de {meet_link}")

    # Se elimina la carpeta screenshot
    print("Limpiando los screenshots anteriores")
    if os.path.exists("screenshots"):
        for f in os.listdir("screenshots"):
            os.remove(f"screenshots/{f}")
    else:
        os.mkdir("screenshots")

    print("comenzando con los drivers de audio virtual")
    # find audio source for specified browser
    subprocess.check_output(
        "sudo rm -rf /var/run/pulse /var/lib/pulse /root/.config/pulse", shell=True
    )
    subprocess.check_output(
        "sudo pulseaudio -D --verbose --exit-idle-time=-1 --system --disallow-exit  >> /dev/null 2>&1",
        shell=True,
    )
    subprocess.check_output(
        'sudo pactl load-module module-null-sink sink_name=DummyOutput sink_properties=device.description="Virtual_Dummy_Output"',
        shell=True,
    )
    subprocess.check_output(
        'sudo pactl load-module module-null-sink sink_name=MicOutput sink_properties=device.description="Virtual_Microphone_Output"',
        shell=True,
    )
    subprocess.check_output(
        "sudo pactl set-default-source MicOutput.monitor", shell=True
    )
    subprocess.check_output("sudo pactl set-default-sink MicOutput", shell=True)
    subprocess.check_output(
        "sudo pactl load-module module-virtual-source source_name=VirtualMic",
        shell=True,
    )

    options = uc.ChromeOptions()

    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-setuid-sandbox")
    # options.add_argument('--headless=new')
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    log_path = "chromedriver.log"

    driver = uc.Chrome(service_log_path=log_path, use_subprocess=False, options=options)

    driver.set_window_size(1920, 1080)

    email = USER_GMAIL
    password = USER_PASSWORD
    gladia_api_key = GLADIA_API_KEY


    if email == "" or password == "":
        print("No email or password specified")
        return

    print("Iniciando sesión en Google")
    await google_sign_in(email, password, driver)

    driver.get(meet_link)

    driver.execute_cdp_cmd(
        "Browser.grantPermissions",
        {
            "origin": meet_link,
            "permissions": [
                "geolocation",
                "audioCapture",
                "displayCapture",
                "videoCapture",
                "videoCapturePanTiltZoom",
            ],
        },
    )

    print("screenshot")
    driver.save_screenshot("screenshots/initial.png")
    print("Inicio listo")

    try:
        driver.find_element(
            By.XPATH,
            "/html/body/div/div[3]/div[2]/div/div/div/div/div[2]/div/div[1]/button",
        ).click()
        sleep(2)
    except:
        print("No popup")

    # disable microphone
    print("Deshabilitando micrófono")

    sleep(10)
    missing_mic = False

    try:
        print("Tratando de deshabilitar micrófono")
        driver.find_element(By.CLASS_NAME, "VfPpkd-vQzf8d").find_element(By.XPATH, "..")
        sleep(2)
        # take screenshot

        driver.save_screenshot("screenshots/missing_mic.png")

        # save the webpage source html
        with open("screenshots/webpage.html", "w") as f:
            f.write(driver.page_source)

        missing_mic = True
    except:
        pass

    try:
        print("Micrófono habilitado...")
        driver.find_element(
            By.XPATH,
            "/html/body/div/div[3]/div[2]/div/div/div/div/div[2]/div/div[1]/button",
        ).click()
        sleep(2)
        # take screenshot
        driver.save_screenshot("screenshots/allow_microphone.png")
        print("Done save allow microphone")
    except:
        print("No Allow Microphone popup")

    # if not missing_mic:
    try:
        print("Try to disable microphone")
        driver.find_element(By.CSS_SELECTOR, ".U26fgb").click()
    except:
        print("No microphone to disable")

    sleep(2)

    driver.save_screenshot("screenshots/disable_microphone.png")
    print("Done save microphone")

    # disable microphone
    print("Camara deshabilitada")
    if not missing_mic:
        driver.find_element(
            By.XPATH,
            '//*[@id="yDmH0d"]/c-wiz/div/div/div[14]/div[3]/div/div[2]/div[4]/div/div/div[1]/div[1]/div/div[6]/div[2]/div',
        ).click()
        sleep(2)
    else:
        print("assuming missing mic = missing camera")
    driver.save_screenshot("screenshots/disable_camera.png")
    print("Done save camera")
    print("************")
  
    joined = False
    print('.............')
   
    #     s
    join_button = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".UywwFc-LgbsSe"))
    )

    if not join_button:
        print("no tiene nada")
    else:
        try:
            join_button.click()
        except Exception as e:
            print(e)

        except Exception as e:
            print(e)
        
    driver.save_screenshot("screenshots/uihhuh.png")

 
    print("Start recording") #-t {duration}
    # record_command = f"ffmpeg -y -video_size 1920x1080 -framerate 30 -f x11grab -i :99 -f pulse -i default -t {dura} -c:v libx264 -pix_fmt yuv420p -c:a aac -strict experimental recordings/output.mp4"
    record_command = f"ffmpeg -y -video_size 1920x1080 -framerate 30 -f x11grab -i :99 -f pulse -i default -c:v libx264 -pix_fmt yuv420p -c:a aac -strict experimental recordings/output.mkv"

    END_CALL_ELEMENT = (By.CLASS_NAME, "BOo8qd")
    driver.save_screenshot("screenshots/gente.png")
    async def monitor_call_end(driver, ffmpeg_task):
        while True:
            try:
                end_call_indicator = driver.find_element(*END_CALL_ELEMENT)
                if end_call_indicator:
                    print("Videeollamada finalizada. Deteniendo videollamada")
                    ffmpeg_task.cancel()
                    break
            except NoSuchElementException:
                await asyncio.sleep(5)

    driver.save_screenshot("screenshots/ingreso.png")
    
    ffmpeg_task = asyncio.create_task(run_command_async(record_command))
    monitor_task = asyncio.create_task(monitor_call_end(driver, ffmpeg_task))
    await asyncio.gather(ffmpeg_task, monitor_task, return_exceptions=True)

    print("Grabación detenida...")


    print("Grabación lista")

    print("Transcribing using Gladia")

    file_path = "recordings/output.mkv"  # Change with your file path

    if os.path.exists(file_path):  # This is here to check if the file exists
        print("- File exists")
    else:
        print("- File does not exist")

    file_name, file_extension = os.path.splitext(
        file_path
    )  

    diarization = False

    with open(file_path, "rb") as f:  # Open the file
        file_content = f.read()  # Read the content of the file
        
    headers = {
        "x-gladia-key": gladia_api_key,
        "accept": "application/json",
    }

    files = [("audio", (file_path, file_content, "video/" + file_extension[1:]))]

    print("- Uploading file to Gladia...")
    upload_response = make_request(
        "https://api.gladia.io/v2/upload/", headers, "POST", files=files
    )
    print("Upload response with File ID:", upload_response)
    audio_url = upload_response.get("audio_url")

    data = {
        "audio_url": audio_url,
        "diarization": diarization,
    }

    headers["Content-Type"] = "application/json"

    print("- Sending request to Gladia API...")
    post_response = make_request(
        "https://api.gladia.io/v2/transcription/", headers, "POST", data=data
    )

    print("Post response with Transcription ID:", post_response)
    result_url = post_response.get("result_url")

    if result_url:
        while True:
            print("Polling for results...")
            poll_response = make_request(result_url, headers)

            if poll_response.get("status") == "done":
                file_path = "recordings/transcript.json"
                print("- Transcription done | recording results to {file_path}")
                # save the json response to recordings folder as transcript.json
                with open(file_path, "w") as f:
                    json.dump(poll_response, f, indent=2)
                break
            elif poll_response.get("status") == "error":
                file_path = "recordings/error.json"
                print("- Transcription failed | recording results to {file_path}")
                with open(file_path, "w") as f:
                    json.dump(poll_response, f, indent=2)
            else:
                print("Transcription status:", poll_response.get("status"))
            sleep(1)

    print("- End of work")

    def make_txt_file(json_file, event_id, summary, participants, time_meet):
        # Leer el archivo JSON
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Extraer "full_transcript" desde el JSON anidado
        full_transcript = data.get("result", {}).get("transcription", {}).get("full_transcript", "")

        # Decodificar el contenido de "full_transcript" correctamente
        try:
            full_transcript_decoded = full_transcript.encode("latin1").decode("utf-8")
        except UnicodeDecodeError:
            # Si falla, intenta usar la transcripción original
            full_transcript_decoded = full_transcript

        # Crear el contenido del archivo TXT
        txt_content = f"eventId: {event_id}\n"
        txt_content += f"summary: {summary}\n"
        txt_content += f"participants: {', '.join(participants)}\n"
        txt_content += f"time: {time_meet}\n"
        txt_content += "\nfull_transcript:\n"
        txt_content += full_transcript_decoded

        if not os.path.exists(volumen_path):
            os.makedirs(volumen_path)

        # Crear el archivo TXT con el nombre del "event_id"
        print(f"Ruta definida para el volumen: {volumen_path}")

        file_name = f"{event_id}.txt"
        # Obtener la ruta completa del archivo
        file_path = os.path.join(volumen_path, file_name)
        with open(file_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(txt_content)
        print("Contenido del directorio después de guardar el archivo:")
        print(os.listdir(volumen_path))
        if os.path.exists(file_path):
            print(f"El archivo se creó correctamente en: {file_path}")
        else:
            print(f"ERROR: No se encontró el archivo en: {file_path}")

        print(f"Archivo '{file_name}' creado exitosamente.")

        return file_path

# Llamar a la función con el archivo JSON
    file_path = make_txt_file("recordings/transcript.json", event_id, summary, participants, time_meet)
    print(file_path)

    save_meeting(event_id, summary, time_meet, participants, file_path)



if __name__ == "__main__":
    click.echo("Sistema de grabación de videollamada iniciado...")
    asyncio.run(join_meet())
    click.echo("Sistema finalizado.")

