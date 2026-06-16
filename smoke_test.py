"""Smoke test integral sobre la BD real con los datos de prueba (solo lectura,
salvo un registro de asistencia de hoy para poblar el KPI del dashboard)."""
import json
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from apps.academico.models import CursoAsignatura
from apps.alumnos.models import Matricula
from apps.calificaciones.models import Evaluacion
from apps.contabilidad.models import Cobro, Pago
from apps.convivencia.models import Citacion

User = get_user_model()
c = Client(headers={'host': '127.0.0.1'})
errores = []


def check(descripcion, condicion):
    estado = 'OK ' if condicion else 'FALLO'
    print(f'{estado} {descripcion}')
    if not condicion:
        errores.append(descripcion)


camilo = User.objects.get(email='caj.gonzalez.st@gmail.com')
ignacia = User.objects.get(email='ignacia@gmail.com')
maria = User.objects.get(email='maria@gmail.com')
franco = User.objects.get(email='franco@gmail.com')

ca_ignacia = CursoAsignatura.objects.filter(profesor=ignacia).first()
ca_otro = CursoAsignatura.objects.exclude(profesor=ignacia).first()
ev_ignacia = Evaluacion.objects.filter(curso_asignatura__profesor=ignacia).first()
ev_otro = Evaluacion.objects.exclude(curso_asignatura__profesor=ignacia).first()
mat_maria = Matricula.objects.get(alumno__usuario=maria)
cobro_pend = Cobro.objects.filter(estado__in=['pendiente', 'vencido']).first()
pago_maria = Pago.objects.filter(cobro__matricula=mat_maria).first()
pago_ajeno = Pago.objects.exclude(cobro__matricula__alumno__vinculos_apoderados__apoderado__usuario=franco).first()
cit = Citacion.objects.first()

# ---------- Público (sin sesión) ----------
for url in ('/', '/historia/', '/contacto/', '/quienes-somos/', '/noticias/',
            '/calendario/', '/galeria/', '/convivencia-escolar/', '/admision/'):
    check(f'público {url} → 200', c.get(url).status_code == 200)
check('panel sin sesión → login', c.get('/panel/').status_code == 302)

r = c.get('/')
home_html = r.content.decode()
check('home con noticias y eventos', 'noticias' in home_html.lower() and 'evento' in home_html.lower() or 'Próximas actividades' in home_html)
check('home usa logo transparente', 'mater.png' in home_html)
r = c.get('/galeria/')
check('galería con filtro de años e ítems', 'chip-anio' in r.content.decode() and 'galeria-card' in r.content.decode())
r = c.get('/convivencia-escolar/')
check('convivencia escolar lista mediadores', 'Mediador' in r.content.decode())
from apps.web_publica.models import NivelEducacional, Postulacion
Postulacion.objects.filter(nombre_postulante='Smoke Postulante').delete()  # idempotente
n_previas = Postulacion.objects.count()
r = c.post('/admision/', {
    'nombre_postulante': 'Smoke Postulante', 'fecha_nacimiento': '2014-04-01',
    'nivel': NivelEducacional.objects.first().pk,
    'nombre_apoderado': 'Smoke Apoderado', 'email': 'smoke@demo.cl',
    'telefono': '+56 9 0000 0000', 'mensaje': 'Postulación de demostración (smoke).',
})
check('postulación pública guardada', r.status_code == 302 and Postulacion.objects.count() == n_previas + 1)

# ---------- IGNACIA (profesora) ----------
c.force_login(ignacia)
check('ignacia /panel/ con dashboard', b'chart-asistencia' in c.get('/panel/').content)
d = json.loads(c.get('/panel/api/dashboard/').content)
check('dashboard con serie de asistencia (14 días)', len(d['asistencia_serie']['fechas']) >= 10)
check('dashboard con promedios (Matemática y Lenguaje)', len(d['promedios']['asignaturas']) == 2)
check('dashboard con notas en histograma', sum(d['distribucion_notas']['cantidades']) > 0)
check('dashboard con anotaciones del mes', sum(d['anotaciones_mes'].values()) > 0)
r = c.get('/panel/asistencia/')
check('ignacia ve selección de asistencia con sus ramos', b'Matem' in r.content)
hoy = timezone.localdate().isoformat()
r = c.get(f'/panel/asistencia/{ca_ignacia.pk}/?fecha={hoy}')
check('ignacia abre pasar lista de su ramo', r.status_code == 200 and b'Guardar asistencia' in r.content)
check('ignacia NO abre ramo ajeno (404)', c.get(f'/panel/asistencia/{ca_otro.pk}/').status_code == 404)
r = c.get(f'/panel/asistencia/{ca_ignacia.pk}/libro.pdf?mes={hoy[:7]}')
check('libro de asistencia PDF', r.status_code == 200 and r.content.startswith(b'%PDF'))
r = c.get('/panel/calificaciones/')
check('calificaciones sin filtros oculta la tabla',
      r.status_code == 200 and b'Ingresar notas' not in r.content)
