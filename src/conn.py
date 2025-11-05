from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os


db = SQLAlchemy()

def init_app(app: Flask):
    
       
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("CONFIG_ERROR: No se encontro la variable de entorno DATABASE_URI"
        "Asegurate de tener un archivo .env y de que Main.py llama a load_dotenv().")

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app
