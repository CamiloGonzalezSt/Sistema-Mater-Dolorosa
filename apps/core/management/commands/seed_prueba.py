"""
Datos mínimos de prueba: solo los usuarios que el usuario especificó.
Uso: python manage.py seed_prueba
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser
from apps.alumnos.models import PerfilAlumno, PerfilApoderado, AlumnoApoderado, Matricula
from apps.academico.models import NivelEducacional, Curso, Asignatura, CursoAsignatura


class Command(BaseCommand):
    help = 'Crea usuarios de prueba específicos'

    def handle(self, *args, **options):
        # Limpiar usuarios existentes
        CustomUser.objects.filter(email__in=[
            'gcastro@gmail.com', 'fsoto@gmail.com',
            'icid@gmail.com', 'jmunoz@gmail.com'
        ]).delete()

        # Crear apoderado 1 + alumno 1
        gcastro = CustomUser.objects.create_user(
            email='gcastro@gmail.com',
            password='gcastro2026',
            first_name='Gisselle',
            last_name='Castro',
            role='apoderado'
        )

        fsoto = CustomUser.objects.create_user(
            email='fsoto@gmail.com',
            password='fsoto2026',
            first_name='Felipe',
            last_name='Soto',
            role='alumno'
        )

        # Crear apoderado 2 + alumno 2
        icid = CustomUser.objects.create_user(
            email='icid@gmail.com',
            password='icid2026',
            first_name='Ignacia',
            last_name='Cid',
            role='apoderado'
        )

        jmunoz = CustomUser.objects.create_user(
            email='jmunoz@gmail.com',
            password='jmunoz2026',
            first_name='Javiera',
            last_name='Muñoz',
            role='alumno'
        )

        # Crear perfiles
        PerfilAlumno.objects.get_or_create(usuario=fsoto)
        PerfilAlumno.objects.get_or_create(usuario=jmunoz)
        PerfilApoderado.objects.get_or_create(usuario=gcastro)
        PerfilApoderado.objects.get_or_create(usuario=icid)

        # Vincular apoderados a alumnos
        AlumnoApoderado.objects.get_or_create(
            alumno=PerfilAlumno.objects.get(usuario=fsoto),
            apoderado=PerfilApoderado.objects.get(usuario=gcastro)
        )
        AlumnoApoderado.objects.get_or_create(
            alumno=PerfilAlumno.objects.get(usuario=jmunoz),
            apoderado=PerfilApoderado.objects.get(usuario=icid)
        )

        # Crear cursos y matrículas
        nivel_2m, _ = NivelEducacional.objects.get_or_create(nombre='2° Medio', orden=10)
        nivel_8b, _ = NivelEducacional.objects.get_or_create(nombre='8° Básico', orden=5)

        curso_2m, _ = Curso.objects.get_or_create(
            nivel=nivel_2m,
            letra='A',
            anio_escolar=2026,
            defaults={'nombre': '2° Medio A'}
        )
        curso_8b, _ = Curso.objects.get_or_create(
            nivel=nivel_8b,
            letra='A',
            anio_escolar=2026,
            defaults={'nombre': '8° Básico A'}
        )

        Matricula.objects.get_or_create(
            alumno=PerfilAlumno.objects.get(usuario=fsoto),
            curso=curso_2m,
            anio_escolar=2026
        )
        Matricula.objects.get_or_create(
            alumno=PerfilAlumno.objects.get(usuario=jmunoz),
            curso=curso_8b,
            anio_escolar=2026
        )

        self.stdout.write(self.style.SUCCESS('✓ Usuarios de prueba creados'))
        self.stdout.write('  - gcastro@gmail.com / gcastro2026 (apoderado)')
        self.stdout.write('  - fsoto@gmail.com / fsoto2026 (alumno)')
        self.stdout.write('  - icid@gmail.com / icid2026 (apoderado)')
        self.stdout.write('  - jmunoz@gmail.com / jmunoz2026 (alumno)')
