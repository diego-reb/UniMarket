# Usar imagen base de Python 3.11 slim
FROM python:3.11-slim

# Variables de entorno para evitar warnings y mejorar rendimiento
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de la app
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requerimientos e instalar dependencias
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Exponer puerto para Render
EXPOSE 5000

# Usar Gunicorn para producción con 4 workers
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "Main:app"]
