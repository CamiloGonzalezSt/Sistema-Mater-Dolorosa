from django.contrib import admin

from .models import Mensaje


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('asunto', 'tipo', 'remitente', 'destinatario', 'pupilo', 'enviado_el', 'leido')
    list_filter = ('tipo', 'leido', 'enviado_el')
    search_fields = (
        'asunto', 'cuerpo',
        'remitente__first_name', 'remitente__last_name', 'remitente__email',
        'destinatario__first_name', 'destinatario__last_name',
    )
    autocomplete_fields = ('remitente', 'destinatario', 'pupilo')
    list_select_related = ('remitente', 'destinatario', 'pupilo__usuario')
    date_hierarchy = 'enviado_el'
