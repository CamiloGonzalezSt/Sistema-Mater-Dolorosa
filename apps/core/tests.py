import json
from datetime import date

from django.test import TestCase

from apps.asistencia.models import RegistroAsistencia
from apps.core.testing import crear_escenario


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()
        cls.url = '/panel/api/dashboard/'

    def test_requiere_rol_docente(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 302)
        self.client.force_login(self.esc.alumnos[0].usuario)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_datos_del_profesor(self):
        from django.utils import timezone
        hoy = timezone.localdate()
        for matricula, estado in zip(self.esc.matriculas, ['presente', 'ausente']):
            RegistroAsistencia.objects.create(
                matricula=matricula, curso_asignatura=self.esc.ca,
                fecha=hoy, estado=estado, registrado_por=self.esc.profesor)
        self.client.force_login(self.esc.profesor)
        datos = json.loads(self.client.get(self.url).content)
        self.assertEqual(datos['asistencia_hoy']['porcentaje_presentes'], 50.0)
        self.assertEqual(datos['asistencia_hoy']['total_registros'], 2)
        self.assertIn('promedios', datos)
        self.assertIn('distribucion_notas', datos)

    def test_home_renderiza_dashboard_solo_a_docentes(self):
        self.client.force_login(self.esc.profesor)
        self.assertContains(self.client.get('/panel/'), 'chart-asistencia')
        self.client.force_login(self.esc.alumnos[0].usuario)
        self.assertNotContains(self.client.get('/panel/'), 'chart-asistencia')
