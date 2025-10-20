from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# Inicializamos la BD
db = SQLAlchemy()

def init_app(app: Flask):
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        ##'postgresql://postgres:postgres@localhost:5432/UniMarket'
        'postgresql://postgres:lenovoblue@localhost:5432/UniMarket'

    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app
