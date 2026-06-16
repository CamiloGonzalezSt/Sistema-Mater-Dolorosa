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
| Base de datos | **SQLite** (producción en Render), MySQL (desarrollo local opcional) |
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
| Excel export | `openpyxl` — cobros y notas exportables a `.xlsx` |
| PDF | `reportlab` (disponible, se usa en asistencia/calificaciones) |
| Scraping | `beautifulsoup4` + `requests` para importar noticias desde materdolorosa.cl |

---

## 3. Entorno de desarrollo

### Local (Windows 11)
```
- Python venv en ./venv/
- SQLite local (db.sqlite3) — migrado de MySQL para facilitar deploy
- Servidor de desarrollo: python manage.py runserver

# Variables de entorno (.env en la raíz)
SECRET_KEY=django-insecure-dev-key-only-for-testing
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
USE_SQLITE=True
ADMIN_2FA=False          # no activar sin antes enrolar el dispositivo

# Settings
config/settings/base.py         -- compartido (con soporte SQLite/MySQL condicional)
config/settings/development.py  -- DEBUG=True, sin HTTPS, SQLite
config/settings/production.py   -- HTTPS, HSTS, WhiteNoise comprimido
```

Para correr tests:
```
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py test
# → 80 tests, todos en verde
```

### Producción (Render)
```
URL en vivo: https://mater-dolorosa.onrender.com/

Configuración:
- Environment: Python 3
- Build: pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
- Start: gunicorn config.wsgi:application
- Database: SQLite en disco de Render
- Plan: Free tier (duerme tras 15 min de inactividad, primer request ~10s)

Ver DEPLOY.md para instrucciones detalladas de deploy.
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
/panel/calificaciones/                        → libro de notas (admin/profesor)
/panel/calificaciones/exportar/               → export notas a .xlsx (admin/profesor)
/panel/calificaciones/mis-notas/              → mis notas (solo alumno)
/panel/convivencia/
/panel/contabilidad/
/panel/contabilidad/export-xlsx/              → exportar cobros a Excel (solo admin)
/panel/mi-cuenta/
/panel/mensajes/
/panel/materiales/
/panel/pupilos/           → vista del apoderado (sus alumnos)
/panel/postulaciones/

/admin/                   → Django Admin (2FA si ADMIN_2FA=True)
```

---

## 7. Features implementadas

### Tanda 1 — Fundacionales
- Design tokens unificados (`--color-navy`, `--color-gold`, etc.) en `static/css/base.css`
- Lenguaje visual consistente sitio público + panel (navbar, cards, chips, botones)
- Configuración de producción (HTTPS, HSTS, WhiteNoise, logging, email SMTP)
- Scraping automático de noticias desde materdolorosa.cl (`importar_noticias`, `importar_galeria`)
- django-axes (brute-force), CSRF, XFrameOptions, content-type nosniff
- django-simple-history en Calificacion, Pago, Anotacion

### Tanda 2 — Performance, PWA y UX

