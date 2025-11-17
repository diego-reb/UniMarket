# Usar imagen
FROM python:3.11-slim
#Crear directorio dentro del contenedor
WORKDIR /app
#Copiar el archivo del proyecto 
COPY . .
#Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt
#Expone el puerto de flask 
EXPOSE 5000
#Ejecutar la app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "Main:app"]

