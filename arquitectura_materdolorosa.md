# Arquitectura del Sistema: Mater Dolorosa
**Stack:** Python 3.12 · Django 5.x · MySQL 8.x · HTML5 · CSS3 · JavaScript (Vanilla + HTMX)

---

## 1. Arquitectura del Sistema

### Patrón: Monolito Modular con Django Apps

```
materdolorosa/                  # Proyecto raíz Django
├── config/                     # Settings, URLs raíz, WSGI/ASGI
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── core/                   # Modelos base, mixins, utilidades
│   ├── accounts/               # Usuarios, roles, autenticación
│   ├── web_publica/            # Sitio público (home, noticias, contacto)
│   ├── alumnos/                # Perfiles alumnos + apoderados
│   ├── profesores/             # Perfiles profesores + asignaturas
│   ├── academico/              # Cursos, horarios, asignaturas
│   ├── asistencia/             # Registro diario de asistencia
│   ├── calificaciones/         # Libro de notas, períodos, promedios
│   └── contabilidad/           # Pagos, aranceles, egresos
├── static/                     # CSS, JS, imágenes globales
├── media/                      # Uploads (documentos, fotos)
├── templates/                  # Templates base + por app
└── requirements/
    ├── base.txt
    ├── development.txt
    └── production.txt
```

### Flujo de Comunicación Frontend ↔ Backend

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTE (Browser)                        │
│  Web Pública (HTML/CSS/JS)  │  CRM Interno (HTML + HTMX/Fetch) │
└──────────────┬──────────────┴──────────────┬────────────────────┘
               │ HTTP/HTTPS (Request)         │ HTMX Partial Requests
               ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Nginx (Reverse Proxy)                       │
│              SSL Termination · Static Files                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                   Gunicorn (WSGI Server)                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    Django Application                           │
│  Middleware Stack → URL Router → Views → Forms/Serializers      │
│  ┌─────────────┐  ┌────────────────┐  ┌──────────────────────┐ │
│  │  Templates  │  │   ORM Queries  │  │  Django Auth + RBAC  │ │
│  └─────────────┘  └───────┬────────┘  └──────────────────────┘ │
└──────────────────────────┬┘────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     MySQL 8.x                                   │
│         (InnoDB · utf8mb4 · transacciones ACID)                 │
└─────────────────────────────────────────────────────────────────┘
```

**Decisiones arquitectónicas clave:**
- HTMX para interacciones dinámicas del CRM sin SPA completa (reduce complejidad, mantiene Django templates)
- Django Class-Based Views (CBVs) con mixins de permisos para RBAC
- Caché con Redis para sesiones y queries costosas (libro de notas, reportes)
- Celery + Redis para tareas asíncronas (envío de correos, generación de reportes PDF)

---

## 2. Modelo de Datos Relacional (MySQL)

### Tablas Core y Relaciones

```sql
-- ============================================================
-- ACCOUNTS: Usuarios y Roles
-- ============================================================
CustomUser (AbstractUser)
  id, email (UNIQUE), rut (UNIQUE, VARCHAR 12), first_name,
  last_name, phone, role (ENUM: admin|profesor|alumno|apoderado),
  is_active, date_joined, foto (ImageField, nullable)

-- ============================================================
-- ACADEMICO: Estructura curricular
-- ============================================================
NivelEducacional
  id, nombre (VARCHAR 50)              -- Ej: "1° Básico" → "4° Medio"

Curso
  id, nivel_id (FK→NivelEducacional), letra (CHAR 1),
  año_escolar (YEAR), capacidad (INT)
  UNIQUE(nivel_id, letra, año_escolar)

Asignatura
  id, nombre (VARCHAR 100), codigo (VARCHAR 20, UNIQUE),
  horas_semanales (INT)

-- N:M Curso ↔ Asignatura mediada por CursoAsignatura
CursoAsignatura
  id, curso_id (FK→Curso), asignatura_id (FK→Asignatura),
  profesor_id (FK→CustomUser), año_escolar (YEAR)
  UNIQUE(curso_id, asignatura_id, año_escolar)

