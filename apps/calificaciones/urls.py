from django.urls import path

from .views import (
    ExportarNotasExcelView,
    IngresarNotasView,
    MisNotasView,
    SeleccionEvaluacionView,
)
from .views_pdf import InformeNotasPDFView

app_name = 'calificaciones'

urlpatterns = [
    path('', SeleccionEvaluacionView.as_view(), name='seleccionar'),
    path('evaluacion/<int:pk>/', IngresarNotasView.as_view(), name='ingresar'),
    path('informe/<int:pk>/informe.pdf', InformeNotasPDFView.as_view(), name='informe_pdf'),
    path('exportar/', ExportarNotasExcelView.as_view(), name='exportar_excel'),
    path('mis-notas/', MisNotasView.as_view(), name='mis_notas'),
]
