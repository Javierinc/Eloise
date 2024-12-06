# Usa una imagen base ligera con Python
FROM python:3.9-slim-bullseye

RUN mkdir /app /app/files 
# Establece el directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema necesarias para las librerías
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requisitos
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente de la aplicación
COPY . .

# Crea el directorio para los archivos de configuración
RUN mkdir -p /app/files

# Configura el volumen para los archivos externos
VOLUME /app/files

# Comando para ejecutar la aplicación
CMD ["python", "-u","main.py"]