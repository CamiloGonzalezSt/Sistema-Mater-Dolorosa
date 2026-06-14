from datetime import date, timedelta

from django.core import mail
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.core.testing import crear_escenario

from .models import RegistroAsistencia


class RegistroAsistenciaModeloTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()
        cls.fecha = date(cls.esc.anio, 6, 10)

    def test_unico_por_matricula_clase_y_fecha(self):
        datos = dict(
            matricula=self.esc.matriculas[0], curso_asignatura=self.esc.ca,
            fecha=self.fecha, estado='presente', registrado_por=self.esc.profesor)
        RegistroAsistencia.objects.create(**datos)
        with self.assertRaises(IntegrityError):
            RegistroAsistencia.objects.create(**{**datos, 'estado': 'ausente'})

    def test_clean_rechaza_clase_de_otro_curso(self):
        registro = RegistroAsistencia(
            matricula=self.esc.matriculas[0],
            curso_asignatura=self.esc.ca_ajena,  # curso B, alumno del A
            fecha=self.fecha, estado='presente',
            registrado_por=self.esc.profesor)
        with self.assertRaises(ValidationError):
            registro.full_clean()


class AsistenciaVistasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()
        cls.url = f'/panel/asistencia/{cls.esc.ca.pk}/'
        cls.fecha = date(cls.esc.anio, 6, 10).isoformat()

    def _post_asistencia(self, estados):
        datos = {'fecha': self.fecha}
        for matricula, estado in zip(self.esc.matriculas, estados):
            datos[f'm{matricula.pk}-estado'] = estado
            datos[f'm{matricula.pk}-observacion'] = ''
        return self.client.post(self.url, datos)

    def test_alumno_recibe_403(self):
        self.client.force_login(self.esc.alumnos[0].usuario)
        self.assertEqual(self.client.get('/panel/asistencia/').status_code, 403)

    def test_profesor_ajeno_recibe_404(self):
        self.client.force_login(self.esc.profesor_ajeno)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_admin_accede_a_cualquier_asignatura(self):
        self.client.force_login(self.esc.admin)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_registro_y_reedicion_sin_duplicar(self):
        self.client.force_login(self.esc.profesor)
        respuesta = self._post_asistencia(['presente', 'ausente'])
        self.assertEqual(respuesta.status_code, 302)
        registros = RegistroAsistencia.objects.filter(
            curso_asignatura=self.esc.ca, fecha=self.fecha)
        self.assertEqual(registros.count(), 2)

        respuesta = self._post_asistencia(['presente', 'justificado'])
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(registros.count(), 2)
        self.assertEqual(
            registros.get(matricula=self.esc.matriculas[1]).estado, 'justificado')

    def test_alerta_email_al_alcanzar_tres_ausencias(self):
        matricula = self.esc.matriculas[1]
        base = date(self.esc.anio, 6, 10)
        for delta in (1, 2):  # dos ausencias previas en los últimos 30 días
            RegistroAsistencia.objects.create(
                matricula=matricula, curso_asignatura=self.esc.ca,
                fecha=base - timedelta(days=delta), estado='ausente',
                registrado_por=self.esc.profesor)
        mail.outbox = []
        self.client.force_login(self.esc.profesor)
        self._post_asistencia(['presente', 'ausente'])  # tercera ausencia
        alertas = [m for m in mail.outbox if 'Alerta de inasistencias' in m.subject]
        self.assertEqual(len(alertas), 1)
        self.assertIn(self.esc.apoderados[1].usuario.email, alertas[0].to)

    def test_libro_pdf(self):
        self.client.force_login(self.esc.profesor)
        RegistroAsistencia.objects.create(
            matricula=self.esc.matriculas[0], curso_asignatura=self.esc.ca,
            fecha=date(self.esc.anio, 6, 10), estado='presente',
            registrado_por=self.esc.profesor)
        respuesta = self.client.get(
            f'/panel/asistencia/{self.esc.ca.pk}/libro.pdf?mes={self.esc.anio}-06')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'application/pdf')
        self.assertTrue(respuesta.content.startswith(b'%PDF'))
