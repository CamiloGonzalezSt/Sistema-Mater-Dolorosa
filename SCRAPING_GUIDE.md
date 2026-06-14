# Guía de Scraping: Importar contenido desde www.materdolorosa.cl

## ✅ Qué ya funciona

El script de scraping importa automáticamente:
- **Noticias** con título, descripción, imagen y fecha
- Descargas automáticas de imágenes
- Validación de duplicados (no reimporta la misma noticia)

## 📝 Cómo usar

### Opción 1: Importar todas las noticias
```bash
python manage.py importar_noticias
```

### Opción 2: Importar solo N páginas
```bash
python manage.py importar_noticias --paginas 5
```

### Opción 3: Permitir duplicados (reimporta todo)
```bash
python manage.py importar_noticias --permitir-duplicados
```

### Opción 4: Combinar opciones
```bash
python manage.py importar_noticias --paginas 3 --permitir-duplicados
```

## 🔍 Qué importó en la última ejecución

Ejecutado: `python manage.py importar_noticias --paginas 1`

Resultado:
```
✅ Charla «Prevención del consumo de drogas»
✅ Cuasimodo 2026
✅ Olimpiadas MaterMate 2026
✅ Lunes de Ángeles 2026
✅ Soledad de María
✅ Celebración Última Cena 2026

Resumen: 6 creadas, 0 saltadas
```

Todas las noticias están publicadas automáticamente y visibles en `/noticias/`.

## 📂 Dónde está el código

- **Scraper principal**: `apps/web_publica/scrapers.py`
  - Clase `ScraperMaterdolorosa`
  - Métodos: `scrape_noticias()`, `importar_noticias()`

- **Comando Django**: `apps/web_publica/management/commands/importar_noticias.py`
  - Interfaz CLI

## 🚀 Próximos pasos (opcional)

Puedes extender el scraper para importar:

1. **Eventos del calendario**
   - URL: `https://www.materdolorosa.cl/` (sección de eventos)
   - Campos: titulo, fecha, hora, lugar

2. **Galería de fotos**
   - URL: `https://www.materdolorosa.cl/galeria/`
   - Campos: imagen, año

3. **Mediadores escolares**
   - URL: `https://www.materdolorosa.cl/convivencia-escolar/`
   - Campos: nombre, descripción, curso

4. **Información institucional**
   - Historia, misión, visión
   - Contactos

## 📊 Información técnica

- **Base URL**: https://www.materdolorosa.cl
- **Parser**: BeautifulSoup4
- **Descargas HTTP**: requests library
- **Almacenamiento**: Django Media Files (MEDIA_ROOT)
- **DB**: MySQL 8.x

## ⚙️ Configuración en settings.py

```python
AXES_FAILURE_LIMIT = 5  # 5 intentos fallidos
AXES_COOLOFF_TIME = timedelta(minutes=15)  # Bloqueo por 15 min
SESSION_COOKIE_SAMESITE = 'Lax'  # Protección CSRF
SECURE_REFERRER_POLICY = 'same-origin'
```

## 🔒 Seguridad

El scraper es seguro para ejecutar:
- ✅ Respeta el User-Agent
- ✅ Valida duplicados
- ✅ Maneja errores de red gracefully
- ✅ Registra todo en logs
- ✅ No overload al servidor (timeout 10s por request)

---

**Para más detalles**, revisa el código en `apps/web_publica/scrapers.py`.
