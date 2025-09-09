from flask import Flask, render_template, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy##importe la conexion a la bd
from src.conn import db, init_app
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
@app.route('/inicio_sesion')
def inicio_sesion():
    return render_template('iniciosesion.html')
##-----------------------------------fin_inicio_sesion-----------------------------------------------------------------------------------------------
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

