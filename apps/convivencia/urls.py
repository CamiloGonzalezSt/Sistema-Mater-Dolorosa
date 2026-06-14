from django.urls import path

from .views import (
    CerrarCitacionView,
    CrearAnotacionView,
    CrearCitacionView,
    HojaVidaView,
    SeleccionAlumnoView,
)

app_name = 'convivencia'

urlpatterns = [
    path('', SeleccionAlumnoView.as_view(), name='seleccionar'),
    path('alumno/<int:pk>/', HojaVidaView.as_view(), name='hoja_vida'),
    path('alumno/<int:pk>/anotacion/', CrearAnotacionView.as_view(), name='anotar'),
    path('alumno/<int:pk>/citacion/', CrearCitacionView.as_view(), name='citar'),
    path('citacion/<int:pk>/cerrar/', CerrarCitacionView.as_view(), name='cerrar_citacion'),
]
