from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Anotacion, Citacion


@admin.register(Anotacion)
class AnotacionAdmin(SimpleHistoryAdmin):
    list_display = ('matricula', 'tipo', 'fecha', 'registrado_por', 'toma_conocimiento')
    list_filter = ('tipo', 'toma_conocimiento', 'matricula__anio_escolar', 'fecha')
    search_fields = (
        'matricula__alumno__rut_alumno',
        'matricula__alumno__usuario__first_name',
        'matricula__alumno__usuario__last_name',
        'descripcion',
    )
    autocomplete_fields = ('matricula', 'registrado_por')
    list_select_related = ('matricula__alumno__usuario', 'registrado_por')
    date_hierarchy = 'fecha'
    history_list_display = ('tipo', 'toma_conocimiento')


@admin.register(Citacion)
class CitacionAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'apoderado', 'fecha_hora', 'estado', 'registrado_por')
    list_filter = ('estado', 'matricula__anio_escolar')
    search_fields = (
        'matricula__alumno__rut_alumno',
        'matricula__alumno__usuario__first_name',
        'matricula__alumno__usuario__last_name',
        'apoderado__usuario__first_name',
        'apoderado__usuario__last_name',
        'motivo',
    )
    autocomplete_fields = ('matricula', 'apoderado', 'registrado_por')
    list_select_related = ('matricula__alumno__usuario', 'apoderado__usuario', 'registrado_por')
    date_hierarchy = 'fecha_hora'
