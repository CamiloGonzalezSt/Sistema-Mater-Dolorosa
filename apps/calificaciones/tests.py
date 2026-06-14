from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.core.testing import crear_escenario

from .models import Calificacion


class CalificacionModeloTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()

    def test_una_nota_por_alumno_y_evaluacion(self):
        datos = dict(
            evaluacion=self.esc.evaluacion, matricula=self.esc.matriculas[0],
            puntaje_obtenido=Decimal('45'), nota=Decimal('5.5'))
        Calificacion.objects.create(**datos)
        with self.assertRaises(IntegrityError):
            Calificacion.objects.create(**datos)

    def test_clean_rechaza_puntaje_sobre_el_maximo(self):
        calificacion = Calificacion(
            evaluacion=self.esc.evaluacion, matricula=self.esc.matriculas[0],
            puntaje_obtenido=Decimal('70'), nota=Decimal('7.0'))
        with self.assertRaises(ValidationError):
            calificacion.full_clean()

    def test_nota_fuera_de_escala_chilena_rechazada(self):
        for nota in (Decimal('0.5'), Decimal('7.5')):
            calificacion = Calificacion(
                evaluacion=self.esc.evaluacion, matricula=self.esc.matriculas[0],
                puntaje_obtenido=Decimal('30'), nota=nota)
            with self.assertRaises(ValidationError):
                calificacion.full_clean()


class CalificacionVistasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()
        cls.url = f'/panel/calificaciones/evaluacion/{cls.esc.evaluacion.pk}/'

    def _post_notas(self, valores):
        datos = {}
        for matricula, (puntaje, nota) in zip(self.esc.matriculas, valores):
            datos[f'm{matricula.pk}-puntaje_obtenido'] = puntaje
            datos[f'm{matricula.pk}-nota'] = nota
            datos[f'm{matricula.pk}-observacion'] = ''
        return self.client.post(self.url, datos)

    def test_profesor_ajeno_recibe_404(self):
        self.client.force_login(self.esc.profesor_ajeno)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_guardado_omite_filas_en_blanco(self):
        self.client.force_login(self.esc.profesor)
        respuesta = self._post_notas([('45.0', '5.5'), ('', '')])
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            Calificacion.objects.filter(evaluacion=self.esc.evaluacion).count(), 1)

    def test_nota_invalida_rerenderiza_con_errores(self):
        self.client.force_login(self.esc.profesor)
        respuesta = self._post_notas([('45.0', '9.9'), ('', '')])
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'errorlist')
        self.assertEqual(Calificacion.objects.count(), 0)

    def test_edicion_queda_auditada_con_usuario(self):
        self.client.force_login(self.esc.profesor)
        self._post_notas([('45.0', '5.5'), ('', '')])
        self._post_notas([('50.0', '6.0'), ('', '')])
        calificacion = Calificacion.objects.get(
            evaluacion=self.esc.evaluacion, matricula=self.esc.matriculas[0])
        historial = calificacion.history.order_by('history_date')
        self.assertEqual(historial.count(), 2)
        self.assertEqual(historial.last().nota, Decimal('6.0'))
        self.assertEqual(historial.last().history_user, self.esc.profesor)

    def test_informe_pdf(self):
        self.client.force_login(self.esc.profesor)
        Calificacion.objects.create(
            evaluacion=self.esc.evaluacion, matricula=self.esc.matriculas[0],
            puntaje_obtenido=Decimal('45'), nota=Decimal('5.5'))
        respuesta = self.client.get(
            f'/panel/calificaciones/informe/{self.esc.matriculas[0].pk}/informe.pdf')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'application/pdf')
        self.assertTrue(respuesta.content.startswith(b'%PDF'))

    def test_informe_pdf_de_alumno_ajeno_404(self):
        self.client.force_login(self.esc.profesor_ajeno)
        respuesta = self.client.get(
            f'/panel/calificaciones/informe/{self.esc.matriculas[0].pk}/informe.pdf')
        self.assertEqual(respuesta.status_code, 404)
