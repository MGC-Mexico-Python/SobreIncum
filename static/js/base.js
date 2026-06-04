/* =========================
   REGISTRO PLUGINS
   ========================= */
Chart.register(ChartDataLabels);

/* =========================
   FORMATO MONEDA
   ========================= */
function formatoMoneda(valor) {

    return '$' + valor.toLocaleString(
        'es-MX',
        {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }
    );
}

/* =========================
   FORMATO NÚMERO
   ========================= */
function formatoNumero(valor) {

    return valor.toLocaleString(
        'es-MX'
    );
}

/* =========================
   FORMATEADOR DINÁMICO
   ========================= */
function obtenerFormateador(
    usarFormatoMoneda
) {

    return (valor) => {

        if (usarFormatoMoneda) {

            return formatoMoneda(
                valor
            );
        }

        return formatoNumero(
            valor
        );
    };
}

/* =========================
   CREAR GRÁFICA DE LÍNEA
   ========================= */
function crearGraficaLinea({

    canvasId,

    labels,

    valores,

    titulo = '',

    colorLinea = '#2d2d2d',

    colorFondo = 'rgba(45, 45, 45, 0.10)',

    porcentajeTop = 0.15,

    usarFormatoMoneda = true
}) {

    /* =========================
       CANVAS
       ========================= */
    const canvas = document.getElementById(
        canvasId
    );

    if (!canvas) {

        console.error(
            `No existe canvas: ${canvasId}`
        );

        return;
    }

    const ctx = canvas.getContext('2d');

    /* =========================
       VALIDACIÓN
       ========================= */
    if (!valores.length) {

        console.error(
            'No hay valores para graficar'
        );

        return;
    }

    /* =========================
       ESCALA DINÁMICA
       ========================= */
    const valorMaximo = Math.max(
        ...valores
    );

    const topY = valorMaximo * (
        1 + porcentajeTop
    );

    /* =========================
       FORMATEADOR
       ========================= */
    const formatearValor =
        obtenerFormateador(
            usarFormatoMoneda
        );

    /* =========================
       CHART
       ========================= */
    return new Chart(ctx, {

        type: 'line',

        data: {

            labels: labels,

            datasets: [{

                label: titulo,

                data: valores,

                borderColor: colorLinea,

                backgroundColor:
                    colorFondo,

                borderWidth: 3,

                tension: 0.25,

                fill: true,

                pointRadius: 5,

                pointHoverRadius: 7,

                datalabels: {

                    color: '#2d2d2d',

                    anchor: 'end',

                    align: 'top',

                    offset: 6,

                    clamp: true,

                    font: {

                        weight: '700',

                        size: 11
                    },

                    formatter: (value) => {

                        return formatearValor(
                            value
                        );
                    }
                }
            }]
        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            layout: {

                padding: {

                    top: 10,

                    left: 35,

                    right: 35,

                    bottom: 0
                }
            },

            interaction: {

                intersect: false,

                mode: 'index'
            },

            animation: {

                duration: 1200
            },

            plugins: {

                legend: {

                    display: false
                },

                title: {

                    display: true,

                    text: titulo,

                    color: '#2d2d2d',

                    font: {

                        size: 18,

                        weight: '700'
                    },

                    padding: {

                        top: 10,

                        bottom: 25
                    }
                },

                tooltip: {

                    displayColors: false,

                    callbacks: {

                        label: (context) => {

                            return formatearValor(
                                context.raw
                            );
                        }
                    }
                }
            },

            scales: {

                x: {

                    grid: {

                        display: false
                    },

                    ticks: {

                        color: '#626060',

                        font: {

                            size: 12,

                            weight: '600'
                        }
                    }
                },

                y: {

                    display: false,

                    beginAtZero: true,

                    max: topY,

                    grid: {

                        display: false
                    },

                    border: {

                        display: false
                    }
                }
            }
        },

        plugins: [ChartDataLabels]
    });
}