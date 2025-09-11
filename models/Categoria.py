# models/Categoria.py
from src.conn import db  # importa tu instancia db de la app principal

class Categoria(db.Model):
    __tablename__ = 'categoria'  # igual que en tu tabla SQL

    id_categoria = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    # relación inversa opcional: te permitirá acceder a los productos
    productos = db.relationship('Producto', backref='categoria', lazy=True)

    def __repr__(self):
        return f'<Categoria {self.nombre}>'
