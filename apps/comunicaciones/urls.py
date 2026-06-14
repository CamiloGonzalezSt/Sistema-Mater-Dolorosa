from django.urls import path

from .views import EnviarMensajeView, MarcarLeidoView, MensajesView

app_name = 'comunicaciones'

urlpatterns = [
    path('', MensajesView.as_view(), name='mensajes'),
    path('nuevo/', EnviarMensajeView.as_view(), name='enviar'),
    path('<int:pk>/leido/', MarcarLeidoView.as_view(), name='marcar_leido'),
]
