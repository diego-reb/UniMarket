from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

import paypalrestsdk
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
import traceback
import cloudinary
import cloudinary.uploader
import cloudinary.api
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com" 
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
app = Flask(__name__) 
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,    
    "pool_recycle": 180,      
    "pool_size": 5,
    "max_overflow": 10
}
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
app.secret_key = 'contraseña_secreta'
init_app(app)


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

UNIBOT_TRAINING = """
Eres UniBot, el asistente de soporte de inteligencia artificial del portal UniMarket, el mercado exclusivo para la comunidad del ITIZ. Tu rol es **ESTRICTO Y LIMITADO**: proporcionar información precisa ÚNICAMENTE sobre las políticas, mecánicas, productos y funcionalidades de la plataforma UniMarket. Sé amigable, conciso y utiliza los siguientes 'guiones' de respuesta para asegurar la coherencia:

---
**BASE DE CONOCIMIENTO (NARRATIVAS DE RESPUESTA):**

**1. Proceso de Registro e Inicio de Sesión (Disparadores: "¿Cómo me registro?", "Quiero crear una cuenta", "¿Cómo entro?"):**
"¡Bienvenido a la comunidad UniMarket! Para comenzar, debes saber que existen dos roles principales. Sigue estos pasos según tu objetivo:
Para Compradores:
1. Selecciona la opción 'Registrarse' y elige el perfil de 'Comprador'. Puedes hacerlo manualmente o vincular tu cuenta Google.
2. Si es manual, ingresa tu correo institucional del ITIZ (es obligatorio) y verifica tu cuenta aceptando el correo de verificación.
Para Vendedores:
1. Elige el perfil de 'Vendedor' al registrarte y completa tus datos.
2. Esto te dará acceso inmediato a tu Dashboard de ventas.
🛡️ Nota de Seguridad: Todos los inicios de sesión están protegidos con reCAPTCHA para evitar bots."

**2. Proceso de Compra (Para Compradores) (Disparadores: "¿Cómo compro algo?", "Pasos para comprar", "Hacer un pedido"):**
"¡Comprar en UniMarket es muy fácil! Aquí tienes la ruta completa:
1. Explora: Navega por las categorías o usa el buscador.
2. Selecciona: Agrega los productos que desees a tu carrito.
3. Revisa: Ve a tu carrito y verifica el total.
4. Programa la Entrega: Elige una fecha (próximos 5 días hábiles), un horario (Matutino: 7 am a 1 pm o Vespertino: 2 pm a 8 pm) y el punto de entrega dentro del campus.
5. Paga: Selecciona tu método de pago (**Mercado Pago** o **Efectivo**) y confirma.
¡Listo! Recibirás una confirmación inmediata."

**3. Proceso de Venta y Publicación (Para Vendedores) (Disparadores: "¿Cómo vendo un producto?", "Quiero publicar un artículo", "Subir productos"):**
"¡Genial que quieras emprender! Para publicar tu primer producto:
1. Entra a tu cuenta y ve a tu Dashboard de Vendedor.
2. Haz clic en 'Agregar productos'.
3. Llena los detalles clave (Nombre, Descripción, Precio, Stock, Imagen).
4. Dale a 'Publicar' y tu producto aparecerá instantáneamente en el catálogo general.
Desde ahí también podrás gestionar tu inventario."

**4. Política de Envíos y Entregas (Disparadores: "¿Dónde entregan?", "¿A qué hora puedo recoger?", "Puntos de entrega"):**
"Para garantizar la seguridad y el orden, las entregas se realizan exclusivamente dentro del campus del ITIZ.
📍 **Puntos de Encuentro Oficiales (Entrega y Devolución):**
- La Entrada (Torniquetes de entrada)
- Cafetería
- Duela
- Prefectura o Dirección (Administración)
⏰ **Horarios Disponibles (Entregas y Devoluciones):**
- Matutino: 7:00 am - 1:00 pm (intervalos de 1 hora entre entregas).
- Vespertino: 2:00 pm - 8:00 pm.
Tú eliges la combinación de lugar y hora al momento de la compra."

**5. Cancelaciones y Devoluciones (Disparadores: "Quiero cancelar mi pedido", "No me gustó el producto", "¿Puedo devolver algo?"):**
"Entendemos que los planes cambian. Aquí están las reglas para proteger a ambas partes:
**Para Cancelar:**
- ✅ **SÍ puedes:** Si faltan más de **36 horas** para la hora de entrega pactada.
- ❌ **NO puedes:** Si faltan menos de 36 horas.
**Para Devoluciones:**
- Tienes hasta **3 días** después de la entrega para solicitarla.
- Debes contactar directamente al vendedor y coordinar la devolución en uno de los puntos y horarios oficiales mencionados arriba."

**6. Penalizaciones (Sistema de No-Show) (Disparadores: "¿Qué pasa si no recojo mi pedido?", "No llegué a la entrega", "Consecuencias"):**
"Es muy importante respetar el tiempo de los demás. Si no te presentas a recibir tu pedido (**No-Show**), el sistema aplica suspensiones temporales automáticas:
- 🟡 **1ª Falta:** Suspensión de cuenta por **12 horas**.
- 🟠 **2ª Falta:** Suspensión de cuenta por **24 horas** (12 + 12).
- 🔴 **3ª Falta:** Suspensión de cuenta por **36 horas** (24 + 12), y así sucesivamente.
¡Evita esto cancelando con tiempo (36 horas antes) si sabes que no podrás asistir!"

**7. Métodos de Pago y Seguridad (Disparadores: "¿Es seguro?", "¿Cómo pago?", "Formas de pago"):**
"Tu seguridad es nuestra prioridad en UniMarket.
💳 **Métodos de Pago:** Aceptamos **Mercado Pago** para transacciones digitales y también pagos en **Efectivo** (contra entrega).
🛡️ **Seguridad:** Tus datos personales están ocultos, las cuentas están verificadas con correo institucional y monitoreamos para evitar bots."

**8. Sobre UniBot (Capacidades) (Disparadores: "¿Quién eres?", "¿Qué haces?", "¿Me puedes ayudar con mi tarea?"):**
"Soy UniBot, tu asistente personal dentro de UniMarket 🤖. Puedo ayudarte a: explicar cómo registrarte, comprar o vender; aclarar dudas sobre horarios, puntos de entrega y políticas; y guiarte si tienes problemas con la plataforma. **Lo que NO hago:** No tengo información sobre temas externos al ITIZ o a UniMarket, incluyendo tareas o información académica general."

**8. Productos (Disparadores: "¿Que productos puedo vender?", "¿Qué productos existen?", "¿Cuales categorias hay?"):**
"En Unimarket contamos con varias categorias, para la compra y venta estudiantil, entre las existentes son Maquillaje, comida, Ropa, Dulceria, los cuales mientras cuentes ya con un registro con nosotros puedes comprar o vender"

**9. Productos (Disparadores: "¿Qué productos puedo vender?", "¿Qué productos existen?", "¿Cuales categorías hay?", "¿Puedo vender maquillaje?", "¿Dónde compro uniformes?", "¿Hay snacks?", "¿Tienen sudaderas?", "¿Qué tipo de comida venden?", Maquillaje, comida, dulces, accesorios, lapices, categorias)**
"¡Claro! En Unimarket tenemos una amplia variedad de categorías para la compra y venta de productos entre estudiantes.

🛍️ Nuestras categorías principales son:

Maquillaje: (Paletas de sombras, labiales, bases, etc.)

Comida: (Platillos caseros, almuerzos, postres, etc.)

Ropa: (Uniformes, sudaderas, camisetas, accesorios)

Dulcería: (Snacks, bebidas, caramelos, chocolates)

Para poder comprar o vender cualquiera de estos artículos, solo necesitas contar con un registro activo en nuestra plataforma."
---
**REGLA DE RESTRICCIÓN ESTRICTA (IMPERATIVA):**

Si la pregunta del usuario es sobre un tema que **NO** está cubierto por estas narrativas o la BASE DE CONOCIMIENTO (ej: información académica, noticias, problemas personales), **DEBES RESPONDER EXCLUSIVAMENTE**:

> **"Lo siento, mi función es estrictamente asistirte con preguntas sobre el mercado universitario UniMarket y sus políticas de venta/entrega. No tengo información sobre ese tema."**

**Pregunta del usuario a responder:** 
"""

