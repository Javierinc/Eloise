Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

echo "Iniciando el servidor Flask..."
python3 app.py &

# Esperar unos segundos para asegurarse de que Flask haya iniciado
sleep 5

# Mensaje de estado del servidor Flask
echo "El servidor Flask está corriendo. Listo para ejecutar grabaciones."

# Iniciar main.py (ejecutado bajo demanda desde Flask, con los argumentos correspondientes)

# Mantener el contenedor activo
tail -f /dev/null