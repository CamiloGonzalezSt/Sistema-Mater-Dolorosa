"""
Datos mínimos de prueba: solo los usuarios que el usuario especificó.
Uso: python manage.py seed_prueba
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser

USUARIOS = [
    {
        'email': 'gcastro@gmail.com',
        'password': 'gcastro2026',
        'first_name': 'Gisselle',
        'last_name': 'Castro',
        'role': 'apoderado',
        'rut': '12345678-5',
        'username': 'gcastro',
    },
    {
        'email': 'fsoto@gmail.com',
        'password': 'fsoto2026',
        'first_name': 'Felipe',
        'last_name': 'Soto',
        'role': 'alumno',
        'rut': '23456789-6',
        'username': 'fsoto',
    },
    {
        'email': 'icid@gmail.com',
        'password': 'icid2026',
        'first_name': 'Ignacia',
        'last_name': 'Cid',
        'role': 'apoderado',
        'rut': '34567890-5',
        'username': 'icid',
    },
    {
        'email': 'jmunoz@gmail.com',
        'password': 'jmunoz2026',
        'first_name': 'Javiera',
        'last_name': 'Muñoz',
        'role': 'alumno',
        'rut': '45678901-3',
        'username': 'jmunoz',
    },
]


class Command(BaseCommand):
    help = 'Crea usuarios de prueba específicos'

    def handle(self, *args, **options):
        emails = [u['email'] for u in USUARIOS]
        eliminados, _ = CustomUser.objects.filter(email__in=emails).delete()
        if eliminados:
            self.stdout.write(f'  Eliminados {eliminados} usuarios anteriores')

        for u in USUARIOS:
            try:
                password = u.pop('password')
                user = CustomUser(**u)
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  OK {u["email"]}'))
                u['password'] = password  # restaurar por si se llama dos veces
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ERROR {u["email"]}: {e}'))
                u['password'] = password

        self.stdout.write(self.style.SUCCESS('seed_prueba completado'))
