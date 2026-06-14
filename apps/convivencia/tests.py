from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.core.testing import crear_escenario

from .models import Anotacion, Citacion


class CitacionModeloTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()

    def test_clean_rechaza_apoderado_no_vinculado(self):
        citacion = Citacion(
            matricula=self.esc.matriculas[0],
            apoderado=self.esc.apoderado_no_vinculado,
            fecha_hora=timezone.now(), motivo='Motivo',
            registrado_por=self.esc.profesor)
        with self.assertRaises(ValidationError):
            citacion.full_clean()


class ConvivenciaVistasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()
        cls.matricula = cls.esc.matriculas[0]
        cls.base = f'/panel/convivencia/alumno/{cls.matricula.pk}/'

    def test_profesor_ajeno_no_ve_la_hoja_de_vida(self):
        self.client.force_login(self.esc.profesor_ajeno)
        self.assertEqual(self.client.get(self.base).status_code, 404)

    def test_anotacion_negativa_notifica_a_apoderados(self):
        self.client.force_login(self.esc.profesor)
        mail.outbox = []
        respuesta = self.client.post(f'{self.base}anotacion/', {
            'tipo': 'negativa',
            'fecha': timezone.localdate().isoformat(),
            'descripcion': 'Interrumpe la clase.',
        })
        self.assertEqual(respuesta.status_code, 302)
        anotacion = Anotacion.objects.get(matricula=self.matricula)
        self.assertEqual(anotacion.registrado_por, self.esc.profesor)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.esc.apoderados[0].usuario.email, mail.outbox[0].to)

    def test_anotacion_positiva_no_envia_email(self):
        self.client.force_login(self.esc.profesor)
        mail.outbox = []
        self.client.post(f'{self.base}anotacion/', {
            'tipo': 'positiva',
            'fecha': timezone.localdate().isoformat(),
            'descripcion': 'Excelente participación.',
        })
        self.assertEqual(len(mail.outbox), 0)

    def test_flujo_citacion_completo_con_notificaciones(self):
        self.client.force_login(self.esc.profesor)
        mail.outbox = []
        respuesta = self.client.post(f'{self.base}citacion/', {
            'apoderado': self.esc.apoderados[0].pk,
            'fecha_hora': f'{self.esc.anio}-06-20T16:30',
            'motivo': 'Revisar avance.',
        })
        self.assertEqual(respuesta.status_code, 302)
        citacion = Citacion.objects.get(matricula=self.matricula)
        self.assertEqual(citacion.estado, 'programada')
        self.assertEqual(len(mail.outbox), 1)

        respuesta = self.client.post(
            f'/panel/convivencia/citacion/{citacion.pk}/cerrar/',
            {'estado': 'realizada', 'acuerdos': 'Compromiso de apoyo.'})
        self.assertEqual(respuesta.status_code, 302)
        citacion.refresh_from_db()
        self.assertEqual(citacion.estado, 'realizada')
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('Resultado', mail.outbox[1].subject)

    def test_citacion_a_apoderado_no_vinculado_rechazada(self):
        self.client.force_login(self.esc.profesor)
        respuesta = self.client.post(f'{self.base}citacion/', {
            'apoderado': self.esc.apoderado_no_vinculado.pk,
            'fecha_hora': f'{self.esc.anio}-06-20T16:30',
            'motivo': 'Motivo.',
        })
        self.assertEqual(respuesta.status_code, 200)  # re-render con error
        self.assertEqual(Citacion.objects.count(), 0)

    def test_anotacion_auditada(self):
        self.client.force_login(self.esc.profesor)
        self.client.post(f'{self.base}anotacion/', {
            'tipo': 'observacion',
            'fecha': timezone.localdate().isoformat(),
            'descripcion': 'Observación inicial.',
        })
        anotacion = Anotacion.objects.get(matricula=self.matricula)
        self.assertEqual(anotacion.history.count(), 1)
        self.assertEqual(anotacion.history.first().history_user, self.esc.profesor)
