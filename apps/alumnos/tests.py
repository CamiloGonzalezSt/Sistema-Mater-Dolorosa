from datetime import date

from django.db import IntegrityError
from django.test import TestCase

from apps.core.testing import crear_escenario

from .models import Matricula


class MatriculaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()

    def test_anio_escolar_se_autocompleta_desde_el_curso(self):
        matricula = self.esc.matriculas[0]
        self.assertEqual(matricula.anio_escolar, self.esc.curso.anio_escolar)

    def test_una_sola_matricula_por_alumno_y_anio(self):
        with self.assertRaises(IntegrityError):
            Matricula.objects.create(
                alumno=self.esc.alumnos[0], curso=self.esc.otro_curso,
                fecha_matricula=date(self.esc.anio, 4, 1))

    def test_portal_apoderado_notas_promedios_y_umbral(self):
        from decimal import Decimal

        from apps.calificaciones.models import Calificacion, Evaluacion

        ev2 = Evaluacion.objects.create(
            curso_asignatura=self.esc.ca, periodo=self.esc.periodo,
            tipo=self.esc.tipo, nombre='Prueba 2', fecha=date(self.esc.anio, 6, 8),
            puntaje_maximo=Decimal('60'))
        # Promedio 3.5 → Reprobado (3.0 y 4.0)
        Calificacion.objects.create(
            evaluacion=self.esc.evaluacion, matricula=self.esc.matriculas[0],
            puntaje_obtenido=Decimal('20'), nota=Decimal('3.0'))
        Calificacion.objects.create(
            evaluacion=ev2, matricula=self.esc.matriculas[0],
            puntaje_obtenido=Decimal('34'), nota=Decimal('4.0'))

        self.client.force_login(self.esc.apoderados[0].usuario)
        respuesta = self.client.get('/panel/pupilos/notas/')
        contenido = respuesta.content.decode()
        self.assertIn('3,50', contenido.replace('3.50', '3,50'))
        self.assertIn('Reprobado', contenido)
        self.assertIn('estado-reprobado', contenido)
        # Solo ve a su pupilo
        self.assertNotIn(
            self.esc.alumnos[1].usuario.get_full_name(), contenido)

        # Exactamente 4.0 → Aprobado (caso límite del umbral)
        Calificacion.objects.filter(matricula=self.esc.matriculas[0]).update(
            nota=Decimal('4.0'))
        contenido = self.client.get('/panel/pupilos/notas/').content.decode()
        self.assertIn('Aprobado', contenido)
        self.assertNotIn('Reprobado', contenido)

    def test_portal_apoderado_bloqueado_para_otros_roles(self):
        for usuario in (self.esc.profesor, self.esc.alumnos[0].usuario):
            self.client.force_login(usuario)
            for url in ('/panel/pupilos/notas/', '/panel/pupilos/anotaciones/',
                        '/panel/pupilos/citaciones/'):
                self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_portal_apoderado_citaciones_separa_programadas(self):
        from django.utils import timezone

        from apps.convivencia.models import Citacion

        Citacion.objects.create(
            matricula=self.esc.matriculas[0], apoderado=self.esc.apoderados[0],
            fecha_hora=timezone.now(), motivo='Reunión pendiente',
            registrado_por=self.esc.profesor)
        Citacion.objects.create(
            matricula=self.esc.matriculas[0], apoderado=self.esc.apoderados[0],
            fecha_hora=timezone.now(), motivo='Reunión pasada',
            estado='realizada', acuerdos='Compromiso de estudio.',
            registrado_por=self.esc.profesor)
        self.client.force_login(self.esc.apoderados[0].usuario)
        contenido = self.client.get('/panel/pupilos/citaciones/').content.decode()
        self.assertIn('Reunión pendiente', contenido)
        self.assertIn('Compromiso de estudio.', contenido)

    def test_historial_multianio_se_conserva(self):
        from apps.academico.models import Curso
        curso_siguiente = Curso.objects.create(
            nivel=self.esc.nivel, letra='A', anio_escolar=self.esc.anio + 1)
        Matricula.objects.create(
            alumno=self.esc.alumnos[0], curso=curso_siguiente,
            fecha_matricula=date(self.esc.anio + 1, 3, 1))
        anios = list(
            self.esc.alumnos[0].matriculas.order_by('anio_escolar')
            .values_list('anio_escolar', flat=True))
        self.assertEqual(anios, [self.esc.anio, self.esc.anio + 1])
