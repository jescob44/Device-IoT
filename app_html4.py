#Instalar Flask-WTF para trabajar con formularios y Flask-Login para gestionar la autenticación de usuarios
#pip install Flask-WTF Flask-Login
import os
from flask import Flask, render_template, request, url_for, jsonify, redirect, flash, send_file, abort
from datetime import datetime, timedelta
import requests
import pandas as pd
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
from functools import wraps

import base64


app = Flask(__name__)

datos = [] #Variable usada para almacenar los datos json
datos_matriz = []

ADMIN_KEY = '1234'  # Clave para agregar admnistrador o borrar usuarios

URL = "http://localhost:8000"
ARCHIVO = "./data/datos.csv"

# Autenticacion de usuarios
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta'  # Cambia esto a una clave segura en un entorno de producción

login_manager = LoginManager(app)
login_manager.login_view = 'login'

username = ""
password = ""

# Diccionario global para almacenar los datos de cada usuario por separado
usuarios_datos = {}

# Filtro para eliminar la extensión del archivo en las plantillas de codigo
@app.template_filter('without_extension')
def without_extension(file_name):
    return file_name.rsplit('.', 1)[0] if '.' in file_name else file_name

# Función para leer usuarios desde un archivo
def cargar_usuarios():
    usuarios = []
    with open('static/Datos/users.txt', 'r') as file:
        for line in file:
            user_id, usertype, username, password, name, lastname, email, phone, career, document = line.strip().split(',')
            usuarios.append(User(int(user_id), usertype, username, password))  # Convertir user_id a entero
    return usuarios

# Verifica el atributo usertype en lugar de id:
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.usertype != 'Administrador':
            # flash("Acceso no permitido para este tipo de usuario.", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function
class User(UserMixin):
    def __init__(self, user_id, usertype, username, password):
        self.id = user_id  # Identificador único (Flask-Login usa esto)
        self.usertype = usertype  # Tipo de usuario (Administrador o Estudiante)
        self.username = username  # Nombre de usuario único
        self.password = password  # Contraseña del usuario

    def get_id(self):
        # Flask-Login usará este método para obtener el identificador único
        return self.id

    @staticmethod
    def verify_auth(username, password):
        # Verifica si el usuario y la contraseña coinciden
        return next((user for user in users if user.username == username and user.password == password), None)

    def __repr__(self):
        return f"User(id={self.id}, usertype={self.usertype}, username={self.username})"

# Cargar usuarios desde el archivo
users = cargar_usuarios()

@login_manager.request_loader
def load_user_from_header(request): # Función para cargar el usuario desde la cabecera de la petición del cliente(Arduino)
    global username, password
    auth = request.authorization
    if not auth:
        return None
    user = User.verify_auth(auth.username, auth.password)
    username = auth.username
    password = auth.password
    if not user:
        abort(401)
    return user

@login_manager.user_loader
def load_user(user_id):  # Flask-Login pasa `user_id`
    global usernamePage, passwordPage
    usuario = next((usuario for usuario in users if usuario.id == int(user_id)), None)
    if usuario:
        usernamePage = usuario.username
        passwordPage = usuario.password
    return usuario

@login_manager.request_loader
def load_user_from_header(request):
    auth = request.authorization
    if not auth:
        return None
    user = User.verify_auth(auth.username, auth.password)
    if not user:
        abort(401)
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.verify_auth(username, password)
        if user:
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Usuario o contraseña incorrectos.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('login.html')

