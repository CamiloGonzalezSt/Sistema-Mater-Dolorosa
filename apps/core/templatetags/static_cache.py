"""Etiqueta `static_v`: como `{% static %}` pero añade `?v=<mtime>` para
romper la caché del navegador automáticamente cada vez que el archivo cambia.

Uso:
    {% load static_cache %}
    <link rel="stylesheet" href="{% static_v 'css/publica.css' %}">
"""
import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(path):
    url = static(path)
    ruta_absoluta = finders.find(path)
    if ruta_absoluta and os.path.exists(ruta_absoluta):
        version = int(os.path.getmtime(ruta_absoluta))
        separador = '&' if '?' in url else '?'
        return f'{url}{separador}v={version}'
    return url
