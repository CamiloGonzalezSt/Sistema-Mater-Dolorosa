from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Cobro, Pago, TipoArancel


@admin.register(TipoArancel)
class TipoArancelAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'monto_base')
    search_fields = ('nombre',)


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    autocomplete_fields = ('registrado_por',)


@admin.register(Cobro)
class CobroAdmin(admin.ModelAdmin):
    list_display = (
        'matricula', 'tipo_arancel', 'periodo', 'monto',
        'saldo', 'estado', 'fecha_vencimiento',
    )
    list_filter = ('estado', 'tipo_arancel', 'periodo', 'matricula__anio_escolar')
    search_fields = (
        'matricula__alumno__rut_alumno',
        'matricula__alumno__usuario__first_name',
        'matricula__alumno__usuario__last_name',
        'periodo',
    )
    autocomplete_fields = ('matricula', 'tipo_arancel')
    list_select_related = ('matricula__alumno__usuario', 'tipo_arancel')
    inlines = [PagoInline]

    @admin.display(description='saldo')
    def saldo(self, obj):
        return f'${obj.saldo_pendiente:,.0f}'


@admin.register(Pago)
class PagoAdmin(SimpleHistoryAdmin):
    list_display = ('cobro', 'monto_pagado', 'fecha_pago', 'medio_pago', 'registrado_por')
    list_filter = ('medio_pago', 'fecha_pago')
    search_fields = (
        'cobro__matricula__alumno__rut_alumno',
        'cobro__matricula__alumno__usuario__first_name',
        'cobro__matricula__alumno__usuario__last_name',
        'cobro__periodo',
    )
    autocomplete_fields = ('cobro', 'registrado_por')
    list_select_related = ('cobro__matricula__alumno__usuario', 'registrado_por')
    date_hierarchy = 'fecha_pago'
    history_list_display = ('monto_pagado', 'medio_pago')
