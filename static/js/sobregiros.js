/* =========================
   DATOS SOBREGIROS
   ========================= */
const labelsSemana = window.datosSemana.map(
    item => item.Fecha
);

const valoresSemana = window.datosSemana.map(
    item => item['Monto sobregiro']
);

/* =========================
   CREAR GRÁFICA
   ========================= */
crearGraficaLinea({

    canvasId: 'grafica-semana-sobregiro',

    labels: labelsSemana,

    valores: valoresSemana,

    titulo: 'Sobregiros en la semana',

    usarFormatoMoneda: true
});

iniciarBuscador(window.clientesAutocomplete)