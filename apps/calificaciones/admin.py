from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Calificacion, Evaluacion, PeriodoEvaluacion, TipoEvaluacion


@admin.register(PeriodoEvaluacion)
class PeriodoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'anio_escolar', 'fecha_inicio', 'fecha_fin')
    list_filter = ('anio_escolar',)
    search_fields = ('nombre',)


@admin.register(TipoEvaluacion)
class TipoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ponderacion_porcentaje')
    search_fields = ('nombre',)


class CalificacionInline(admin.TabularInline):
    model = Calificacion
    extra = 0
    autocomplete_fields = ('matricula',)


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'curso_asignatura', 'periodo', 'tipo', 'fecha', 'puntaje_maximo')
    list_filter = ('periodo__anio_escolar', 'periodo', 'tipo')
    search_fields = ('nombre', 'curso_asignatura__asignatura__nombre')
    autocomplete_fields = ('curso_asignatura', 'periodo', 'tipo')
    list_select_related = ('curso_asignatura__asignatura', 'curso_asignatura__curso__nivel', 'periodo', 'tipo')
    date_hierarchy = 'fecha'
    inlines = [CalificacionInline]


@admin.register(Calificacion)
class CalificacionAdmin(SimpleHistoryAdmin):
    list_display = ('matricula', 'evaluacion', 'nota', 'puntaje_obtenido', 'fecha_registro')
    list_filter = ('evaluacion__periodo__anio_escolar', 'evaluacion__periodo', 'evaluacion__tipo')
    search_fields = (
        'matricula__alumno__rut_alumno',
        'matricula__alumno__usuario__first_name',
        'matricula__alumno__usuario__last_name',
        'evaluacion__nombre',
    )
    autocomplete_fields = ('evaluacion', 'matricula')
    list_select_related = ('matricula__alumno__usuario', 'evaluacion')
    history_list_display = ('nota', 'puntaje_obtenido')
