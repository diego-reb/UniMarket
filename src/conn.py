from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def init_app(app: Flask):

    load_dotenv()

    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError(
            "CONFIG_ERROR: No se encontró la variable DATABASE_URL. "
            "Asegúrate de tener un .env y que Render tenga configurada la variable."
        )

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    return app
