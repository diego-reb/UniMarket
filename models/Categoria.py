
from src.conn import db  

class Categoria(db.Model):
    __tablename__ = 'categoria'  

    id_categoria = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    productos = db.relationship('Producto', backref='categoria', lazy=True)

    def __repr__(self):
        return f'<Categoria {self.nombre}>'
