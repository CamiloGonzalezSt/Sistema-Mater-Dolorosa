from django.contrib import admin

from .models import PerfilProfesor


@admin.register(PerfilProfesor)
class PerfilProfesorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'titulo')
    list_filter = ('especialidad',)
    search_fields = (
        'usuario__first_name',
        'usuario__last_name',
        'usuario__rut',
        'usuario__email',
        'especialidad',
    )
    autocomplete_fields = ('usuario',)
    list_select_related = ('usuario',)
