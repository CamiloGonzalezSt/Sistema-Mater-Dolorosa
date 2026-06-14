from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from apps.alumnos.models import AlumnoApoderado, Matricula, PerfilApoderado


class Anotacion(models.Model):
    """Anotación de la hoja de vida del alumno, anclada a su matrícula (año escolar).
    Documento con valor legal: se audita con historial completo."""

    class Tipo(models.TextChoices):
        POSITIVA = 'positiva', 'Positiva'
        NEGATIVA = 'negativa', 'Negativa'
        OBSERVACION = 'observacion', 'Observación'

    matricula = models.ForeignKey(
        Matricula,
        on_delete=models.PROTECT,
        related_name='anotaciones',
        verbose_name='matrícula',
    )
    tipo = models.CharField('tipo', max_length=12, choices=Tipo.choices)
    descripcion = models.TextField('descripción')
    fecha = models.DateField('fecha', default=timezone.localdate)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='anotaciones_registradas',
        verbose_name='registrado por',
    )
    toma_conocimiento = models.BooleanField(
        'apoderado tomó conocimiento', default=False
    )

    history = HistoricalRecords(verbose_name='historial de anotación')

    class Meta:
        verbose_name = 'anotación'
        verbose_name_plural = 'anotaciones'
        ordering = ['-fecha', '-id']
        indexes = [models.Index(fields=['matricula', 'fecha'])]

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.matricula.alumno} ({self.fecha})'


class Citacion(models.Model):
    """Citación de un apoderado por motivos académicos o de convivencia."""

    class Estado(models.TextChoices):
        PROGRAMADA = 'programada', 'Programada'
        REALIZADA = 'realizada', 'Realizada'
        AUSENTE = 'ausente', 'Apoderado ausente'

    matricula = models.ForeignKey(
        Matricula,
        on_delete=models.PROTECT,
        related_name='citaciones',
        verbose_name='matrícula',
    )
    apoderado = models.ForeignKey(
        PerfilApoderado,
        on_delete=models.PROTECT,
        related_name='citaciones',
        verbose_name='apoderado citado',
    )
    fecha_hora = models.DateTimeField('fecha y hora')
    motivo = models.TextField('motivo')
    estado = models.CharField(
        'estado', max_length=10, choices=Estado.choices, default=Estado.PROGRAMADA
    )
    acuerdos = models.TextField(
        'acuerdos', blank=True,
        help_text='Se completa al realizar la reunión.',
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='citaciones_registradas',
        verbose_name='registrado por',
    )

    class Meta:
        verbose_name = 'citación'
        verbose_name_plural = 'citaciones'
        ordering = ['-fecha_hora']
        indexes = [models.Index(fields=['matricula', 'fecha_hora'])]

    def clean(self):
        if self.matricula_id and self.apoderado_id:
            vinculado = AlumnoApoderado.objects.filter(
                alumno_id=self.matricula.alumno_id, apoderado_id=self.apoderado_id
            ).exists()
            if not vinculado:
                raise ValidationError(
                    'El apoderado citado no está vinculado a este alumno.'
                )

    def __str__(self):
        return f'Citación {self.get_estado_display().lower()} — {self.matricula.alumno} ({self.fecha_hora:%d-%m-%Y %H:%M})'
