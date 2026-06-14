"""Datos de prueba completos para TODO el sistema (período de marcha blanca).

Uso:
    python manage.py seed_demo            # crea todo
    python manage.py seed_demo --limpiar  # elimina lo creado

Integra las cuentas reales existentes:
  - ignacia@gmail.com (profesora): recibe asignaturas, jefatura y perfil
  - maria@gmail.com (alumna): perfil, matrícula en 7° Básico A, notas, asistencia
  - franco@gmail.com (apoderado): perfil vinculado a María, citaciones, cobros
Y crea además ~20 alumnos demo con apoderados (emails válidos en minúsculas:
alumnoNN@demo.cl / apoderadoNN@demo.cl, contraseña Demo#2026), un segundo
profesor demo, y datos en TODOS los módulos: asistencia (14 días hábiles),
calificaciones, convivencia y contabilidad (cobros pagados/parciales/
pendientes/vencidos/condonados con sus pagos y auditoría).
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import ProtectedError
from django.utils import timezone

from django.core.files.base import ContentFile

from apps.academico.models import (
    Asignatura, Curso, CursoAsignatura, MaterialAcademico, NivelEducacional,
)
from apps.comunicaciones.models import Mensaje
from apps.web_publica.models import (
    EventoCalendario, ItemGaleria, Noticia, Postulacion,
)
from apps.alumnos.models import AlumnoApoderado, Matricula, PerfilAlumno, PerfilApoderado
from apps.asistencia.models import RegistroAsistencia
from apps.calificaciones.models import (
    Calificacion, Evaluacion, PeriodoEvaluacion, TipoEvaluacion,
)
from apps.contabilidad.models import Cobro, Pago, TipoArancel
from apps.convivencia.models import Anotacion, Citacion
from apps.profesores.models import PerfilProfesor

User = get_user_model()

NIVELES = ['7° Básico', '8° Básico']
NOMBRES = [
    ('Sofía', 'Aravena'), ('Mateo', 'Bustos'), ('Isidora', 'Cárcamo'),
    ('Lucas', 'Donoso'), ('Emilia', 'Escobar'), ('Tomás', 'Fuentes'),
    ('Florencia', 'Garrido'), ('Benjamín', 'Hidalgo'), ('Antonia', 'Ibáñez'),
    ('Vicente', 'Jara'), ('Maite', 'Klein'), ('Joaquín', 'Lagos'),
    ('Catalina', 'Maldonado'), ('Agustín', 'Navarro'), ('Trinidad', 'Ortiz'),
    ('Martín', 'Paredes'), ('Josefa', 'Quiroz'), ('Diego', 'Riquelme'),
    ('Amanda', 'Saavedra'), ('Cristóbal', 'Toledo'),
]
ARANCELES = [
    ('Matrícula', Decimal('250000')),
    ('Mensualidad', Decimal('150000')),
    ('Taller extraprogramático', Decimal('25000')),
]


def rut_con_dv(cuerpo: int) -> str:
    suma, mult = 0, 2
    for d in reversed(str(cuerpo)):
        suma += int(d) * mult
        mult = mult + 1 if mult < 7 else 2
    resto = 11 - suma % 11
    dv = '0' if resto == 11 else 'K' if resto == 10 else str(resto)
    return f'{cuerpo}-{dv}'


class Command(BaseCommand):
    help = 'Crea (o elimina con --limpiar) los datos de prueba de todo el sistema.'

    def add_arguments(self, parser):
        parser.add_argument('--limpiar', action='store_true')

    def handle(self, *args, **options):
        if options['limpiar']:
            self._limpiar()
            self.stdout.write(self.style.SUCCESS('Datos de prueba eliminados.'))
            return
        random.seed(2026)
        self._limpiar()
        with transaction.atomic():
            resumen = self._crear()
        for linea in resumen:
            self.stdout.write(f'  {linea}')
        self.stdout.write(self.style.SUCCESS(
            'Datos de prueba creados. Cuentas demo: alumnoNN@demo.cl / '
            'apoderadoNN@demo.cl / profesor.demo@demo.cl (clave Demo#2026).'
        ))

    # ------------------------------------------------------------------
    def _usuario_real(self, email, role, nombre, apellido):
        """Obtiene la cuenta real si existe (completando nombre si falta);
        si no existe, la crea como demo."""
        usuario = User.objects.filter(email=email).first()
        if usuario is None:
            return User.objects.create_user(
                username=email.split('@')[0] + '_demo', email=email,
                password='Demo#2026', rut=rut_con_dv(29000000 + ord(email[0])),
                role=role, first_name=nombre, last_name=apellido)
        if not usuario.get_full_name():
            usuario.first_name = nombre
            usuario.last_name = apellido
            usuario.save(update_fields=['first_name', 'last_name'])
        return usuario

    def _crear(self):
        hoy = timezone.localdate()
        anio = hoy.year
        admin = User.objects.filter(role='admin').order_by('id').first()

        # --- Cuentas reales integradas ---
        ignacia = self._usuario_real('ignacia@gmail.com', 'profesor', 'Ignacia', 'Cid')
        maria = self._usuario_real('maria@gmail.com', 'alumno', 'María', 'González')
        franco = self._usuario_real('franco@gmail.com', 'apoderado', 'Franco', 'González')

        perfil_ignacia, _ = PerfilProfesor.objects.get_or_create(
            usuario=ignacia,
            defaults={'especialidad': 'Educación General Básica',
                      'titulo': 'Profesora de Estado'})
        profe2 = User.objects.create_user(
            username='profesor_demo', email='profesor.demo@demo.cl',
            password='Demo#2026', rut=rut_con_dv(20999999), role='profesor',
            first_name='Roberto', last_name='Demo')
        perfil_profe2 = PerfilProfesor.objects.create(
            usuario=profe2, especialidad='Lenguaje', titulo='Profesor de Estado')

        # --- Estructura académica ---
        asig_mat = Asignatura.objects.create(nombre='Matemática', codigo='DEMO-MAT', horas_semanales=6)
        asig_len = Asignatura.objects.create(nombre='Lenguaje', codigo='DEMO-LEN', horas_semanales=6)
        asig_his = Asignatura.objects.create(nombre='Historia', codigo='DEMO-HIS', horas_semanales=4)
        cursos, cas = [], []
        for i, nombre_nivel in enumerate(NIVELES):
            nivel, _ = NivelEducacional.objects.get_or_create(nombre=nombre_nivel)
            curso = Curso.objects.create(
                nivel=nivel, letra='A', anio_escolar=anio, capacidad=35,
                profesor_jefe=perfil_ignacia if i == 0 else perfil_profe2)
            cursos.append(curso)
            for asig, profe in ((asig_mat, ignacia), (asig_len, ignacia), (asig_his, profe2)):
                cas.append(CursoAsignatura.objects.create(
                    curso=curso, asignatura=asig, profesor=profe, anio_escolar=anio))

        # --- Alumnos y apoderados ---
        matriculas_por_curso = {c.pk: [] for c in cursos}

        perfil_maria, _ = PerfilAlumno.objects.get_or_create(
            usuario=maria,
            defaults={'rut_alumno': rut_con_dv(24500000),
                      'fecha_nacimiento': hoy.replace(year=anio - 13),
                      'direccion': 'Av. Principal 1234', 'comuna': 'Santiago'})
        perfil_franco, _ = PerfilApoderado.objects.get_or_create(
            usuario=franco, defaults={'relacion': 'padre'})
        AlumnoApoderado.objects.get_or_create(
            alumno=perfil_maria, apoderado=perfil_franco,
            defaults={'es_principal': True})
        matriculas_por_curso[cursos[0].pk].append(Matricula.objects.create(
            alumno=perfil_maria, curso=cursos[0],
            fecha_matricula=hoy.replace(month=3, day=1)))

        for i, (nombre, apellido) in enumerate(NOMBRES):
            curso = cursos[0] if i < 10 else cursos[1]
            alum_u = User.objects.create_user(
                username=f'alumno{i:02d}_demo', email=f'alumno{i:02d}@demo.cl',
                password='Demo#2026', rut=rut_con_dv(21000000 + i),
                role='alumno', first_name=nombre, last_name=apellido)
            perfil = PerfilAlumno.objects.create(
                usuario=alum_u, rut_alumno=rut_con_dv(22000000 + i),
                fecha_nacimiento=hoy.replace(year=anio - 13) - timedelta(days=i * 37),
                direccion=f'Pasaje Los Aromos {100 + i}', comuna='Santiago')
            apod_u = User.objects.create_user(
                username=f'apoderado{i:02d}_demo', email=f'apoderado{i:02d}@demo.cl',
                password='Demo#2026', rut=rut_con_dv(23000000 + i),
                role='apoderado', first_name=f'Apoderado(a) {nombre}',
                last_name=apellido)
            apod = PerfilApoderado.objects.create(
                usuario=apod_u, relacion=random.choice(['padre', 'madre', 'tutor']))
            AlumnoApoderado.objects.create(alumno=perfil, apoderado=apod, es_principal=True)
            matriculas_por_curso[curso.pk].append(Matricula.objects.create(
                alumno=perfil, curso=curso, fecha_matricula=hoy.replace(month=3, day=1)))

        todas = [m for ms in matriculas_por_curso.values() for m in ms]
        # Variedad de estados de matrícula (sin tocar a María ni los 3 primeros)
        todas[-1].estado = Matricula.Estado.RETIRADO
        todas[-1].save()

        # --- Asistencia: 14 días hábiles, todas las clases ---
        estados = ['presente'] * 17 + ['ausente', 'atrasado', 'justificado']
        dia, habiles, n_asistencia = hoy, 0, 0
        vigentes = {c.pk: [m for m in ms if m.estado in ('regular', 'repitente')]
                    for c, ms in ((c, matriculas_por_curso[c.pk]) for c in cursos)}
        while habiles < 14:
            if dia.weekday() < 5:
                for ca in cas:
                    for m in vigentes[ca.curso_id]:
                        RegistroAsistencia.objects.create(
                            matricula=m, curso_asignatura=ca, fecha=dia,
                            estado=random.choice(estados),
                            registrado_por=ca.profesor)
                        n_asistencia += 1
                habiles += 1
            dia -= timedelta(days=1)

        # --- Calificaciones ---
        periodo1 = PeriodoEvaluacion.objects.create(
            nombre='1° Semestre', anio_escolar=anio,
            fecha_inicio=hoy.replace(month=3, day=1), fecha_fin=hoy.replace(month=7, day=15))
        PeriodoEvaluacion.objects.create(
            nombre='2° Semestre', anio_escolar=anio,
            fecha_inicio=hoy.replace(month=7, day=28), fecha_fin=hoy.replace(month=12, day=15))
        tipo_prueba = TipoEvaluacion.objects.create(nombre='Prueba', ponderacion_porcentaje=Decimal('60'))
        tipo_trabajo = TipoEvaluacion.objects.create(nombre='Trabajo', ponderacion_porcentaje=Decimal('40'))
        n_notas = 0
        for ca in cas:
            for n, tipo in ((1, tipo_prueba), (2, tipo_prueba), (3, tipo_trabajo)):
                ev = Evaluacion.objects.create(
                    curso_asignatura=ca, periodo=periodo1, tipo=tipo,
                    nombre=f'{tipo.nombre} N°{n} {ca.asignatura.nombre}',
                    fecha=hoy - timedelta(days=7 * n), puntaje_maximo=Decimal('60'))
                for m in vigentes[ca.curso_id]:
                    nota = Decimal(str(round(min(7.0, max(2.0, random.gauss(5.3, 1.0))), 1)))
                    Calificacion.objects.create(
                        evaluacion=ev, matricula=m,
                        puntaje_obtenido=(nota / Decimal('7') * 60).quantize(Decimal('0.01')),
                        nota=nota)
                    n_notas += 1

        # --- Convivencia ---
        textos = {
            'positiva': 'Participa activamente y colabora con sus compañeros.',
            'negativa': 'Interrumpe reiteradamente el desarrollo de la clase.',
            'observacion': 'Se observa desmotivación; se sugiere conversar en casa.',
        }
        objetivo_anotaciones = [todas[0]] + random.sample(todas[1:], 11)
        for m in objetivo_anotaciones:
            tipo_a = random.choice(list(textos))
            Anotacion.objects.create(
                matricula=m, tipo=tipo_a, descripcion=textos[tipo_a],
                fecha=hoy - timedelta(days=random.randint(0, max(hoy.day - 1, 1))),
                registrado_por=ignacia,
                toma_conocimiento=random.choice([True, False]))
        for m, estado in ((todas[0], 'programada'), (todas[1], 'realizada'), (todas[2], 'programada')):
            vinculo = m.alumno.vinculos_apoderados.first()
            Citacion.objects.create(
                matricula=m, apoderado=vinculo.apoderado,
                fecha_hora=timezone.now() + timedelta(days=3),
                motivo='Revisar avance académico y compromisos de apoyo.',
                estado=estado,
                acuerdos='Apoyo en el hogar y control en 2 semanas.' if estado == 'realizada' else '',
                registrado_por=ignacia)

        # --- Contabilidad ---
        aranceles = {n: TipoArancel.objects.create(nombre=n, monto_base=monto,
                                                   descripcion=f'{n} año {anio}')
                     for n, monto in ARANCELES}
        mensualidad = aranceles['Mensualidad']
        matricula_ar = aranceles['Matrícula']
        n_cobros = n_pagos = 0
        for m in todas:
            # Matrícula anual: todas pagadas
            cobro = Cobro.objects.create(
                matricula=m, tipo_arancel=matricula_ar, periodo=f'{anio}-matricula',
                monto=matricula_ar.monto_base,
                fecha_vencimiento=hoy.replace(month=3, day=5))
            Pago.objects.create(
                cobro=cobro, monto_pagado=cobro.monto,
                fecha_pago=hoy.replace(month=3, day=random.randint(1, 5)),
                medio_pago=random.choice(['efectivo', 'transferencia']),
                registrado_por=admin)
            n_cobros += 1
            n_pagos += 1
            # Mensualidades marzo→mes actual con estados variados
            for mes in range(3, hoy.month + 1):
                vence = hoy.replace(month=mes, day=5)
                cobro = Cobro.objects.create(
                    matricula=m, tipo_arancel=mensualidad, periodo=f'{anio}-{mes:02d}',
                    monto=mensualidad.monto_base, fecha_vencimiento=vence)
                n_cobros += 1
                suerte = random.random()
                if suerte < 0.65:  # pagada completa
                    Pago.objects.create(
                        cobro=cobro, monto_pagado=cobro.monto,
                        fecha_pago=min(vence, hoy),
                        medio_pago=random.choice(['efectivo', 'transferencia', 'cheque']),
                        registrado_por=admin)
                    n_pagos += 1
                elif suerte < 0.78:  # abono parcial
                    Pago.objects.create(
                        cobro=cobro, monto_pagado=cobro.monto / 2,
                        fecha_pago=min(vence, hoy), medio_pago='transferencia',
                        observacion='Abono parcial acordado con secretaría.',
                        registrado_por=admin)
                    n_pagos += 1
                    cobro.refrescar_estado()
                elif suerte < 0.83:  # condonada
                    cobro.estado = Cobro.Estado.CONDONADO
                    cobro.save(update_fields=['estado'])
                else:  # sin pago: pendiente o vencida según fecha
                    cobro.refrescar_estado()

        # --- Materiales académicos ---
        for ca in cas:
            for n in (1, 2):
                MaterialAcademico.objects.create(
                    curso_asignatura=ca, periodo=periodo1,
                    unidad=f'Unidad {n}',
                    titulo=f'Guía N°{n} de {ca.asignatura.nombre} — {ca.curso}',
                    descripcion='Material de ejercitación para la unidad.',
                    archivo=ContentFile(
                        f'Guia de practica N°{n} de {ca.asignatura.nombre}.\n'
                        f'(Archivo de demostracion)\n'.encode(),
                        name=f'guia_{ca.pk}_{n}.txt'),
                    subido_por=ca.profesor)

        # --- Mensajes: María e Ignacia, Franco solicita citación ---
        Mensaje.objects.create(
            remitente=maria, destinatario=ignacia, pupilo=perfil_maria,
            asunto='Consulta por la prueba de fracciones',
            cuerpo='Profesora, ¿la prueba del lunes incluye la Unidad 2? Gracias.')
        Mensaje.objects.create(
            remitente=franco, destinatario=ignacia, pupilo=perfil_maria,
            tipo=Mensaje.Tipo.SOLICITUD_CITACION,
            asunto='Solicitud de reunión por avance de María',
            cuerpo='Estimada profesora, quisiera coordinar una reunión para conversar sobre el avance de María. Quedo atento a su disponibilidad.')
        Mensaje.objects.create(
            remitente=User.objects.get(username='alumno00_demo'),
            destinatario=ignacia,
            pupilo=PerfilAlumno.objects.get(usuario__username='alumno00_demo'),
            asunto='No puedo descargar la guía',
            cuerpo='Profesora, el archivo de la Unidad 1 no me abre en el celular.',
            leido=True)

        # --- Contenido institucional del sitio público ---
        self._crear_contenido_publico(hoy, anio, cursos)

        return [
            f'Cursos: {len(cursos)} | Asignaturas de curso: {len(cas)}',
            f'Materiales: {MaterialAcademico.objects.count()} | Mensajes: {Mensaje.objects.count()}',
            f'Noticias: {Noticia.objects.count()} | Eventos: {EventoCalendario.objects.count()} | '
            f'Galería: {ItemGaleria.objects.count()} | '
            f'Postulaciones: {Postulacion.objects.count()}',
            f'Alumnos matriculados: {len(todas)} (incluye María González con Franco de apoderado)',
            f'Registros de asistencia: {n_asistencia}',
            f'Calificaciones: {n_notas} en {Evaluacion.objects.count()} evaluaciones',
            f'Anotaciones: {Anotacion.objects.count()} | Citaciones: {Citacion.objects.count()}',
            f'Cobros: {n_cobros} | Pagos: {n_pagos}',
        ]

    # ------------------------------------------------------------------
    def _crear_contenido_publico(self, hoy, anio, cursos):
        from io import BytesIO

        from PIL import Image, ImageDraw

        def imagen_demo(texto, color):
            img = Image.new('RGB', (800, 600), color)
            dibujo = ImageDraw.Draw(img)
            dibujo.text((40, 280), texto, fill='white')
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=70)
            return ContentFile(buffer.getvalue(), name=f'{texto.lower().replace(" ", "_")}.jpg')

        # Las noticias reales se importan con `python manage.py importar_noticias`
        # desde el sitio oficial; el seed ya no crea noticias de ejemplo.

        eventos = [
            (5, 'Reunión de apoderados', 'Salas de cada curso', '19:00'),
            (9, 'Misa de aniversario del colegio', 'Capilla', '10:00'),
            (14, 'Salida pedagógica 7° Básico', 'Museo Interactivo Mirador', '09:00'),
            (21, 'Jornada de convivencia escolar', 'Patio central', None),
            (30, 'Cierre del semestre', 'Gimnasio', '12:00'),
        ]
        for dias, titulo, lugar, hora in eventos:
            EventoCalendario.objects.create(
                titulo=titulo, lugar=lugar,
                hora=hora or None,
                descripcion='Actividad abierta a la comunidad escolar.',
                fecha=hoy + timedelta(days=dias))

        for i in range(6):
            ItemGaleria.objects.create(
                titulo=f'Actividad escolar {i + 1}',
                anio=anio if i < 4 else anio - 1,
                imagen=imagen_demo(f'Galeria {i + 1}', (46 + i * 20, 90, 140)))
        ItemGaleria.objects.create(
            titulo='Himno del colegio (video)', anio=anio,
            video_url='https://www.youtube.com/embed/dQw4w9WgXcQ')

        for i, nombre in enumerate(['Pedro Soto Rivas', 'Antonia Vega Luna', 'Camila Ríos Pino']):
            Postulacion.objects.create(
                nombre_postulante=nombre,
                fecha_nacimiento=hoy.replace(year=anio - 12) - timedelta(days=i * 90),
                nivel=cursos[0].nivel,
                nombre_apoderado=f'Apoderado(a) de {nombre.split()[0]}',
                email=f'postulante{i:02d}@demo.cl', telefono='+56 9 5555 000' + str(i),
                mensaje='Postulación de demostración enviada desde el formulario público.',
                estado=['nueva', 'en_revision', 'aceptada'][i])

    # ------------------------------------------------------------------
    def _limpiar(self):
        # Contenido demo del sitio público. NO se tocan las noticias ni la galería
        # reales (importadas con `importar_noticias` / `importar_galeria`); solo se
        # eliminan los ítems de demostración identificables por su título.
        EventoCalendario.objects.all().delete()
        ItemGaleria.objects.filter(
            titulo__regex=r'^(Actividad escolar [0-9]+|Himno del colegio)'
        ).delete()
        Postulacion.objects.filter(mensaje__icontains='demostración').delete()
        en_cursos_demo = {'matricula__curso__nivel__nombre__in': NIVELES}
        Mensaje.objects.filter(
            destinatario__asignaturas_dictadas__curso__nivel__nombre__in=NIVELES
        ).distinct().delete()
        MaterialAcademico.objects.filter(
            curso_asignatura__curso__nivel__nombre__in=NIVELES).delete()
        Pago.history.model.objects.filter(cobro__matricula__curso__nivel__nombre__in=NIVELES).delete()
        Pago.objects.filter(cobro__matricula__curso__nivel__nombre__in=NIVELES).delete()
        Cobro.objects.filter(**en_cursos_demo).delete()
        TipoArancel.objects.filter(nombre__in=[n for n, _ in ARANCELES]).delete()
        Calificacion.history.model.objects.filter(**en_cursos_demo).delete()
        Calificacion.objects.filter(**en_cursos_demo).delete()
        Evaluacion.objects.filter(curso_asignatura__curso__nivel__nombre__in=NIVELES).delete()
        PeriodoEvaluacion.objects.filter(nombre__in=['1° Semestre', '2° Semestre']).delete()
        TipoEvaluacion.objects.filter(nombre__in=['Prueba', 'Trabajo']).delete()
        Anotacion.history.model.objects.filter(**en_cursos_demo).delete()
        Anotacion.objects.filter(**en_cursos_demo).delete()
        Citacion.objects.filter(**en_cursos_demo).delete()
        RegistroAsistencia.objects.filter(**en_cursos_demo).delete()
        Matricula.objects.filter(curso__nivel__nombre__in=NIVELES).delete()
        CursoAsignatura.objects.filter(asignatura__codigo__startswith='DEMO-').delete()
        PerfilAlumno.objects.filter(usuario__username__endswith='_demo').delete()
        PerfilApoderado.objects.filter(usuario__username__endswith='_demo').delete()
        PerfilProfesor.objects.filter(usuario__username__endswith='_demo').delete()
        User.objects.filter(username__endswith='_demo').delete()
        for curso in Curso.objects.filter(nivel__nombre__in=NIVELES, letra='A'):
            try:
                curso.delete()
            except ProtectedError:
                pass
        for nivel in NivelEducacional.objects.filter(nombre__in=NIVELES):
            try:
                nivel.delete()
            except ProtectedError:
                pass
        Asignatura.objects.filter(codigo__startswith='DEMO-').delete()
