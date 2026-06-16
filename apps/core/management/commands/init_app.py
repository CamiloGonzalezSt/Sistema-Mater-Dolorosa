"""
Comando de inicialización: crea usuarios de prueba y limpia axes.
Se ejecuta en cada deploy para asegurar que la app esté lista.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from axes.models import AccessLog, AccessAttempt


class Command(BaseCommand):
    help = 'Inicializa la app: limpia axes y recrea usuarios de prueba'

    def handle(self, *args, **options):
        # Limpiar intentos de login fallidos (axes)
        AccessLog.objects.all().delete()
        AccessAttempt.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Axes limpiado'))

        # Recrear usuarios de prueba
        try:
            call_command('seed_prueba', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✓ Usuarios de prueba creados'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ seed_prueba: {e}'))
