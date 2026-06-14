from django import forms
from django.conf import settings
from django.core.mail import send_mail

from .models import Postulacion


class PostulacionForm(forms.ModelForm):
    class Meta:
        model = Postulacion
        fields = [
            'nombre_postulante', 'fecha_nacimiento', 'nivel',
            'nombre_apoderado', 'email', 'telefono', 'mensaje',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'mensaje': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Cuéntanos sobre el postulante o tus consultas (opcional)',
            }),
        }


class ContactoForm(forms.Form):
    nombre = forms.CharField(
        label='Nombre completo',
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Tu nombre'}),
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'tucorreo@ejemplo.cl'}),
    )
    telefono = forms.CharField(
        label='Teléfono (opcional)',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '+56 9 1234 5678'}),
    )
    mensaje = forms.CharField(
        label='Mensaje',
        max_length=2000,
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': '¿En qué podemos ayudarte?'}),
    )

    def enviar(self):
        datos = self.cleaned_data
        cuerpo = (
            f"Nuevo mensaje desde el formulario de contacto:\n\n"
            f"Nombre: {datos['nombre']}\n"
            f"Email: {datos['email']}\n"
            f"Teléfono: {datos['telefono'] or 'No indicado'}\n\n"
            f"Mensaje:\n{datos['mensaje']}\n"
        )
        send_mail(
            subject=f"[Contacto Web] Mensaje de {datos['nombre']}",
            message=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
        )
