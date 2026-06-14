from django.contrib import admin

from .models import (
    EquipoConvivencia, EventoCalendario, ItemGaleria, Noticia, Postulacion,
)


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha', 'publicada')
    list_filter = ('publicada', 'fecha')
    search_fields = ('titulo', 'bajada', 'cuerpo')
    date_hierarchy = 'fecha'


@admin.register(EventoCalendario)
class EventoCalendarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha', 'hora', 'lugar')
    list_filter = ('fecha',)
    search_fields = ('titulo', 'descripcion', 'lugar')
    date_hierarchy = 'fecha'


@admin.register(ItemGaleria)
class ItemGaleriaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'anio', 'es_video', 'creado_el')
    list_filter = ('anio',)
    search_fields = ('titulo',)

    @admin.display(boolean=True, description='video')
    def es_video(self, obj):
        return obj.es_video


@admin.register(EquipoConvivencia)
class EquipoConvivenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cargo', 'orden')
    search_fields = ('nombre', 'cargo')
    ordering = ('orden', 'nombre')


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display = ('nombre_postulante', 'nivel', 'nombre_apoderado', 'email', 'estado', 'creado_el')
    list_filter = ('estado', 'nivel')
    search_fields = ('nombre_postulante', 'nombre_apoderado', 'email')
    date_hierarchy = 'creado_el'
