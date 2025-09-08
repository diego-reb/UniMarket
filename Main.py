from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from src.conn import get_connection ##importe la conexion a la bd

app = Flask(__name__) ##iniciar proyecto
app.secret_key = 'contraseña_secreta'


##---------------------------------------------------test------------------------------------------------------------------------------------------
@app.route('/test')
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        version = cur.fetchone()
        cur.close()
        conn.close()
        return f"Conectada a la base de datos"
    except Exception as e:
        return f"Error de conexion: {e}"

##-----------------------------------------------------fin_test--------------------------------------------------------------------------------
if __name__ == '__main__': ##depurar proyecto 
    app.run(debug=True) ## ejecutar proyecto

