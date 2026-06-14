from django.urls import path

from .views import (
    ComprobantePagoPDFView,
    GenerarCobrosView,
    ListadoCobrosView,
    RegistrarPagoView,
)

app_name = 'contabilidad'

urlpatterns = [
    path('', ListadoCobrosView.as_view(), name='cobros'),
    path('generar/', GenerarCobrosView.as_view(), name='generar'),
    path('cobro/<int:pk>/pago/', RegistrarPagoView.as_view(), name='registrar_pago'),
    path('pago/<int:pk>/comprobante.pdf', ComprobantePagoPDFView.as_view(), name='comprobante_pdf'),
]
