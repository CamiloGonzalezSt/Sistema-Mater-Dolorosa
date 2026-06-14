from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords

from apps.academico.models import CursoAsignatura
from apps.alumnos.models import Matricula


class PeriodoEvaluacion(models.Model):
    """Período lectivo de evaluación: '1° Semestre 2026', etc."""

    nombre = models.CharField('nombre', max_length=50)
    anio_escolar = models.PositiveSmallIntegerField('año escolar')
    fecha_inicio = models.DateField('fecha de inicio')
    fecha_fin = models.DateField('fecha de término')

    class Meta:
        verbose_name = 'período de evaluación'
        verbose_name_plural = 'períodos de evaluación'
        ordering = ['-anio_escolar', 'fecha_inicio']
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'anio_escolar'],
                name='unique_periodo_nombre_anio',
            ),
        ]

    def clean(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio >= self.fecha_fin:
            raise ValidationError('La fecha de inicio debe ser anterior a la de término.')

    def __str__(self):
        return f'{self.nombre} {self.anio_escolar}'


class TipoEvaluacion(models.Model):
    """Tipo de instrumento y su ponderación: 'Prueba' 40%, 'Trabajo' 20%, etc."""

    nombre = models.CharField('nombre', max_length=50, unique=True)
    ponderacion_porcentaje = models.DecimalField(
        'ponderación (%)',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
    )

    class Meta:
        verbose_name = 'tipo de evaluación'
        verbose_name_plural = 'tipos de evaluación'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.ponderacion_porcentaje}%)'


class Evaluacion(models.Model):
    """Una evaluación concreta aplicada en una clase: 'Prueba N°1 Fracciones'."""

    curso_asignatura = models.ForeignKey(
        CursoAsignatura,
        on_delete=models.PROTECT,
        related_name='evaluaciones',
        verbose_name='asignatura de curso',
    )
    periodo = models.ForeignKey(
        PeriodoEvaluacion,
        on_delete=models.PROTECT,
        related_name='evaluaciones',
        verbose_name='período',
    )
    tipo = models.ForeignKey(
        TipoEvaluacion,
        on_delete=models.PROTECT,
        related_name='evaluaciones',
        verbose_name='tipo',
    )
    nombre = models.CharField('nombre', max_length=150)
    fecha = models.DateField('fecha')
    puntaje_maximo = models.DecimalField('puntaje máximo', max_digits=6, decimal_places=2)

    class Meta:
        verbose_name = 'evaluación'
        verbose_name_plural = 'evaluaciones'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.nombre} — {self.curso_asignatura}'


class Calificacion(models.Model):
    """Nota de un alumno (vía su matrícula) en una evaluación. Auditada con historial."""

    evaluacion = models.ForeignKey(
        Evaluacion,
        on_delete=models.PROTECT,
        related_name='calificaciones',
        verbose_name='evaluación',
    )
    matricula = models.ForeignKey(
        Matricula,
        on_delete=models.PROTECT,
        related_name='calificaciones',
        verbose_name='matrícula',
    )
    puntaje_obtenido = models.DecimalField('puntaje obtenido', max_digits=6, decimal_places=2)
    nota = models.DecimalField(
        'nota',
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.0')), MaxValueValidator(Decimal('7.0'))],
    )
    observacion = models.TextField('observación', blank=True)
    fecha_registro = models.DateTimeField('fecha de registro', auto_now_add=True)

    history = HistoricalRecords(verbose_name='historial de calificación')

    class Meta:
        verbose_name = 'calificación'
        verbose_name_plural = 'calificaciones'
        ordering = ['-fecha_registro']
        constraints = [
            models.UniqueConstraint(
                fields=['evaluacion', 'matricula'],
                name='unique_calificacion_evaluacion_matricula',
            ),
        ]
        indexes = [
            models.Index(fields=['matricula', 'evaluacion']),
        ]

    def clean(self):
        if self.matricula_id and self.evaluacion_id:
            if self.matricula.curso_id != self.evaluacion.curso_asignatura.curso_id:
                raise ValidationError(
                    'La matrícula del alumno y la evaluación pertenecen a cursos distintos.'
                )
        if self.puntaje_obtenido is not None and self.evaluacion_id:
            if self.puntaje_obtenido > self.evaluacion.puntaje_maximo:
                raise ValidationError(
                    'El puntaje obtenido no puede superar el puntaje máximo de la evaluación.'
                )

    def __str__(self):
        return f'{self.matricula.alumno} — {self.evaluacion.nombre}: {self.nota}'
