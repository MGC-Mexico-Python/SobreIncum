/* =========================
   ESTADO
   ========================= */
let graficaActiva = null;
let esMonto       = true;
let esSemanas     = true;

/* =========================
   DATOS
   ========================= */
function obtenerDatos() {
    if (esMonto && esSemanas)   return { datos: window.grafSemanalMonto,   labelKey: 'Fecha', valorKey: 'Monto vencimiento',  titulo: 'Monto por semana',   esMonto: true  };
    if (esMonto && !esSemanas)  return { datos: window.grafMensualMonto,   labelKey: 'Fecha', valorKey: 'Monto vencimiento',  titulo: 'Monto por mes',      esMonto: true  };
    if (!esMonto && esSemanas)  return { datos: window.grafSemanalEventos, labelKey: 'Fecha', valorKey: 'Interlocutor',     titulo: 'Eventos por semana', esMonto: false };
    if (!esMonto && !esSemanas) return { datos: window.grafMensualEventos, labelKey: 'Fecha', valorKey: 'Interlocutor',     titulo: 'Eventos por mes',    esMonto: false };
}

/* =========================
   RENDERIZAR GRÁFICA
   ========================= */
function renderizarGrafica() {

    


    if (graficaActiva) {
        graficaActiva.destroy();
        graficaActiva = null;
    }

    const { datos, labelKey, valorKey, titulo, esMonto } = obtenerDatos();

    graficaActiva = crearGraficaLinea({
        canvasId          : 'grafica-cliente',
        labels            : datos.map(d => d[labelKey]),
        valores           : datos.map(d => d[valorKey]),
        titulo            : titulo,
        usarFormatoMoneda : esMonto
    });
}

/* =========================
   TOGGLE TIPO
   ========================= */
function iniciarToggleTipo() {
    document.querySelectorAll('.toggle-tipo-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.toggle-tipo-btn').forEach(b => b.classList.remove('activo'));
            btn.classList.add('activo');
            esMonto = btn.id === 'btn-monto';
            renderizarGrafica();
        });
    });
}

/* =========================
   TOGGLE TEMPORALIDAD
   ========================= */
function iniciarToggleTemporalidad() {
    const btn = document.getElementById('btn-temporalidad');

    btn.addEventListener('click', () => {
        esSemanas = !esSemanas;
        btn.innerHTML = esSemanas ? 'Meses &#8594;' : '&#8592; Semanas';
        renderizarGrafica();
    });
}

/* =========================
   INIT
   ========================= */
iniciarToggleTipo();
iniciarToggleTemporalidad();
renderizarGrafica();