"""Marca como vencidos los cobros pendientes con fecha de vencimiento pasada.
En producción se ejecuta diariamente vía cron."""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.contabilidad.models import Cobro


class Command(BaseCommand):
    help = 'Marca como vencidos los cobros pendientes cuya fecha de vencimiento pasó.'

    def handle(self, *args, **options):
        actualizados = Cobro.objects.filter(
            estado=Cobro.Estado.PENDIENTE,
            fecha_vencimiento__lt=timezone.localdate(),
        ).update(estado=Cobro.Estado.VENCIDO)
        self.stdout.write(self.style.SUCCESS(f'Cobros marcados como vencidos: {actualizados}'))
