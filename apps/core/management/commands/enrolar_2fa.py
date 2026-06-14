"""Enrola un dispositivo TOTP (2FA) para un usuario del admin.

Uso:
    python manage.py enrolar_2fa admin@ejemplo.cl

Escanea el QR que muestra (Google Authenticator, Authy, etc.). Después activa
ADMIN_2FA=True en el entorno y reinicia el servidor para exigir el token en /admin/.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django_otp.plugins.otp_totp.models import TOTPDevice


class Command(BaseCommand):
    help = 'Crea (o reemplaza) un dispositivo TOTP de 2FA para el admin indicado.'

    def add_arguments(self, parser):
        parser.add_argument('email', help='Correo del usuario a enrolar')

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            user = User.objects.get(email=options['email'])
        except User.DoesNotExist:
            raise CommandError(f"No existe un usuario con email {options['email']}")

        if not (user.is_staff or user.is_superuser):
            self.stdout.write(self.style.WARNING(
                'Aviso: este usuario no es staff/superuser; el 2FA del admin solo '
                'aplica a quienes acceden a /admin/.'
            ))

        TOTPDevice.objects.filter(user=user).delete()
        device = TOTPDevice.objects.create(user=user, name='admin', confirmed=True)

        self.stdout.write(self.style.SUCCESS(f'Dispositivo 2FA creado para {user.email}.'))
        self.stdout.write('Escanea este código con tu app de autenticación:\n')
        try:
            import qrcode

            qr = qrcode.QRCode(border=1)
            qr.add_data(device.config_url)
            qr.make()
            qr.print_ascii(out=self.stdout, invert=True)
        except Exception:
            self.stdout.write(self.style.WARNING('(qrcode no disponible para dibujar el QR)'))

        self.stdout.write('\nSi no puedes escanear, usa esta URI en tu app:')
        self.stdout.write(device.config_url)
        self.stdout.write(self.style.WARNING(
            '\nLuego activa ADMIN_2FA=True en el entorno y reinicia el servidor.'
        ))
