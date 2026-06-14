from django.contrib import admin

from .models import (
    Asignatura, Curso, CursoAsignatura, MaterialAcademico, NivelEducacional,
)


@admin.register(MaterialAcademico)
class MaterialAcademicoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso_asignatura', 'periodo', 'unidad', 'subido_por', 'creado_el')
    list_filter = ('periodo', 'curso_asignatura__asignatura')
    search_fields = ('titulo', 'unidad', 'curso_asignatura__asignatura__nombre')
    autocomplete_fields = ('curso_asignatura', 'periodo', 'subido_por')
    list_select_related = ('curso_asignatura__asignatura', 'curso_asignatura__curso__nivel', 'periodo', 'subido_por')


@admin.register(NivelEducacional)
class NivelEducacionalAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


class CursoAsignaturaInline(admin.TabularInline):
    model = CursoAsignatura
    extra = 0
    autocomplete_fields = ('asignatura', 'profesor')


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'nivel', 'letra', 'anio_escolar', 'capacidad', 'profesor_jefe')
    list_filter = ('anio_escolar', 'nivel')
    search_fields = ('nivel__nombre', 'letra')
    autocomplete_fields = ('profesor_jefe',)
    list_select_related = ('nivel', 'profesor_jefe__usuario')
    inlines = [CursoAsignaturaInline]


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'horas_semanales')
    search_fields = ('nombre', 'codigo')


@admin.register(CursoAsignatura)
class CursoAsignaturaAdmin(admin.ModelAdmin):
    list_display = ('asignatura', 'curso', 'profesor', 'anio_escolar')
    list_filter = ('anio_escolar', 'asignatura')
    search_fields = (
        'asignatura__nombre',
        'profesor__first_name',
        'profesor__last_name',
        'profesor__rut',
    )
    autocomplete_fields = ('curso', 'asignatura', 'profesor')
    list_select_related = ('asignatura', 'curso__nivel', 'profesor')
