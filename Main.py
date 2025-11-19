from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, flash, request, redirect, url_for, Blueprint, jsonify, session
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm import joinedload
from flask_mail import Mail, Message
from mailjet_rest import Client
from itsdangerous import URLSafeTimedSerializer
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
import mercadopago
sdk = mercadopago.SDK(os.getenv('MP_ACCESS_TOKEN'))
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
app = Flask(__name__) 
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,    
    "pool_recycle": 180,      
    "pool_size": 5,
    "max_overflow": 10
}
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
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

app.config['MAIL_SERVER']='in-v3.mailjet.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = '1702071fc3b62a1b32c6f74a66b7bc6d'
app.config['MAIL_PASSWORD'] = '19b0b111b8ff934c3a4646cdc404f2d7'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


##----------------------------------------------------fin_correo-----------------------------------------------------------------------------------
##-----------------------------------------------------google----------------------------------------------------------------------------------------
app.config['GOOGLE_CLIENT_ID'] = "460522583219-pg00bvtl0i6biecghpor9sh1qite5f6a.apps.googleusercontent.com"
app.config['GOOGLE_CLIENT_SECRET'] = "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"
app.config['GOOGLE_DISCOVERY_URL'] = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])
REDIRECT_URI = "https://unimarket-620z.onrender.com/login/google/callback"

##-----------------------------------------------------fin_google------------------------------------------------------------------------------------
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
        redirect_uri=REDIRECT_URI,
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
        redirect_url=REDIRECT_URI,
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
        estado=True, 
        email_confirmado=True
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
login_manager.login_view = 'inicio_sesion'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/inicio_sesion', methods=['GET', 'POST'])
def inicio_sesion():

    if 'intentos' not in session:
        session['intentos'] = 0
        session['bloqueado_hasta'] = None

    if session.get('bloqueado_hasta'):
        try:
            bloqueado = datetime.fromisoformat(session['bloqueado_hasta'])
        except:
            bloqueado = None

        if bloqueado and datetime.now() < bloqueado:
            tiempo_restante = (bloqueado - datetime.now()).seconds
            flash(f"Demasiados intentos fallados. Intenta de nuevo en {tiempo_restante} segundos.", "error")
            return render_template('iniciosesion.html')

   
    if request.method == 'POST':

        
        recaptcha_response = request.form.get('g-recaptcha-response')
        secret_key = "6LfABAksAAAAAFmP6QGGr1-D_LKmAoYFjjQR-ZRP"
        verify_url = "https://www.google.com/recaptcha/api/siteverify"

        payload = {'secret': secret_key, 'response': recaptcha_response}
        r = requests.post(verify_url, data=payload)
        result = r.json()

        if not result.get("success"):
            flash("Por favor verifica que no eres un robot.", "error")
            return redirect(url_for('inicio_sesion'))

        correo = request.form.get('correo')
        password = request.form.get('password')

        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and not usuario.check_password(password):
            flash("Tu cuenta fue creada con Google. Restablece tu contraseña para iniciar sesión manualmente.", "error")
            return redirect(url_for('restablecer_contraseña'))

        if usuario and usuario.check_password(password):

            if not usuario.email_confirmado:
                flash("Debes confirmar tu correo antes de iniciar sesión.", "error")
                return redirect(url_for('inicio_sesion'))

            if not usuario.estado:
                flash("Tu cuenta está deshabilitada. Contáctanos para más información.", "error")
                return redirect(url_for('inicio_sesion'))

            session['intentos'] = 0
            session['bloqueado_hasta'] = None
            login_user(usuario)
            flash("Inicio de sesión exitoso.", "success")

            if usuario.id_rol == 1:
                return redirect(url_for('Admin'))
            if usuario.id_rol == 2:
                return redirect(url_for('vendedor'))
            return redirect(url_for('index'))

        else:
            session['intentos'] += 1

            if session['intentos'] >= 3:
                session['bloqueado_hasta'] = (datetime.now() + timedelta(minutes=1)).isoformat()
                flash("Has excedido el número de intentos. Espera 1 minuto antes de volver a intentar.", "error")
            else:
                intentos_restantes = 3 - session['intentos']
                flash(f"Correo o contraseña incorrectos. Intentos restantes: {intentos_restantes}", "error")

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
            flash("Las contraseñas no coinciden", "error")
            return redirect(url_for('registro'))

        usuario_existente = db.session.scalar(
            db.select(Usuario).where(Usuario.correo == correo)
        )

        if usuario_existente:
            flash("Ese correo electrónico ya está en uso. Por favor, inicia sesión.", "error")
            return redirect(url_for('registro'))

        try:
            nuevo_usuario = Usuario(
                nombre=nombre,
                correo=correo,
                telefono=telefono,
                id_rol=2 if tipo_cuenta == 'vendedor' else 3
            )
            nuevo_usuario.set_password(password)

            db.session.add(nuevo_usuario)
            db.session.commit()

            token = s.dumps(correo, salt='email-confirm')
            confirm_url = url_for('confirmar_correo', token=token, _external=True)

            estado_envio = enviar_correo_confirmacion(
                destinatario=correo, 
                nombre_usuario=nombre, 
                confirm_url=confirm_url
            )

            if estado_envio == 200:
                flash("Registro creado. Revisa tu correo para confirmar la cuenta.", "success")
            else:
                flash("Registro creado, pero hubo un problema al enviar el correo de confirmación.", "error")

            session['usuario_temp_id'] = nuevo_usuario.id_usuario
            return redirect(url_for('choose_role'))


        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear la cuenta: {e}. Por favor, inténtalo de nuevo.", "error")
            return redirect(url_for('registro'))

    return render_template('registro.html')

