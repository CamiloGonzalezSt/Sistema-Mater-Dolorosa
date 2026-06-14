from django import forms
from django.contrib.auth import get_user_model

from apps.academico.models import Curso

from .models import Calificacion, PeriodoEvaluacion


class FiltroEvaluacionesForm(forms.Form):
    """Los tres filtros son obligatorios: la tabla solo se muestra al completarlos."""

    curso = forms.ModelChoiceField(
        label='Curso', queryset=Curso.objects.select_related('nivel'),
        empty_label='— Curso —')
    profesor = forms.ModelChoiceField(
        label='Profesor',
        queryset=get_user_model().objects.filter(role='profesor').order_by('last_name'),
        empty_label='— Profesor —')
    periodo = forms.ModelChoiceField(
        label='Período', queryset=PeriodoEvaluacion.objects.all(),
        empty_label='— Período —')


class CalificacionForm(forms.ModelForm):
    """Una fila del libro de notas. La vista fija evaluacion y matricula en la
    instancia; is_valid() ejecuta el clean() del modelo (curso coherente,
    puntaje <= máximo, nota 1.0-7.0)."""

    class Meta:
        model = Calificacion
        fields = ['puntaje_obtenido', 'nota', 'observacion']
        widgets = {
            'puntaje_obtenido': forms.NumberInput(
                attrs={'step': '0.01', 'min': '0', 'class': 'input-nota'}
            ),
            'nota': forms.NumberInput(
                attrs={'step': '0.1', 'min': '1.0', 'max': '7.0', 'class': 'input-nota'}
            ),
            'observacion': forms.TextInput(
                attrs={'placeholder': 'Observación (opcional)', 'class': 'input-obs'}
            ),
        }
