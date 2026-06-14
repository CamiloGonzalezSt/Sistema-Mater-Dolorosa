from django import forms

from .models import Mensaje


class MensajeAlumnoForm(forms.ModelForm):
    """Alumno → profesor. La vista limita los destinatarios a sus profesores."""

    class Meta:
        model = Mensaje
        fields = ['destinatario', 'asunto', 'cuerpo']
        widgets = {'cuerpo': forms.Textarea(attrs={'rows': 5})}


class MensajeApoderadoForm(forms.ModelForm):
    """Apoderado → profesor: mensaje o solicitud de citación, indicando el pupilo."""

    class Meta:
        model = Mensaje
        fields = ['pupilo', 'destinatario', 'tipo', 'asunto', 'cuerpo']
        widgets = {'cuerpo': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pupilo'].required = True
