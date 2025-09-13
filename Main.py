from flask import Flask, render_template, flash, request, redirect, url_for, Blueprint, jsonify 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm import joinedload
from src.conn import db, init_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user 
from werkzeug.security import generate_password_hash, check_password_hash
from models.Usuario import Usuario
from models.Rol import Rol
from models.Producto import Producto
from models.Pedido import Pedido, DetallePedido
from models.Categoria import Categoria
import os 
from werkzeug.utils import secure_filename

app = Flask(__name__) ##iniciar proyecto
app.secret_key = 'contraseña_secreta'
init_app(app)

##---------------------------------------------------foto------------------------------------------------------------------------------------------

UPLOAD_FOLDER = 'static/uploads/productos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

##---------------------------------------------------fin_foto--------------------------------------------------------------------------------------
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
                flash("Inicio de sesion exitoso", "login")

                if usuario.id_rol==1:
                    return redirect(url_for('Admin'))
                elif usuario.id_rol==2:
                    return redirect(url_for('vendedor'))
                elif usuario.id_rol==3:
                    return redirect(url_for('comprador'))
                else:
                    return redirect(url_for('index'))
              
            else:
                flash("Cuenta deshabilitada, contactanos", "login")
                
        else:
            flash("Correo o contraseña incorrectos", "login")
            
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
            return redirect(url_for('registro_administrador'))
        
        existente = Usuario.query.filter_by(correo=correo).first()
        if existente:
            flash("El correo ya esta en uso")
            return redirect(url_for('registro_administrador'))
        
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
        return redirect(url_for('inicio_sesion'))
    return render_template('registroadministrador.html')
##-------------------------------------------------------------carrito-------------------------------------------------------------------------------------
@app.route('/carrito')
@login_required
def carrito():
    return render_template('carritocomprador.html')
##-------------------------------------------------------------fin_carrito------------------------------------------------------------------
##-------------------------------------------------------------Admin-------------------------------------------------------------------------------------
@app.route('/admin')
@login_required
def Admin():
    
    usuarios = Usuario.query.options(joinedload(Usuario.rol)).all()
    productos = Producto.query.all()
    vendedores = Usuario.query.filter_by(id_rol=2).all() 
    rol = Rol.query.all()
    categorias = Categoria.query.all()

    

    return render_template('usuariosadmin.html',
                           usuarios=usuarios,
                           productos=productos,
                           rol=rol, vendedores=vendedores,
                           categorias=categorias)

@app.route('/usuario/crear', methods=['POST'])
@login_required
def crear_usuario():
    nombre = request.form['nombre']
    correo = request.form['correo']
    password = request.form['password']
    confirmar = request.form['confirmar']
    telefono = request.form.get('telefono')
    id_rol = request.form['id_rol']

    if password != confirmar:
        flash("Las contraseñas no coinciden", "error")
        return redirect(url_for('Admin'))
    
    existente = Usuario.query.filter_by(correo=correo).first()
    if existente:
        flash("El correo ya está en uso", "error")
        return redirect(url_for('Admin'))
    
    nuevo_usuario = Usuario(
        nombre=nombre,
        correo=correo,
        telefono=telefono,
        id_rol=id_rol,
        estado=True
    )
    nuevo_usuario.set_password(password)
    db.session.add(nuevo_usuario)
    db.session.commit()

    flash(f"Usuario {nombre} creado correctamente", "success")
    return redirect(url_for('Admin'))

@app.route('/usuario/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        usuario.nombre = request.form['nombre']
        usuario.correo = request.form['correo']
        usuario.telefono = request.form['telefono']
        usuario.estado = request.form['estado'] == 'True'
        usuario.id_rol = request.form['id_rol']  
        db.session.commit()
        flash('Usuario actualizado correctamente', 'success')
        return redirect(url_for('Admin'))
    
    usuarios = Usuario.query.options(joinedload(Usuario.rol)).all()
    productos = Producto.query.all()
    rol = Rol.query.all()
    return render_template(
        'usuariosadmin.html',
        usuarios=usuarios,
        productos=productos,
        usuario_editar=usuario,
        rol=rol
    )

@app.route('/usuario/eliminar/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado correctamente', 'success')
    return redirect(url_for('Admin'))

@app.route('/producto/crear', methods=['POST'])
@login_required
def crear_producto_post():
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = float(request.form['precio'])
    stock = int(request.form['stock'])
    id_vendedor = int(request.form['id_vendedor'])
    id_categoria = int(request.form['id_categoria'])
    
    foto_file = request.files.get('foto')
    filename = None
    if foto_file:
       filename = secure_filename(foto_file.filename)
       upload_folder = os.path.join(app.root_path, 'static', 'uploads')
       os.makedirs(upload_folder, exist_ok=True)
       foto_file.save(os.path.join(upload_folder, filename))

    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock,
        id_vendedor=id_vendedor,
        foto=filename,
        id_categoria=id_categoria, 
        estado=True
    )
    db.session.add(nuevo_producto)
    db.session.commit()
    flash(f'Producto {nombre} creado correctamente', 'success')
    return redirect(url_for('Admin'))

