/* =========================
   DATOS INCUMPLIMIENTOS
   ========================= */
const labelsSemana = window.datosSemana.map(
    item => item.Fecha
);

const valoresSemana = window.datosSemana.map(
    item => item['Monto vencimiento']
);

/* =========================
   CREAR GRÁFICA
   ========================= */
crearGraficaLinea({

    canvasId: 'grafica-semana-incumplimiento',

    labels: labelsSemana,

    valores: valoresSemana,

    titulo: 'Incumplimientos en la semana',

    usarFormatoMoneda: true
});

iniciarBuscador(window.clientesAutocomplete, {
    modulo       : 'incumplimientos',
    apiUrl       : '/api/incumplimientos/cliente/',
    campoMonto   : 'Money Monto vencimiento',
    etiquetaMonto: 'Vencimiento',
    rutaCliente  : '/incumplimientos/cliente/'
});

/* =========================
   DESCARGAR EXCEL
   ========================= */

const btnDescargar = document.getElementById('btn-descargar-xls');

if (btnDescargar) {

    btnDescargar.addEventListener('click', () => {

        window.location.href = '/api/incumplimientos/exportar';

    });

}