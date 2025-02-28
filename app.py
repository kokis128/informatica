from flask import Flask, request, render_template, redirect, url_for, session
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = "supersecreto"  # Clave para las sesiones

# Función para obtener una conexión a la base de datos
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin",
        database="informatica"
    )

# Función para registrar un usuario con contraseña hasheada
def register_user(username, password):
    db = get_db_connection()
    cursor = db.cursor()

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                       (username, hashed_password.decode('utf-8')))
        db.commit()
        return "Usuario registrado con éxito"
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        db.close()

# Función para verificar credenciales
def verify_user(username, password):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[0].encode('utf-8')):
        return True
    return False

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if verify_user(username, password):
        session['user'] = username  # Guardar usuario en sesión
        return redirect(url_for('index'))
    else:
        return "Credenciales incorrectas"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        return register_user(username, password)
    return render_template('register.html')

@app.route('/service')
def index():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)  # Para obtener un diccionario en vez de tuplas
    cursor.execute("""
        SELECT s.*, p.nombre, p.curso, p.division 
        FROM servicios s 
        JOIN propietarios p ON s.propietario_id = p.id
    """)
    servicios = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template('service.html', servicios=servicios)

@app.route('/registrar', methods=['POST'])
def registrar():
    if 'user' not in session:
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    curso = request.form.get('curso', None)
    division = request.form.get('division', None)
    tipo_dispositivo = request.form['tipo_dispositivo']
    servicio_realizado = request.form['servicio_realizado']
    usuario_registro = session['user']

    db = get_db_connection()
    cursor = db.cursor()

    # Verificar si el propietario ya existe
    cursor.execute("SELECT id FROM propietarios WHERE nombre = %s", (nombre,))
    propietario = cursor.fetchone()

    if not propietario:
        cursor.execute("INSERT INTO propietarios (nombre, curso, division) VALUES (%s, %s, %s)", 
                       (nombre, curso, division))
        db.commit()
        propietario_id = cursor.lastrowid  # Obtener el ID recién insertado
    else:
        propietario_id = propietario[0]

    # Insertar el servicio
    cursor.execute("""
        INSERT INTO servicios (propietario_id, usuario_registro, tipo_dispositivo, servicio_realizado, estado)
        VALUES (%s, %s, %s, %s, 'pendiente')
    """, (propietario_id, usuario_registro, tipo_dispositivo, servicio_realizado))
    
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('index'))

@app.route('/actualizar_estado/<int:id>', methods=['POST'])
def actualizar_estado(id):
    estado = request.form['estado']

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE servicios SET estado = %s WHERE id = %s", (estado, id))
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
