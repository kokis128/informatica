from flask import Flask, request, render_template, redirect, url_for, session,jsonify
import mysql.connector
import bcrypt
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecreto"  # Clave para las sesiones

# Función para obtener una conexión a la base de datos
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
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
        SELECT s.*, p.nombre, p.curso, p.division, p.dni
        FROM servicios s 
        JOIN propietarios p ON s.propietario_id = p.id order by fecha_entrada desc
        
    """)
    servicios = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template('service.html', servicios=servicios)

from flask import flash  # Importar flash para enviar mensajes



@app.route('/registrar', methods=['POST'])
def registrar():
    if 'user' not in session:
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    curso = request.form.get('curso')
    division = request.form.get('division')
    dni = request.form.get('dni')
    tipo_dispositivo = request.form['tipo_dispositivo']
    numero_serie=request.form['numero_serie']
    servicio_realizado = request.form['servicio_realizado']
    usuario_registro = session['user']

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Buscar si el propietario ya existe por DNI
    cursor.execute("SELECT id, nombre FROM propietarios WHERE dni = %s", (dni,))
    propietario = cursor.fetchone()

    if propietario:
        propietario_id = propietario['id']
        flash(f"El propietario {propietario['nombre']} ya está registrado. Se procederá a cargar el servicio.", 'info')
    else:
        # Si el propietario no existe, lo registramos
        cursor.execute("""
            INSERT INTO propietarios (nombre, curso, division, dni) 
            VALUES (%s, %s, %s, %s)
        """, (nombre, curso, division, dni))
        db.commit()
        propietario_id = cursor.lastrowid
        flash("Nuevo propietario registrado y servicio agregado correctamente.", 'success')

    # Insertar el nuevo servicio para el propietario encontrado o registrado
    cursor.execute("""
        INSERT INTO servicios (propietario_id, usuario_registro, tipo_dispositivo, servicio_realizado,numero_serie, estado)
        VALUES (%s, %s, %s, %s,%s, 'pendiente')
    """, (propietario_id,usuario_registro, tipo_dispositivo,servicio_realizado,numero_serie))
    
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('index'))  # Redirigir a la vista principal


@app.route('/actualizar_estado/<int:id>', methods=['POST'])
def actualizar_estado(id):
    estado = request.form['estado']
    
   
    db = get_db_connection()
    cursor = db.cursor()
    if estado == 'Entregado':
        fecha_salida= datetime.now() 
        usuario_registroS = session['user']  
        cursor.execute("UPDATE servicios SET estado = %s,fecha_salida=%s,usuario_registroS=%s WHERE id = %s", (estado,fecha_salida,usuario_registroS, id))
    else:
         cursor.execute("UPDATE servicios SET estado = %s WHERE id = %s", (estado, id))
        
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return render_template('login.html')



@app.route('/buscar_propietario', methods=['GET'])
def buscar_propietario():
    dni = request.args.get('dni', '')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT nombre, curso, division FROM propietarios WHERE dni = %s", (dni,))
    propietario = cursor.fetchone()
    cursor.close()
    db.close()

    return jsonify(propietario if propietario else {})  # Devuelve {} si no hay resultados


@app.route('/delete/<string:id>')
def delete(id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("DELETE FROM servicios WHERE id = %s",(id,))
    db.commit() 
    cursor.close()
    db.close()
    return redirect(url_for('index'))

@app.route('/update/<id>', methods=['POST'])
def update_service(id):
    if request.method=='POST':
        tipo_dispositivo=request.form['tipo_dispositivo']
        servicio_realizado=request.form['servicio_realizado']
        numero_serie=request.form['numero_serie']
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
       
       
        


        cursor.execute("""UPDATE servicios SET tipo_dispositivo = %s,
                    servicio_realizado=%s,
                    numero_serie=%s
                    WHERE id =%s                  
                    """,(tipo_dispositivo, servicio_realizado, numero_serie,id))
        
        
        db.commit() 
        cursor.close()
        db.close()
        return (redirect(url_for('index')))  



@app.route('/edit/<id>')
def get_service(id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
   
    cursor.execute("SELECT * from servicios WHERE id = %s",(id,))
    data= cursor.fetchall()
   
    
    cursor.close()
    db.close()
    return render_template('edit-service.html', service=data)
    

if __name__ == '__main__':
    app.run(debug=True)
