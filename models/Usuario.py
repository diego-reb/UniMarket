from src.conn import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20))
    id_rol = db.Column(db.Integer, db.ForeignKey('rol.id_rol'), nullable=False)
    estado = db.Column(db.Boolean, default=True)
    email_confirmado = db.Column(db.Boolean, default=False)

    rol = db.relationship('Rol', backref= db.backref('usuarios',lazy=True))

    def set_password(self, password):
        self.password= generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_id(self):
        return self.id_usuario