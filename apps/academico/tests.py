from django.db import IntegrityError
from django.test import TestCase

from apps.core.testing import crear_escenario

from .models import Curso, CursoAsignatura


class RestriccionesAcademicasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()

    def test_curso_unico_por_nivel_letra_anio(self):
        with self.assertRaises(IntegrityError):
            Curso.objects.create(
                nivel=self.esc.nivel, letra='A', anio_escolar=self.esc.anio)

    def test_cursoasignatura_unica_por_curso_asignatura_anio(self):
        with self.assertRaises(IntegrityError):
            CursoAsignatura.objects.create(
                curso=self.esc.curso, asignatura=self.esc.asignatura,
                profesor=self.esc.profesor_ajeno, anio_escolar=self.esc.anio)

    def test_alumno_ve_materiales_solo_de_su_curso(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from .models import MaterialAcademico
        MaterialAcademico.objects.create(
            curso_asignatura=self.esc.ca, periodo=self.esc.periodo,
            titulo='Guía de su curso',
            archivo=SimpleUploadedFile('guia.txt', b'contenido'),
            subido_por=self.esc.profesor)
        MaterialAcademico.objects.create(
            curso_asignatura=self.esc.ca_ajena, periodo=self.esc.periodo,
            titulo='Guía de otro curso',
            archivo=SimpleUploadedFile('otra.txt', b'contenido'),
            subido_por=self.esc.profesor_ajeno)

        self.client.force_login(self.esc.alumnos[0].usuario)
        respuesta = self.client.get('/panel/materiales/')
        self.assertContains(respuesta, 'Guía de su curso')
        self.assertNotContains(respuesta, 'Guía de otro curso')
        # El profesor no entra a la vista del alumno; el alumno no entra a gestión
        self.assertEqual(self.client.get('/panel/materiales/gestion/').status_code, 403)
        self.client.force_login(self.esc.profesor)
        self.assertEqual(self.client.get('/panel/materiales/').status_code, 403)

    def test_profesor_sube_y_elimina_solo_material_propio(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from .models import MaterialAcademico
        self.client.force_login(self.esc.profesor)
        respuesta = self.client.post('/panel/materiales/gestion/', {
            'curso_asignatura': self.esc.ca.pk,
            'periodo': self.esc.periodo.pk,
            'unidad': 'Unidad 1',
            'titulo': 'Guía de fracciones',
            'descripcion': '',
            'archivo': SimpleUploadedFile('fracciones.txt', b'1/2'),
        })
        self.assertEqual(respuesta.status_code, 302)
        material = MaterialAcademico.objects.get()
        self.assertEqual(material.subido_por, self.esc.profesor)

        self.client.force_login(self.esc.profesor_ajeno)
        respuesta = self.client.post(
            f'/panel/materiales/gestion/{material.pk}/eliminar/')
        self.assertEqual(respuesta.status_code, 404)
        self.assertTrue(MaterialAcademico.objects.filter(pk=material.pk).exists())

    def test_jefaturas_historicas_navegables(self):
        from apps.profesores.models import PerfilProfesor
        perfil = PerfilProfesor.objects.create(
            usuario=self.esc.profesor, especialidad='Matemática', titulo='Profesor')
        self.esc.curso.profesor_jefe = perfil
        self.esc.curso.save()
        self.assertEqual(list(perfil.jefaturas.all()), [self.esc.curso])