-- ============================================================
-- ALUMNOS Y APODERADOS
-- ============================================================
PerfilAlumno
  id, usuario_id (FK→CustomUser, OneToOne),
  curso_id (FK→Curso), rut_alumno (VARCHAR 12),
  fecha_nacimiento (DATE), direccion, comuna, fecha_matricula

PerfilApoderado
  id, usuario_id (FK→CustomUser, OneToOne),
  relacion (VARCHAR 50)                -- padre, madre, tutor

-- N:M Alumno ↔ Apoderado
AlumnoApoderado
  id, alumno_id (FK→PerfilAlumno), apoderado_id (FK→PerfilApoderado),
  es_principal (BOOL, default False)

-- ============================================================
-- PROFESORES
-- ============================================================
PerfilProfesor
  id, usuario_id (FK→CustomUser, OneToOne),
  especialidad (VARCHAR 100), titulo (VARCHAR 200),
  jefe_de_curso_id (FK→Curso, nullable, OneToOne)

-- ============================================================
-- ASISTENCIA
-- ============================================================
RegistroAsistencia
  id, alumno_id (FK→PerfilAlumno), curso_asignatura_id (FK→CursoAsignatura),
  fecha (DATE), estado (ENUM: presente|ausente|justificado|atrasado),
  observacion (TEXT, nullable), registrado_por_id (FK→CustomUser)
  UNIQUE(alumno_id, curso_asignatura_id, fecha)
  INDEX(alumno_id, fecha)
  INDEX(curso_asignatura_id, fecha)

-- ============================================================
-- CALIFICACIONES
-- ============================================================
PeriodoEvaluacion
  id, nombre (VARCHAR 50),             -- "1° Semestre", "2° Semestre"
  año_escolar (YEAR), fecha_inicio (DATE), fecha_fin (DATE)

TipoEvaluacion
  id, nombre (VARCHAR 50),             -- "Prueba", "Control", "Trabajo"
  ponderacion_porcentaje (DECIMAL 5,2)

Evaluacion
  id, curso_asignatura_id (FK→CursoAsignatura),
  periodo_id (FK→PeriodoEvaluacion), tipo_id (FK→TipoEvaluacion),
  nombre (VARCHAR 150), fecha (DATE), puntaje_maximo (DECIMAL 6,2)

Calificacion
  id, evaluacion_id (FK→Evaluacion), alumno_id (FK→PerfilAlumno),
  puntaje_obtenido (DECIMAL 6,2), nota (DECIMAL 4,2),
  observacion (TEXT, nullable), fecha_registro (DATETIME auto_now_add)
  UNIQUE(evaluacion_id, alumno_id)
  INDEX(alumno_id, evaluacion_id)

-- ============================================================
-- CONTABILIDAD
-- ============================================================
TipoArancel
  id, nombre (VARCHAR 100),            -- "Matrícula", "Mensualidad", "Taller"
  monto_base (DECIMAL 10,2), descripcion (TEXT)

Cobro
  id, alumno_id (FK→PerfilAlumno), tipo_arancel_id (FK→TipoArancel),
  periodo (VARCHAR 20),                -- "2025-03", "2025-matricula"
  monto (DECIMAL 10,2), fecha_vencimiento (DATE),
  estado (ENUM: pendiente|pagado|vencido|condonado),
  created_at (DATETIME auto_now_add)
  INDEX(alumno_id, estado)

Pago
  id, cobro_id (FK→Cobro), monto_pagado (DECIMAL 10,2),
  fecha_pago (DATE), medio_pago (ENUM: efectivo|transferencia|cheque|otro),
  comprobante (FileField, nullable), registrado_por_id (FK→CustomUser),
  observacion (TEXT, nullable)