@app.route('/api/chat', methods=['POST'])
def chat_api():
    import time
    import re

    data = request.json
    user_message = data.get("message")
    chat_history = data.get("history", [])

    if not user_message:
        return jsonify({"reply": "⚠️ El mensaje está vacío."}), 400

    
    unimarket_keywords = [
        'registro', 'registrarse', 'cuenta', 'login', 'inicio de sesión', 'sesión', 'perfil', 
        'comprador', 'vendedor', 'dashboard', 'verificación', 'captcha',
        
        'comprar', 'compra', 'pedido', 'orden', 'carrito', 'agregar', 'pagar', 
        'método de pago', 'mercadopago', 'efectivo', 'entrega', 'horario',
        
        'vender', 'venta', 'publicar', 'producto', 'subir', 'inventario', 'stock',
        
        'producto', 'productos', 'categoría', 'categorías', 'maquillaje', 'comida',
        'ropa', 'dulcería', 'snacks', 'uniformes', 'sudaderas', 'accesorios',
        
        'entrega', 'entregar', 'punto de entrega', 'horario', 'matutino', 'vespertino',
        'cafetería', 'duela', 'prefectura', 'dirección', 'torniquetes',
        
        'cancelación', 'cancelar', 'devolución', 'devolver', 'política', 'términos',
        'suspensión', 'penalización', 'no-show', 'falta', 'seguridad',
        
        'unimarket', 'plataforma', 'funcionamiento', 'cómo funciona', 'ayuda',
        'soporte', 'asistente', 'unibot', 'chatbot', 'itiz', 'campus'
    ]
    
    message_lower = user_message.lower()
    message_lower = re.sub(r'[^\w\sáéíóúüñ]', '', message_lower)
    
    is_unimarket_related = any(keyword in message_lower for keyword in unimarket_keywords)
    
    if not is_unimarket_related:
        return jsonify({
            "reply": "Lo siento, mi función es estrictamente asistirte con preguntas sobre el mercado universitario UniMarket y sus políticas de venta/entrega. No tengo información sobre ese tema."
        })

    MODEL_NAME = "gemini-2.5-flash"
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        return jsonify({"reply": "⚠️ No se encontró la clave del chatbot."}), 500

    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

    prompt = f"""
    {UNIBOT_TRAINING}
    
    Pregunta del usuario: {user_message}
    
    Recuerda: Si la pregunta NO está cubierta por la base de conocimiento, responde EXCLUSIVAMENTE:
    "Lo siento, mi función es estrictamente asistirte con preguntas sobre el mercado universitario UniMarket y sus políticas de venta/entrega. No tengo información sobre ese tema."
    """
    
    payload = {
        "contents": chat_history + [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500
        }
    }

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(API_URL, json=payload, timeout=15)
            response.raise_for_status()
            result = response.json()

            reply = "⚠️ El chatbot no pudo generar una respuesta en este momento."
            candidates = result.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    reply = parts[0].get("text", reply)

            return jsonify({"reply": reply})

        except requests.exceptions.RequestException as e:
            print(f"Intento {attempt+1} fallido:", e)
            if attempt < max_retries:
                time.sleep(2)
            else:
                return jsonify({"reply": "⚠️ Lo siento, no se pudo conectar con el chatbot. Intenta más tarde."}), 500

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
        session['nuevo_usuario'] = {
            "nombre": nombre,
            "correo": correo,
            "telefono": '',
        }
        session['correo_google'] = correo  
        session['nombre_google'] = nombre
        return redirect(url_for('choose_role'))  


    login_user(usuario)
    flash("Inicio de sesión exitoso con Google", "login")

    if usuario.id_rol == 1:
        return redirect(url_for('Admin'))
    elif usuario.id_rol == 2:
        return redirect(url_for('vendedor'))
    else:
        return redirect(url_for('index'))

