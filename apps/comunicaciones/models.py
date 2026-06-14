from django.conf import settings
from django.db import models

from apps.alumnos.models import PerfilAlumno


class Mensaje(models.Model):
    """Mensaje de un alumno o apoderado hacia un profesor.
    Las solicitudes de citación son mensajes tipados: el profesor las lee en su
    bandeja y crea la Citacion formal desde convivencia."""

    class Tipo(models.TextChoices):
        MENSAJE = 'mensaje', 'Mensaje'
        SOLICITUD_CITACION = 'solicitud_citacion', 'Solicitud de citación'

    remitente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mensajes_enviados',
        verbose_name='remitente',
    )
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='mensajes_recibidos',
        verbose_name='profesor destinatario',
        limit_choices_to={'role': 'profesor'},
    )
    pupilo = models.ForeignKey(
        PerfilAlumno,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='mensajes',
        verbose_name='alumno relacionado',
        help_text='El apoderado indica por cuál pupilo escribe.',
    )
    tipo = models.CharField(
        'tipo', max_length=20, choices=Tipo.choices, default=Tipo.MENSAJE
    )
    asunto = models.CharField('asunto', max_length=150)
    cuerpo = models.TextField('mensaje')
    enviado_el = models.DateTimeField('enviado el', auto_now_add=True)
    leido = models.BooleanField('leído', default=False)

    class Meta:
        verbose_name = 'mensaje'
        verbose_name_plural = 'mensajes'
        ordering = ['-enviado_el']
        indexes = [models.Index(fields=['destinatario', 'leido'])]

    def __str__(self):
        return f'{self.get_tipo_display()}: {self.asunto} ({self.remitente} → {self.destinatario})'
