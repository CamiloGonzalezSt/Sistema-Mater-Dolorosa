# Sistema Mater Dolorosa — Contexto completo del proyecto

> Este documento es el punto de partida para cualquier nueva sesión de trabajo.
> Describe la arquitectura, los modelos de datos, las features implementadas y el roadmap.

---

## 1. ¿Qué es el proyecto?

Portal web y sistema de gestión interna del **Colegio Mater Dolorosa** (Huechuraba, Santiago).
Tiene dos grandes partes:

| Parte | URL base | Propósito |
|-------|----------|-----------|
| **Sitio público** | `/` | Noticias, galería, calendario, admisión, contacto |
| **Panel interno** | `/panel/` | Asistencia, notas, convivencia, cobros, mensajes |

---

## 2. Stack técnico

| Componente | Tecnología |
|-----------|-----------|
| Backend | **Django 5.2** (Python) |
| Base de datos | **MySQL 8** (InnoDB, utf8mb4) |
| ORM | Django ORM (sin DRF — solo vistas Django clásicas + JSON para el dashboard) |
| Frontend | HTML + CSS (design tokens) + JS vanilla |
| Fuente ícono | Tabler Icons (subset de 18 íconos, `~5 KB`) |
| Fuente display | Sora (OFL, auto-hospedada, pesos 400/700/800) |
| Estáticos | WhiteNoise (comprimidos/cacheables en producción) |
| Auth | `CustomUser` con `AbstractUser`, login por **email** (no username) |
| Seguridad | `django-axes` (5 intentos, bloqueo 15 min), CSRF, sessions 1h, HTTPS en prod |
| Auditoría | `django-simple-history` en `Calificacion`, `Pago`, `Anotacion` |
| 2FA (admin) | `django-otp` + `OTPAdminSite` tras flag `ADMIN_2FA` (apagado por defecto) |
| PWA | `manifest.webmanifest` + Service Worker (`sw.js`), íconos 192/512 |
| SEO | `sitemap.xml`, `robots.txt`, `og:image`, `meta description` |
| Excel export | `openpyxl` — cobros exportables a `.xlsx` (solo admin) |
| PDF | `reportlab` (disponible, se usa en asistencia/calificaciones) |
| Scraping | `beautifulsoup4` + `requests` para importar noticias desde materdolorosa.cl |

---

## 3. Entorno de desarrollo

```
# Stack local (Windows 11)
- Python venv en ./venv/
- MySQL local en puerto 3306 (o 3308 según disponibilidad)
- Servidor de desarrollo: python manage.py runserver

# Variables de entorno (.env en la raíz)
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=mater_dolorosa
DB_USER=...
DB_PASSWORD=...
DB_HOST=127.0.0.1
DB_PORT=3306
ADMIN_2FA=False          # no activar sin antes enrolar el dispositivo

# Settings
config/settings/base.py         -- compartido
config/settings/development.py  -- DEBUG=True, sin HTTPS
config/settings/production.py   -- HTTPS, HSTS, WhiteNoise comprimido
```

Para correr tests:
```
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py test
# → 80 tests, todos en verde
```

---

## 4. Estructura de apps

```
apps/
├── accounts/       # CustomUser (rol: admin/profesor/alumno/apoderado)
├── academico/      # NivelEducacional, Curso, Asignatura, CursoAsignatura, MaterialAcademico
├── alumnos/        # PerfilAlumno, Matricula, PerfilApoderado, AlumnoApoderado
├── profesores/     # PerfilProfesor (especialidad, título)
├── asistencia/     # RegistroAsistencia (presente/ausente/justificado/atrasado)
├── calificaciones/ # PeriodoEvaluacion, TipoEvaluacion, Evaluacion, Calificacion
├── convivencia/    # Anotacion (hoja de vida), Citacion (apoderados)
├── contabilidad/   # TipoArancel, Cobro, Pago
├── comunicaciones/ # Mensaje (alumno/apoderado → profesor)
├── web_publica/    # Noticia, EventoCalendario, ItemGaleria, Postulacion, EquipoConvivencia
└── core/           # HomeView, DashboardDataView, mixins, context_processors, templatetags
```

---

## 5. Modelos clave

### 5.1 Usuarios y roles (`apps/accounts`)

```python
class CustomUser(AbstractUser):
    email    # campo de login (único)
    rut      # RUT chileno validado
    role     # 'admin' | 'profesor' | 'alumno' | 'apoderado'
    phone
    foto
```

Roles definidos en `CustomUser.Role`. RBAC manual: `RoleRequiredMixin` en `apps/core/mixins.py`.

### 5.2 Estructura académica