@app.route('/choose_role')
def choose_role():
    if 'nuevo_usuario' not in session:
        return redirect(url_for('index'))
    return render_template('Rol.html')  

@app.route('/set_rol', methods=['POST'])
def set_rol():
    if 'nuevo_usuario' not in session:
        return redirect(url_for('index'))
    
    rol = request.form.get('rol')
    
    if rol not in ['2', '3']: 
        flash("Rol inválido", "error")
        return redirect(url_for('choose_role'))
    
    session['rol_elegido'] = int(rol)
    return redirect(url_for('complete_registration'))

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

    # Clean up session
    session.pop('nuevo_usuario', None)
    session.pop('rol_elegido', None)
    session.pop('correo_google', None)
    session.pop('nombre_google', None)

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
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("name")
        correo = request.form.get("email")
        telefono = request.form.get("phone")
        password = request.form.get("password")
        confirm_pass = request.form.get("confirm-password")
        tipo_cuenta = request.form.get("tipo")  # Comprador o Vendedor

        if not tipo_cuenta:
            flash("Debes seleccionar un tipo de cuenta (Comprador o Vendedor).")
            return redirect(url_for("registro"))

        if password != confirm_pass:
            flash("Las contraseñas no coinciden.")
            return redirect(url_for("registro"))

        correo_existente = db.session.scalar(
            db.select(Usuario).where(Usuario.correo == correo)
        )
        if correo_existente:
            flash("El correo ya está registrado.")
            return redirect(url_for("registro"))

        rol_obj = db.session.scalar(
            db.select(Rol).where(Rol.nombre.ilike(tipo_cuenta))
        )

        if not rol_obj:
            flash("Error: El rol seleccionado no existe en la base de datos.")
            return redirect(url_for("registro"))

        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            password=generate_password_hash(password),
            id_rol=rol_obj.id_rol,
            estado=True,
            email_confirmado=False,
            intentos=0,
            bloqueo_hasta=None
        )

        try:
            db.session.add(nuevo_usuario)
            db.session.commit()

            # 🔥 ENVIAR CORREO DESPUÉS DEL COMMIT
            token = s.dumps(correo, salt='email-confirm')
            confirm_url = url_for('confirmar_correo', token=token, _external=True)

            enviar_correo_confirmacion(
                destinatario=correo,
                nombre_usuario=nombre,
                confirm_url=confirm_url
            )

            flash("Cuenta creada correctamente. Revisa tu correo para verificar tu cuenta.")
            return redirect(url_for("inicio_sesion"))


        except Exception as e:
            db.session.rollback()
            print("Error al registrar usuario:", e)
            flash("Ocurrió un error al crear la cuenta. Intenta nuevamente.")
            return redirect(url_for("registro"))

    return render_template("registro.html")


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
                "From": {"Email": MAILJET_SENDER, "Name": "UniMarket Soporte"},
                "To": [{"Email": destinatario, "Name": nombre_usuario}],
                "Subject": "Confirma tu correo - UniMarket",
                "HTMLPart": f"""
                    <h3>Hola {nombre_usuario}!</h3>
                    <p>Haz clic en el siguiente enlace para confirmar tu cuenta:</p>
                    <a href="{confirm_url}">Confirmar mi cuenta</a>
                """
            }
        ]
    }
    try:
        result = mailjet.send.create(data=data)
        return result.status_code

    except Exception as e:
        print("ERROR MAILJET:", e)
        return 500