# Registrar nuevos usuarios
@app.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register_user():
    if request.method == 'POST':
        usertype = request.form['usertype']
        username = request.form['username']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        phone = request.form['phone']
        career = request.form['career']
        document = request.form['document']
        admin_key = request.form['admin_key']
        action = request.form['action']
        
        if action == 'Agregar Usuario':
            if usertype == 'Administrador':
                if admin_key != ADMIN_KEY:
                    flash('Clave de administrador incorrecta.', 'danger')
                    return '', 204  # Retorna respuesta vacía con código 204 (No Content)
            else:
                print("usertype: ", usertype)

            user_exists = any(user.username == username for user in users)
            
            if user_exists:
                flash('El nombre de usuario ya existe. Por favor elija otro.', 'danger')
                return '', 204
            
            user_id = max(user.id for user in users) + 1
            new_user = User(user_id, usertype, username, password)
            users.append(new_user)
            
            with open('static/Datos/users.txt', 'a') as file:
                file.write(f'{user_id},{usertype},{username},{password},{firstname},{lastname},{email},{phone},{career},{document}\n')

            flash('Usuario registrado exitosamente.', 'success')
            return redirect(url_for('register_user'))
            # return '', 204

        if action == 'Actualizar Usuario':
            if usertype == 'Administrador':
                if admin_key != ADMIN_KEY:
                    flash('Clave de administrador incorrecta.', 'danger')
                    return '', 204  # Retorna respuesta vacía con código 204 (No Content)
            else:
                print("usertype: ", usertype)
                
            user_to_update = next((user for user in users if user.username == username), None)
            
            if user_to_update:
                with open('static/Datos/users.txt', 'r') as file:
                    lines = file.readlines()

                with open('static/Datos/users.txt', 'w') as file:
                    for line in lines:
                        user_data = line.strip().split(',')
                        if user_data[2] == username:
                            updated_line = f'{user_data[0]},{usertype},{username},{password},{firstname},{lastname},{email},{phone},{career},{document}\n'
                            file.write(updated_line)
                        else:
                            file.write(line)

                user_to_update.usertype = usertype
                user_to_update.password = password

                flash('Usuario actualizado exitosamente.', 'success')
            else:
                flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('register_user'))
            # return '', 204

        if action == 'Eliminar Usuario':
            if admin_key != ADMIN_KEY:
                flash('Clave de administrador incorrecta.', 'danger')
                return '', 204
            
            user_to_delete = next((user for user in users if user.username == username), None)
            if user_to_delete:
                users.remove(user_to_delete)

                with open('static/Datos/users.txt', 'r') as file:
                    lines = file.readlines()

                with open('static/Datos/users.txt', 'w') as file:
                    for line in lines:
                        if not line.startswith(f'{user_to_delete.id},'):
                            file.write(line)

                            # Eliminar archivos relacionados
                            archivos = [
                                f'static/Datos/{username}_Data.txt',
                                f'static/Datos/{username}_DatosTemp.txt'
                            ]                          
                            for archivo in archivos:
                                try:
                                    if os.path.exists(archivo):
                                        os.remove(archivo)
                                except Exception as e:
                                    print(f"Error al eliminar el archivo {archivo}: {str(e)}")
                flash('Usuario eliminado exitosamente.', 'success')
            else:
                flash('Usuario no encontrado.', 'danger')

            return '', 204
    return render_template('usuarios.html')  # Solo para GET requests

# Esta función se usa para buscar un usuario por su nombre de usuario y mostrar sus datos en
# el contenido para el correo.
@app.route('/buscar_usuario/<username>', methods=['GET'])
def buscar_usuario(username):
    try:
        with open('static/Datos/users.txt', 'r') as file:
            for line in file:
                user_data = line.strip().split(',')
                # print("user_data: ", user_data)
                if user_data[2] == username:  # Asumiendo que el username está en la tercera posición
                    # Devolver los datos del usuario encontrado
                    return jsonify({
                        'id': user_data[0],
                        'usertype': user_data[1],
                        'username': user_data[2],
                        'password': user_data[3],
                        'firstname': user_data[4],
                        'lastname': user_data[5],
                        'email': user_data[6],
                        'phone': user_data[7],
                        'career': user_data[8],
                        'document': user_data[9]
                    }), 200
        
        # Si no se encuentra el usuario
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    except Exception as e:
        # En caso de error al leer el archivo
        return jsonify({'error': f'Error al buscar usuario: {str(e)}'}), 500

# Ejemplo de cómo usar esta función en una ruta Flask
# @app.route('/buscar_usuario/<username>', methods=['GET'])
# def obtener_usuario(username):
#     return buscar_usuario(username)

# obtener los datos de los usuarios
@app.route('/obtener_usuarios', methods=['GET'])
def obtener_usuarios():
    try:
        # Se tienen los usuarios almacenados en un archivo
        with open('static/Datos/users.txt', 'r') as file:
            usuarios = file.readlines() 
            # Separa los datos de los usuarios en una lista
            usuarios = [usuario.strip().split(',') for usuario in usuarios]
            return jsonify(usuarios=usuarios)
    except Exception as e:
        return jsonify({'error': str(e)})

