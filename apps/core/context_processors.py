"""Context processors globales del panel."""
from apps.comunicaciones.models import Mensaje


def notificaciones(request):
    """Expone el número de mensajes no leídos del usuario para el navbar."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    no_leidos = Mensaje.objects.filter(destinatario=user, leido=False).count()
    return {'mensajes_no_leidos': no_leidos}
