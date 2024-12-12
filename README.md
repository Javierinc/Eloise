# Eloise 🏵️

Eloise es un sistema automatizado diseñado para capturar requerimientos y compromisos presentes en reuniones por videollamadas de Google Meet. Este sistema ofrece un resumen de dichas reuniones mediante una interfaz de chat, permitiendo a los usuarios realizar consultas específicas y obtener respuestas detalladas sobre las reuniones registradas.

## Módulos del Sistema

### 1. **G_calendar_module**
- **Descripción**: Este módulo busca eventos de videollamadas en el Google Calendar del usuario, notifica los eventos próximos al módulo `event_monitor_calendar` y los almacena en una base de datos.
- **Responsabilidad Principal**: Asegurarse de que los eventos sean identificados y procesados antes de su inicio.

### 2. **Event_monitor_calendar**
- **Descripción**: Tras recibir una notificación de un evento próximo, este módulo recupera los metadatos del evento desde la base de datos y los envía al módulo `recording_transcription_module`.
- **Responsabilidad Principal**: Servir como intermediario para preparar el módulo de grabación y transcripción.

### 3. **Recording_transcription_module**
- **Descripción**: Este módulo conecta a la videollamada, la graba, transcribe el audio y guarda los metadatos y el path del archivo de la transcripción.
- **Basado en**: [Gladia Samples - Gmeet Bot](https://github.com/gladiaio/gladia-samples/tree/main/integrations-examples/gmeet-bot)
- **Modificaciones Implementadas**:
  - Creación de un endpoint con Flask para recibir datos de conexión.
  - Detección automática de la finalización de la videollamada.
  - Almacenamiento de metadatos de la videollamada en la base de datos.

### 4. **Chat_text_analysis_module**
- **Descripción**: Este módulo genera resúmenes de los compromisos de las reuniones y los pone a disposición del usuario a través de una interfaz de chat. También responde a consultas específicas relacionadas con las reuniones.

---

## Requisitos Previos

### Claves API Necesarias
Antes de configurar el sistema, debes generar las siguientes API keys y agregarlas en los archivos correspondientes:
1. **Google Calendar API**: Para acceso al calendario del usuario. En este [video](https://youtu.be/B2E82UPUnOY?t=285) puedes ver como obtener el`credentials.json` necesario para acceder al calendario.
2. **Gladia API Key**: Crea una cuenta en [Gladia](https://app.gladia.io/auth/signup), habilita un API Key para ser utilizada en el módulo de transcripción.
3. **ChatGPT API Key**: Crea una cuenta en [OpenAI](https://platform.openai.com/docs/overview) y genera un API Key para la generación de resúmenes y respuestas en el chat.
4. **Firebase**: Crea un proyecto en [Firebase](https://firebase.google.com/) para untilizar una Firestore database donde se almacenaran los datos de las videollamadas. Sigue este [video](https://youtu.be/NC_7PhTUxs8?t=348) para poder descargar el `serviceAccountKey.json`

---

## Instalación y Configuración

### 1. **Clonar el Repositorio**
```bash
git clone https://github.com/Javierinc/Eloise.git
cd Eloise
```

***Construir la imagen para el módulo de sincronización de calendario***
```bash
cd G_calendar_module
docker build -t G_calendar_module -f Dockerfile .

# Construir la imagen para el monitor de eventos
cd ../event_monitor_calendar
docker build -t event_monitor_module -f Dockerfile .

# Construir la imagen para el bot de grabación y transcripción
cd ../recording_transcription_module/gmeet
docker build -t recording_transcription_module -f Dockerfile .

# Construir la imagen para el módulo de chat
cd ../chat_text_analysis_module
docker build -t chat_text_analysis_module -f Dockerfile .

***Crea en tu equipo los volúmenes para que interectuen con los contenedores***

Por ejemplo:
  - C:\\services_json (aquí debes dejar tus credenciales de los servicios de Google)
  - C:\\recordings
  - C:\\screenshots
  - C:\\transcription_storage

### **Ejecutar el sistema con docker-compose**
Una vez creadas todas las imágenes, navega a la carpeta `docker` y ejecuta:

```bash
cd docker
docker-compose up
```
### 3. **Uso**

**Interactuar con Eloise**
- Abre tu navegador y accede a http://localhost:8080 para interactuar con el chat de Eloise.
- Usa la interfaz para hacer consultas sobre las reuniones registradas.

