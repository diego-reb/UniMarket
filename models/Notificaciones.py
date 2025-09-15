from src.conn import db

class Notificacion(db.Model):
    __tablename__ = 'notificacion'
    id_notificacion = db.Column(db.Integer, primary_key=True)
    id_vendedor = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedido.id_pedido'), nullable=False)
    visto = db.Column(db.Boolean, default=False)

    pedido = db.relationship('Pedido', backref=db.backref('notificaciones', lazy=True))