@app.route('/producto/editar/<int:id>', methods=['POST'])
@login_required
def editar_producto(id):
    # Obtener el producto a editar
    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':
        # Actualizar los campos del producto
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.precio = float(request.form['precio'])
        producto.stock = int(request.form['stock'])
        producto.id_vendedor = int(request.form['id_vendedor'])
        producto.id_categoria = int(request.form['id_categoria'])

        # Actualizar foto si se cargó una nueva
        foto_file = request.files.get('foto')
        if foto_file and foto_file.filename != '':
            filename = secure_filename(foto_file.filename)
            upload_folder = os.path.join(app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            foto_file.save(os.path.join(upload_folder, filename))
            producto.foto = filename

        db.session.commit()
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('Admin'))

    # Para GET: enviar todas las listas que usa la plantilla
    usuarios = Usuario.query.all()
    rol = Rol.query.all()
    productos = Producto.query.all()
    vendedores = Usuario.query.filter_by(id_rol=2).all()  # Suponiendo rol 2 = vendedor
    categorias = Categoria.query.all()

    return render_template('usuariosadmin.html',
                           usuarios=usuarios,
                           rol=rol,
                           productos=productos,
                           vendedores=vendedores,
                           categorias=categorias,
                           producto_editar=producto)

@app.route('/producto/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash(f'Producto {producto.nombre} eliminado correctamente', 'success')
    return redirect(url_for('Admin'))


##-------------------------------------------------------------fin_Admin------------------------------------------------------------------
##-------------------------------------------------------------vendedor-------------------------------------------------------------------------------------
@app.route('/vendedor')
@login_required
def vendedor():
   categorias = Categoria.query.all()
   productos = Producto.query.filter_by(id_vendedor=current_user.id_usuario).all()
   
   return render_template('usuariovendedor.html', productos=productos, categorias=categorias) 

@app.route('/producto/crear/V', methods=['POST'])
@login_required
def crear_producto():
    
    nombre = request.form['nombre']
    descripcion = request.form.get('descripcion')
    precio = float(request.form['precio'])
    stock = int(request.form['stock'])
    id_categoria = int(request.form['id_categoria'])  

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'productos')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    foto = request.files.get('foto')
    if foto and allowed_file(foto.filename):
        filename = secure_filename(f"{current_user.id_usuario}_{foto.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        foto.save(filepath)

       
        foto_path = f'uploads/productos/{filename}'
    else:
        foto_path = None

    producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock,
        foto=foto_path,
        id_categoria=id_categoria,
        id_vendedor=current_user.id_usuario,
        estado=True
    )

    db.session.add(producto)
    db.session.commit()

    flash('Producto creado correctamente', 'success')
    return redirect(url_for('vendedor'))

@app.route('/producto/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto_vendedor(id):
    producto = Producto.query.get_or_404(id)
    if producto.id_vendedor != current_user.id_usuario:
        return jsonify({'success': False})
    
    db.session.delete(producto)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/producto/entregado/<int:id>', methods=['POST'])
@login_required
def producto_entregado(id):
    producto = Producto.query.get_or_404(id)
    if producto.id_vendedor != current_user.id_usuario:
        return jsonify({'success': False})

    producto.estado = True  
    db.session.commit()
    return jsonify({'success': True})

@app.route('/vendedor/pedidos')
@login_required
def pedidos_vendedor():
    pedidos = (
         db.session.query(Pedido)
        .join(DetallePedido, DetallePedido.id_pedido == Pedido.id_pedido)
        .join(Producto, Producto.id_producto == DetallePedido.id_producto)
        .filter(Producto.id_vendedor == current_user.id_usuario)
        .all()
    )

    pedidos_list = []
    for pedido in pedidos:
        for detalle in pedido.detalles:
            pedidos_list.append({
                "id_pedido": pedido.id_pedido,
                "producto": detalle.producto.nombre,
                "cantidad": detalle.cantidad,
                "precio_unitario": float(detalle.precio_unitario),
                "subtotal": float(detalle.subtotal)
        })

    return jsonify(pedidos_list)

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

