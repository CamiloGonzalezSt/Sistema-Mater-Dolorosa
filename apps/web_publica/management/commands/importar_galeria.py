"""Django management command: python manage.py importar_galeria."""
from django.core.management.base import BaseCommand

from apps.web_publica.models import ItemGaleria
from apps.web_publica.scrapers import ScraperMaterdolorosa


class Command(BaseCommand):
    help = 'Importa imágenes a la galería desde www.materdolorosa.cl'

    def add_arguments(self, parser):
        parser.add_argument('--paginas', type=int, default=None,
                            help='Número máximo de páginas a scrapear')
        parser.add_argument('--permitir-duplicados', action='store_true',
                            help='Permite importar ítems con título duplicado')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando importacion de galeria...'))
        scraper = ScraperMaterdolorosa(verbose=True)
        creadas, saltadas = scraper.importar_galeria(
            modelo_item=ItemGaleria,
            limite_paginas=options['paginas'],
            permitir_duplicados=options['permitir_duplicados'],
        )
        self.stdout.write(self.style.SUCCESS(
            f'Galeria completada: {creadas} creadas, {saltadas} saltadas'
        ))
