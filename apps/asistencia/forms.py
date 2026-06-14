from datetime import date

from django import forms

from apps.academico.models import CursoAsignatura

from .models import RegistroAsistencia


class SeleccionAsistenciaForm(forms.Form):
    curso_asignatura = forms.ModelChoiceField(
        label='Asignatura',
        queryset=CursoAsignatura.objects.none(),  # la vista lo filtra por usuario
        empty_label='— Selecciona una asignatura —',
    )
    fecha = forms.DateField(
        label='Fecha',
        initial=date.today,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )


class RegistroAsistenciaForm(forms.ModelForm):
    """Una fila del libro de asistencia. La vista fija matricula, curso_asignatura,
    fecha y registrado_por en la instancia; is_valid() ejecuta el clean() del modelo."""

    # Orden de presentación en pantalla (solo UI, no altera el modelo)
    ORDEN_ESTADOS = [
        RegistroAsistencia.Estado.PRESENTE,
        RegistroAsistencia.Estado.AUSENTE,
        RegistroAsistencia.Estado.ATRASADO,
        RegistroAsistencia.Estado.JUSTIFICADO,
    ]

    class Meta:
        model = RegistroAsistencia
        fields = ['estado', 'observacion']
        widgets = {
            'estado': forms.RadioSelect,
            'observacion': forms.TextInput(
                attrs={'placeholder': 'Observación (opcional)', 'class': 'input-obs'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estado'].choices = [
            (estado.value, estado.label) for estado in self.ORDEN_ESTADOS
        ]
