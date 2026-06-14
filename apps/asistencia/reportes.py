"""Libro de asistencia mensual por asignatura de curso, en PDF apaisado."""
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph

from apps.alumnos.models import Matricula
from apps.core.pdf import ESTILO_NORMAL, construir_pdf, tabla_datos

from .models import RegistroAsistencia

SIMBOLO = {'presente': 'P', 'ausente': 'A', 'justificado': 'J', 'atrasado': 'T'}
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def libro_asistencia_pdf(curso_asignatura, anio, mes):
    registros = (
        RegistroAsistencia.objects.filter(
            curso_asignatura=curso_asignatura, fecha__year=anio, fecha__month=mes
        )
        .select_related('matricula')
        .order_by('fecha')
    )
    fechas = sorted({r.fecha for r in registros})
    por_celda = {(r.matricula_id, r.fecha): SIMBOLO[r.estado] for r in registros}

    matriculas = (
        Matricula.objects.filter(
            curso=curso_asignatura.curso,
            estado__in=[Matricula.Estado.REGULAR, Matricula.Estado.REPITENTE],
        )
        .select_related('alumno__usuario')
        .order_by('alumno__usuario__last_name', 'alumno__usuario__first_name')
    )

    elementos = []
    if fechas:
        filas = [['Alumno'] + [f.strftime('%d') for f in fechas] + ['% Asist.']]
        for m in matriculas:
            celdas = [por_celda.get((m.pk, f), '·') for f in fechas]
            con_registro = [c for c in celdas if c != '·']
            presentes = sum(1 for c in con_registro if c in ('P', 'T'))
            pct = f'{100 * presentes / len(con_registro):.0f}%' if con_registro else '—'
            filas.append([m.alumno.usuario.get_full_name()] + celdas + [pct])
        anchos = [6 * cm] + [0.62 * cm] * len(fechas) + [1.6 * cm]
        elementos.append(tabla_datos(filas, anchos=anchos, fuente=7.5))
        elementos.append(Paragraph(
            'P: presente · A: ausente · J: justificado · T: atrasado · ·: sin registro. '
            'El % considera presentes y atrasados sobre los días con registro.',
            ESTILO_NORMAL,
        ))
    else:
        elementos.append(Paragraph(
            'No hay registros de asistencia para este mes.', ESTILO_NORMAL
        ))

    subtitulo = (
        f'Libro de asistencia — {MESES[mes - 1].capitalize()} {anio}<br/>'
        f'{curso_asignatura.asignatura.nombre} · {curso_asignatura.curso} · '
        f'Profesor(a): {curso_asignatura.profesor.get_full_name()}'
    )
    return construir_pdf('Libro de Asistencia', subtitulo, elementos, apaisado=True)
