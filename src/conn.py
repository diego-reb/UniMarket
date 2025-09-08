import psycopg2

def get_connection():
    conn=psycopg2.connect(
        dbname="SaborLocal",
        user="postgres",
        password="admin",
        host="Localhost"
    )
    return conn