```
NivelEducacional ("1° Básico" ... "4° Medio")
  └── Curso (nivel + letra + anio_escolar + profesor_jefe)
        └── CursoAsignatura (curso + asignatura + profesor + anio_escolar)
              ├── RegistroAsistencia (matricula + fecha + estado)
              ├── Evaluacion (tipo + nombre + fecha + puntaje_maximo)
              │     └── Calificacion (matricula + nota) [auditada]
              └── MaterialAcademico (archivo + periodo + titulo)

PerfilAlumno ──── Matricula (alumno + curso + anio_escolar + estado)
```

### 5.3 Contabilidad

```
TipoArancel (nombre + monto_base)
  └── Cobro (matricula + tipo_arancel + periodo + monto + fecha_vencimiento + estado)
        └── Pago (monto_pagado + medio_pago + comprobante) [auditado]
```

`Cobro.refrescar_estado()` recalcula automáticamente: pendiente → vencido → pagado.

### 5.4 Comunicaciones

```
Mensaje (remitente → destinatario[profesor] + pupilo? + tipo + asunto + cuerpo + leido)
```
- Tipos: `mensaje` | `solicitud_citacion`
- Las notificaciones del navbar (`campana`) leen `leido=False` del usuario autenticado.

### 5.5 Convivencia

```
Anotacion (matricula + tipo[positiva/negativa/observacion] + descripcion + fecha) [auditada]
Citacion  (matricula + apoderado + fecha_hora + motivo + estado + acuerdos)
```

### 5.6 Sitio público

```
Noticia (titulo + bajada + cuerpo + imagen + fecha + publicada)
EventoCalendario (titulo + fecha + hora + lugar)
ItemGaleria (titulo + anio + imagen | video_url)
Postulacion (nombre_postulante + nivel + apoderado + email + estado)
EquipoConvivencia (nombre + cargo + descripcion)
```

---

## 6. URL map completo

```
/                         → web_publica:home
/noticias/                → lista de noticias
/noticias/<slug>/         → detalle noticia
/calendario/              → grilla mensual con eventos
/galeria/                 → galería con filtro por año
/quienes-somos/
/historia/
/convivencia-escolar/
/admision/
/contacto/
/postular/

/sitemap.xml              → SEO sitemap
/robots.txt
/manifest.webmanifest     → PWA manifest
/sw.js                    → Service Worker

/accounts/login/
/accounts/logout/
/accounts/password-reset/

/panel/                   → Dashboard (requiere login)
/panel/api/dashboard/     → JSON con KPIs
/panel/asistencia/
/panel/calificaciones/
/panel/convivencia/
/panel/contabilidad/
/panel/contabilidad/export-xlsx/  → exportar cobros a Excel (solo admin)
/panel/mi-cuenta/
/panel/mensajes/
/panel/materiales/
/panel/pupilos/           → vista del apoderado (sus alumnos)
/panel/postulaciones/

/admin/                   → Django Admin (2FA si ADMIN_2FA=True)
```

---

## 7. Features implementadas (9 en la última tanda)

