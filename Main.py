from flask import Flask, render_template, flash, request, redirect, url_for, Blueprint, jsonify 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm import joinedload
from src.conn import db, init_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user 
from werkzeug.security import generate_password_hash, check_password_hash
from models.Usuario import Usuario
from models.Rol import Rol
from models.Producto import Producto
from models import Categoria

app = Flask(__name__) ##iniciar proyecto
app.secret_key = 'contraseña_secreta'
init_app(app)

##---------------------------------------------------test------------------------------------------------------------------------------------------
@app.route('/test')
def test_db():
    try:
        result = db.session.execute('SELECT 1')
        return f"Conectada a la base de datos"
    except Exception as e:
        return f"Error de conexion: {e}"

##-----------------------------------------------------fin_test--------------------------------------------------------------------------------
##-----------------------------------index-----------------------------------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

##-----------------------------------fin_index-----------------------------------------------------------------------------------------------
##-----------------------------------inicio_sesion-------------------------------------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view= 'inicio_sesion'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
@app.route('/inicio_sesion', methods=['GET','POST'])
def inicio_sesion():
    if request.method == 'POST':
       
        correo = request.form['correo']
        password = request.form['password']

        usuario = Usuario.query.filter_by(correo=correo).first()
        

        if usuario and usuario.check_password(password):
            if usuario.estado:
                login_user(usuario)
                flash("Inicio de sesion exitoso")

                if usuario.id_rol==1:
                    return redirect(url_for('Admin'))
                elif usuario.id_rol==2:
                    return redirect(url_for('vendedor'))
                elif usuario.id_rol==3:
                    return redirect(url_for('comprador'))
                else:
                    return redirect(url_for('index'))
              
            else:
                flash("Cuenta deshabilitada, contactanos")
                
        else:
            flash("Correo o contraseña incorrectos")
            
    return render_template('iniciosesion.html')
##-----------------------------------fin_inicio_sesion-----------------------------------------------------------------------------------------------

##-----------------------------------cerrar_sesion-------------------------------------------------------------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesion")
    return redirect(url_for('index'))
##-----------------------------------fin_cerrar_sesion-----------------------------------------------------------------------------------------------
##-----------------------------------registro-------------------------------------------------------------------------------------
@app.route('/registro', methods=['GET','POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['name'].strip()
        correo = request.form['email'].strip()
        telefono = request.form['phone'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm-password'].strip()
        tipo_cuenta = request.form.get('tipo')  

        if password != confirm_password:
            flash("Las contraseñas no coinciden")
            return redirect(url_for('registro'))

        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            id_rol=2 if tipo_cuenta == 'vendedor' else 3
        )
        nuevo_usuario.set_password(password)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Usuario registrado con éxito")
        return redirect(url_for('inicio_sesion'))

    return render_template('registro.html')

##-------------------------------------------------------------fin_registro------------------------------------------------------------------
##--------------------------------------------------------------registro_administrador--------------------------------------------------------------
@app.route('/RA', methods=['GET','POST'])

def registro_administrador():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        password = request.form['password']
        confirmar = request.form['confirmar']

        if password != confirmar:
            flash("Las contraseñas no coinciden")
            return redirect(url_for('RA'))
        
        existente = Usuario.query.filter_by(correo=correo).first()
        if existente:
            flash("El correo ya esta en uso")
            return redirect(url_for('RA'))
        
        nuevo_admin = Usuario(
            nombre=nombre,
            correo=correo,
            password=generate_password_hash(password),
            id_rol=1,
            estado=True

        )
        db.session.add(nuevo_admin)
        db.session.commit()
        flash("Administrador registrado con exito")
        return redirect(url_for('Admin'))
    return render_template('registroadministrador.html')
##-------------------------------------------------------------carrito-------------------------------------------------------------------------------------
@app.route('/carrito')
@login_required
def carrito():
    return render_template('carritocomprador.html')
##-------------------------------------------------------------fin_carrito------------------------------------------------------------------
##-------------------------------------------------------------Admin-------------------------------------------------------------------------------------
@app.route('/admin')
def Admin():
    usuarios = Usuario.query.options(joinedload(Usuario.rol)).all()
    productos = Producto.query.all()
    return render_template('usuariosadmin.html', usuarios=usuarios, productos=productos)

@app.route('/usuario/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        usuario.nombre = request.form['nombre']
        usuario.email = request.form['email']
        usuario.rol = int(request.form['rol'])
        db.session.commit()
        flash('Usuario actualizado correctamente', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/usuario/eliminar/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado correctamente', 'success')
    return redirect(url_for('admin_panel'))

# Similar para productos:
@app.route('/producto/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.precio = float(request.form['precio'])
        producto.estado = request.form['estado'] == 'published'
        db.session.commit()
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('editar_producto.html', producto=producto)

@app.route('/producto/eliminar/<int:id>', methods=['POST'])
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado correctamente', 'success')
    return redirect(url_for('admin_panel'))
##-------------------------------------------------------------fin_Admin------------------------------------------------------------------
##-------------------------------------------------------------vendedor-------------------------------------------------------------------------------------
@app.route('/vendedor')
@login_required
def vendedor():
    return render_template('usuariovendedor.html')
##-------------------------------------------------------------fin_vendedor------------------------------------------------------------------
##-------------------------------------------------------------comprador-------------------------------------------------------------------------------------
@app.route('/comprador')
@login_required
def comprador():
    return render_template('usuariocomprador.html')
##-------------------------------------------------------------fin_comprador------------------------------------------------------------------



if __name__ == '__main__': ##depurar proyecto 
   with app.app_context():
        db.create_all()  # Crea las tablas si no existen
   app.run(debug=True)

