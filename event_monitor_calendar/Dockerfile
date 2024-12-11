# Utilizar una imagen base de Python con una versión reciente
FROM python:3.9-slim
RUN mkdir /app /app/files /app/transcription_storage 

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar las dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY app.py .

# Exponer el puerto donde se ejecutará la aplicación
EXPOSE 3000

# Configurar el comando para ejecutar la aplicación
CMD ["python", "-u", "app.py"]