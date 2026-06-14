"""Informe de notas por alumno en PDF."""
from collections import defaultdict
from decimal import Decimal

from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer

from apps.core.pdf import ESTILO_NORMAL, ESTILO_SECCION, construir_pdf, tabla_datos

from .models import Calificacion


def informe_notas_pdf(matricula):
    calificaciones = (
        Calificacion.objects.filter(matricula=matricula)
        .select_related(
            'evaluacion__curso_asignatura__asignatura',
            'evaluacion__periodo',
            'evaluacion__tipo',
        )
        .order_by(
            'evaluacion__curso_asignatura__asignatura__nombre', 'evaluacion__fecha'
        )
    )

    por_asignatura = defaultdict(list)
    for cal in calificaciones:
        por_asignatura[cal.evaluacion.curso_asignatura.asignatura.nombre].append(cal)

    elementos = []
    promedios = []
    for asignatura, cals in por_asignatura.items():
        promedio = sum(c.nota for c in cals) / len(cals)
        promedios.append(promedio)
        filas = [['Evaluación', 'Tipo', 'Período', 'Fecha', 'Nota']]
        for c in cals:
            filas.append([
                c.evaluacion.nombre,
                c.evaluacion.tipo.nombre,
                str(c.evaluacion.periodo),
                c.evaluacion.fecha.strftime('%d-%m-%Y'),
                f'{c.nota:.1f}',
            ])
        filas.append(['', '', '', 'Promedio', f'{promedio:.2f}'])
        elementos.append(Paragraph(asignatura, ESTILO_SECCION))
        elementos.append(tabla_datos(filas, anchos=[6.5 * cm, 3 * cm, 3.5 * cm, 2.5 * cm, 2 * cm]))
        elementos.append(Spacer(1, 0.4 * cm))

    if promedios:
        general = sum(promedios, Decimal(0)) / len(promedios)
        elementos.append(Paragraph(
            f'<b>Promedio general: {general:.2f}</b>', ESTILO_SECCION
        ))
    else:
        elementos.append(Paragraph(
            'El alumno aún no registra calificaciones en este año escolar.', ESTILO_NORMAL
        ))

    alumno = matricula.alumno
    subtitulo = (
        f'Informe de calificaciones — Año escolar {matricula.anio_escolar}<br/>'
        f'Alumno(a): {alumno.usuario.get_full_name()} · RUT {alumno.rut_alumno}<br/>'
        f'Curso: {matricula.curso}'
    )
    return construir_pdf('Informe de Notas', subtitulo, elementos)
