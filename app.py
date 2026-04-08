from flask import Flask, render_template, request, redirect, url_for
from flask import jsonify
import psycopg2
import requests
import os

FACTILIZA_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MDQxNSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6ImNvbnN1bHRvciJ9.YLU3smsbaMKFGSz-PccnOZIJQszi_WZNKfFD-P5vGQI'

app = Flask(__name__, template_folder='templates')

# Configuración de la base de datos
DB_HOST = 'dpg-d7bbofpr0fns73b1hv2g-a.oregon-postgres.render.com'
DB_NAME = 'db_personas_zzlo'
DB_USER = 'db_personas_zzlo_user'
DB_PASSWORD = 'BOfDe6sv6nJHUPMgWOdHfBETrHJoluZD'


def conectar_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
        return conn
    except psycopg2.Error as e:
        print("Error al conectar a la base de datos:", e)


def crear_persona(dni, nombre, apellido, direccion, telefono):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO personas (dni, nombre, apellido, direccion, telefono) VALUES (%s, %s, %s, %s, %s)",
                   (dni, nombre, apellido, direccion, telefono))
    conn.commit()
    conn.close()

def obtener_registros():
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM personas order by apellido")
    registros = cursor.fetchall()
    conn.close()
    return registros

@app.route('/consultar_dni/<dni>')
def consultar_dni(dni):
    try:
        response = requests.get(
            f'https://api.factiliza.com/v1/dni/info/{dni}',
            headers={'Authorization': f'Bearer {FACTILIZA_TOKEN}'}
        )
        data = response.json()
        if data.get('success'):
            info = data['data']
            return jsonify({
                'success': True,
                'nombres': info.get('nombres', ''),
                'apellido_paterno': info.get('apellido_paterno', ''),
                'apellido_materno': info.get('apellido_materno', ''),
                'direccion': info.get('direccion_completa', '')
            })
        return jsonify({'success': False, 'message': 'DNI no encontrado'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    dni = request.form['dni']
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    direccion = request.form['direccion']
    telefono = request.form['telefono']
    crear_persona(dni, nombre, apellido, direccion, telefono)
    mensaje_confirmacion = "Registro Exitoso"
    return redirect(url_for('index', mensaje_confirmacion=mensaje_confirmacion))

@app.route('/administrar')
def administrar():
    registros=obtener_registros()
    return render_template('administrar.html',registros=registros)

@app.route('/editar/<dni>')
def editar(dni):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM personas WHERE dni = %s", (dni,))
    registro = cursor.fetchone()
    conn.close()
    return render_template('editar.html', registro=registro)

@app.route('/actualizar/<dni>', methods=['POST'])
def actualizar(dni):
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    direccion = request.form['direccion']
    telefono = request.form['telefono']
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE personas SET nombre=%s, apellido=%s, direccion=%s, telefono=%s WHERE dni=%s",
                   (nombre, apellido, direccion, telefono, dni))
    conn.commit()
    conn.close()
    return redirect(url_for('administrar'))

@app.route('/eliminar/<dni>', methods=['POST'])
def eliminar_registro(dni):
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
    cursor=conn.cursor()
    cursor.execute("DELETE FROM personas WHERE dni = %s", (dni,))
    conn.commit()
    conn.close()
    return redirect(url_for('administrar'))

if __name__ == '__main__':
    #Esto es nuevo
    port = int(os.environ.get('PORT',5000))    
    app.run(host='0.0.0.0', port=port, debug=True)
