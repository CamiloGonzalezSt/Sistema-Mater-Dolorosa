from django.contrib import admin

from .models import RegistroAsistencia


@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'curso_asignatura', 'fecha', 'estado', 'registrado_por')
    list_filter = ('estado', 'fecha', 'curso_asignatura__anio_escolar')
    search_fields = (
        'matricula__alumno__rut_alumno',
        'matricula__alumno__usuario__first_name',
        'matricula__alumno__usuario__last_name',
        'curso_asignatura__asignatura__nombre',
    )
    autocomplete_fields = ('matricula', 'curso_asignatura', 'registrado_por')
    list_select_related = (
        'matricula__alumno__usuario',
        'curso_asignatura__asignatura',
        'curso_asignatura__curso__nivel',
        'registrado_por',
    )
    date_hierarchy = 'fecha'
