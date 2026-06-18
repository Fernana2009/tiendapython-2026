from flask import Flask, render_template, request, redirect, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from conexion import conexion, cursor
import os

app = Flask(__name__)

app.secret_key = "123456"

CARPETA = "static/uploads"
app.config["UPLOAD_FOLDER"] = CARPETA

os.makedirs(CARPETA, exist_ok=True)


@app.route("/")
def inicio():

    if "correo" not in session:
        return redirect("/login")

    return render_template("index.html")


@app.route("/guardar", methods=["POST"])
def guardar():

    if "correo" not in session:
        return redirect("/login")

    # Recogemos los campos de texto del formulario
    nombre = request.form["nombre"]
    precio = request.form["precio"]
    stock = request.form["stock"]
    
    # CORRECCIÓN: Ahora se recibe como texto (URL) en lugar de request.files
    imagen_url = request.form["imagen"] 

    # Guardamos directamente la URL de internet en la base de datos
    sql = """
    INSERT INTO productos(nombre, precio, stock, imagen)
    VALUES(%s, %s, %s, %s)
    """

    valores = (nombre, precio, stock, imagen_url)

    cursor.execute(sql, valores)
    conexion.commit()

    flash("Producto guardado correctamente")

    return redirect("/registrar-producto")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        correo = request.form["correo"]
        clave = request.form["clave"]

        sql = """
        SELECT * FROM usuarios
        WHERE correo = %s
        """

        valores = (correo,)

        cursor.execute(sql, valores)

        usuario_encontrado = cursor.fetchone()

        if usuario_encontrado:

            clave_bd = usuario_encontrado[2]

            if check_password_hash(clave_bd, clave):

                session["id_usuario"] = usuario_encontrado[0]
                session["correo"] = usuario_encontrado[1]
                session["rol"] = usuario_encontrado[3]

                flash("Bienvenido al sistema")

                return redirect("/")

        flash("Correo o contraseña incorrectos")

        return redirect("/login")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    flash("Sesión cerrada correctamente")

    return redirect("/login")


@app.route("/crear-admin")
def crear_admin():

    correo = "admin@gmail.com"
    clave = generate_password_hash("123456")
    rol = "Administrador"

    sql = """
    INSERT INTO usuarios(correo, clave, rol)
    VALUES(%s, %s, %s)
    """

    valores = (correo, clave, rol)

    cursor.execute(sql, valores)
    conexion.commit()

    return "Administrador creado correctamente"

@app.route("/registrar-producto")
def registrar_producto():

    if "correo" not in session:
        return redirect("/login")

    return render_template("registrar_producto.html")


@app.route("/ver-productos")
def ver_productos():

    if "correo" not in session:
        return redirect("/login")

    buscar = request.args.get("buscar", "")

    if buscar != "":
        sql = """
        SELECT * FROM productos
        WHERE nombre LIKE %s
        """

        valores = ("%" + buscar + "%",)

        cursor.execute(sql, valores)

    else:
        sql = "SELECT * FROM productos"
        cursor.execute(sql)

    productos = cursor.fetchall()

    return render_template(
        "ver_productos.html",
        productos=productos,
        buscar=buscar
    )
# =========================================================
# RUTA CORREGIDA: Eliminar producto definitivamente
# =========================================================
@app.route("/eliminar/<int:id>", methods=["GET"])
def eliminar(id):
    if "correo" not in session:
        return "No autorizado", 401

    try:
        # 1. Preparamos la consulta SQL
        sql = "DELETE FROM productos WHERE id = %s"
        valores = (id,)
        
        # 2. Ejecutamos el borrado
        cursor.execute(sql, valores)
        
        # 3. ¡CRITICAL! Confirmamos los cambios en la Base de Datos
        conexion.commit()
        
        # 4. Respondemos con un estado exitoso puro (200) sin redirecciones
        return "OK", 200
        
    except Exception as e:
        # Si algo falla en la base de datos, lo veremos en la consola de la terminal
        print(f"Error crítico al eliminar producto en la BD: {e}")
        return "Error interno", 500