```

### Relaciones Clave para ORM

```
CustomUser      1 ──── 1   PerfilAlumno
CustomUser      1 ──── 1   PerfilProfesor
CustomUser      1 ──── 1   PerfilApoderado
NivelEducacional 1 ──── N  Curso
Curso           N ──── M   Asignatura          (via CursoAsignatura)
CursoAsignatura 1 ──── N   RegistroAsistencia
CursoAsignatura 1 ──── N   Evaluacion
Evaluacion      1 ──── N   Calificacion
PerfilAlumno    N ──── M   PerfilApoderado     (via AlumnoApoderado)
PerfilAlumno    1 ──── N   Cobro
Cobro           1 ──── N   Pago
```

**Optimización ORM:**
```python
# Ejemplo: cargar libro de notas sin N+1 queries
calificaciones = (
    Calificacion.objects
    .select_related('evaluacion__tipo', 'evaluacion__periodo', 'alumno__usuario')
    .filter(evaluacion__curso_asignatura=curso_asignatura)
    .order_by('alumno__usuario__last_name', 'evaluacion__fecha')
)
```

---

## 3. Seguridad y Privacidad

### Matriz RBAC (Control de Acceso Basado en Roles)

| Módulo / Acción              | Admin | Profesor (propio curso) | Alumno (propio) | Apoderado (su pupilo) |
|------------------------------|:-----:|:-----------------------:|:---------------:|:---------------------:|
| Gestión de usuarios          | CRUD  | —                       | —               | —                     |
| Crear/editar cursos          | CRUD  | —                       | —               | —                     |
| Ver perfil alumno            | ✓     | ✓ (solo su curso)       | ✓               | ✓                     |
| Editar perfil alumno         | ✓     | —                       | —               | —                     |
| Registrar asistencia         | ✓     | ✓ (solo su asignatura)  | —               | —                     |
| Ver asistencia               | ✓     | ✓                       | ✓               | ✓                     |
| Ingresar calificaciones      | ✓     | ✓ (solo su asignatura)  | —               | —                     |
| Ver calificaciones           | ✓     | ✓                       | ✓               | ✓                     |
| Gestión de cobros/pagos      | ✓     | —                       | —               | Ver saldo             |
| Configuración del sistema    | ✓     | —                       | —               | —                     |
| Sitio web público            | CRUD  | —                       | —               | —                     |

### Implementación RBAC en Django

```python
# apps/core/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = []

    def test_func(self):
        return self.request.user.role in self.allowed_roles

class ProfesorCursoMixin(LoginRequiredMixin):
    """Garantiza que el profesor solo acceda a sus cursos asignados."""
    def dispatch(self, request, *args, **kwargs):
        curso_asignatura_id = kwargs.get('pk')
        if not request.user.role == 'admin':
            owns = CursoAsignatura.objects.filter(
                id=curso_asignatura_id,
                profesor=request.user
            ).exists()
            if not owns:
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
```

### Medidas de Seguridad

**Protección de datos de menores (Ley 19.628 Chile + estándares COPPA):**
```python
# config/settings/base.py

# CSRF y sesiones
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True          # Solo HTTPS en producción
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600          # 1 hora — expiración agresiva
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Seguridad HTTP Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Campos sensibles — nunca en logs
SENSITIVE_FIELDS = ['rut', 'fecha_nacimiento', 'direccion', 'password']
```

**Sanitización y validación:**
```python
# apps/alumnos/validators.py
import re
from django.core.exceptions import ValidationError

def validar_rut_chileno(rut: str) -> None:
    rut = rut.replace('.', '').replace('-', '').upper()
    if not re.fullmatch(r'\d{7,8}[0-9K]', rut):
        raise ValidationError('RUT inválido.')
    # Verificar dígito verificador
    cuerpo, dv = rut[:-1], rut[-1]
    suma, mult = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * mult
        mult = mult % 7 + 2
    dv_calc = 'K' if (11 - suma % 11) == 10 else str(11 - suma % 11)
    if dv != dv_calc:
        raise ValidationError('RUT inválido (dígito verificador incorrecto).')
```

**Protección de archivos media (documentos privados):**
```python
# Archivos subidos → fuera del directorio static, validados antes de servir
# Usar django-sendfile2 en producción (Nginx X-Accel-Redirect)
SENDFILE_BACKEND = 'django_sendfile.backends.nginx'
SENDFILE_ROOT = '/srv/media/private/'
SENDFILE_URL = '/protected-media/'
```

**Auditoría:**
```python
# Usar django-simple-history en modelos críticos
from simple_history.models import HistoricalRecords

