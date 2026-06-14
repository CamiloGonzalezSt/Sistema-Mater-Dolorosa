from datetime import date, timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from apps.core.testing import crear_escenario

from .models import EventoCalendario, ItemGaleria, Noticia, Postulacion


class WebPublicaTests(TestCase):
    def test_paginas_publicas_responden_sin_sesion(self):
        for url in ('/', '/historia/', '/contacto/', '/quienes-somos/',
                    '/noticias/', '/calendario/', '/galeria/',
                    '/convivencia-escolar/', '/admision/'):
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200, url)
            self.assertContains(respuesta, 'Iniciar sesión')

    def test_formulario_contacto_envia_email(self):
        mail.outbox = []
        respuesta = self.client.post('/contacto/', {
            'nombre': 'Juan Pérez', 'email': 'juan@ejemplo.cl',
            'telefono': '', 'mensaje': 'Consulta por admisión.',
        })
        self.assertRedirects(respuesta, '/contacto/')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Juan Pérez', mail.outbox[0].body)

    def test_formulario_contacto_invalido_no_envia(self):
        mail.outbox = []
        respuesta = self.client.post('/contacto/', {
            'nombre': '', 'email': 'no-es-email', 'mensaje': '',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_mensaje_excesivamente_largo_rechazado(self):
        mail.outbox = []
        respuesta = self.client.post('/contacto/', {
            'nombre': 'Juan', 'email': 'juan@ejemplo.cl',
            'telefono': '', 'mensaje': 'A' * 2001,
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)


class NoticiasTests(TestCase):
    def test_solo_noticias_publicadas_son_visibles(self):
        visible = Noticia.objects.create(
            titulo='Noticia pública', bajada='Bajada', cuerpo='Cuerpo')
        oculta = Noticia.objects.create(
            titulo='Borrador secreto', bajada='Bajada', cuerpo='Cuerpo',
            publicada=False)
        respuesta = self.client.get('/noticias/')
        self.assertContains(respuesta, 'Noticia pública')
        self.assertNotContains(respuesta, 'Borrador secreto')
        self.assertEqual(
            self.client.get(f'/noticias/{visible.pk}/').status_code, 200)
        self.assertEqual(
            self.client.get(f'/noticias/{oculta.pk}/').status_code, 404)


class CalendarioGaleriaTests(TestCase):
    def test_calendario_no_muestra_eventos_de_meses_pasados(self):
        hoy = timezone.localdate()
        EventoCalendario.objects.create(titulo='Evento futuro', fecha=hoy + timedelta(days=10))
        EventoCalendario.objects.create(titulo='Evento antiguo', fecha=hoy - timedelta(days=60))
        respuesta = self.client.get('/calendario/')
        self.assertContains(respuesta, 'Evento futuro')
        self.assertNotContains(respuesta, 'Evento antiguo')

    def test_galeria_filtra_por_anio(self):
        anio = timezone.localdate().year
        ItemGaleria.objects.create(
            titulo='Video actual', anio=anio,
            video_url='https://www.youtube.com/embed/x')
        ItemGaleria.objects.create(
            titulo='Video antiguo', anio=anio - 1,
            video_url='https://www.youtube.com/embed/y')
        respuesta = self.client.get(f'/galeria/?anio={anio}')
        self.assertContains(respuesta, 'Video actual')
        self.assertNotContains(respuesta, 'Video antiguo')
        respuesta = self.client.get(f'/galeria/?anio={anio - 1}')
        self.assertContains(respuesta, 'Video antiguo')


class AdmisionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()

    def _datos(self, **extra):
        datos = {
            'nombre_postulante': 'Pedro Postulante',
            'fecha_nacimiento': date(2014, 5, 1).isoformat(),
            'nivel': self.esc.nivel.pk,
            'nombre_apoderado': 'Ana Apoderada',
            'email': 'ana@ejemplo.cl',
            'telefono': '+56 9 1234 5678',
            'mensaje': 'Consulta por cupos.',
        }
        datos.update(extra)
        return datos

    def test_postulacion_publica_crea_registro_y_notifica(self):
        mail.outbox = []
        respuesta = self.client.post('/admision/', self._datos())
        self.assertRedirects(respuesta, '/admision/')
        postulacion = Postulacion.objects.get()
        self.assertEqual(postulacion.estado, Postulacion.Estado.NUEVA)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Nueva postulación', mail.outbox[0].subject)

    def test_fecha_nacimiento_futura_rechazada(self):
        futura = (timezone.localdate() + timedelta(days=30)).isoformat()
        respuesta = self.client.post('/admision/', self._datos(fecha_nacimiento=futura))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Postulacion.objects.count(), 0)

    def test_panel_postulaciones_solo_admin(self):
        respuesta = self.client.get('/panel/postulaciones/')
        self.assertEqual(respuesta.status_code, 302)
        for usuario in (self.esc.profesor, self.esc.apoderados[0].usuario):
            self.client.force_login(usuario)
            self.assertEqual(
                self.client.get('/panel/postulaciones/').status_code, 403)

    def test_admin_lista_y_cambia_estado(self):
        self.client.post('/admision/', self._datos())
        postulacion = Postulacion.objects.get()
        self.client.force_login(self.esc.admin)
        respuesta = self.client.get('/panel/postulaciones/')
        self.assertContains(respuesta, 'Pedro Postulante')
        respuesta = self.client.post(
            f'/panel/postulaciones/{postulacion.pk}/estado/',
            {'estado': 'en_revision'})
        self.assertEqual(respuesta.status_code, 302)
        postulacion.refresh_from_db()
        self.assertEqual(postulacion.estado, 'en_revision')
