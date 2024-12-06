# Usa una imagen base oficial de Python
FROM python:3.9-slim-bullseye

RUN mkdir /app /app/files 
# Establecer el directorio de trabajo
WORKDIR /app


# Instalar dependencias del sistema necesarias para Firebase y otras librerías
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar los requisitos de Python
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente de la aplicación
COPY . .

# # Exponer el puerto para la API (opcional, si el contenedor también expone servicios)
# EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python", "-u", "app.py"]
