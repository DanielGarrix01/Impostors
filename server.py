from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import string
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Guardamos las partidas activas
partidas = {}

def generar_codigo():
    letras = lambda n: ''.join(random.choices(string.ascii_uppercase, k=n))
    numeros = lambda n: ''.join(random.choices(string.digits, k=n))
    return f"{letras(3)}-{numeros(3)}-{letras(3)}"

@app.route('/')
def index():
    return render_template('host.html')

@app.route('/player')
def player():
    return render_template('game_run.html')

# SocketIO Events

@socketio.on('crear_partida')
def crear_partida(data):
    host = data['host']
    codigo = generar_codigo()
    partidas[codigo] = {
        'host': host,
        'jugadores': [],
        'estado': 'esperando'
    }
    emit('partida_creada', {'codigo': codigo})

@socketio.on('unirse_partida')
def unirse_partida(data):
    nombre = data['nombre']
    codigo = data['codigo']
    if codigo in partidas and partidas[codigo]['estado'] == 'esperando':
        partidas[codigo]['jugadores'].append(nombre)
        join_room(codigo)
        # Actualizamos lista de jugadores al host
        emit('jugadores_actualizados', {'jugadores': partidas[codigo]['jugadores']}, room=codigo)
        emit('unido', {'status': 'ok'})
    else:
        emit('unido', {'status': 'error', 'mensaje': 'Código inválido o partida ya iniciada'})

@socketio.on('iniciar_partida')
def iniciar_partida(data):
    codigo = data['codigo']
    if codigo in partidas:
        partidas[codigo]['estado'] = 'jugando'
        emit('partida_iniciada', room=codigo)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
