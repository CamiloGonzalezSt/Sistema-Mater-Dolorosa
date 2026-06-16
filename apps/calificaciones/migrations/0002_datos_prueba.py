"""Data migration: perfiles, vínculos, matrículas, asignaturas y notas de prueba.

Complementa accounts.0002 (que crea los usuarios). Crea:
  - Perfiles de alumno/apoderado y sus vínculos
  - Matrículas (Felipe -> 2° Medio, Javiera -> 8° Básico)
  - 8 asignaturas dictadas por un profesor demo
  - 4 evaluaciones por asignatura con su nota (notas pseudo-aleatorias fijas)

Se ejecuta con `migrate` (que SÍ corre en el Build Command de Render).
Idempotente: todo via get_or_create.
"""
import random
import sys
from datetime import date
from decimal import Decimal

from django.db import migrations

ANIO = 2026

# (nombre, código, horas semanales)
ASIGNATURAS = [
    ('Matemática', 'MAT', 6),
    ('Lenguaje', 'LEN', 6),
    ('Historia', 'HIS', 4),
    ('Ciencias', 'CIE', 4),
    ('Química', 'QUI', 3),
    ('Educación Física', 'EDF', 2),
    ('Música', 'MUS', 2),
    ('Tecnología', 'TEC', 2),
]

# (email_alumno, nivel, letra, rut_alumno)
ALUMNOS = [
    ('fsoto@gmail.com', '2° Medio', 'A', '23456789-6'),
    ('jmunoz@gmail.com', '8° Básico', 'A', '45678901-3'),
]

# (email_apoderado, email_alumno)
VINCULOS = [
    ('gcastro@gmail.com', 'fsoto@gmail.com'),
    ('icid@gmail.com', 'jmunoz@gmail.com'),
]

EVALUACIONES = [
    ('Prueba 1', date(2026, 3, 20)),
    ('Prueba 2', date(2026, 4, 20)),
    ('Prueba 3', date(2026, 5, 20)),
    ('Trabajo Final', date(2026, 6, 10)),
]


