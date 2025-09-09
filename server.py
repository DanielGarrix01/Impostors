# server.py
# Servidor Flask + Flask-SocketIO listo para ejecutarse en Render usando eventlet.
# Explicaciones dentro del código para que aprendas.

# IMPORTS
# Primero importamos eventlet y lo parcheamos: esto hace que sockets, timeouts,
# etc. funcionen de manera "no bloqueante" con eventlet.
import eventlet
eventlet.monkey_patch()  # <- importante, parchea módulos estándar para eventlet

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from socketio import WSGIApp  # para envolver la app con Socket.IO en WSGI
import random, string, os

# APP
app = Flask(__name__)
# Inicializamos SocketIO y forzamos async_mode a 'eventlet' por claridad.
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- Estructura de partidas en memoria ---
# Guardamos las partidas activas en un diccionario:
# partidas = { "ABC-123-XYZ": { "host": "Raul", "jugadores": [...], "estado": "esperando" } }
partidas = {}

def generar_codigo():
    """Genera un código del tipo ABC-123-XYZ"""
    letras = lambda n: ''.join(random.choices(string.ascii_uppercase, k=n))
    numeros = lambda n: ''.join(random.choices(string.digits, k=n))
    return f"{letras(3)}-{numeros(3)}-{letras(3)}"

# RUTAS HTTP (sirven host y jugador)
@app.route('/')
def index():
    # host.html debe estar en templates/
    return render_template('host.html')

@app.route('/player')
def player():
    # game_run.html debe estar en templates/
    return render_template('game_run.html')

# ---------- EVENTOS DE SOCKET.IO ----------
@socketio.on('crear_partida')
def crear_partida(data):
    """Crea una partida nueva con código único y la guarda en memoria."""
    host = data.get('host', 'Host')
    codigo = generar_codigo()
    partidas[codigo] = {
        'host': host,
        'jugadores': [],
        'estado': 'esperando'
    }
    # Emitimos al creador el código generado
    emit('partida_creada', {'codigo': codigo})

@socketio.on('unirse_partida')
def unirse_partida(data):
    """Un jugador se une a la partida si existe y está en 'esperando'"""
    nombre = data.get('nombre', '').strip()
    codigo = data.get('codigo', '').strip().upper()

    if not nombre:
        emit('unido', {'status': 'error', 'mensaje': 'Nombre vacío'})
        return

    if codigo in partidas and partidas[codigo]['estado'] == 'esperando':
        partidas[codigo]['jugadores'].append(nombre)
        join_room(codigo)  # agrega esta conexión a la sala del código
        # notificamos a todos en la sala (host incluido) la lista actualizada
        emit('jugadores_actualizados', {'jugadores': partidas[codigo]['jugadores']}, room=codigo)
        emit('unido', {'status': 'ok'})
    else:
        emit('unido', {'status': 'error', 'mensaje': 'Código inválido o partida ya iniciada'})

@socketio.on('iniciar_partida')
def iniciar_partida(data):
    """Host inicia la partida: cambiamos el estado y avisamos a la sala."""
    codigo = data.get('codigo', '').strip().upper()
    if codigo in partidas:
        partidas[codigo]['estado'] = 'jugando'
        emit('partida_iniciada', room=codigo)

# ---------- ARRANQUE (importante para Render) ----------
if __name__ == '__main__':
    # Puerto que Render (u otro host) puede pasar por env var PORT:
    port = int(os.environ.get("PORT", 5000))

    # Construimos el WSGI app que combina SocketIO y Flask:
    # WSGIApp recibe (socketio_server, flask_app)
    wsgi_app = WSGIApp(socketio, app)

    # Ejecutamos server con eventlet (servidor apto para producción en este contexto)
    print(f"Iniciando servidor en 0.0.0.0:{port} con eventlet")
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', port)), wsgi_app)
