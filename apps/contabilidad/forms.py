from django import forms

from apps.academico.models import Curso

from .models import Cobro, Pago, TipoArancel


class GeneracionCobrosForm(forms.Form):
    """Generación masiva: un cobro por cada matrícula vigente del alcance."""

    tipo_arancel = forms.ModelChoiceField(
        label='Tipo de arancel', queryset=TipoArancel.objects.all()
    )
    periodo = forms.CharField(
        label='Período', max_length=20,
        help_text='Ej: "2026-03". Se omiten matrículas que ya tienen este cobro.',
    )
    monto = forms.DecimalField(
        label='Monto', max_digits=10, decimal_places=2, required=False,
        help_text='Vacío = usar el monto base del arancel.',
    )
    fecha_vencimiento = forms.DateField(
        label='Fecha de vencimiento',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    curso = forms.ModelChoiceField(
        label='Curso (opcional)', queryset=Curso.objects.select_related('nivel'),
        required=False, empty_label='— Todo el colegio —',
    )


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['monto_pagado', 'fecha_pago', 'medio_pago', 'comprobante', 'observacion']
        widgets = {
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'observacion': forms.Textarea(attrs={'rows': 2}),
        }


class CondonarForm(forms.Form):
    """Confirmación simple para condonar un cobro."""
    confirmar = forms.BooleanField(label='Confirmo la condonación de este cobro')
