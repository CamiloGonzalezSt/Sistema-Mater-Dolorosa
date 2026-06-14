from django import forms

from .models import Anotacion, Citacion


class AnotacionForm(forms.ModelForm):
    class Meta:
        model = Anotacion
        fields = ['tipo', 'fecha', 'descripcion', 'toma_conocimiento']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }


class CitacionForm(forms.ModelForm):
    """Alta de citación. La vista limita el queryset de apoderado a los del alumno."""

    class Meta:
        model = Citacion
        fields = ['apoderado', 'fecha_hora', 'motivo']
        widgets = {
            'fecha_hora': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'motivo': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_hora'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M']


class CitacionResultadoForm(forms.ModelForm):
    """Cierre de la citación: estado final y acuerdos alcanzados."""

    class Meta:
        model = Citacion
        fields = ['estado', 'acuerdos']
        widgets = {'acuerdos': forms.Textarea(attrs={'rows': 4})}