| # | Feature | Ubicación principal |
|---|---------|-------------------|
| 1 | **Subset de íconos Tabler** (~1 MB → ~5 KB) | `static/css/tabler-icons.subset.css`, `scripts/subset_icons.py` |
| 2 | **Fuente Sora** (OFL, auto-hospedada) | `static/css/fonts/Sora-*.woff2`, `static/css/base.css` |
| 3 | **sitemap.xml** (páginas + noticias) | `apps/web_publica/views.py → sitemap_xml` |
| 4 | **PWA instalable** (manifest + SW + íconos) | `templates/manifest.webmanifest`, `templates/sw.js`, `static/img/icon-{192,512}.png` |
| 5 | **Tendencia ▲/▼ KPI asistencia** | `apps/core/views.py → DashboardDataView` → `tendencia_asistencia` |
| 6 | **Campana de notificaciones** (mensajes no leídos) | `apps/core/context_processors.py → notificaciones`, `templates/base.html` |
| 7 | **Calendario en grilla mensual** (navegación ‹ ›) | `apps/web_publica/views.py → CalendarioView`, `templates/web_publica/calendario.html` |
| 8 | **Export a Excel (.xlsx)** de cobros | `apps/contabilidad/views.py → ExportCobrosXlsxView` |
| 9 | **2FA para /admin/** (django-otp, flag `ADMIN_2FA`) | `config/settings/base.py`, `config/urls.py`, `apps/core/management/commands/enrolar_2fa.py` |

### Features anteriores (fundacionales)
- Design tokens unificados (`--color-navy`, `--color-gold`, etc.) en `static/css/base.css`
- Lenguaje visual consistente sitio público + panel (navbar, cards, chips, botones)
- Configuración de producción (HTTPS, HSTS, WhiteNoise, logging, email SMTP)
- Scraping automático de noticias desde materdolorosa.cl (`importar_noticias`, `importar_galeria`)
- Django axes (brute-force protection), CSRF, XFrameOptions, content-type nosniff
- django-simple-history en Calificacion, Pago, Anotacion

---

## 8. Comandos de gestión disponibles

```bash
# Poblar datos de demo (crea usuarios/cursos/alumnos de prueba)
python manage.py seed_demo

# Importar noticias desde el sitio web del colegio
python manage.py importar_noticias

# Importar galería desde el sitio web del colegio
python manage.py importar_galeria

# Marcar cobros vencidos (pensado para cron diario)
python manage.py marcar_vencidos

# Enrolar 2FA para el admin (generar QR TOTP)
python manage.py enrolar_2fa <email>
# Después de escanear el QR, activar con ADMIN_2FA=True en .env
```

---

## 9. Archivos CSS / estáticos clave

```
static/
├── css/
│   ├── base.css                      # design tokens + estilos globales + Sora @font-face
│   ├── panel.css                     # estilos del panel interno (dashboard, KPIs, campana)
│   ├── publica.css                   # estilos del sitio público (hero, cards, calendario)
│   ├── tabler-icons.subset.css       # solo los 18 íconos usados (1.1 KB)
│   └── fonts/
│       ├── tabler-icons.subset.woff2 # fuente subset (4.2 KB)
│       ├── Sora-Regular.woff2
│       ├── Sora-Bold.woff2
│       └── Sora-ExtraBold.woff2
└── img/
    ├── mater.png                     # logo del colegio (usado en header, login, OG)
    ├── icon-192.png                  # ícono PWA
    └── icon-512.png                  # ícono PWA
```

`{% static_v 'css/base.css' %}` — templatetag personalizado que agrega `?v=<hash>` para cache-busting automático (en `apps/core/templatetags/static_cache.py`).

---

## 10. Tests

80 tests en verde. Correr con:
```bash
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py test
```

Cada app tiene su `tests.py`. El smoke test rápido es `smoke_test.py` en la raíz.

---

## 11. Cosas pendientes de acción manual (requieren el admin)

### A. Activar 2FA en /admin/
```bash
# 1. Enrolar dispositivo (genera QR para Google Authenticator)
python manage.py enrolar_2fa caj.gonzalez.st@gmail.com

# 2. Activar en .env
ADMIN_2FA=True

# 3. Reiniciar servidor
```
Afecta solo a `/admin/`. El panel `/panel/` no requiere 2FA.

### B. Configurar SMTP en producción
Agregar en `.env` de producción:
```
EMAIL_HOST=smtp.tu-proveedor.cl
EMAIL_PORT=587
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
EMAIL_USE_TLS=True
```

---

## 12. Roadmap propuesto (próximas features)

Ordenado por impacto/esfuerzo:

| Prioridad | Feature | Descripción |
|-----------|---------|-------------|
| Alta | **Export notas a Excel** | Similar al export de cobros, para calificaciones por curso/período |
| Alta | **PDF boletín de notas** | Boletín semestral del alumno en PDF (reportlab ya instalado) |
| Media | **Tendencias en más KPIs** | Notas y convivencia con ▲/▼ como la asistencia |
| Media | **Alertas automáticas** | Email al apoderado cuando alumno falta mucho o baja nota |
| Media | **Vista apoderado** | Dashboard propio: ver notas, asistencia y cobros de sus hijos |
| Baja | **Personalización de dashboard** | Cada profesor puede reordenar sus KPIs |
| Baja | **Agenda compartida** | Eventos visibles para profesores + apoderados |

---

## 13. Historial de commits (referencia rápida)

```
9adea1d Renombrar logo a mater.png y fijar requirements.txt
22ec98c Merge branch 'main' of https://github.com/CamiloGonzalezSt/Sistema-Mater-Dolorosa
fc2e8a6 2FA opcional para el panel de administración (django-otp)
a7a74c7 Exportar cobros a Excel (.xlsx)
110588d Calendario en grilla mensual con navegación
15d783a Campana de notificaciones in-app (mensajes no leídos)
ea1bad8 Tendencia ▲/▼ en el KPI de asistencia del dashboard
9490c40 SEO (sitemap) + PWA instalable
b205798 Fuente display Sora (OFL) para títulos
1bc147a Subset de Tabler Icons: ~1 MB -> ~5 KB
e8e3ac0 Producción + quick wins (estáticos, email, logging, SEO, a11y)
b1c97d5 Unificación del lenguaje visual (sitio público + panel)
d75b977 Sistema de design tokens + limpieza de base.css
2554f77 Estado inicial del proyecto Mater Dolorosa
```

---

## 14. Repositorio

- **GitHub:** https://github.com/CamiloGonzalezSt/Sistema-Mater-Dolorosa
- **Rama principal:** `main`
- **Git user:** camiloGonzalezs
- **Email admin:** caj.gonzalez.st@gmail.com
