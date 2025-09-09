from src.conn import db
from werkzeug.security import generate_password_hash, check_password_hash

class Rol(db.Model):
    __tablename__='rol'
    id_rol = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)