class Calificacion(models.Model):
    # ...campos...
    history = HistoricalRecords()
```

---

## 4. Roadmap de Desarrollo MVP

### Fase 1 — Fundación (Semanas 1–3)
**Objetivo:** Infraestructura base operativa.

- [ ] Setup proyecto Django con estructura modular (`config/`, `apps/`)
- [ ] Configuración MySQL + migraciones iniciales
- [ ] `CustomUser` con roles RBAC + autenticación (login/logout/reset password)
- [ ] Sistema de templates base (layout admin CRM + layout web pública)
- [ ] Deploy staging en VPS (Nginx + Gunicorn + Let's Encrypt)
- [ ] Variables de entorno con `python-decouple`, `.env` excluido de git
- [ ] Pipeline CI básico (GitHub Actions: lint + tests)

**Entregable:** Entorno funcional con login por roles.

---

### Fase 2 — Web Pública + Perfiles (Semanas 4–6)
**Objetivo:** Sitio público renovado + gestión de usuarios del CRM.

- [ ] App `web_publica`: Home, Noticias/Blog, Galería, Contacto
- [ ] Panel admin para gestión de contenido web (sin CMS externo)
- [ ] CRUD completo: Alumnos, Profesores, Apoderados
- [ ] Asignación Alumno ↔ Apoderado ↔ Curso
- [ ] Estructura académica: NivelEducacional, Curso, Asignatura, CursoAsignatura
- [ ] Gestión de foto de perfil con validación de tipo/tamaño

**Entregable:** CRM con gestión de usuarios operativa + web pública live.

---

### Fase 3 — Módulos Académicos Core (Semanas 7–10)
**Objetivo:** Asistencia y libro de calificaciones funcionales.

- [ ] Módulo Asistencia: registro diario por asignatura, vista resumen, alertas por inasistencia
- [ ] Módulo Calificaciones: ingreso de notas, cálculo automático de promedio ponderado
- [ ] Reportes: libro de asistencia PDF, informe de notas por alumno/curso
- [ ] Dashboard por rol (resúmenes estadísticos con Chart.js)
- [ ] Notificaciones por email al apoderado (Celery + SMTP)
- [ ] Tests unitarios e integración (coverage ≥ 80% en módulos críticos)

**Entregable:** Profesores pueden operar asistencia y notas. Apoderados ven el estado de su pupilo.

---

### Fase 4 — Contabilidad + Hardening (Semanas 11–14)
**Objetivo:** Módulo de pagos funcional + sistema production-ready.

- [ ] Módulo Contabilidad: aranceles, generación masiva de cobros, registro de pagos
- [ ] Estado de cuenta por alumno (vista apoderado)
- [ ] Generación de comprobante de pago PDF
- [ ] Auditoría completa con `django-simple-history`
- [ ] Rate limiting en endpoints de login (django-axes)
- [ ] Backup automatizado de MySQL (script + cron)
- [ ] Monitoreo con Sentry (errores) + UptimeRobot (disponibilidad)
- [ ] Revisión de seguridad: `python manage.py check --deploy`
- [ ] Documentación técnica y manual de usuario básico

**Entregable:** Sistema completo en producción, seguro y monitoreado.

---

## Dependencias Principales

```txt
# requirements/base.txt
Django==5.2.*
mysqlclient==2.2.*
django-environ==0.11.*
Pillow==11.*
django-simple-history==3.*
django-axes==7.*
django-sendfile2==0.3.*
celery==5.*
redis==5.*
reportlab==4.*          # Generación de PDFs
weasyprint==63.*        # PDFs desde HTML/CSS (alternativa)
gunicorn==22.*
```

```txt
# requirements/development.txt
-r base.txt
django-debug-toolbar==4.*
coverage==7.*
factory-boy==3.*        # Fixtures para tests
```
