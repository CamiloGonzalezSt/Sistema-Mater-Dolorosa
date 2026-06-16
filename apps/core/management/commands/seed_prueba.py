"""
Datos mínimos de prueba: solo los usuarios que el usuario especificó.
Uso: python manage.py seed_prueba
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Crea usuarios de prueba específicos'

    def handle(self, *args, **options):
        try:
            # Limpiar usuarios existentes
            CustomUser.objects.filter(email__in=[
                'gcastro@gmail.com', 'fsoto@gmail.com',
                'icid@gmail.com', 'jmunoz@gmail.com'
            ]).delete()

            # Crear apoderado 1 + alumno 1
            CustomUser.objects.create_user(
                email='gcastro@gmail.com',
                password='gcastro2026',
                first_name='Gisselle',
                last_name='Castro',
                role='apoderado'
            )

            CustomUser.objects.create_user(
                email='fsoto@gmail.com',
                password='fsoto2026',
                first_name='Felipe',
                last_name='Soto',
                role='alumno'
            )

            # Crear apoderado 2 + alumno 2
            CustomUser.objects.create_user(
                email='icid@gmail.com',
                password='icid2026',
                first_name='Ignacia',
                last_name='Cid',
                role='apoderado'
            )

            CustomUser.objects.create_user(
                email='jmunoz@gmail.com',
                password='jmunoz2026',
                first_name='Javiera',
                last_name='Muñoz',
                role='alumno'
            )

            self.stdout.write(self.style.SUCCESS('✓ Usuarios de prueba creados'))
            self.stdout.write('  - gcastro@gmail.com / gcastro2026')
            self.stdout.write('  - fsoto@gmail.com / fsoto2026')
            self.stdout.write('  - icid@gmail.com / icid2026')
            self.stdout.write('  - jmunoz@gmail.com / jmunoz2026')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
