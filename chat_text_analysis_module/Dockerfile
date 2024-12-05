# Usa una imagen base oficial de Python
FROM python:3.9-bullseye

RUN mkdir /app /app/files /app/transcription_storage 

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para paquetes como firebase-admin
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    gcc \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*


# Configurar el locale `es_ES.UTF-8`
RUN echo "es_ES.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen

# Configurar variables de entorno para el locale
ENV LANG=es_ES.UTF-8
ENV LANGUAGE=es_ES:es
ENV LC_ALL=es_ES.UTF-8

# Copiar los archivos de dependencias al contenedor
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Actualizar las bibliotecas específicas
RUN pip install --upgrade openai langchain-openai

# Copiar el resto del código de la aplicación al contenedor
COPY . .

# Exponer el puerto usado por Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación
ENTRYPOINT ["streamlit", "run"]
CMD ["app.py"]
