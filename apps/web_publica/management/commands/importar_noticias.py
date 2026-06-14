"""Django management command: python manage.py importar_noticias."""
import logging

from django.core.management.base import BaseCommand

from apps.web_publica.models import Noticia
from apps.web_publica.scrapers import ScraperMaterdolorosa

logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = 'Importa noticias desde www.materdolorosa.cl'

    def add_arguments(self, parser):
        parser.add_argument(
            '--paginas',
            type=int,
            default=None,
            help='Número máximo de páginas a scrapear (None = todas)',
        )
        parser.add_argument(
            '--permitir-duplicados',
            action='store_true',
            help='Permite importar noticias con título duplicado',
        )
        parser.add_argument(
            '--sin-color',
            action='store_true',
            help='Desactiva colores en output',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando importación de noticias...'))

        scraper = ScraperMaterdolorosa(verbose=True)

        try:
            creadas, saltadas = scraper.importar_noticias(
                modelo_noticia=Noticia,
                limite_paginas=options['paginas'],
                permitir_duplicados=options['permitir_duplicados'],
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Importación completada: {creadas} creadas, {saltadas} saltadas'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error durante importación: {e}'))
            raise
