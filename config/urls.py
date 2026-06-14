"""URLs raíz del proyecto Mater Dolorosa."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from apps.contabilidad.views import MiCuentaView
from apps.core.views import DashboardDataView, HomeView
from apps.web_publica.views import CambiarEstadoPostulacionView, PostulacionesAdminView

urlpatterns = [
    path(
        'robots.txt',
        TemplateView.as_view(template_name='robots.txt', content_type='text/plain'),
        name='robots',
    ),
    path('', include('apps.web_publica.urls')),
    path('panel/', HomeView.as_view(), name='home'),
    path('panel/api/dashboard/', DashboardDataView.as_view(), name='dashboard_data'),
    path('panel/asistencia/', include('apps.asistencia.urls')),
    path('panel/calificaciones/', include('apps.calificaciones.urls')),
    path('panel/convivencia/', include('apps.convivencia.urls')),
    path('panel/contabilidad/', include('apps.contabilidad.urls')),
    path('panel/mi-cuenta/', MiCuentaView.as_view(), name='mi_cuenta'),
    path('panel/mensajes/', include('apps.comunicaciones.urls')),
    path('panel/materiales/', include('apps.academico.urls')),
    path('panel/pupilos/', include('apps.alumnos.urls')),
    path('panel/postulaciones/', PostulacionesAdminView.as_view(), name='postulaciones_admin'),
    path('panel/postulaciones/<int:pk>/estado/', CambiarEstadoPostulacionView.as_view(), name='postulacion_estado'),
    path('accounts/', include('apps.accounts.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
