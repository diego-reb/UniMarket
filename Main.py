from flask import Flask, render_template, flash, request, redirect, url_for, Blueprint, jsonify, session
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm import joinedload
from flask_mail import Mail, Message
import smtplib
from email.mime.text import MIMEText
from collections import defaultdict
import json
from src.conn import db, init_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user 
from werkzeug.security import generate_password_hash, check_password_hash
from models.Usuario import Usuario
from models.Rol import Rol
from models.Producto import Producto
from models.Pedido import Pedido, DetallePedido
from models.Categoria import Categoria
from models.Notificaciones import Notificacion  
import os 
from werkzeug.utils import secure_filename
from oauthlib.oauth2 import WebApplicationClient
import requests
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"



app = Flask(__name__) ##iniciar proyecto
app.secret_key = 'contraseña_secreta'
init_app(app)

##---------------------------------------------------foto------------------------------------------------------------------------------------------

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

##---------------------------------------------------fin_foto--------------------------------------------------------------------------------------
##---------------------------------------------------no cache--------------------------------------------------------------------------------------

@app.after_request
def add_header(response):
    response.headers['cache-control']='no-store, no-cache, must-revalidate'
    response.headers['Pragma']='no-cache'
    response.headers['Expires']='0'
    return response

##---------------------------------------------------fin_no_cache-----------------------------------------------------------------------------------


##----------------------------------------------------correo----------------------------------------------------------------------------------------

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'dzgarcia10@gmail.com'
app.config['MAIL_PASSWORD'] = 'zxbi yzge pbjn onkq'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

##----------------------------------------------------fin_correo-----------------------------------------------------------------------------------
##-----------------------------------------------------google----------------------------------------------------------------------------------------
app.config['GOOGLE_CLIENT_ID'] = "460522583219-pg00bvtl0i6biecghpor9sh1qite5f6a.apps.googleusercontent.com"
app.config['GOOGLE_CLIENT_SECRET'] = "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"
app.config['GOOGLE_DISCOVERY_URL'] = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])
REDIRECT_URI = "http://127.0.0.1:5000/login/google/callback"

##-----------------------------------------------------fin_google------------------------------------------------------------------------------------
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
    categorias = Categoria.query.all()
    productos = Producto.query.all()

    productos_data = []
    for p in productos:
        productos_data.append({
            'id': p.id_producto,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'precio':float(p.precio),
            'foto':p.foto,
            'vendedor': p.vendedor.nombre,
            'categoria_id':p.categoria.id_categoria
        })
   

    return render_template('index.html', categorias=categorias, productos = productos_data)

##-----------------------------------fin_index-----------------------------------------------------------------------------------------------

##-------------------------------------inicio_sesion google--------------------------------------------------------------------------------
@app.route('/login/google')
def google_login():
    google_provider_cfg = requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri="http://127.0.0.1:5000/login/google/callback",  
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route('/login/google/callback')
def google_callback():
    code = request.args.get("code")
    session.clear()

    google_provider_cfg = requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url="http://127.0.0.1:5000/login/google/callback",
        code=code
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET']),
    )

    client.parse_request_body_response(token_response.text)

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    userinfo = userinfo_response.json()

    correo = userinfo.get("email")
    nombre = userinfo.get("name", "")

    usuario = Usuario.query.filter_by(correo=correo).first()
    if not usuario:
        session['nuevo_usuario']={
            "nombre":nombre,
            "correo":correo,
            "telefono":'',
            }
        return redirect(url_for('choose_role'))

    login_user(usuario)
    flash("Inicio de sesión exitoso con Google", "login")

    if usuario.id_rol == 1:
        return redirect(url_for('Admin'))
    elif usuario.id_rol == 2:
        return redirect(url_for('vendedor'))
    else:
        return redirect(url_for('index'))
    
@app.route('/complete_registration')
def complete_registration():
    if 'nuevo_usuario' not in session or 'rol_elegido' not in session:
        return redirect(url_for('index'))  

    datos = session['nuevo_usuario']
    rol = session['rol_elegido']

    usuario = Usuario(
        nombre=datos['nombre'],
        correo=datos['correo'],
        telefono=datos['telefono'],
        id_rol=rol,
        estado=True
    )
    usuario.password = generate_password_hash('google_login')
    db.session.add(usuario)
    db.session.commit()

    login_user(usuario)

    session.pop('nuevo_usuario')
    session.pop('rol_elegido')

    flash("Registro completado y sesión iniciada", "login")
    if rol == 2:
        return redirect(url_for('vendedor'))
    else:
        return redirect(url_for('index'))


