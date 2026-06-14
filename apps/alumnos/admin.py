from django.contrib import admin

from .models import AlumnoApoderado, Matricula, PerfilAlumno, PerfilApoderado


class AlumnoApoderadoInline(admin.TabularInline):
    model = AlumnoApoderado
    extra = 0
    autocomplete_fields = ('apoderado',)


class MatriculaInline(admin.TabularInline):
    model = Matricula
    extra = 0
    autocomplete_fields = ('curso',)
    ordering = ('-anio_escolar',)


@admin.register(PerfilAlumno)
class PerfilAlumnoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'rut_alumno', 'curso_actual', 'comuna')
    list_filter = ('comuna', 'matriculas__curso__anio_escolar')
    search_fields = (
        'rut_alumno',
        'usuario__first_name',
        'usuario__last_name',
        'usuario__email',
    )
    autocomplete_fields = ('usuario',)
    list_select_related = ('usuario',)
    inlines = [MatriculaInline, AlumnoApoderadoInline]

    @admin.display(description='matrícula vigente')
    def curso_actual(self, obj):
        matricula = obj.matriculas.order_by('-anio_escolar').first()
        return matricula.curso if matricula else '—'


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'curso', 'anio_escolar', 'estado', 'fecha_matricula')
    list_filter = ('anio_escolar', 'estado', 'curso__nivel')
    search_fields = (
        'alumno__rut_alumno',
        'alumno__usuario__first_name',
        'alumno__usuario__last_name',
    )
    autocomplete_fields = ('alumno', 'curso')
    list_select_related = ('alumno__usuario', 'curso__nivel')


@admin.register(PerfilApoderado)
class PerfilApoderadoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'relacion')
    list_filter = ('relacion',)
    search_fields = (
        'usuario__first_name',
        'usuario__last_name',
        'usuario__rut',
        'usuario__email',
    )
    autocomplete_fields = ('usuario',)
    list_select_related = ('usuario',)