##-------------------------------------------------------------fin_registro------------------------------------------------------------------

##-------------------------------------------------------------Confirmar correo---------------------------------------------------------------------


s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

API_KEY = os.getenv('MAILJET_API_KEY')
API_SECRET = os.getenv('MAILJET_API_SECRET')
MAILJET_SENDER = os.getenv('MAILJET_SENDER')

mailjet = Client(auth=(API_KEY, API_SECRET), version='v3.1')

mailjet = Client(auth=(API_KEY, API_SECRET), version='v3.1')
def enviar_correo_confirmacion(destinatario, nombre_usuario, confirm_url):
    data = {
      'Messages': [
        {
          "From": {
            "Email": MAILJET_SENDER,
            "Name": "UniMarket Soporte"
          },
          "To": [
            {
              "Email": destinatario,
              "Name": nombre_usuario
            }
          ],
          "Subject": "Confirma tu correo - UniMarket",
          "TextPart": f"Hola {nombre_usuario}, por favor confirma tu correo aquí: {confirm_url}",
          "HTMLPart": f"""
            <h3>Hola {nombre_usuario}!</h3>
            <p>Haz clic en el siguiente enlace para confirmar tu cuenta en UniMarket:</p>
            <a href="{confirm_url}">Confirmar mi cuenta</a>
            <p>Si no solicitaste esto, ignora este correo.</p>
          """
        }
      ]
    }
    try:
        result = mailjet.send.create(data=data)
        return result.status_code
    except Exception as e:
        print(f"Error enviando mailjet: {e}")
        return 500

@app.route('/confirmar/<token>')
def confirmar_correo(token):
    try:
        correo = s.loads(token, salt='email-confirm', max_age= 60*60*24)
    except SignatureExpired:
        flash("El enlace ha expirado. Solicita uno nuevo", "error")
        return redirect(url_for('reenviar_confirmacion'))
    except BadSignature:
        flash("Enlace inválido.", "error")
        return redirect(url_for('inicio_sesion'))

    usuario= Usuario.query.filter_by(correo=correo).first()
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for('registro'))

    if usuario.email_confirmado:
        mensaje = "El correo ya se confirmo. Redirigiendo al inicio de sesion"
    else:
        usuario.email_confirmado = True
        db.session.commit()
        mensaje = "Correo confirmado con éxito. Ya puedes iniciar sesión."
    
    return render_template('correo_confirmacion.html', mensaje=mensaje)