##-------------------------------------fin_inicio_sesion google-------------------------------------------------------------------------------
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
                    return redirect(url_for('index'))
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

    if usuario.pedidos_comprador or usuario.pedidos_vendedor:
        flash ("No se puede eliminar el usuario con pedidos asocidos","error")
        return redirect(url_for('Admin'))
    
    if usuario.productos:
        flash("No se puede eliminar el usuario con productos asosociados", "error")
        return redirect(url_for('Admin'))


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
    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.precio = float(request.form['precio'])
        producto.stock = int(request.form['stock'])
        producto.id_vendedor = int(request.form['id_vendedor'])
        producto.id_categoria = int(request.form['id_categoria'])

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

    usuarios = Usuario.query.all()
    rol = Rol.query.all()
    productos = Producto.query.all()
    vendedores = Usuario.query.filter_by(id_rol=2).all()  
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
    DetallePedido.query.filter_by(id_producto=id).delete()
    db.session.delete(producto)
    db.session.commit()
    flash(f'Producto {producto.nombre} eliminado correctamente', 'success')
    return redirect(url_for('Admin'))


##-------------------------------------------------------------fin_Admin------------------------------------------------------------------
##-------------------------------------------------------------vendedor-------------------------------------------------------------------------------------
@app.route('/vendedor')
@login_required
def vendedor():
    pedidos_raw = Pedido.query.filter_by(id_vendedor=current_user.id_usuario).all()
    categorias = Categoria.query.all()
    productos = Producto.query.filter_by(id_vendedor=current_user.id_usuario).all()

    pedidos_pendientes = []
    pedidos_entregados = []

    for p in pedidos_raw:
        comprador = Usuario.query.get(p.id_comprador)

        detalles = DetallePedido.query.filter_by(id_pedido=p.id_pedido).all()
        lista_productos = []
        for d in detalles:
            prod = Producto.query.get(d.id_producto)
            if prod:
                lista_productos.append(f"{prod.nombre} x {d.cantidad}")

        pedido_dict = {
            'id_pedido': p.id_pedido,
            'fecha': p.fecha,
            'total': p.total,
            'estado': p.estado,
            'comprador_nombre': comprador.nombre if comprador else "Desconocido",
            'comprador_correo': comprador.correo if comprador else "Desconocido",
            'comprador_telefono': comprador.telefono if comprador else "Desconocido",
            'productos': lista_productos
        }

        if p.estado.lower() == 'pendiente':
            pedidos_pendientes.append(pedido_dict)
        else:
            pedidos_entregados.append(pedido_dict)

    return render_template(
        'usuariovendedor.html',
        productos=productos,
        categorias=categorias,
        pedidos=pedidos_pendientes,
        historial=pedidos_entregados  
    )


@app.route('/producto/<int:id>')
@login_required
def obtener_producto(id):
    p = Producto.query.get_or_404(id)
    return jsonify({
        'id_producto': p.id_producto,
        'nombre': p.nombre,
        'descripcion': p.descripcion,
        'stock': p.stock,
        'precio': p.precio,
        'id_categoria': p.id_categoria
    })