def crear_datos(apps, schema_editor):
    # No sembrar datos demo durante la suite de tests (la BD de test debe
    # quedar limpia; varios tests asumen conteos desde cero). Sí corre en
    # `migrate` normal (Render, desarrollo).
    if 'test' in sys.argv:
        return

    User = apps.get_model('accounts', 'CustomUser')
    PerfilAlumno = apps.get_model('alumnos', 'PerfilAlumno')
    PerfilApoderado = apps.get_model('alumnos', 'PerfilApoderado')
    AlumnoApoderado = apps.get_model('alumnos', 'AlumnoApoderado')
    Matricula = apps.get_model('alumnos', 'Matricula')
    Nivel = apps.get_model('academico', 'NivelEducacional')
    Curso = apps.get_model('academico', 'Curso')
    Asignatura = apps.get_model('academico', 'Asignatura')
    CursoAsignatura = apps.get_model('academico', 'CursoAsignatura')
    Periodo = apps.get_model('calificaciones', 'PeriodoEvaluacion')
    TipoEval = apps.get_model('calificaciones', 'TipoEvaluacion')
    Evaluacion = apps.get_model('calificaciones', 'Evaluacion')
    Calificacion = apps.get_model('calificaciones', 'Calificacion')

    # Profesor que dicta todas las asignaturas (RUT 22222222-2 válido)
    profesor, _ = User.objects.get_or_create(
        email='docente@materdolorosa.cl',
        defaults={
            'username': 'docente',
            'first_name': 'Docente',
            'last_name': 'Demo',
            'role': 'profesor',
            'rut': '22222222-2',
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
        },
    )

    # Asignaturas (compartidas entre cursos)
    asignaturas = {}
    for nombre, codigo, horas in ASIGNATURAS:
        a, _ = Asignatura.objects.get_or_create(
            codigo=codigo,
            defaults={'nombre': nombre, 'horas_semanales': horas},
        )
        asignaturas[codigo] = a

    # Período y tipo de evaluación
    periodo, _ = Periodo.objects.get_or_create(
        nombre='1° Semestre',
        anio_escolar=ANIO,
        defaults={'fecha_inicio': date(2026, 3, 1), 'fecha_fin': date(2026, 7, 15)},
    )
    tipo, _ = TipoEval.objects.get_or_create(
        nombre='Prueba',
        defaults={'ponderacion_porcentaje': Decimal('100.00')},
    )

    # Por cada alumno: perfil, curso, matrícula, asignaturas, evaluaciones y notas
    for email, nivel_nombre, letra, rut_alumno in ALUMNOS:
        user_alumno = User.objects.get(email=email)
        perfil, _ = PerfilAlumno.objects.get_or_create(
            usuario=user_alumno,
            defaults={
                'rut_alumno': rut_alumno,
                'fecha_nacimiento': date(2010, 5, 15),
                'direccion': 'Av. Recoleta 4500',
                'comuna': 'Huechuraba',
            },
        )

        nivel, _ = Nivel.objects.get_or_create(nombre=nivel_nombre)
        curso, _ = Curso.objects.get_or_create(
            nivel=nivel, letra=letra, anio_escolar=ANIO,
            defaults={'capacidad': 35},
        )

        # anio_escolar se setea explícito: el save() histórico no lo autocompleta
        matricula, _ = Matricula.objects.get_or_create(
            alumno=perfil, anio_escolar=ANIO,
            defaults={
                'curso': curso,
                'fecha_matricula': date(2026, 3, 1),
                'estado': 'regular',
            },
        )

        for nombre, codigo, horas in ASIGNATURAS:
            ca, _ = CursoAsignatura.objects.get_or_create(
                curso=curso, asignatura=asignaturas[codigo], anio_escolar=ANIO,
                defaults={'profesor': profesor},
            )
            rng = random.Random(f'{email}-{codigo}')
            for nombre_ev, fecha_ev in EVALUACIONES:
                ev, _ = Evaluacion.objects.get_or_create(
                    curso_asignatura=ca, periodo=periodo, tipo=tipo, nombre=nombre_ev,
                    defaults={'fecha': fecha_ev, 'puntaje_maximo': Decimal('100.00')},
                )
                nota = Decimal(str(round(rng.uniform(3.0, 7.0), 1)))
                puntaje = (nota / Decimal('7.0') * Decimal('100')).quantize(Decimal('0.01'))
                Calificacion.objects.get_or_create(
                    evaluacion=ev, matricula=matricula,
                    defaults={'puntaje_obtenido': puntaje, 'nota': nota},
                )

    # Vínculos apoderado -> alumno
    for apo_email, alu_email in VINCULOS:
        apo_user = User.objects.get(email=apo_email)
        perfil_apo, _ = PerfilApoderado.objects.get_or_create(
            usuario=apo_user, defaults={'relacion': 'madre'},
        )
        perfil_alu = PerfilAlumno.objects.get(usuario__email=alu_email)
        AlumnoApoderado.objects.get_or_create(
            alumno=perfil_alu, apoderado=perfil_apo,
            defaults={'es_principal': True},
        )


def borrar_datos(apps, schema_editor):
    User = apps.get_model('accounts', 'CustomUser')
    PerfilAlumno = apps.get_model('alumnos', 'PerfilAlumno')
    Calificacion = apps.get_model('calificaciones', 'Calificacion')

    emails_alumno = [a[0] for a in ALUMNOS]
    matriculas = [
        m
        for p in PerfilAlumno.objects.filter(usuario__email__in=emails_alumno)
        for m in p.matriculas.all()
    ]
    Calificacion.objects.filter(matricula__in=matriculas).delete()
    PerfilAlumno.objects.filter(usuario__email__in=emails_alumno).delete()
    User.objects.filter(email='docente@materdolorosa.cl').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('calificaciones', '0001_initial'),
        ('accounts', '0002_usuarios_prueba'),
        ('alumnos', '0002_remove_perfilalumno_curso_and_more'),
        ('academico', '0003_materialacademico'),
    ]

    operations = [
        migrations.RunPython(crear_datos, borrar_datos),
    ]
