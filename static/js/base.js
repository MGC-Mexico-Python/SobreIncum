/* =========================
   REGISTRO PLUGINS
   ========================= */
Chart.register(ChartDataLabels);

function colorTema(nombre) {
    return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}

function conAlfa(hex, alfa) {
    const n = parseInt(hex.replace('#', ''), 16);
    return `rgba(${n >> 16}, ${(n >> 8) & 255}, ${n & 255}, ${alfa})`;
}

Chart.defaults.font.family = colorTema('--font-sans');

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

    colorLinea = colorTema('--accent-2'),

    colorFondo = conAlfa(colorTema('--accent-2'), 0.14),

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

                    color: colorTema('--text-1'),

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

                    color: colorTema('--text-1'),

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

                        color: colorTema('--text-2'),

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

/* =========================
   AUTOCOMPLETE
   ========================= */

function iniciarBuscador(lista, contexto) {
    // contexto = { modulo: 'sobregiros' | 'incumplimientos',
    //              apiUrl: '/api/cliente/' | '/api/incumplimientos/cliente/',
    //              campoMonto: 'Money Monto sobregiro' | 'Money Monto vencimiento',
    //              etiquetaMonto: 'Sobregiro' | 'Vencimiento',
    //              rutaCliente: '/sobregiros/cliente/' | '/incumplimientos/cliente/' }
    const ctx = contexto || {
        modulo       : 'sobregiros',
        apiUrl       : '/api/cliente/',
        campoMonto   : 'Money Monto sobregiro',
        etiquetaMonto: 'Sobregiro',
        rutaCliente  : '/sobregiros/cliente/'
    };

    const input = document.getElementById('input-buscador');
    const dropdown = document.getElementById('dropdown-buscador');

    input.addEventListener('input', () => {
        const valor = input.value.trim().toUpperCase();
        dropdown.innerHTML = '';

        if (!valor) {
            const contenedor = document.querySelector('.contenido-tarjetas');
            if (contenedor.dataset.originalHtml) {
                contenedor.innerHTML = contenedor.dataset.originalHtml;
                delete contenedor.dataset.originalHtml;
            }
            return;
        }

        const filtrados = lista.filter(c =>
            c.Interlocutor.toUpperCase().includes(valor) ||
            c["Razon Social"].toUpperCase().includes(valor)
        );

        filtrados.forEach(c => {
            const li = document.createElement('li');
            li.textContent = `${c.Interlocutor} — ${c["Razon Social"]}`;
            li.addEventListener('click', () => {
                input.value = c.Interlocutor;
                dropdown.innerHTML = '';

                fetch(`${ctx.apiUrl}${c.Interlocutor}`)
                    .then(res => res.json())
                    .then(data => {
                        renderizarTarjetaBuscador(c.Interlocutor, c["Razon Social"], data, ctx);
                    });
            });
            dropdown.appendChild(li);
        });
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.encabezado-buscador')) {
            dropdown.innerHTML = '';
        }
    });
}

/* =========================
   TARJETA BUSCADOR
   ========================= */

function renderizarTarjetaBuscador(interlocutor, razonSocial, data, ctx) {
    const contexto = ctx || {
        campoMonto   : 'Money Monto sobregiro',
        etiquetaMonto: 'Sobregiro',
        rutaCliente  : '/sobregiros/cliente/'
    };

    const contenedor = document.querySelector('.contenido-tarjetas');

    if (!contenedor.dataset.originalHtml) {
        contenedor.dataset.originalHtml = contenedor.innerHTML;
    }

    const registro = Array.isArray(data) ? data[0] : data;
    const monto = registro?.[contexto.campoMonto] ?? null;

    contenedor.innerHTML = `
        <a id="tarjeta-buscador" href="${contexto.rutaCliente}${interlocutor}" class="tarjetas">
            <div class="tarjetas-i">
                <span class="t-razon">${razonSocial}</span>
                <span class="t-interlocutor">${interlocutor}</span>
            </div>
            <div class="tarjetas-d">
                <span class="t-monto">${monto ? contexto.etiquetaMonto + ': ' + monto : 'Sin ' + contexto.etiquetaMonto.toLowerCase() + ' hoy'}</span>
            </div>
        </a>
    `;
}

/* =========================
   TEMA
   ========================= */
function recolorearGrafica(grafica) {
    const linea = colorTema('--accent-2');
    const dataset = grafica.data.datasets[0];
    dataset.borderColor = linea;
    dataset.backgroundColor = conAlfa(linea, 0.14);
    dataset.datalabels.color = colorTema('--text-1');
    grafica.options.plugins.title.color = colorTema('--text-1');
    grafica.options.scales.x.ticks.color = colorTema('--text-2');
    grafica.update('none');
}

function aplicarTema(tema) {
    document.documentElement.dataset.theme = tema;
    try { localStorage.setItem('tema', tema); } catch (e) {}
    Object.values(Chart.instances).forEach(recolorearGrafica);
}

const btnTema = document.getElementById('btn-tema');

if (btnTema) {
    btnTema.addEventListener('click', () => {
        aplicarTema(
            document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'
        );
    });
}