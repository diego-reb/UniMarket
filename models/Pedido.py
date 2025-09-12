from src.conn import db
from models.Usuario import Usuario
from models.Producto import Producto

class Pedido(db.Model):
    __tablename__ = 'pedido'

    id_pedido = db.Column(db.Integer, primary_key=True)
    id_comprador = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    fecha = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    total = db.Column(db.Numeric(10,2), nullable=False)
    estado = db.Column(db.String(20), default='Pendiente')

    comprador = db.relationship('Usuario', backref=db.backref('pedidos', lazy=True))
    detalles = db.relationship('DetallePedido', backref='pedido', lazy=True)

    def __repr__(self):
        return f'<Pedido {self.id_pedido} - Total: ${self.total} - Estado: {self.estado}>'

class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedido'

    id_detalle = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedido.id_pedido'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10,2), nullable=False)
    subtotal = db.Column(db.Numeric(10,2), nullable=False)

    producto = db.relationship('Producto', backref=db.backref('detalles_pedido', lazy=True))

    def __repr__(self):
        return f'<DetallePedido {self.id_detalle} - Producto: {self.producto.nombre} - Cantidad: {self.cantidad}>'
