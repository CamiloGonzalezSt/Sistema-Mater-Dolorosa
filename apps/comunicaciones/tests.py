from django.core import mail
from django.test import TestCase

from apps.core.testing import crear_escenario

from .models import Mensaje


class MensajesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()
        cls.alumno_u = cls.esc.alumnos[0].usuario
        cls.apoderado_u = cls.esc.apoderados[0].usuario

    def test_alumno_envia_mensaje_con_copia_email(self):
        self.client.force_login(self.alumno_u)
        mail.outbox = []
        respuesta = self.client.post('/panel/mensajes/nuevo/', {
            'destinatario': self.esc.profesor.pk,
            'asunto': 'Duda de la prueba',
            'cuerpo': '¿Entra la unidad 2?',
        })
        self.assertEqual(respuesta.status_code, 302)
        mensaje = Mensaje.objects.get()
        self.assertEqual(mensaje.remitente, self.alumno_u)
        self.assertEqual(mensaje.pupilo, self.esc.alumnos[0])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.esc.profesor.email, mail.outbox[0].to)

    def test_alumno_no_puede_escribir_a_profesor_que_no_le_hace_clases(self):
        self.client.force_login(self.alumno_u)
        respuesta = self.client.post('/panel/mensajes/nuevo/', {
            'destinatario': self.esc.profesor_ajeno.pk,
            'asunto': 'Hola', 'cuerpo': 'Hola',
        })
        self.assertEqual(respuesta.status_code, 200)  # re-render con error
        self.assertEqual(Mensaje.objects.count(), 0)

    def test_apoderado_solicita_citacion(self):
        self.client.force_login(self.apoderado_u)
        mail.outbox = []
        respuesta = self.client.post('/panel/mensajes/nuevo/', {
            'pupilo': self.esc.alumnos[0].pk,
            'destinatario': self.esc.profesor.pk,
            'tipo': 'solicitud_citacion',
            'asunto': 'Solicito reunión',
            'cuerpo': 'Quisiera conversar sobre el avance.',
        })
        self.assertEqual(respuesta.status_code, 302)
        mensaje = Mensaje.objects.get()
        self.assertEqual(mensaje.tipo, 'solicitud_citacion')
        self.assertIn('Solicitud de citación', mail.outbox[0].subject)

    def test_apoderado_no_puede_usar_pupilo_ajeno(self):
        self.client.force_login(self.apoderado_u)
        respuesta = self.client.post('/panel/mensajes/nuevo/', {
            'pupilo': self.esc.alumnos[1].pk,  # pupilo de otro apoderado
            'destinatario': self.esc.profesor.pk,
            'tipo': 'mensaje', 'asunto': 'X', 'cuerpo': 'X',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Mensaje.objects.count(), 0)

    def test_bandeja_del_profesor_y_marcar_leido(self):
        mensaje = Mensaje.objects.create(
            remitente=self.alumno_u, destinatario=self.esc.profesor,
            asunto='Consulta', cuerpo='Texto')
        otro = Mensaje.objects.create(
            remitente=self.alumno_u, destinatario=self.esc.profesor_ajeno,
            asunto='Para otro profesor', cuerpo='Texto')
        self.client.force_login(self.esc.profesor)
        respuesta = self.client.get('/panel/mensajes/')
        self.assertContains(respuesta, 'Consulta')
        self.assertNotContains(respuesta, 'Para otro profesor')

        self.client.post(f'/panel/mensajes/{mensaje.pk}/leido/')
        mensaje.refresh_from_db()
        self.assertTrue(mensaje.leido)
        # No puede marcar mensajes ajenos
        respuesta = self.client.post(f'/panel/mensajes/{otro.pk}/leido/')
        self.assertEqual(respuesta.status_code, 404)
