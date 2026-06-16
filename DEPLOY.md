# Deploy en Render

Guía paso a paso para subir Mater Dolorosa a Render.

## Requisitos

- Cuenta en Render (https://render.com)
- Repositorio en GitHub (ya tienes: CamiloGonzalezSt/Sistema-Mater-Dolorosa)

## Pasos

### 1. Conectar GitHub a Render

1. Ve a https://render.com y entra con tu cuenta
2. Dashboard → New → Web Service
3. Conecta tu repositorio: "Connect GitHub account"
4. Busca y selecciona `Sistema-Mater-Dolorosa`
5. Autoriza Render para acceder a tu GitHub

### 2. Configurar el Web Service

En el formulario de creación, rellena:

| Campo | Valor |
|-------|-------|
| **Name** | `mater-dolorosa` (o el que prefieras) |
| **Environment** | `Python 3` |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput` |
| **Start Command** | `gunicorn config.wsgi:application` |
| **Plan** | Free |

### 3. Configurar Variables de Entorno

En el formulario, baja a **Environment** y agrega:

```
DJANGO_SETTINGS_MODULE = config.settings.production
SECRET_KEY = [Render genera automáticamente]
DEBUG = False
ALLOWED_HOSTS = mater-dolorosa.onrender.com
USE_SQLITE = True
ADMIN_2FA = False
```

**Importante:**
- Render generará un `SECRET_KEY` automático si dejas el campo vacío
- Reemplaza `mater-dolorosa.onrender.com` con tu dominio real (Render te lo asignará)

### 4. Deploy

1. Haz clic en **Create Web Service**
2. Render inicia el build automáticamente (toma ~2-3 min)
3. Ve al tab **Logs** para ver el progreso
4. Una vez listo, verás la URL: `https://mater-dolorosa.onrender.com`

### 5. Crear un Superuser (Admin)

Una vez desplegado, abre una shell en Render:

1. Dashboard → tu service → Shell
2. Ejecuta:
```bash
python manage.py createsuperuser
```
3. Completa email, contraseña, etc.

Ahora puedes entrar en `/admin/` o `/panel/`

## Datos de Prueba

Para agregar datos de prueba (alumnos, cursos, etc.), usa:

```bash
python manage.py seed_prueba
```

## Troubleshooting

### "Static files not found" (404 en CSS/JS)

- Verifica que `collectstatic` pasó en los logs
- Si falla, el `STATIC_ROOT` puede no existir
- Solución: ejecuta manualmente en la shell de Render:
  ```bash
  python manage.py collectstatic --noinput
  ```

### "Database locked" (SQLite)

- SQLite en Render tiene limitaciones de concurrencia
- Esto es normal si hay muchos usuarios simultáneos
- Solución: migrar a PostgreSQL (en Render hay una opción integrada)

### "Secret key invalid"

- Render genera uno automático, pero a veces falla
- Solución: ve a Dashboard → tu service → Environment
  - Borra `SECRET_KEY`
  - Guarda cambios (Render generará uno nuevo)
  - Redeploy

## Próximos Pasos

- **Dominio personalizado:** En Render, puedes agregar tu dominio en Custom Domains
- **PostgreSQL:** Cuando crezcas, crea una PostgreSQL database en Render y cambia `DATABASES` en `config/settings/base.py`
- **Email:** Configura SMTP (Gmail, Mailgun) en las variables de entorno para notificaciones

---

¿Preguntas? Revisa https://render.com/docs
