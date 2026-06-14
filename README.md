# Colegio Mater Dolorosa — Sitio público + CRM/ERP

Plataforma web del Colegio Mater Dolorosa (Huechuraba): **sitio público** institucional
+ **panel interno** (CRM/ERP) para gestionar asistencia, calificaciones, convivencia,
contabilidad, comunicaciones y admisión, con control de acceso por rol (RBAC).

## Stack

- **Backend:** Django 5.2 (Python)
- **Base de datos:** MySQL 8 (InnoDB · utf8mb4)
- **Frontend:** Django Templates + CSS propio (sin framework) + Chart.js e íconos Tabler vendoreados (sin CDN)
- **Auditoría:** django-simple-history · **Seguridad login:** django-axes

## Puesta en marcha (desarrollo)

```bash
# 1. Entorno virtual + dependencias
python -m venv venv
venv\Scripts\activate            # Windows  (source venv/bin/activate en Linux/Mac)
pip install -r requirements/development.txt

# 2. Variables de entorno
copy .env.example .env           # cp en Linux/Mac — luego edita los valores

# 3. Base de datos (Docker)
docker compose up -d             # MySQL en el puerto definido en .env (DB_PORT, ej. 3308)

# 4. Migraciones + datos de prueba (opcional)
python manage.py migrate
python manage.py seed_demo       # datos demo para marcha blanca

# 5. Servidor
python manage.py runserver
```

App en http://localhost:8000 · panel en `/panel/` · admin en `/admin/`.

## Comandos útiles

| Comando | Descripción |
|---------|-------------|
| `python manage.py test` | Suite completa (80 tests) |
| `python manage.py seed_demo [--limpiar]` | Crea/elimina datos demo |
| `python manage.py importar_noticias [--paginas N]` | Importa noticias reales desde materdolorosa.cl |
| `python manage.py importar_galeria [--paginas N]` | Importa imágenes a la galería |
| `python manage.py marcar_vencidos` | Marca cobros vencidos |

## Configuración por entorno

`config/settings/` → `base.py` (común), `development.py`, `production.py`.
Selecciona con `DJANGO_SETTINGS_MODULE` (por defecto `config.settings.development`).

## Estructura

```
apps/                # 11 apps de dominio
  accounts/          # usuario custom + RBAC + validación RUT
  web_publica/       # sitio público (noticias, galería, admisión, contacto)
  academico/ alumnos/ profesores/
  asistencia/ calificaciones/ convivencia/ contabilidad/ comunicaciones/
  core/              # panel de inicio, dashboard, mixins, templatetags
config/              # settings, urls, wsgi/asgi
templates/           # plantillas (base, web_publica, panel por módulo, registration)
static/              # css, js, fonts, img (vendoreados)
requirements/        # base.txt + development.txt
```

## Roles (RBAC)

`admin` · `profesor` · `alumno` · `apoderado`. El panel y cada vista filtran según el rol
mediante `apps/core/mixins.py:RoleRequiredMixin`.

## Documentación adicional

- [`arquitectura_materdolorosa.md`](arquitectura_materdolorosa.md) — decisiones de arquitectura
- [`SCRAPING_GUIDE.md`](SCRAPING_GUIDE.md) — importación de contenido del sitio oficial
