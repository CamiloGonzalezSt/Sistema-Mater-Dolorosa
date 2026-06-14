"""Carga los integrantes reales del equipo de convivencia
(datos públicos del sitio oficial www.materdolorosa.cl)."""
from django.db import migrations

EQUIPO = [
    ('Paola Vidal', 'Encargada de Convivencia Escolar', 10),
    ('Miriam Ross', 'Orientadora', 20),
    ('Daniela Robles', 'Psicóloga', 30),
]


def cargar_equipo(apps, schema_editor):
    EquipoConvivencia = apps.get_model('web_publica', 'EquipoConvivencia')
    for nombre, cargo, orden in EQUIPO:
        EquipoConvivencia.objects.get_or_create(
            nombre=nombre, defaults={'cargo': cargo, 'orden': orden}
        )


def borrar_equipo(apps, schema_editor):
    EquipoConvivencia = apps.get_model('web_publica', 'EquipoConvivencia')
    EquipoConvivencia.objects.filter(
        nombre__in=[nombre for nombre, _, _ in EQUIPO]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('web_publica', '0002_equipoconvivencia'),
    ]

    operations = [
        migrations.RunPython(cargar_equipo, borrar_equipo),
    ]
