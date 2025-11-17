# Usar imagen base
FROM python:3.11-slim

# Crear directorio de la app
WORKDIR /app

# Copiar todo el proyecto al contenedor
COPY . .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer puerto (Render usará $PORT)
EXPOSE 5000

# Comando para correr la app con Gunicorn y puerto dinámico
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:$PORT -w 4 Main:app"]
