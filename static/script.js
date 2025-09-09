const socket = io();

if(document.getElementById('btnCrear')){
    // Host
    const btnCrear = document.getElementById('btnCrear');
    const nombreHost = document.getElementById('nombreHost');
    const codigoPartidaP = document.getElementById('codigoPartida');
    const listaJugadores = document.getElementById('listaJugadores');
    const btnIniciar = document.getElementById('btnIniciar');

    let codigoActual = '';

    btnCrear.addEventListener('click', ()=>{
        socket.emit('crear_partida', {host: nombreHost.value});
    });

    socket.on('partida_creada', (data)=>{
        codigoActual = data.codigo;
        codigoPartidaP.innerText = `Código de partida: ${codigoActual}`;
        btnIniciar.style.display = 'block';
    });

    socket.on('jugadores_actualizados', (data)=>{
        listaJugadores.innerHTML = '';
        data.jugadores.forEach(j => {
            const li = document.createElement('li');
            li.innerText = j;
            listaJugadores.appendChild(li);
        });
    });

    btnIniciar.addEventListener('click', ()=>{
        socket.emit('iniciar_partida', {codigo: codigoActual});
    });
}

// Jugador
if(document.getElementById('btnUnirse')){
    const btnUnirse = document.getElementById('btnUnirse');
    const nombreJugador = document.getElementById('nombreJugador');
    const codigoPartida = document.getElementById('codigoPartida');
    const mensaje = document.getElementById('mensaje');

    btnUnirse.addEventListener('click', ()=>{
        socket.emit('unirse_partida', {
            nombre: nombreJugador.value,
            codigo: codigoPartida.value
        });
    });

    socket.on('unido', (data)=>{
        if(data.status === 'ok'){
            mensaje.innerText = 'Te uniste correctamente!';
        } else {
            mensaje.innerText = `Error: ${data.mensaje}`;
        }
    });

    socket.on('partida_iniciada', ()=>{
        mensaje.innerText = 'La partida ha comenzado!';
    });
}
