from flask import Flask, request, url_for, redirect, render_template

userVal = "Alex"
userVal2 = "Alex2"
app = Flask(__name__)

#Punto 1
@app.route('/', methods=['GET'])
def hello_world():
    print("Hello, World!")
    return "<h2>Hello, World!</h2>"

#Punto 2
@app.route("/usuario", methods=['GET'])
def user1():
    print(userVal)
    return 'Perfil de 'f'{userVal}'

#Punto 3
@app.route("/usuario/editar", methods=['GET'])
def change():
    global userVal
    userVal = userVal2
    return 'El nuevo usuario es: 'f'{userVal}'

#Punto 4
@app.route("/user/<username111>", methods=['PUT'])
def profile2(username111):
    global userVal
    userVal = username111
    return 'El usuario es: 'f'{userVal}'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000,debug=True)
