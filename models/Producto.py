from src.conn import db
from models.Categoria import Categoria
from models.Usuario import Usuario

class Producto(db.Model):
    __tablename__='producto'

    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    precio = db.Column(db.Numeric(10,2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    foto = db.Column(db.String(255)) 
    estado = db.Column(db.String(20), default='activo')

    id_categoria = db.Column(db.Integer,
                             db.ForeignKey('categoria.id_categoria'),
                             nullable=False)
    id_vendedor = db.Column(db.Integer,
                            db.ForeignKey('usuario.id_usuario'),
                            nullable=False)

    vendedor = db.relationship('Usuario', backref=db.backref('productos', lazy=True))

    def __repr__(self):
        return f'<Producto {self.nombre} - ${self.precio}>'