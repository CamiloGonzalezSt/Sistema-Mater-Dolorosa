"""Data migration: crea los usuarios de prueba para la marcha blanca.

Se ejecuta con `python manage.py migrate`, que SÍ corre en el Build Command
de Render (a diferencia del `release:` del Procfile, que Render ignora en
servicios creados manualmente). Idempotente: no duplica si ya existen.
"""
from django.contrib.auth.hashers import make_password
from django.db import migrations

USUARIOS = [
    {'email': 'gcastro@gmail.com', 'password': 'gcastro2026',
     'first_name': 'Gisselle', 'last_name': 'Castro',
     'role': 'apoderado', 'rut': '12345678-5', 'username': 'gcastro'},
    {'email': 'fsoto@gmail.com', 'password': 'fsoto2026',
     'first_name': 'Felipe', 'last_name': 'Soto',
     'role': 'alumno', 'rut': '23456789-6', 'username': 'fsoto'},
    {'email': 'icid@gmail.com', 'password': 'icid2026',
     'first_name': 'Ignacia', 'last_name': 'Cid',
     'role': 'apoderado', 'rut': '34567890-5', 'username': 'icid'},
    {'email': 'jmunoz@gmail.com', 'password': 'jmunoz2026',
     'first_name': 'Javiera', 'last_name': 'Muñoz',
     'role': 'alumno', 'rut': '45678901-3', 'username': 'jmunoz'},
]


def crear_usuarios(apps, schema_editor):
    User = apps.get_model('accounts', 'CustomUser')
    for u in USUARIOS:
        if not User.objects.filter(email=u['email']).exists():
            User.objects.create(
                email=u['email'],
                username=u['username'],
                first_name=u['first_name'],
                last_name=u['last_name'],
                role=u['role'],
                rut=u['rut'],
                password=make_password(u['password']),
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )


def borrar_usuarios(apps, schema_editor):
    User = apps.get_model('accounts', 'CustomUser')
    User.objects.filter(email__in=[u['email'] for u in USUARIOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_usuarios, borrar_usuarios),
    ]
