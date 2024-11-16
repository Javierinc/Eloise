import asyncio
import os
import signal
import subprocess
import click
import datetime
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

#Con sys se extraen los datos que llegan al endpoint de start record
meet_link = sys.argv[1]  # El primer argumento pasado (el enlace)
duration = sys.argv[2]  # El segundo argumento pasado (la duración)

#Enlace y duración para utilizar
print(f"Link: {meet_link}")
print(f"Duration: {duration}")



def make_request(url, headers, method="GET", data=None, files=None):
    if method == "POST":
        response = requests.post(url, headers=headers, json=data, files=files)
    else:
        response = requests.get(url, headers=headers)
    return response.json()


async def run_command_async(command):
    process = await asyncio.create_subprocess_shell(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
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

    # eliminar la carpeta screenshots si existe incluso si no está vacía
    print("Limpiando los screenshots anteriores")
    if os.path.exists("screenshots"):
        # for each file in the folder delete it
        for f in os.listdir("screenshots"):
            os.remove(f"screenshots/{f}")
    else:
        os.mkdir("screenshots")

    print("comenzando con los drivers de audio virtual")
    # buscar fuente de audio para el navegador especificado
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


    email = os.getenv("GMAIL_USER_EMAIL", "")
    password = os.getenv("GMAIL_USER_PASSWORD", "")
    gladia_api_key = (os.getenv("GLADIA_API_KEY", ""),)

    if email == "" or password == "":
        print("No se especifica email o contraseña")
        return

    if gladia_api_key == "":
        print("No hay API KEY de Gladia")
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

    # deshabilita microfono
    print("Deshabilitando micrófono")

    sleep(10)
    missing_mic = False

    try:
        print("Tratando de deshabilitar micrófono")
        driver.find_element(By.CLASS_NAME, "VfPpkd-vQzf8d").find_element(By.XPATH, "..")
        sleep(2)
        # toma un screenshot

        driver.save_screenshot("screenshots/missing_mic.png")

        # guarda la fuente html de la pagina web
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
        #toma un screenshot
        driver.save_screenshot("screenshots/allow_microphone.png")
        
    except:
        print("No permitir popup de microfono")

    # si no hay ausencia de microfono:
    try:
        print("Trata de deshabilitar microfono")
        driver.find_element(By.CSS_SELECTOR, ".U26fgb").click()
    except:
        print("No hay microfono que deshabilitar")

    sleep(2)

    driver.save_screenshot("screenshots/disable_microphone.png")
    
    print("Camara deshabilitada")
    if not missing_mic:
        driver.find_element(
            By.XPATH,
            '//*[@id="yDmH0d"]/c-wiz/div/div/div[14]/div[3]/div/div[2]/div[4]/div/div/div[1]/div[1]/div/div[6]/div[2]/div',
        ).click()
        sleep(2)
    else:
        print("asumiendo que el microfono esta deshabilitado esta deshabilitada la camara")
    driver.save_screenshot("screenshots/disable_camera.png")
    
    print("************")
    

    # Trata cada 5 segundos por un maximo de 5 minutos
    now = datetime.datetime.now()
    max_time = now + datetime.timedelta(
        minutes=os.getenv("MAX_WAITING_TIME_IN_MINUTES", 5)
    )

    joined = False
    print('.............')
   
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

        
    driver.save_screenshot("screenshots/luriluri.png")


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
                    print("Videollamada finalizada. Deteniendo videollamada")
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

    file_path = "recordings/output.mkv" 

    if os.path.exists(file_path):  # Verifica si el archivo existe
        print("- existe archivo")
    else:
        print("- archivo no existe")

    file_name, file_extension = os.path.splitext(
        file_path
    )  

    diarization = False

    with open(file_path, "rb") as f:  # abre el archivo
        file_content = f.read()  # lee contenido del archivo
  
    headers = {
        "x-gladia-key": gladia_api_key,
        "accept": "application/json",
    }

    files = [("audio", (file_path, file_content, "video/" + file_extension[1:]))]

    print("- Subiendo archivo a Gladia...")
    upload_response = make_request(
        "https://api.gladia.io/v2/upload/", headers, "POST", files=files
    )
    print("Carga con respuesta con ID de archivo:", upload_response)
    audio_url = upload_response.get("audio_url")

    data = {
        "audio_url": audio_url,
        "diarization": diarization,
    }

    headers["Content-Type"] = "application/json"

    print("- Enviando request a Gladia API...")
    post_response = make_request(
        "https://api.gladia.io/v2/transcription/", headers, "POST", data=data
    )

    print("Post respons con Transcription ID:", post_response)
    result_url = post_response.get("result_url")

    if result_url:
        while True:
            print("obteniendo resultado...")
            poll_response = make_request(result_url, headers)

            if poll_response.get("status") == "done":
                file_path = "recordings/transcript.json"
                print("- Transcription done | recording results to {file_path}")
                # guarda la respuesta json en la carpeta de grabaciones como transcript.json
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

    print("- Trabajo terminado")


if __name__ == "__main__":
    click.echo("Sistema de grabación de videollamada iniciado...")
    asyncio.run(join_meet())
    click.echo("Sistema finalizado.")