# Antes de agregar un usuario nuevo se verifica que el usuario no exista
@app.route('/agregar_usuario', methods=['POST'])
def agregar_usuario():
    nuevo_usuario = request.form['nombre']  # Obtener el nombre del formulario
    nuevo_email = request.form['email']  # Obtener el email del formulario
    
    # Verificar si el usuario ya existe
    with open('usuarios.txt', 'r') as file:
        usuarios = file.readlines()
        for usuario in usuarios:
            nombre, email = usuario.strip().split(',')
            if nombre == nuevo_usuario or email == nuevo_email:
                return jsonify({'existe': True, 'mensaje': 'El usuario o email ya existe.'})

    # Si no existe, se agrega
    with open('usuarios.txt', 'a') as file:
        file.write(f"{nuevo_usuario},{nuevo_email}\n")
    
    return jsonify({'existe': False, 'mensaje': 'Usuario agregado correctamente.'})

new_date = datetime.utcnow()
# Cambiar el formato de hora utc a gtn-5
new_date = new_date + timedelta(hours=-5)

tiemp= str(new_date)
data = [
    [tiemp, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]
data2 = [
    [tiemp, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

# Abre el generador de codigo para arduino
@app.route("/generador")
@login_required
def generador():
    file_list = os.listdir('static/codigos')
    
    return render_template("Generador_codigo.html", file_list=file_list)

@app.route("/")
@login_required
def home():
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    city = 'Medellín,CO'  # Reemplaza con la ciudad de tu elección
    return render_template("account4.html", data=data,current_date=current_date,current_time=current_time)

@app.route('/', methods=['GET'])
@login_required
def hello_world():
    print("Hello, World!")
    return render_template("home.html")

@app.route("/usuario", methods=['GET'])
@login_required
def user1():
    print(userVal)
    return render_template("account4.1.html")

@app.route("/user", methods=['POST'])
@login_required
def profile2():
    global userVal
    userVal = request.form["user_name"]

    if not(userVal) is None:
        return redirect (url_for("user1"))
    
#Metodo PUT usado para actualizar una linea de elementos
@app.route('/usuario/actualizar', methods=['POST'])
@login_required
def actualizar_datos():
    datoActualizar = None
    timeOld = request.form["time_old"]
    timeNew = request.form["time_new"]
    # Busca el valor de tiempo en la lista
    for k in range(len(data)):
        formatoTime = "%Y-%m-%d %H:%M:%S"
        tiempo = datetime.strptime(data[k][0], formatoTime)
        timeOld2 = datetime.strptime(timeOld, formatoTime)
        timeNew2 = datetime.strptime(timeNew, formatoTime)
        if tiempo == timeOld2:
            data[k][0] = timeNew2
            datoActualizar = data[k][0]
            print("Se encontro dato para actualizar....................")
            break
    if datoActualizar:
        return jsonify({"mensaje": f"Tiempo {timeOld2} modificado a {timeNew2}"}), 200
    else:
        return jsonify({"mensaje": f"Tiempo {timeOld2} no encontrado"}), 404

@app.route("/data", methods=['GET', 'POST'])
@login_required
def get_post_data():
    global temperatura, datos_matriz, usernamePage, passwordPage, autorizacion
    data = []
    if request.method == "POST":
        # Verificar la cabecera de autorización 
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            print("No se encontró la cabecera de autorización")
            return jsonify({"error": "Unauthorized"}), 401
        
        # Decodificar la cabecera de autorización
        auth_type, auth_credentials = auth_header.split()
        autorizacion = auth_credentials
        if auth_type.lower() != 'basic':
            print("Tipo de autorización inválido")
            return jsonify({"error": "Invalid authorization type"}), 401
        decoded_credentials = base64.b64decode(auth_credentials).decode('utf-8')
        username_deco, password_deco = decoded_credentials.split(':')
   
        expected_username = current_user.username  # Obtener usuario autenticado
        expected_password = current_user.password  # Obtener contraseña asociada (o desde DB)

        if username_deco != expected_username or password_deco != expected_password:
            print("Credenciales inválidas")
            return jsonify({"error": "Unauthorized"}), 401
        
        dato = request.json
        new_date = datetime.utcnow() + timedelta(hours=-5)

        # Nombre del archivo específico para cada usuario
        file_name = f"{username_deco}_Data.txt"
        file_path = os.path.join("static/Datos/", file_name)

        # Leer los datos anteriores del archivo, si existen
        user_data = []
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                try:
                    user_data = eval(file.read())
                    if not isinstance(user_data, list):
                        user_data = []
                except Exception as e:
                    print(f"Error al leer el archivo: {e}")
                    user_data = []

        # Agregar el nuevo dato a los datos del usuario
        user_data.append(
            [
                new_date.strftime("%Y-%m-%d %H:%M:%S"),
                dato.get("input_1", 0),
                dato.get("input_2", 0),
                dato.get("input_3", 0),
                dato.get("input_4", 0),
                dato.get("input_5", 0),
                dato.get("input_6", 0),
                dato.get("dig_1", 0),
                dato.get("dig_2", 0),
                dato.get("dig_3", 0),
                dato.get("dig_4", 0),
                dato.get("dig_5", 0),
                dato.get("dig_6", 0),
                dato.get("dig_7", 0),
                dato.get("dig_8", 0),
                dato.get("dig_9", 0),
                dato.get("dig_10", 0),
            ]
        )

        # Guardar todos los datos actualizados en el archivo del usuario
        with open(file_path, 'w') as file:
            file.write(str(user_data))

        # Enviar los datos solo al usuario autenticado
        if current_user.username == username_deco:
            usuario_id = current_user.username
            # Crear el nombre del archivo con el nombre del usuario
            filename = f'static/Datos/{usuario_id}_DatosTemp.txt'
            try:
                # Leer los datos del archivo
                with open(filename, 'r') as f:
                    elementos = f.read()
                    elementos = json.loads(elementos)
            except FileNotFoundError:
                elementos = '[11111111]'  # Retorna una lista vacía si el archivo no existe
            return jsonify("usuarios_datos[usuario_id]: ", elementos)
        # return jsonify({"message": "Datos recibidos correctamente"}), 200
        return ('', 204)
    # Si es GET, leer todos los datos del archivo del usuario
    file_name = f"{current_user.username}_Data.txt"
    file_path = os.path.join("static/Datos/", file_name)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                data = eval(file.read())
                if not isinstance(data, list):
                    data = []
            except Exception as e:
                print(f"Error al leer el archivoooooo: {e}")
    else:
        data = []
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "No hay datos"})





# def get_data(url):
#     headers={"Accept":"application/json"}
#     response = requests.get(url, headers=headers)
#     return response.json()

# @app.route("/save_data", methods=['GET', 'POST'])
# @login_required
# def save_data():
#     data = get_data(URL + "/data")
#     df=pd.DataFrame(data)
#     df=df.rename(columns={0:"timestamp",1:"Temperatura",2:"Humedad",3:"input_1",4:"input_2"   }).set_index("timestamp")
#     df.to_csv(ARCHIVO)
#     return send_file(ARCHIVO, as_attachment=True, download_name='datos.csv', mimetype='text/csv')

# La siguiente funcion se usa para cargar los datos desde un archivo csv
@app.route("/load_data", methods=['GET', 'POST'])
@login_required
def load_data():
    error_message = None
    json_data2 = None

    if 'archivo' not in request.files:
        print("No se encontró archivo 1")
        error_message = ""
        return render_template('account4.2.html', json_data2=json_data2, error_message=error_message)
    
    archivo = request.files["archivo"]
    if archivo.filename == '':
        print("No se encontró archivo 2")
        error_message = "No se seleccionó ningún archivo"
        return render_template('account4.2.html', json_data2=json_data2, error_message=error_message)

    if not archivo:
        print("No hay archivos cargados, renderizar la tabla vacía")
        error_message = "No hay archivos cargados"
        return render_template('account4.2.html', json_data2=json_data2, error_message=error_message)

    try:
        df = pd.read_csv(archivo)
        print("Se encontró archivo")
        print(df)
        # Convertir el DataFrame a un formato JSON con la estructura deseada
        
        json_data2 = df.apply(lambda row: [
            pd.to_datetime(row['timestamp']).strftime("%Y-%m-%d %H:%M:%S"),
            row['input_1'],
            row['input_2'],
            row['input_3'],
            row['input_4'],
            row['input_5'],
            row['input_6'],

            row['dg1'],
            row['dg2'],
            row['dg3'],
            row['dg4'],
            row['dg5'],
            row['dg6'],
            row['dg7'],
            row['dg8'],
            row['dg9'],
            row['dg10'],
        ], axis=1).tolist()

    except Exception as e:
        error_message = "Error al procesar el archivo, verifique la extensión y su contenido."
        print("Error al procesar el archivo:", error_message)
    
    return render_template("account4.2.html", json_data2=json_data2, error_message=error_message)

#Dashboard para agregar los elementos visuales, solo permite ubicar y configurar
@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template("Dashboard.html")

#Dashboard para mostrar los elementos visuales e interactuar con ellos
@app.route("/Dashboard_visualizacion", methods=['GET', 'POST'])
@login_required
def Dashboard_visualizacion():
    return render_template("Dashboard_visualizacion.html")

#Enviar los datos de la matriz de elementos
@app.route('/guardar_estado_botones', methods=['POST'])
@login_required
def guardar_estado_botones():
 # Obtener los datos JSON recibidos
    datos_matriz = request.get_json()

    # Obtener el ID del usuario autenticado y almaceenar en la variable usuario_id
    usuario_id = current_user.username

    # Guardar los datos en el diccionario usando el ID del usuario como clave
    usuarios_datos[usuario_id] = datos_matriz

    # Obtener el nombre de usuario actual
    username = current_user.username
    # Crear el nombre del archivo con el nombre del usuario
    filename = f'{username}_DatosTemp.txt' # Almacena los datos en un archivo temporal
    # Para convertir datos_matriz a una cadena de texto
    datos_matriz = json.dumps(datos_matriz)
    # Guardar los datos en el archivo
    with open(f'static/Datos/{filename}', 'w') as f:
        f.write(datos_matriz)

    # Retornar los datos almacenados para este usuario
    return jsonify(usuarios_datos[usuario_id])



#Borrar los datos almacenados en la lista con lo que se puede limpiar la tabla y la grafica
@app.route('/borrar_datos', methods=['POST'])
@login_required
def borrar_datos2():
    # Limpiar la variable de datos en memoria
    data = []  # Borra los datos almacenados en la lista

    # Obtener el nombre del archivo para el usuario actual
    file_name = f"{current_user.username}_Data.txt"
    file_path = os.path.join("static/Datos/", file_name)
    
    # Borrar el contenido del archivo (abrir en modo 'w' lo vacía)
    with open(file_path, 'w') as file:
        file.write('')  # Escribir un archivo vacío
    
    return render_template("account4.2.html")

# Funcion que permite guardar los elementos de la matriz en un archivo txt
@app.route('/guardar_datos', methods=['POST'])
def guardar_datos():
    data = request.get_json()
    elementos = data.get('elementos', '')

    # Obtener el nombre de usuario actual
    username = current_user.username

    # Crear el nombre del archivo con el nombre del usuario
    filename = f'{username}_Dashboard.txt'

    # Guardar los datos en el archivo
    with open(f'static/Dashboard/{filename}', 'w') as f:
        f.write(elementos)

    return jsonify({'message': 'Datos guardados correctamente'}), 200

# Funcion que permite cargar los elementos de la matriz desde un archivo txt
@app.route('/cargar_datos', methods=['GET'])
@login_required
def cargar_datos():
    # Obtener el nombre de usuario actual
    username = current_user.username

    # Crear el nombre del archivo con el nombre del usuario
    filename = f'static/Dashboard/{username}_Dashboard.txt'

    try:
        # Leer los datos del archivo
        with open(filename, 'r') as f:
            elementos = f.read()
    except FileNotFoundError:
        elementos = '[]'  # Retorna una lista vacía si el archivo no existe

    return jsonify({'elementos': elementos}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6005)
