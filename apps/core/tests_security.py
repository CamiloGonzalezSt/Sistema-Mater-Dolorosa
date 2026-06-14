"""Tests transversales de hardening: headers HTTP y aislamiento de roles."""
from django.test import TestCase

from apps.core.testing import crear_escenario


class SecurityHeadersTests(TestCase):
    def test_x_frame_options_deny(self):
        resp = self.client.get('/')
        self.assertEqual(resp.get('X-Frame-Options'), 'DENY')

    def test_x_content_type_options_nosniff(self):
        resp = self.client.get('/')
        self.assertEqual(resp.get('X-Content-Type-Options'), 'nosniff')

    def test_referrer_policy_same_origin(self):
        resp = self.client.get('/')
        self.assertEqual(resp.get('Referrer-Policy'), 'same-origin')


class RoleIsolationTests(TestCase):
    """Verifica que ningún rol puede acceder a recursos de otros roles."""

    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()

    def _assert_acceso_denegado(self, url, usuario):
        self.client.force_login(usuario)
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [302, 403], msg=f'{usuario.role} no debería acceder a {url}')
        self.client.logout()

    def test_alumno_no_accede_a_panel_cobros(self):
        self._assert_acceso_denegado('/panel/contabilidad/', self.esc.alumnos[0].usuario)

    def test_apoderado_no_accede_a_panel_cobros(self):
        self._assert_acceso_denegado('/panel/contabilidad/', self.esc.apoderados[0].usuario)

    def test_profesor_no_accede_a_panel_cobros(self):
        self._assert_acceso_denegado('/panel/contabilidad/', self.esc.profesor)

    def test_sin_sesion_redirige_a_login(self):
        resp = self.client.get('/panel/contabilidad/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp['Location'])
