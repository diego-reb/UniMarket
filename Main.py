from flask import Flask, render_template, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy 
from src.conn import db, init_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user 
from models.Usuario import Usuario
from models.Rol import Rol

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
        print("Formulario recibido:")
        print(request.form)
        correo = request.form['correo']
        password = request.form['password']
        id_rol = int(request.form['id_rol'])

        usuario = Usuario.query.filter_by(correo=correo, id_rol=id_rol).first()
        print("Usuario encontrado:", usuario)

        if usuario and usuario.check_password(password):
            if usuario.estado:
                login_user(usuario)
                flash("Inicio de sesion exitoso")
                print("login Excitoso")
                return redirect(url_for('index'))
            else:
                flash("Cuenta deshabilitada, contactanos")
                print("cuenta sin habilitar")
        else:
            flash("Correo o contraseña incorrectos")
            print("login_fallado")
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

if __name__ == '__main__': ##depurar proyecto 
   with app.app_context():
        db.create_all()  # Crea las tablas si no existen
   app.run(debug=True)

