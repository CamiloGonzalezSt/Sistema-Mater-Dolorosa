"""Scrapers para importar contenido de www.materdolorosa.cl."""
import logging
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone

logger = logging.getLogger(__name__)


class ScraperMaterdolorosa:
    """Extrae contenido del sitio oficial (https://www.materdolorosa.cl)."""

    BASE_URL = 'https://www.materdolorosa.cl'
    NOTICIAS_URL = f'{BASE_URL}/noticias'
    TIMEOUT = 10

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; MaterdolorosaBot/1.0)'
        })

    def log(self, msg):
        if self.verbose:
            logger.info(msg)

    def _fetch_page(self, url, params=None):
        """Descarga y parsea una página HTML."""
        try:
            resp = self.session.get(url, params=params, timeout=self.TIMEOUT)
            resp.raise_for_status()
            return BeautifulSoup(resp.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f'Error al descargar {url}: {e}')
            return None

    def _download_imagen(self, img_url, filename_hint=None):
        """Descarga una imagen y retorna (ContentFile, nombre_archivo)."""
        if not img_url:
            return None, None
        img_url = urljoin(self.BASE_URL, img_url)
        try:
            resp = requests.get(img_url, timeout=self.TIMEOUT)
            resp.raise_for_status()
            # Extrae nombre del archivo de la URL
            parsed = urlparse(img_url)
            filename = Path(parsed.path).name or (filename_hint or 'imagen.jpg')
            content = ContentFile(resp.content, name=filename)
            return content, filename
        except requests.RequestException as e:
            logger.warning(f'No se pudo descargar imagen {img_url}: {e}')
            return None, None

    def scrape_noticias(self, limite_paginas=None):
        """Extrae todas las noticias (o N primeras páginas).

        Retorna lista de dicts: {titulo, bajada, cuerpo, imagen, fecha, autor}
        """
        noticias = []
        pagina = 1

        while True:
            if limite_paginas and pagina > limite_paginas:
                break

            self.log(f'Scrapeando página {pagina} de noticias...')
            params = {'page': pagina} if pagina > 1 else {}
            soup = self._fetch_page(self.NOTICIAS_URL, params=params)

            if not soup:
                break

            # Busca tarjetas de noticias (structure can vary; adapt as needed)
            articulos = soup.select('article, .post-item, .noticia-card')

            if not articulos:
                logger.warning(f'No se encontraron artículos en página {pagina}')
                break

            for art in articulos:
                datos = self._extraer_noticia(art)
                if datos:
                    noticias.append(datos)

            # Verifica si hay más páginas (busca link "Siguiente")
            siguiente = soup.select_one('a.next, .pagination a[rel="next"]')
            if not siguiente or pagina >= (limite_paginas or 999):
                break

            pagina += 1

        self.log(f'Total de noticias scrapeadas: {len(noticias)}')
        return noticias

    def _extraer_noticia(self, articulo_elem):
        """Extrae datos de un elemento <article>."""
        try:
            # Adaptar selectores según la estructura real del sitio
            titulo_elem = articulo_elem.select_one('h2, h3, .title, .post-title')
            titulo = titulo_elem.get_text(strip=True) if titulo_elem else None

            if not titulo:
                return None

            # Bajada / excerpt
            bajada_elem = articulo_elem.select_one('.excerpt, .post-excerpt, p')
            bajada = bajada_elem.get_text(strip=True) if bajada_elem else ''

            # Imagen destacada
            img_elem = articulo_elem.select_one('img')
            img_src = img_elem.get('src') if img_elem else None

            # Fecha
            fecha_elem = articulo_elem.select_one('.date, .post-date, time')
            fecha_texto = fecha_elem.get_text(strip=True) if fecha_elem else None
            fecha = self._parsear_fecha(fecha_texto) if fecha_texto else timezone.now().date()

            # Autor
            autor_elem = articulo_elem.select_one('.author, .by')
            autor = autor_elem.get_text(strip=True) if autor_elem else 'admin'

            # Link al artículo completo (opcional, para fetch de más contenido)
            link_elem = articulo_elem.select_one('a')
            link = link_elem.get('href') if link_elem else None

            return {
                'titulo': titulo,
                'bajada': bajada,
                'cuerpo': bajada,  # En un scrape básico, reutilizamos bajada
                'imagen_url': img_src,
                'fecha': fecha,
                'autor': autor,
                'link': link,
            }
        except Exception as e:
            logger.error(f'Error extrayendo noticia: {e}')
            return None

    def _parsear_fecha(self, texto):
        """Intenta parsear fecha en formato "abril 30, 2026" → date object."""
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
        }
        try:
            partes = texto.lower().split()
            if len(partes) >= 2:
                mes = meses.get(partes[0])
                dia = int(partes[1].rstrip(','))
                anio = int(partes[-1]) if partes[-1].isdigit() else timezone.localdate().year
                if mes:
                    return timezone.datetime(anio, mes, dia).date()
        except Exception as e:
            logger.warning(f'No se pudo parsear fecha "{texto}": {e}')
        return timezone.now().date()

    def importar_noticias(self, modelo_noticia, limite_paginas=None, permitir_duplicados=False):
        """Scrapea e importa noticias directamente a Django.

        Args:
            modelo_noticia: Clase Noticia de Django
            limite_paginas: Si es int, procesa solo N páginas
            permitir_duplicados: Si False, salta noticias que ya existan por título

        Retorna: (creadas, saltadas)
        """
        noticias_raw = self.scrape_noticias(limite_paginas=limite_paginas)
        creadas, saltadas = 0, 0

        for datos in noticias_raw:
            # Verifica duplicados
            if not permitir_duplicados and modelo_noticia.objects.filter(
                titulo=datos['titulo']
            ).exists():
                self.log(f"⏭️  Saltando duplicado: {datos['titulo'][:50]}...")
                saltadas += 1
                continue

            # Descarga la imagen
            imagen_content = None
            if datos['imagen_url']:
                imagen_content, filename = self._download_imagen(
                    datos['imagen_url'],
                    filename_hint=f"{datos['titulo'][:30]}.jpg"
                )

            # Crea la noticia
            noticia = modelo_noticia(
                titulo=datos['titulo'],
                bajada=datos['bajada'][:200],  # Trunca a 200 chars
                cuerpo=datos['cuerpo'],
                publicada=True,  # Las importadas comienzan publicadas
            )

            if imagen_content:
                noticia.imagen.save(
                    f"noticias/{timezone.now().year}/{filename}",
                    imagen_content,
                    save=False
                )

            noticia.save()
            creadas += 1
            self.log(f"✅ Importada: {datos['titulo'][:60]}...")

        self.log(f'\nResumen: {creadas} creadas, {saltadas} saltadas')
        return creadas, saltadas

    # ------------------------------------------------------------------
    # Galería: extrae las imágenes destacadas de los posts de noticias
    # (el sitio oficial no tiene un módulo de galería separado).
    # ------------------------------------------------------------------
    def scrape_galeria(self, limite_paginas=None):
        """Reutiliza el scrape de noticias y devuelve solo las que tienen imagen.

        Retorna lista de dicts: {titulo, imagen_url, anio}.
        """
        noticias = self.scrape_noticias(limite_paginas=limite_paginas)
        items = []
        for n in noticias:
            if n.get('imagen_url'):
                items.append({
                    'titulo': n['titulo'],
                    'imagen_url': n['imagen_url'],
                    'anio': n['fecha'].year,
                })
        self.log(f'Total de imágenes para galería: {len(items)}')
        return items

    def importar_galeria(self, modelo_item, limite_paginas=None, permitir_duplicados=False):
        """Scrapea imágenes de los posts e importa a ItemGaleria.

        Args:
            modelo_item: Clase ItemGaleria de Django
            limite_paginas: Si es int, procesa solo N páginas
            permitir_duplicados: Si False, salta ítems con el mismo título

        Retorna: (creadas, saltadas)
        """
        items_raw = self.scrape_galeria(limite_paginas=limite_paginas)
        creadas, saltadas = 0, 0

        for datos in items_raw:
            if not permitir_duplicados and modelo_item.objects.filter(
                titulo=datos['titulo']
            ).exists():
                self.log(f"⏭️  Saltando duplicado: {datos['titulo'][:50]}...")
                saltadas += 1
                continue

            imagen_content, filename = self._download_imagen(
                datos['imagen_url'],
                filename_hint=f"{datos['titulo'][:30]}.jpg",
            )
            if not imagen_content:
                self.log(f"⚠️  Sin imagen descargable: {datos['titulo'][:50]}")
                saltadas += 1
                continue

            item = modelo_item(titulo=datos['titulo'][:150], anio=datos['anio'])
            item.imagen.save(
                f"galeria/{datos['anio']}/{filename}", imagen_content, save=False
            )
            item.save()
            creadas += 1
            self.log(f"✅ Imagen importada: {datos['titulo'][:60]}...")

        self.log(f'\nResumen galería: {creadas} creadas, {saltadas} saltadas')
        return creadas, saltadas