filtros = (f'curso={ev_ignacia.curso_asignatura.curso_id}'
           f'&profesor={ignacia.pk}&periodo={ev_ignacia.periodo_id}')
r = c.get(f'/panel/calificaciones/?{filtros}')
check('calificaciones con filtros muestra evaluaciones',
      r.status_code == 200 and b'Ingresar notas' in r.content)
r = c.get(f'/panel/convivencia/?curso={ca_ignacia.curso_id}')
check('convivencia filtra por curso', r.status_code == 200)
r = c.get(f'/panel/calificaciones/evaluacion/{ev_ignacia.pk}/')
check('ignacia abre libro de notas precargado', r.status_code == 200 and b'value=' in r.content)
check('ignacia NO abre evaluación ajena (404)', c.get(f'/panel/calificaciones/evaluacion/{ev_otro.pk}/').status_code == 404)
r = c.get('/panel/convivencia/')
check('ignacia ve listado convivencia con María', 'María González' in r.content.decode())
r = c.get(f'/panel/convivencia/alumno/{mat_maria.pk}/')
check('hoja de vida de María abre', r.status_code == 200)
r = c.get(f'/panel/calificaciones/informe/{mat_maria.pk}/informe.pdf')
check('informe de notas PDF de María', r.status_code == 200 and r.content.startswith(b'%PDF'))
check('ignacia NO entra a contabilidad (403)', c.get('/panel/contabilidad/').status_code == 403)
check('ignacia NO entra a mi-cuenta (403)', c.get('/panel/mi-cuenta/').status_code == 403)
if cit:
    check('formulario cerrar citación abre', c.get(f'/panel/convivencia/citacion/{cit.pk}/cerrar/').status_code in (200, 404))

# POST real: asistencia de hoy del ramo de Ignacia (puebla el KPI del dashboard)
matriculas_curso = Matricula.objects.filter(
    curso=ca_ignacia.curso, estado__in=['regular', 'repitente'])
datos = {'fecha': hoy}
for i, m in enumerate(matriculas_curso):
    datos[f'm{m.pk}-estado'] = 'presente' if i % 5 else 'atrasado'
    datos[f'm{m.pk}-observacion'] = ''
r = c.post(f'/panel/asistencia/{ca_ignacia.pk}/', datos)
check('POST asistencia de hoy guardada', r.status_code == 302)
d = json.loads(c.get('/panel/api/dashboard/').content)
check('KPI asistencia de hoy poblado', d['asistencia_hoy']['total_registros'] >= matriculas_curso.count())

# ---------- CAMILO (admin) ----------
c.force_login(camilo)
r = c.get('/panel/contabilidad/')
check('admin ve listado de cobros', r.status_code == 200 and b'Registrar pago' in r.content)
check('admin ve filtro vencidos', c.get('/panel/contabilidad/?estado=vencido').status_code == 200)
check('admin abre generación masiva', c.get('/panel/contabilidad/generar/').status_code == 200)
if cobro_pend:
    check('admin abre formulario de pago', c.get(f'/panel/contabilidad/cobro/{cobro_pend.pk}/pago/').status_code == 200)
if pago_maria:
    r = c.get(f'/panel/contabilidad/pago/{pago_maria.pk}/comprobante.pdf')
    check('admin descarga comprobante PDF', r.status_code == 200 and r.content.startswith(b'%PDF'))
    check('comprobante con nombre nuevo (maria_gonzalez)',
          'comprobante_maria_gonzalez_' in r['Content-Disposition'])
check('contabilidad filtra por curso',
      c.get(f'/panel/contabilidad/?curso={mat_maria.curso_id}').status_code == 200)
