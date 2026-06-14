/* Dashboard del panel — consume /panel/api/dashboard/ y dibuja con Chart.js */
(function () {
    const AZUL = '#2396FC';
    const AZUL_OSCURO = '#010D61';
    const VERDE = '#010D61';   // sin verde en la paleta: positivo = azul marino
    const ROJO = '#59200F';
    const AMBAR = '#FFD204';

    function texto(id, valor) {
        const el = document.getElementById(id);
        if (el) el.textContent = valor;
    }

    fetch('/panel/api/dashboard/', { credentials: 'same-origin' })
        .then((r) => r.json())
        .then((d) => {
            // KPIs
            texto('kpi-asistencia',
                d.asistencia_hoy.porcentaje_presentes === null
                    ? 'Sin registros hoy'
                    : d.asistencia_hoy.porcentaje_presentes + '% presentes hoy');
            texto('kpi-citaciones', d.citaciones_pendientes);

            // Serie de asistencia (línea)
            const elSerie = document.getElementById('chart-asistencia');
            if (elSerie && d.asistencia_serie.fechas.length) {
                new Chart(elSerie, {
                    type: 'line',
                    data: {
                        labels: d.asistencia_serie.fechas,
                        datasets: [{
                            label: '% presentes',
                            data: d.asistencia_serie.porcentajes,
                            borderColor: AZUL,
                            backgroundColor: 'rgba(35, 150, 252, 0.15)',
                            fill: true,
                            tension: 0.3,
                        }],
                    },
                    options: { scales: { y: { min: 0, max: 100 } } },
                });
            } else if (elSerie) {
                elSerie.closest('.dash-card').querySelector('.dash-vacio').hidden = false;
                elSerie.hidden = true;
            }

            // Promedios por asignatura (barras)
            const elProm = document.getElementById('chart-promedios');
            if (elProm && d.promedios.asignaturas.length) {
                new Chart(elProm, {
                    type: 'bar',
                    data: {
                        labels: d.promedios.asignaturas,
                        datasets: [{
                            label: 'Promedio',
                            data: d.promedios.promedios,
                            backgroundColor: AZUL_OSCURO,
                        }],
                    },
                    options: { scales: { y: { min: 1, max: 7 } } },
                });
            } else if (elProm) {
                elProm.closest('.dash-card').querySelector('.dash-vacio').hidden = false;
                elProm.hidden = true;
            }

            // Distribución de notas (histograma)
            const elDist = document.getElementById('chart-distribucion');
            const hayNotas = d.distribucion_notas.cantidades.some((n) => n > 0);
            if (elDist && hayNotas) {
                new Chart(elDist, {
                    type: 'bar',
                    data: {
                        labels: d.distribucion_notas.tramos,
                        datasets: [{
                            label: 'Cantidad de notas',
                            data: d.distribucion_notas.cantidades,
                            backgroundColor: [ROJO, ROJO, AMBAR, AZUL, VERDE, VERDE],
                        }],
                    },
                });
            } else if (elDist) {
                elDist.closest('.dash-card').querySelector('.dash-vacio').hidden = false;
                elDist.hidden = true;
            }

            // Anotaciones del mes (dona)
            const elAnot = document.getElementById('chart-anotaciones');
            const a = d.anotaciones_mes;
            if (elAnot && (a.positivas + a.negativas + a.observaciones) > 0) {
                new Chart(elAnot, {
                    type: 'doughnut',
                    data: {
                        labels: ['Positivas', 'Negativas', 'Observaciones'],
                        datasets: [{
                            data: [a.positivas, a.negativas, a.observaciones],
                            backgroundColor: [VERDE, ROJO, AMBAR],
                        }],
                    },
                });
            } else if (elAnot) {
                elAnot.closest('.dash-card').querySelector('.dash-vacio').hidden = false;
                elAnot.hidden = true;
            }
        })
        .catch(() => texto('kpi-asistencia', 'No se pudo cargar el dashboard'));
})();