@app.route('/vendedor/producto/editar/<int:id>', methods=['POST'])
@login_required
def editar_producto_vendedor(id):
    producto = Producto.query.get_or_404(id)

    if producto.id_vendedor != current_user.id_usuario:
        return jsonify({'success': False, 'error': 'No autorizado'}), 403

    try:
        
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.stock = int(request.form['stock'])
        producto.precio = float(request.form['precio'])
        producto.id_categoria = int(request.form['id_categoria'])

        
        foto = request.files.get('foto')
        if foto and foto.filename != '' and allowed_file(foto.filename):
            filename = secure_filename(f"{current_user.id_usuario}_{foto.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(filepath)
            
            producto.foto = f'uploads/{filename}'

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/producto/crear/V', methods=['POST'])
@login_required
def crear_producto():
    
    nombre = request.form['nombre']
    descripcion = request.form.get('descripcion')
    precio = float(request.form['precio'])
    stock = int(request.form['stock'])
    id_categoria = int(request.form['id_categoria'])  

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')  
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    foto = request.files.get('foto')
    if foto and allowed_file(foto.filename):
        filename = secure_filename(f"{current_user.id_usuario}_{foto.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)  
        foto.save(filepath)
        foto_path = filename  
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

@app.route('/producto/eliminar/<int:id>', methods=['POST', 'DELETE'])
@login_required
def eliminar_producto_vendedor(id):
    producto = Producto.query.get_or_404(id)
    if producto.id_vendedor != current_user.id_usuario:
        return jsonify({'success': False})
    
    db.session.delete(producto)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/pedido/entregado/<int:id>', methods=['POST'])
@login_required
def marcar_entregado(id):
    pedido = Pedido.query.get_or_404(id)
    
    detalles = DetallePedido.query.join(Producto).filter(
        DetallePedido.id_pedido == id,
        Producto.id_vendedor == current_user.id_usuario
    ).all()
    if not detalles:
        return jsonify({'success': False, 'error': 'No autorizado'}), 403

    pedido.estado = 'Entregado'
    db.session.commit()

    comprador = Usuario.query.get(pedido.id_comprador)  
    
    lista_productos = []
    for d in detalles:
        prod = Producto.query.get(d.id_producto)
        if prod:
            lista_productos.append(f"{prod.nombre} x {d.cantidad}")

    return jsonify({
        'success': True,
        'pedido': {
            'id_pedido': pedido.id_pedido,
            'fecha': pedido.fecha.strftime('%d/%m/%Y %H:%M'),
            'total': pedido.total,
            'comprador_nombre': comprador.nombre,
            'comprador_correo': comprador.correo,
            'comprador_telefono': comprador.telefono,
            'productos': lista_productos
        }
    })



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

##-------------------------------------------------------------compra-------------------------------------------------------------------------
@app.route('/compra')
@login_required
def compra():

    return render_template('compra.html', user=current_user)

@app.route('/procesar_compra', methods=['POST'])
@login_required
def procesar_compra():
    cart = json.loads(request.form['cartData'])
    pago = request.form['pago']
    turno = request.form['turno']
    horas = request.form.getlist('horas')

    productos_por_vendedor = defaultdict(list)
    for item in cart:
        vendedor_id = db.session.query(Producto.id_vendedor).filter_by(id_producto=item['id']).scalar()
        productos_por_vendedor[vendedor_id].append(item)

    for vendedor_id, items in productos_por_vendedor.items():
        total = sum(item['price']*item['quantity'] for item in items)
        pedido = Pedido(
            id_comprador=current_user.id_usuario,
            id_vendedor=vendedor_id,
            total=total
        )
        db.session.add(pedido)
        db.session.flush() 

        for item in items:
            detalle = DetallePedido(
                id_pedido=pedido.id_pedido,
                id_producto=item['id'],
                cantidad=item['quantity'],
                precio_unitario=item['price'],
                subtotal=item['price'] * item['quantity']
            )
            db.session.add(detalle)

            notificacion = Notificacion(id_vendedor=vendedor_id, id_pedido=pedido.id_pedido)
            db.session.add(notificacion)

    db.session.commit()

    msg = Message(
        "Confirmación de compra",
        sender="UniMarket@gmail.com",
        recipients=[current_user.correo]
    )
    body = f"Hola {current_user.nombre},\nGracias por tu compra en UniMarket.\n\n"
    for item in cart:
        body += f"{item['name']} x {item['quantity']} = ${item['price'] * item['quantity']: .2f}\n"
    body += f"\nTotal: ${sum(item['price']*item['quantity'] for item in cart): .2f}\nTurno: {turno}\nHoras: {','.join(horas)}\n\nGracias por tu compra."
    msg.body = body
    mail.send(msg)

    return "<h1>Compra finalizada con éxito</h1><p>Revisa tu correo para la confirmación de la compra.</p><a href='/'>Volver al inicio</a>"

##-------------------------------------------------------------fin_compra------------------------------------------------------------------
##-------------------------------------------------------------error_404------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404
##-------------------------------------------------------------fin_error_404------------------------------------------------------------------
##-------------------------------------------------------------Rol-------------------------------------------------------------------------------------
@app.route('/choose_role')
def choose_role():
    
    return render_template("Rol.html")
@app.route('/set_rol', methods=['POST'])
def set_rol():
    rol_elegido = int(request.form.get("rol"))
    
    session['rol_elegido'] = rol_elegido
    
    return redirect(url_for('complete_registration'))

##-------------------------------------------------------------fin_Rol------------------------------------------------------------------



if __name__ == '__main__': # depurar proyecto 
   with app.app_context():
        db.create_all()  # Crea las tablas si no existen
   app.run(debug=True)

