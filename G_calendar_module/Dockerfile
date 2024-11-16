# Usar la imagen base de Python
FROM python:3.10-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto
COPY main.py /app/main.py
COPY requirements.txt /app/requirements.txt

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Establecer las variables de entorno para manejar las credenciales
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/serviceAccountKey.json"
ENV GOOGLE_CREDENTIALS="/app/credentials.json"
ENV GOOGLE_TOKEN="/app/token.json"

# Comando para ejecutar el script
CMD ["python", "main.py"]