@app.route("/confirmar/<token>")
def confirmar_correo(token):
    try:
        correo = s.loads(token, salt="email-confirm", max_age=60*60*24)
    except SignatureExpired:
        flash("El enlace ha expirado.", "error")
        return redirect(url_for("reenviar_confirmacion"))
    except BadSignature:
        flash("Token inválido.", "error")
        return redirect(url_for("login"))

    usuario = Usuario.query.filter_by(correo=correo).first()
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("registro"))

    if usuario.email_confirmado:
        mensaje = "Tu correo ya estaba confirmado."
    else:
        usuario.email_confirmado = True
        db.session.commit()
        mensaje = "Correo confirmado exitosamente."

    return render_template("correo_confirmacion.html", mensaje=mensaje)

@app.route("/reenviar_confirmacion", methods=["GET", "POST"])
def reenviar_confirmacion():
    if request.method == "POST":
        correo = request.form.get("email")
        usuario = Usuario.query.filter_by(correo=correo).first()
        if not usuario:
            flash("Correo no registrado.", "error")
            return redirect(url_for("reenviar_confirmacion"))

        token = s.dumps(correo, salt='email-confirm')
        confirm_url = url_for('confirmar_correo', token=token, _external=True)

        enviar_correo_confirmacion(
            destinatario=correo,
            nombre_usuario=usuario.nombre,
            confirm_url=confirm_url
        )

        flash("Correo reenviado. Revisa tu bandeja de entrada.", "success")
        return redirect(url_for("login"))

    return render_template("reenviar_confirmacion.html")
    
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

    

    return render_template('usuariosadmin.html',usuarios=usuarios,productos=productos,rol=rol, vendedores=vendedores,categorias=categorias)

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
    foto_url = None
    if foto_file:
        upload_result = cloudinary.uploader.upload(foto_file)
        foto_url = upload_result.get("secure_url")

    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock,
        id_vendedor=id_vendedor,
        foto=foto_url,
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
        if foto_file:
            upload_result = cloudinary.uploader.upload(foto_file)
            producto.foto = upload_result.get("secure_url")

        db.session.commit()
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('Admin'))

    usuarios = Usuario.query.all()
    rol = Rol.query.all()
    productos = Producto.query.all()
    vendedores = Usuario.query.filter_by(id_rol=2).all()  
    categorias = Categoria.query.all()

    return render_template('usuariosadmin.html',usuarios=usuarios,rol=rol,productos=productos,vendedores=vendedores,categorias=categorias,producto_editar=producto)

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
            upload_result = cloudinary.uploader.upload(foto)
            producto.foto = upload_result.get("secure_url")

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

    foto = request.files.get('foto')
    foto_path = None

    if foto:
        upload_result = cloudinary.uploader.upload(foto)
        foto_path = upload_result.get("secure_url")



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
@app.route('/api/chat_vendedor', methods=['POST'])
def chat_api_vendedor():
    import time
    import requests
    import os
    import json
    from flask import request, jsonify

    data = request.json
    user_message = data.get("message")
    history = data.get("history", [])
    
    if not user_message and history:
        for msg in reversed(history):
            if msg.get("role") == "user" and msg.get("parts"):
                user_message = msg["parts"][0].get("text", "")
                break
    
    if not user_message or user_message.strip() == "":
        return jsonify({"reply": "⚠️ No se recibió un mensaje válido."}), 400

    MODEL_NAME = "gemini-2.5-flash"
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        return jsonify({"reply": "⚠️ No se encontró la clave del chatbot."}), 500

    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

    SYSTEM_PROMPT = """Eres UniBot, el asistente especializado para vendedores de UniMarket. 
    Tu función es ayudar EXCLUSIVAMENTE con:
    1. Agregar productos
    2. Editar productos  
    3. Eliminar productos
    4. Gestionar pedidos pendientes
    5. Marcar pedidos como entregados
    6. Ver historial de ventas
    7. Navegación en el dashboard
    
    Si te preguntan sobre temas NO relacionados con el dashboard de vendedor, responde:
    "Lo siento, mi función es estrictamente asistirte con preguntas sobre tu panel de vendedor de UniMarket (gestión de productos y pedidos). No tengo información sobre ese tema."
    
    Sé conciso y útil."""

    messages = []
    
    messages.append({"role": "user", "parts": [{"text": SYSTEM_PROMPT}]})
    messages.append({"role": "model", "parts": [{"text": "Entendido. Soy UniBot, asistente para vendedores de UniMarket. ¿En qué puedo ayudarte hoy?"}]})
    if history:
        for msg in history:
            if msg.get("role") == "user" and msg.get("parts"):
                messages.append({"role": "user", "parts": [{"text": msg["parts"][0].get("text", "")}]})
            elif msg.get("role") == "model" and msg.get("parts"):
                messages.append({"role": "model", "parts": [{"text": msg["parts"][0].get("text", "")}]})
    
    messages.append({"role": "user", "parts": [{"text": user_message}]})
    
    payload = {
        "contents": messages,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500
        }
    }

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(API_URL, json=payload, timeout=15)
            response.raise_for_status()
            result = response.json()

            reply = "⚠️ El chatbot no pudo generar una respuesta en este momento."
            candidates = result.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    reply = parts[0].get("text", reply).strip()

            return jsonify({"reply": reply})

        except requests.exceptions.RequestException as e:
            print(f"Intento {attempt+1} fallido:", e)
            if attempt < max_retries:
                time.sleep(2)
            else:
                return jsonify({"reply": "⚠️ Lo siento, no se pudo conectar con el chatbot. Intenta más tarde."}), 500

