from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from apps.core.testing import PASSWORD, crear_escenario

from .validators import validar_rut_chileno


class ValidadorRutTests(TestCase):
    def test_ruts_validos(self):
        for rut in ['11111111-1', '12.345.678-5', '14379130-0', '11111112-K']:
            validar_rut_chileno(rut)  # no debe lanzar

    def test_ruts_invalidos(self):
        for rut in ['12345678-9', '11111111-2', '1234-5', 'no-es-rut', '14379130-K']:
            with self.assertRaises(ValidationError):
                validar_rut_chileno(rut)


class AutenticacionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()

    def test_login_con_email_redirige_al_panel(self):
        respuesta = self.client.post(
            '/accounts/login/',
            {'username': 'prof@test.cl', 'password': PASSWORD},
        )
        self.assertRedirects(respuesta, '/panel/')

    def test_panel_requiere_sesion(self):
        respuesta = self.client.get('/panel/')
        self.assertRedirects(respuesta, '/accounts/login/?next=/panel/')

    def test_logout_redirige_a_web_publica(self):
        self.client.force_login(self.esc.profesor)
        respuesta = self.client.post('/accounts/logout/')
        self.assertRedirects(respuesta, '/')


@override_settings(AXES_FAILURE_LIMIT=3)
class BruteForceProtectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()

    URL = '/accounts/login/'

    def _login_fallido(self):
        self.client.post(self.URL, {'username': 'prof@test.cl', 'password': 'clave_mala'})

    def test_bloqueo_tras_limite_de_intentos(self):
        for _ in range(3):
            self._login_fallido()
        resp = self.client.post(self.URL, {'username': 'prof@test.cl', 'password': PASSWORD})
        self.assertEqual(resp.status_code, 429)

    def test_login_correcto_antes_del_limite_no_bloquea(self):
        for _ in range(2):
            self._login_fallido()
        resp = self.client.post(self.URL, {'username': 'prof@test.cl', 'password': PASSWORD})
        self.assertRedirects(resp, '/panel/')

    @override_settings(AXES_FAILURE_LIMIT=2)
    def test_exito_limpia_el_contador(self):
        from axes.models import AccessAttempt
        self._login_fallido()
        self.client.post(self.URL, {'username': 'prof@test.cl', 'password': PASSWORD})
        self.client.logout()
        self.assertEqual(AccessAttempt.objects.filter(username='prof@test.cl').count(), 0)
