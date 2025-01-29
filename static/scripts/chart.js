let chart;  // Referencia global a la gráfica

function updateChart(newData) {
    const currentTime = Date.now();
    const fiveMinutesAgo = currentTime - 5 * 60 * 1000;
    
    // Filtrar los datos para mantener solo los últimos 5 minutos
    chart.data.datasets[0].data = chart.data.datasets[0].data.filter(point => point.x >= fiveMinutesAgo);

    // Agregar los nuevos puntos de datos
    newData.forEach(dataPoint => {
        chart.data.datasets[0].data.push({
            x: new Date(dataPoint.timestamp).getTime(),
            y: dataPoint.value
        });
    });

    // Actualizar la gráfica
    chart.update({
        preservation: true,  // Mantener la animación de los datos
        duration: 1000       // Duración de la animación en milisegundos
    });
}

// Inicializar la gráfica (solo se hace una vez)
function initializeChart(initialData) {
    const ctx = document.getElementById('myChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Datos del sensor',
                data: initialData.map(dataPoint => ({
                    x: new Date(dataPoint.timestamp).getTime(),
                    y: dataPoint.value
                })),
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1,
                fill: false
            }]
        },
        options: {
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute',
                        displayFormats: {
                            minute: 'HH:mm:ss'
                        }
                    }
                },
                y: {
                    beginAtZero: true
                }
            },
            animation: {
                duration: 0  // Desactivar animación inicial para evitar retraso
            }
        }
    });
}

// Ejemplo de uso
// Inicializar la gráfica con datos iniciales (de los últimos 5 minutos)
fetch('/api/get_initial_data')
    .then(response => response.json())
    .then(initialData => {
        initializeChart(initialData);
    });

// Actualizar la gráfica periódicamente con nuevos datos
setInterval(() => {
    fetch('/api/get_latest_data')  // Asegúrate de que esta ruta devuelva solo los datos nuevos
        .then(response => response.json())
        .then(newData => {
            updateChart(newData);
        });
}, 10000);  // Actualizar cada 10 segundos (ajusta según sea necesario)
