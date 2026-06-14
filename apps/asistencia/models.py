from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.academico.models import CursoAsignatura
from apps.alumnos.models import Matricula


class RegistroAsistencia(models.Model):
    """Asistencia de un alumno (vía su matrícula) a una clase concreta en una fecha."""

    class Estado(models.TextChoices):
        PRESENTE = 'presente', 'Presente'
        AUSENTE = 'ausente', 'Ausente'
        JUSTIFICADO = 'justificado', 'Justificado'
        ATRASADO = 'atrasado', 'Atrasado'

    matricula = models.ForeignKey(
        Matricula,
        on_delete=models.PROTECT,
        related_name='asistencias',
        verbose_name='matrícula',
    )
    curso_asignatura = models.ForeignKey(
        CursoAsignatura,
        on_delete=models.PROTECT,
        related_name='asistencias',
        verbose_name='asignatura de curso',
    )
    fecha = models.DateField('fecha')
    estado = models.CharField('estado', max_length=12, choices=Estado.choices)
    observacion = models.TextField('observación', blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='asistencias_registradas',
        verbose_name='registrado por',
    )

    class Meta:
        verbose_name = 'registro de asistencia'
        verbose_name_plural = 'registros de asistencia'
        ordering = ['-fecha', 'matricula__alumno__usuario__last_name']
        constraints = [
            models.UniqueConstraint(
                fields=['matricula', 'curso_asignatura', 'fecha'],
                name='unique_asistencia_matricula_clase_fecha',
            ),
        ]
        indexes = [
            models.Index(fields=['matricula', 'fecha']),
            models.Index(fields=['curso_asignatura', 'fecha']),
        ]

    def clean(self):
        if self.matricula_id and self.curso_asignatura_id:
            if self.matricula.curso_id != self.curso_asignatura.curso_id:
                raise ValidationError(
                    'La matrícula del alumno y la asignatura pertenecen a cursos distintos.'
                )

    def __str__(self):
        return f'{self.matricula.alumno} — {self.fecha} — {self.get_estado_display()}'