##-------------------------------------------------------------fin_vendedor------------------------------------------------------------------
##-------------------------------------------------------------comprador-------------------------------------------------------------------------------------
def get_paypal_access_token():
    """
    Obtiene un token de acceso de PayPal para autenticar las llamadas a la API.
    """
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        print("ERROR: PAYPAL_CLIENT_ID o PAYPAL_CLIENT_SECRET no están configurados.")
        return None
        
    auth_url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"  # URL corregida
    
    try:
        response = requests.post(
            auth_url,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            },
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            data={'grant_type': 'client_credentials'}
        )
        response.raise_for_status() 
        data = response.json()
        print(f"✅ Token de acceso obtenido exitosamente")
        return data.get('access_token')
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener el token de PayPal: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Respuesta de error: {e.response.text}")
        return None

@app.route('/compra')
@login_required
def comprador():
    return render_template('compra.html', paypal_client_id=PAYPAL_CLIENT_ID)

@app.route('/create-order', methods=['POST'])
@login_required
def create_order():
    """
    Ruta llamada por el frontend para crear una orden de PayPal.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
            
        total_amount = data.get('total', '10.00')

        # Validar que el total sea un número válido
        try:
            amount_float = float(total_amount)
            if amount_float <= 0:
                return jsonify({'error': 'El monto debe ser mayor a 0'}), 400
        except ValueError:
            return jsonify({'error': 'Monto inválido'}), 400

        print(f"🔄 Creando orden de PayPal por: ${total_amount}")

        access_token = get_paypal_access_token()
        if not access_token:
            return jsonify({'error': 'No se pudo autenticar con PayPal. Verifica tus credenciales.'}), 500

        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "USD", 
                    "value": total_amount
                },
                "description": "Compra en UniMarket"
            }],
            "application_context": {
                "brand_name": "UniMarket",
                "return_url": url_for('pago_exitoso', _external=True),
                "cancel_url": url_for('comprador', _external=True)
            }
        }

        create_url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"
        
        print(f"📤 Enviando solicitud a PayPal...")
        response = requests.post(
            create_url,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
            },
            json=order_data,
            timeout=30
        )
        
        if response.status_code != 201:
            error_detail = response.json() if response.content else 'Sin detalles'
            print(f"❌ Error PayPal API: {response.status_code} - {error_detail}")
            return jsonify({'error': f'Error de PayPal: {response.status_code}'}), 500
            
        order = response.json()
        print(f"✅ Orden creada exitosamente - ID: {order.get('id')}")
        
        return jsonify(order), 201
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión con PayPal: {e}")
        return jsonify({'error': 'Error de conexión con PayPal'}), 500
    except Exception as e:
        print(f"❌ Error inesperado en create-order: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/capture-order', methods=['POST'])
@login_required
def capture_order():
    """
    Ruta llamada por el frontend para capturar el pago de PayPal.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
            
        order_id = data.get('orderID')

        if not order_id:
            return jsonify({'error': 'ID de orden faltante'}), 400

        print(f"🔄 Capturando orden PayPal: {order_id}")

        access_token = get_paypal_access_token()
        if not access_token:
            return jsonify({'error': 'No se pudo autenticar con PayPal'}), 500
        
        capture_url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture"
        
        print(f"📤 Enviando captura a PayPal...")
        response = requests.post(
            capture_url,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
            },
            timeout=30
        )
        
        if response.status_code != 201:
            error_detail = response.json() if response.content else 'Sin detalles'
            print(f"❌ Error PayPal Capture: {response.status_code} - {error_detail}")
            return jsonify({'error': f'Error al procesar pago: {response.status_code}'}), 500
            
        capture_data = response.json()

        # Aquí puedes guardar la información de la transacción en tu BD
        if capture_data.get('status') == 'COMPLETED':
            print(f"✅ Pago COMPLETADO - ID: {capture_data['id']}")
            # Guardar en base de datos, enviar email, etc.
            
        return jsonify(capture_data)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión al capturar orden: {e}")
        return jsonify({'error': 'Error al procesar el pago'}), 500
    except Exception as e:
        print(f"❌ Error inesperado en capture-order: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/pago-exitoso')
@login_required
def pago_exitoso():
    """Página de éxito después del pago"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pago Exitoso - UniMarket</title>
        <style>
            body { font-family: Arial, sans-serif; background: #0f172a; color: #e5e7eb; padding: 40px; text-align: center; }
            .container { max-width: 500px; margin: 100px auto; background: #111827; padding: 40px; border-radius: 16px; }
            .success { color: #22c55e; font-size: 48px; margin-bottom: 20px; }
            .btn { background: #22c55e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✓</div>
            <h1>¡Pago Completado Exitosamente!</h1>
            <p>Tu compra ha sido procesada correctamente.</p>
            <a href="/" class="btn">Volver a Comprar</a>
        </div>
    </body>
    </html>
    """

@app.route('/procesar_compra', methods=['POST'])
@login_required
def procesar_compra():
    """
    Procesa compras con otros métodos de pago (no PayPal)
    """
    try:
        cart_data = request.form.get('cartData')
        metodo_pago = request.form.get('pago')
        turno = request.form.get('turno')
        horas = request.form.getlist('horas')
        
        print(f"✅ Procesando compra con {metodo_pago}")
        print(f"📅 Turno: {turno}")
        print(f"⏰ Horas: {horas}")
        print(f"🛒 Carrito: {cart_data}")
        
        # Aquí procesas la compra según el método de pago
        # Guardar en base de datos, etc.
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Compra Exitosa - UniMarket</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #0f172a; color: #e5e7eb; padding: 40px; text-align: center; }}
                .container {{ max-width: 500px; margin: 100px auto; background: #111827; padding: 40px; border-radius: 16px; }}
                .success {{ color: #22c55e; font-size: 48px; margin-bottom: 20px; }}
                .btn {{ background: #22c55e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✓</div>
                <h1>¡Compra Procesada Exitosamente!</h1>
                <p>Método de pago: {metodo_pago.title()}</p>
                <p>Tu pedido ha sido recibido y está siendo procesado.</p>
                <a href="/compra" class="btn">Volver a Comprar</a>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        print(f"❌ Error en procesar_compra: {e}")
        return "Error al procesar la compra", 500

# Ruta para verificar la configuración
@app.route('/config')
def config():
    """Ruta para verificar la configuración de PayPal"""
    config_info = {
        'paypal_client_id_set': bool(PAYPAL_CLIENT_ID),
        'paypal_client_secret_set': bool(PAYPAL_CLIENT_SECRET),
        'paypal_base_url': PAYPAL_BASE_URL
    }
    return jsonify(config_info)
##-------------------------------------------------------------fin_comprador------------------------------------------------------------------

##-------------------------------------------------------------error_404------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404
##-------------------------------------------------------------fin_error_404------------------------------------------------------------------


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



