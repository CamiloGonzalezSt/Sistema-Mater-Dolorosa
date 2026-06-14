from django.conf import settings
from django.db import models


class PerfilProfesor(models.Model):
    """Datos profesionales fijos. Las jefaturas anuales viven en Curso.profesor_jefe
    (accesibles como perfil.jefaturas)."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_profesor',
        verbose_name='usuario',
        limit_choices_to={'role': 'profesor'},
    )
    especialidad = models.CharField('especialidad', max_length=100)
    titulo = models.CharField('título profesional', max_length=200)

    class Meta:
        verbose_name = 'perfil de profesor'
        verbose_name_plural = 'perfiles de profesores'
        ordering = ['usuario__last_name', 'usuario__first_name']

    def __str__(self):
        return f'{self.usuario.get_full_name()} — {self.especialidad}'
