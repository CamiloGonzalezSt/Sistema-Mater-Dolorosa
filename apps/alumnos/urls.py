from django.urls import path

from .views import PupilosAnotacionesView, PupilosCitacionesView, PupilosNotasView

app_name = 'alumnos'

urlpatterns = [
    path('citaciones/', PupilosCitacionesView.as_view(), name='pupilos_citaciones'),
    path('anotaciones/', PupilosAnotacionesView.as_view(), name='pupilos_anotaciones'),
    path('notas/', PupilosNotasView.as_view(), name='pupilos_notas'),
]
