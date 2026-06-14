from django.urls import path

from .views import (
    AdmisionView,
    CalendarioView,
    ContactoView,
    ConvivenciaEscolarView,
    GaleriaView,
    HistoriaView,
    HomePublicaView,
    NoticiaDetalleView,
    NoticiasView,
    QuienesSomosView,
)

app_name = 'web_publica'

urlpatterns = [
    path('', HomePublicaView.as_view(), name='home'),
    path('historia/', HistoriaView.as_view(), name='historia'),
    path('quienes-somos/', QuienesSomosView.as_view(), name='quienes_somos'),
    path('noticias/', NoticiasView.as_view(), name='noticias'),
    path('noticias/<int:pk>/', NoticiaDetalleView.as_view(), name='noticia_detalle'),
    path('calendario/', CalendarioView.as_view(), name='calendario'),
    path('galeria/', GaleriaView.as_view(), name='galeria'),
    path('convivencia-escolar/', ConvivenciaEscolarView.as_view(), name='convivencia_escolar'),
    path('admision/', AdmisionView.as_view(), name='admision'),
    path('contacto/', ContactoView.as_view(), name='contacto'),
]