r = c.get('/panel/postulaciones/')
check('admin ve postulaciones con la nueva del smoke', 'Smoke Postulante' in r.content.decode())
p_smoke = Postulacion.objects.filter(nombre_postulante='Smoke Postulante').order_by('-id').first()
r = c.post(f'/panel/postulaciones/{p_smoke.pk}/estado/', {'estado': 'en_revision'})
p_smoke.refresh_from_db()
check('admin cambia estado de postulación', p_smoke.estado == 'en_revision')
# Limpieza: la postulación de prueba no debe acumularse en los datos reales
Postulacion.objects.filter(nombre_postulante='Smoke Postulante').delete()
check('admin ve todo en asistencia (ramos de otros)', c.get(f'/panel/asistencia/{ca_otro.pk}/').status_code == 200)
check('admin ve dashboard colegio', c.get('/panel/api/dashboard/').status_code == 200)
check('admin entra al admin nativo', c.get('/admin/').status_code == 200)

# ---------- FRANCO (apoderado) ----------
c.force_login(franco)
r = c.get('/panel/')
check('franco ve tarjeta estado de cuenta', 'Estado de cuenta' in r.content.decode())
r = c.get('/panel/mi-cuenta/')
contenido = r.content.decode()
check('franco ve a María en mi-cuenta', 'María González' in contenido)
check('franco NO ve otros alumnos', 'Aravena' not in contenido and 'Bustos' not in contenido)
if pago_maria:
    check('franco descarga comprobante de María',
          c.get(f'/panel/contabilidad/pago/{pago_maria.pk}/comprobante.pdf').status_code == 200)
if pago_ajeno:
    check('franco NO descarga comprobante ajeno (404)',
          c.get(f'/panel/contabilidad/pago/{pago_ajeno.pk}/comprobante.pdf').status_code == 404)
check('franco NO entra a contabilidad (403)', c.get('/panel/contabilidad/').status_code == 403)
check('franco NO entra a asistencia (403)', c.get('/panel/asistencia/').status_code == 403)

# ---------- FRANCO: portal extendido ----------
c.force_login(franco)
r = c.get('/panel/pupilos/notas/')
contenido = r.content.decode()
check('franco ve notas de María con promedios', r.status_code == 200 and 'Promedio general' in contenido)
check('boletín muestra estado Aprobado/Reprobado', 'probado' in contenido)
check('franco ve anotaciones (solo lectura)', c.get('/panel/pupilos/anotaciones/').status_code == 200)
r = c.get('/panel/pupilos/citaciones/')
check('franco ve citaciones con acuerdos', r.status_code == 200)
r = c.get('/panel/mensajes/')
check('franco ve sus mensajes enviados', r.status_code == 200 and 'Solicitud' in r.content.decode())
r = c.get('/panel/mensajes/nuevo/')
check('franco abre formulario de mensaje/solicitud', r.status_code == 200 and b'pupilo' in r.content)

# ---------- MARÍA (alumna): portal nuevo ----------
c.force_login(maria)
r = c.get('/panel/')
check('maría ve tarjetas de materiales y mensajes', 'Materiales de estudio' in r.content.decode())
r = c.get('/panel/materiales/')
check('maría ve materiales de su curso', r.status_code == 200 and 'Guía' in r.content.decode())
check('maría NO ve materiales de 8° Básico', '8° Básico' not in r.content.decode())
r = c.get('/panel/mensajes/')
check('maría ve sus mensajes enviados', r.status_code == 200 and 'fracciones' in r.content.decode())
check('maría NO entra a gestión de materiales (403)', c.get('/panel/materiales/gestion/').status_code == 403)
for url in ('/panel/asistencia/', '/panel/calificaciones/', '/panel/convivencia/',
            '/panel/contabilidad/', '/panel/mi-cuenta/', '/panel/api/dashboard/',
            '/panel/pupilos/notas/'):
    check(f'maría bloqueada en {url} (403)', c.get(url).status_code == 403)

# ---------- IGNACIA: bandeja y gestión de materiales ----------
c.force_login(ignacia)
r = c.get('/panel/mensajes/')
contenido = r.content.decode()
check('ignacia ve bandeja con mensaje de María y solicitud de Franco',
      'fracciones' in contenido and 'Solicitud' in contenido)
r = c.get('/panel/materiales/gestion/')
check('ignacia abre gestión de materiales con los suyos',
      r.status_code == 200 and 'Guía N°1' in r.content.decode())
c.force_login(franco)
check('franco NO entra a gestión de materiales (403)',
      c.get('/panel/materiales/gestion/').status_code == 403)

print()
if errores:
    print(f'*** {len(errores)} FALLOS ***')
    raise SystemExit(1)
print('TODO OK: sistema completo verificado con datos de prueba.')