@app.route('/reenviar_confirmacion', methods=['GET', 'POST'])
def reenviar_confirmacion():
    if request.method == 'POST':
        correo = request.form.get('email')
        usuario = Usuario.query.filter_by(correo=correo).first()
        
        if not usuario:
            flash("No existe usuario con ese correo", "error")
            return redirect(url_for('reenviar_confirmacion'))
        
        if usuario.email_confirmado:
            flash("El correo ya está confirmado", "info")
            return redirect(url_for('inicio_sesion'))

        token = s.dumps(correo, salt='email-confirm')
        confirm_url = url_for('confirmar_correo', token=token, _external=True)
        
        estado_envio = enviar_correo_confirmacion(
            destinatario=correo, 
            nombre_usuario=usuario.nombre, 
            confirm_url=confirm_url
        )

        if estado_envio == 200:
            flash("Se ha reenviado el correo de confirmación.", "success")
        else:
            flash("Hubo un problema al enviar el correo.", "error")

        return redirect(url_for('inicio_sesion'))
    
    return render_template('reenviar_confirmacion.html')
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
            estado=True,
            email_confirmado=True

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

    flash(f"Usuario creado correctamente", "success")
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

        password = request.form.get("password")
        confirmar = request.form.get("confirmar")
        if password.strip() != "":
            if password != confirmar:
                flash("Las contraseñas no coinciden", "error")
                return redirect(url_for('Admin'))
                usuario.set_password(password)

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
@app.route('/procesar_compra', methods=['POST'])
@login_required
def procesar_compra():
    cart = json.loads(request.form["cartData"])
    pago = request.form.get("pago")
    turno = request.form.get("turno")
    horas = request.form.getlist("horas")

    if pago == "mercadopago":
        sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

        items_mp = [{
            "title": item["name"],
            "quantity": int(item["quantity"]),
            "unit_price": float(item["price"])
        } for item in cart]

        preference = {
            "items": items_mp,

            "payer": {
                "email": "test_user_123456@testuser.com"
            },

            "back_urls": {
                "success": url_for("compra_exitosa_mp", _external=True),
                "failure": url_for("compra_fallida_mp", _external=True)
            },
            "auto_return": "approved",

            "metadata": {
                "id_usuario": current_user.id_usuario,
                "cart": json.dumps(cart),
                "turno": turno,
                "horas": json.dumps(horas)
            }
        }

        respuesta = sdk.preference().create(preference)

        init_point = respuesta["response"]["init_point"]
        return redirect(init_point)

    productos_por_vendedor = defaultdict(list)
    for item in cart:
        vendedor_id = db.session.query(Producto.id_vendedor)\
                                .filter_by(id_producto=item['id']).scalar()
        productos_por_vendedor[vendedor_id].append(item)

    for vendedor_id, items in productos_por_vendedor.items():
        total = sum(item['price'] * item['quantity'] for item in items)

        pedido = Pedido(
            id_comprador=current_user.id_usuario,
            id_vendedor=vendedor_id,
            total=total,
            metodo_pago=pago
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

            notificacion = Notificacion(
                id_vendedor=vendedor_id,
                id_pedido=pedido.id_pedido
            )
            db.session.add(notificacion)

    db.session.commit()

    estado_envio = enviar_correo_compra(
        destinatario=current_user.correo,
        nombre_usuario=current_user.nombre,
        cart=cart,
        turno=turno,
        horas=horas
    )

    mensaje_envio = "Correo enviado" if estado_envio == 200 else "Error al enviar correo"

    return f"<h1>Compra finalizada</h1><p>{mensaje_envio}</p><a href='/'>Volver</a>"

##-------------------------------------------------------------fin_compra------------------------------------------------------------------
##-------------------------------------------------------------compra_exitosa_mp-------------------------------------------------------------------------
@app.route('/mp/success')
def compra_exitosa_mp():
    return "<h1>Pago aprobado con Mercado Pago</h1>"

@app.route('/mp/failure')
def compra_fallida_mp():
    return "<h1>El pago no se completó</h1>"
##-------------------------------------------------------------fin_compra_exitosa_mp------------------------------------------------------------------
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

    mensaje = session.pop('mensaje_confirmacion', "Registro completado correctamente.")

    return render_template("correo_confirmacion.html", mensaje=mensaje)


##-------------------------------------------------------------fin_Rol------------------------------------------------------------------

@app.route('/test_mailjet')
def test_mailjet():
    destinatario = 'dzgarcia10@gmail.com'  
    nombre_usuario = 'Prueba'
    confirm_url = 'https://unimarket-620z.onrender.com/test_mailjet'  
    
    estado_envio = enviar_correo_confirmacion(destinatario, nombre_usuario, confirm_url)
    
    if estado_envio == 200:
        return "Correo de prueba enviado correctamente"
    else:
        return f"Error enviando correo: {estado_envio}"



if __name__ == '__main__': # depurar proyecto 
   with app.app_context():
        db.create_all()  
        app.run(host='0.0.0.0', port=5000)



