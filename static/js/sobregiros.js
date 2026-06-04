Chart.register(ChartDataLabels);

function formatoMoneda(valor) {

    return '$' + valor.toLocaleString(
        'es-MX',
        {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }
    );
}

function crearGraficaLinea({
    canvasId,
    labels,
    valores,
    titulo = '',
    colorLinea = '#2d2d2d',
    colorFondo = 'rgba(45, 45, 45, 0.10)',
    porcentajeTop = 0.15
}) {

    const canvas = document.getElementById(
        canvasId
    );

    const ctx = canvas.getContext('2d');

    const valorMaximo = Math.max(...valores);

    const topY = valorMaximo * (
        1 + porcentajeTop
    );

    return new Chart(ctx, {

        type: 'line',

        data: {

            labels: labels,

            datasets: [{

                label: titulo,

                data: valores,

                borderColor: colorLinea,

                backgroundColor: colorFondo,

                borderWidth: 3,

                tension: 0.35,

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

                        return formatoMoneda(
                            value
                        );
                    }
                }
            }]
        },

        options: {

            layout: {

                padding: {

                    top: 0,

                    left: 35,

                    right: 35,
                    
                    bottom:0
                }
            },

            responsive: true,

            maintainAspectRatio: false,

            interaction: {

                intersect: false,

                mode: 'index'
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

                            return formatoMoneda(
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

const labelsSemana = window.datosSemana.map(
    item => item.Fecha
);

const valoresSemana = window.datosSemana.map(
    item => item['Monto sobregiro']
);

crearGraficaLinea({

    canvasId: 'grafica-semana-sobregiro',

    labels: labelsSemana,

    valores: valoresSemana,

    titulo: 'Sobregiros en la semana'
});