"""Escenario compartido para la suite de tests: colegio mínimo funcional."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.academico.models import Asignatura, Curso, CursoAsignatura, NivelEducacional
from apps.alumnos.models import AlumnoApoderado, Matricula, PerfilAlumno, PerfilApoderado
from apps.calificaciones.models import Evaluacion, PeriodoEvaluacion, TipoEvaluacion

PASSWORD = 'ClaveTest#2026'


def rut_valido(cuerpo: int) -> str:
    suma, mult = 0, 2
    for d in reversed(str(cuerpo)):
        suma += int(d) * mult
        mult = mult + 1 if mult < 7 else 2
    resto = 11 - suma % 11
    dv = '0' if resto == 11 else 'K' if resto == 10 else str(resto)
    return f'{cuerpo}-{dv}'


def crear_escenario():
    """Curso con 2 alumnos matriculados (con apoderados vinculados), profesor
    titular con asignatura, profesor ajeno con curso propio, admin y evaluación."""
    User = get_user_model()
    anio = timezone.localdate().year

    nivel = NivelEducacional.objects.create(nombre='1° Medio Test')
    curso = Curso.objects.create(nivel=nivel, letra='A', anio_escolar=anio)
    otro_curso = Curso.objects.create(nivel=nivel, letra='B', anio_escolar=anio)
    asignatura = Asignatura.objects.create(
        nombre='Matemática Test', codigo='MAT-T', horas_semanales=6
    )

    profesor = User.objects.create_user(
        username='prof_t', email='prof@test.cl', password=PASSWORD,
        rut=rut_valido(30000001), role='profesor',
        first_name='Pedro', last_name='Pérez')
    profesor_ajeno = User.objects.create_user(
        username='ajeno_t', email='ajeno@test.cl', password=PASSWORD,
        rut=rut_valido(30000002), role='profesor',
        first_name='Ana', last_name='Ajena')
    admin = User.objects.create_user(
        username='admin_t', email='admin@test.cl', password=PASSWORD,
        rut=rut_valido(30000003), role='admin',
        first_name='Alicia', last_name='Admin')

    ca = CursoAsignatura.objects.create(
        curso=curso, asignatura=asignatura, profesor=profesor, anio_escolar=anio)
    ca_ajena = CursoAsignatura.objects.create(
        curso=otro_curso, asignatura=asignatura, profesor=profesor_ajeno,
        anio_escolar=anio)

    alumnos, matriculas, apoderados = [], [], []
    for i in range(2):
        alum_u = User.objects.create_user(
            username=f'al{i}_t', email=f'al{i}@test.cl', password=PASSWORD,
            rut=rut_valido(31000000 + i), role='alumno',
            first_name=f'Alumno{i}', last_name='Test')
        perfil = PerfilAlumno.objects.create(
            usuario=alum_u, rut_alumno=rut_valido(32000000 + i),
            fecha_nacimiento=date(2010, 1, 1), direccion='Calle 1',
            comuna='Santiago')
        apod_u = User.objects.create_user(
            username=f'ap{i}_t', email=f'ap{i}@test.cl', password=PASSWORD,
            rut=rut_valido(33000000 + i), role='apoderado',
            first_name=f'Apoderado{i}', last_name='Test')
        apoderado = PerfilApoderado.objects.create(usuario=apod_u, relacion='madre')
        AlumnoApoderado.objects.create(
            alumno=perfil, apoderado=apoderado, es_principal=True)
        alumnos.append(perfil)
        apoderados.append(apoderado)
        matriculas.append(Matricula.objects.create(
            alumno=perfil, curso=curso, fecha_matricula=date(anio, 3, 1)))

    apod_suelto_u = User.objects.create_user(
        username='apx_t', email='apx@test.cl', password=PASSWORD,
        rut=rut_valido(33000099), role='apoderado',
        first_name='NoVinculado', last_name='Test')
    apoderado_no_vinculado = PerfilApoderado.objects.create(
        usuario=apod_suelto_u, relacion='tutor')

    periodo = PeriodoEvaluacion.objects.create(
        nombre='1S Test', anio_escolar=anio,
        fecha_inicio=date(anio, 3, 1), fecha_fin=date(anio, 7, 15))
    tipo = TipoEvaluacion.objects.create(
        nombre='Prueba Test', ponderacion_porcentaje=Decimal('60'))
    evaluacion = Evaluacion.objects.create(
        curso_asignatura=ca, periodo=periodo, tipo=tipo,
        nombre='Prueba 1 Test', fecha=date(anio, 6, 1),
        puntaje_maximo=Decimal('60'))

    return SimpleNamespace(
        anio=anio, nivel=nivel, curso=curso, otro_curso=otro_curso,
        asignatura=asignatura, profesor=profesor, profesor_ajeno=profesor_ajeno,
        admin=admin, ca=ca, ca_ajena=ca_ajena, alumnos=alumnos,
        apoderados=apoderados, apoderado_no_vinculado=apoderado_no_vinculado,
        matriculas=matriculas, periodo=periodo, tipo=tipo, evaluacion=evaluacion,
    )