| # | Feature | Ubicación principal |
|---|---------|-------------------|
| 1 | **Subset de íconos Tabler** (~1 MB → ~5 KB) | `static/css/tabler-icons.subset.css`, `scripts/subset_icons.py` |
| 2 | **Fuente Sora** (OFL, auto-hospedada) | `static/css/fonts/Sora-*.woff2`, `static/css/base.css` |
| 3 | **sitemap.xml** (páginas + noticias) | `apps/web_publica/views.py → sitemap_xml` |
| 4 | **PWA instalable** (manifest + SW + íconos) | `templates/manifest.webmanifest`, `templates/sw.js` |
| 5 | **Tendencia ▲/▼ KPI asistencia** | `apps/core/views.py → DashboardDataView` |
| 6 | **Campana de notificaciones** (mensajes no leídos) | `apps/core/context_processors.py → notificaciones` |
| 7 | **Calendario en grilla mensual** (navegación ‹ ›) | `apps/web_publica/views.py → CalendarioView` |
| 8 | **Export cobros a Excel (.xlsx)** | `apps/contabilidad/views.py → ExportarCobrosExcelView` |
| 9 | **2FA para /admin/** (django-otp, flag `ADMIN_2FA`) | `config/settings/base.py`, `config/urls.py` |

### Tanda 3 — Notas y usuarios de prueba

| # | Feature | Detalle |
|---|---------|---------|
| 10 | **Export notas a Excel** | Admin/profesor filtra curso+período → `.xlsx` con columna por evaluación y promedio por alumno. URL: `/panel/calificaciones/exportar/`. Vista: `ExportarNotasExcelView` en `apps/calificaciones/views.py` |
| 11 | **Vista "Mis notas" (alumno)** | Alumno ve sus calificaciones agrupadas por período y asignatura. Diseño con hero, grid de cards, barra de progreso y badges de nota. 4 niveles de color: excelente ≥6, buena ≥5, suficiente ≥4, insuficiente <4. URL: `/panel/calificaciones/mis-notas/`. CSS en `static/css/mis_notas.css` |
| 12 | **Usuarios de prueba creados** | Ver sección 11 |

---

## 8. Usuarios de prueba en la BD

### Usuarios demo generales (seed_demo)
- `profesor.demo@demo.cl` / `Demo#2026` — Profesor
- `alumnoNN@demo.cl` / `Demo#2026` — Alumnos (01 al 20), en 7° Básico A
- `apoderadoNN@demo.cl` / `Demo#2026` — Apoderados vinculados

### Usuarios de prueba manuales
| Email | Contraseña | Rol | Detalle |
|-------|-----------|-----|---------|
| `gcastro@gmail.com` | `gcastro2026` | Apoderado | Gisselle Castro, madre de Felipe Soto |
| `fsoto@gmail.com` | `Demo#2026` | Alumno | Felipe Soto, 2° Medio A, 8 asignaturas × 4 notas |
| `icid@gmail.com` | `icid2026` | Apoderado | Ignacia Cid, madre de Javiera Muñoz |
| `jmunoz@gmail.com` | `Demo#2026` | Alumno | Javiera Muñoz, 8° Básico A, 8 asignaturas × 4 notas |

**Asignaturas de Felipe y Javiera:** Matemática, Lenguaje, Historia, Ciencias, Química, Educación Física, Música, Tecnología (4 evaluaciones cada una en el 1° Semestre 2026).

---

## 9. Archivos CSS / estáticos clave

```
static/
├── css/
│   ├── base.css                      # design tokens + estilos globales + Sora @font-face
│   ├── panel.css                     # estilos del panel interno (dashboard, KPIs, campana, libro de notas)
│   ├── mis_notas.css                 # estilos exclusivos de la vista "Mis notas" del alumno
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

## 10. Comandos de gestión disponibles

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

## 11. Tests

80 tests en verde. Correr con:
```bash
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py test
```

Cada app tiene su `tests.py`. El smoke test rápido es `smoke_test.py` en la raíz.

---

## 12. Cosas pendientes de acción manual (requieren el admin)

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

## 13. Roadmap (pendiente)

| Prioridad | Feature | Descripción |
|-----------|---------|-------------|
| Alta | **PDF boletín de notas** | Boletín semestral del alumno en PDF (reportlab ya instalado) |
| Media | **Tendencias en más KPIs** | Notas y convivencia con ▲/▼ como la asistencia |
| Media | **Alertas automáticas** | Email al apoderado cuando alumno falta mucho o baja nota |
| Media | **Vista apoderado mejorada** | Dashboard propio con notas + asistencia + cobros en una sola pantalla |
| Baja | **Personalización de dashboard** | Cada profesor puede reordenar sus KPIs |
| Baja | **Agenda compartida** | Eventos visibles para profesores + apoderados |

---

## 14. Historial de commits (referencia rápida)

**Sesión actual (Deploy en Render):**
```
d730c7f Cambiar a CompressedStaticFilesStorage (sin validación estricta)
847496c Agregar tabler-icons.woff para compatibilidad con collectstatic
76c6d36 Corregir versión de whitenoise (6.1.2 no existe, usar 6.12.0)
b871729 Corregir encoding corrupto en requirements.txt
8d10ec4 Agregar guía de deploy en Render con instrucciones paso a paso
da730c7 Preparar proyecto para deploy en Render con SQLite
cfcddef Notas del apoderado con mismo diseño que 'Mis notas' del alumno
```

**Sesiones anteriores (Features implementadas):**
```
b630713 Rediseño completo de 'Mis notas': hero, grid de cards y barras de progreso
e41caa7 Export notas a Excel + vista 'Mis notas' para alumnos
d0734db Agregar documento de contexto completo del proyecto
9adea1d Renombrar logo a mater.png y fijar requirements.txt
22ec98c Merge branch 'main'
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

## 15. Repositorio y Deployment

| Recurso | Enlace |
|---------|--------|
| **GitHub** | https://github.com/CamiloGonzalezSt/Sistema-Mater-Dolorosa |
| **Rama principal** | `main` |
| **Git user** | camiloGonzalezs |
| **Email admin** | caj.gonzalez.st@gmail.com |
| **Sitio en vivo (Render)** | https://mater-dolorosa.onrender.com/ |
| **Documentación deploy** | [DEPLOY.md](DEPLOY.md) — pasos para nuevo deploy |

---

## 16. Notas importantes para la próxima sesión

### Base de datos
- **Actual:** SQLite en producción (Render), MySQL opcional en desarrollo
- Si necesitas MySQL en producción, cambiar `USE_SQLITE=False` en .env y agregar credenciales DB_*

### Datos de prueba
- Usuarios de prueba creados con `python manage.py seed_prueba`
- Gisselle Castro (apoderado) → Felipe Soto (alumno 2° Medio)
- Ignacia Cid (apoderado) → Javiera Muñoz (alumno 8° Básico)
- Cada alumno con 8 asignaturas y 4 calificaciones aleatorias

### URLs clave en la app
| Sección | URL |
|---------|-----|
| Sitio público | `/` |
| Login | `/accounts/login/` |
| Panel principal | `/panel/` |
| Mis notas (alumno) | `/panel/calificaciones/mis-notas/` |
| Notas pupilos (apoderado) | `/panel/pupilos/notas/` |
| Admin Django | `/admin/` |

### Limitaciones conocidas (free tier Render)
- Duerme tras 15 min sin requests → primer acceso ~10s de espera
- Mejor rendimiento con upgrade (~$7/mes)
- Base de datos SQLite tiene límite de concurrencia (migrar a PostgreSQL si crece mucho)

### Próximos pasos sugeridos
- [ ] Cambiar a PostgreSQL (integrado en Render) si muchos usuarios simultáneos
- [ ] Agregar dominio personalizado (ej: materdolorosa.cl)
- [ ] Configurar email SMTP para notificaciones
- [ ] Recopilar feedback de usuarios reales
- [ ] Migrar assets pesados a CDN si es necesario
