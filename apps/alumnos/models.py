from django.conf import settings
from django.db import models

from apps.academico.models import Curso
from apps.accounts.validators import validar_rut_chileno


class PerfilAlumno(models.Model):
    """Datos personales fijos del alumno. Su trayectoria por cursos vive en Matricula."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_alumno',
        verbose_name='usuario',
        limit_choices_to={'role': 'alumno'},
    )
    rut_alumno = models.CharField(
        'RUT del alumno',
        max_length=12,
        unique=True,
        validators=[validar_rut_chileno],
    )
    fecha_nacimiento = models.DateField('fecha de nacimiento')
    direccion = models.CharField('dirección', max_length=255)
    comuna = models.CharField('comuna', max_length=100)

    class Meta:
        verbose_name = 'perfil de alumno'
        verbose_name_plural = 'perfiles de alumnos'
        ordering = ['usuario__last_name', 'usuario__first_name']

    def __str__(self):
        return self.usuario.get_full_name() or self.rut_alumno


class Matricula(models.Model):
    """Inscripción de un alumno en un curso para un año escolar.
    El historial académico completo del alumno es su conjunto de matrículas."""

    class Estado(models.TextChoices):
        REGULAR = 'regular', 'Regular'
        REPITENTE = 'repitente', 'Repitente'
        RETIRADO = 'retirado', 'Retirado'
        EGRESADO = 'egresado', 'Egresado'

    alumno = models.ForeignKey(
        PerfilAlumno,
        on_delete=models.CASCADE,
        related_name='matriculas',
        verbose_name='alumno',
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.PROTECT,
        related_name='matriculas',
        verbose_name='curso',
    )
    # Denormalizado desde curso.anio_escolar para poder garantizar a nivel de BD
    # una sola matrícula por alumno y año (MySQL no soporta constraints condicionales
    # ni que crucen tablas). Se autocompleta en save().
    anio_escolar = models.PositiveSmallIntegerField('año escolar', editable=False)
    estado = models.CharField(
        'estado', max_length=10, choices=Estado.choices, default=Estado.REGULAR
    )
    fecha_matricula = models.DateField('fecha de matrícula')

    class Meta:
        verbose_name = 'matrícula'
        verbose_name_plural = 'matrículas'
        ordering = ['-anio_escolar', 'alumno__usuario__last_name']
        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'anio_escolar'],
                name='unique_matricula_alumno_anio',
            ),
        ]

    def save(self, *args, **kwargs):
        self.anio_escolar = self.curso.anio_escolar
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.alumno} — {self.curso} [{self.get_estado_display()}]'


class PerfilApoderado(models.Model):
    class Relacion(models.TextChoices):
        PADRE = 'padre', 'Padre'
        MADRE = 'madre', 'Madre'
        TUTOR = 'tutor', 'Tutor(a)'

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_apoderado',
        verbose_name='usuario',
        limit_choices_to={'role': 'apoderado'},
    )
    relacion = models.CharField(
        'relación con el alumno', max_length=50, choices=Relacion.choices
    )

    class Meta:
        verbose_name = 'perfil de apoderado'
        verbose_name_plural = 'perfiles de apoderados'
        ordering = ['usuario__last_name', 'usuario__first_name']

    def __str__(self):
        return f'{self.usuario.get_full_name()} ({self.get_relacion_display()})'


class AlumnoApoderado(models.Model):
    """Vínculo N:M entre alumnos y apoderados."""

    alumno = models.ForeignKey(
        PerfilAlumno,
        on_delete=models.CASCADE,
        related_name='vinculos_apoderados',
        verbose_name='alumno',
    )
    apoderado = models.ForeignKey(
        PerfilApoderado,
        on_delete=models.CASCADE,
        related_name='vinculos_alumnos',
        verbose_name='apoderado',
    )
    es_principal = models.BooleanField('es apoderado principal', default=False)

    class Meta:
        verbose_name = 'vínculo alumno-apoderado'
        verbose_name_plural = 'vínculos alumno-apoderado'
        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'apoderado'],
                name='unique_alumno_apoderado',
            ),
        ]

    def __str__(self):
        principal = ' [principal]' if self.es_principal else ''
        return f'{self.apoderado} → {self.alumno}{principal}'
