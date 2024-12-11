# Usa una imagen base ligera con Python
FROM python:3.9-slim-bullseye

# Establece el directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema necesarias para las librerías
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libssl-dev \
    libffi-dev \
    python3-dev \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configura la zona horaria
ENV TZ=America/Santiago
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copia el archivo de requisitos
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente de la aplicación
COPY . .

# Configura el volumen para los archivos externos
VOLUME /app/files

# Exponer el puerto que usa la aplicación (si aplica)
EXPOSE 3000

# Comando para ejecutar la aplicación
CMD ["python", "-u", "app.py"]
