from django.urls import path

from .views import RegistrarAsistenciaView, SeleccionAsistenciaView
from .views_pdf import LibroAsistenciaPDFView

app_name = 'asistencia'

urlpatterns = [
    path('', SeleccionAsistenciaView.as_view(), name='seleccionar'),
    path('<int:pk>/', RegistrarAsistenciaView.as_view(), name='registrar'),
    path('<int:pk>/libro.pdf', LibroAsistenciaPDFView.as_view(), name='libro_pdf'),
]
