from django.conf import settings
from django.db import models


class NivelEducacional(models.Model):
    """Nivel del sistema escolar: '1° Básico' → '4° Medio'."""

    nombre = models.CharField('nombre', max_length=50, unique=True)

    class Meta:
        verbose_name = 'nivel educacional'
        verbose_name_plural = 'niveles educacionales'
        ordering = ['id']

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    """Un curso concreto de un año escolar: '3° Básico A (2026)'."""

    nivel = models.ForeignKey(
        NivelEducacional,
        on_delete=models.PROTECT,
        related_name='cursos',
        verbose_name='nivel educacional',
    )
    letra = models.CharField('letra', max_length=1)
    anio_escolar = models.PositiveSmallIntegerField('año escolar')
    capacidad = models.PositiveSmallIntegerField('capacidad', default=35)
    # FK por string para evitar import circular con apps.profesores.
    # La jefatura vive en el curso (que es anual): cada año escolar tiene su jefe.
    profesor_jefe = models.ForeignKey(
        'profesores.PerfilProfesor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jefaturas',
        verbose_name='profesor jefe',
    )

    class Meta:
        verbose_name = 'curso'
        verbose_name_plural = 'cursos'
        ordering = ['-anio_escolar', 'nivel_id', 'letra']
        constraints = [
            models.UniqueConstraint(
                fields=['nivel', 'letra', 'anio_escolar'],
                name='unique_curso_nivel_letra_anio',
            ),
        ]

    def __str__(self):
        return f'{self.nivel} {self.letra} ({self.anio_escolar})'


class Asignatura(models.Model):
    nombre = models.CharField('nombre', max_length=100)
    codigo = models.CharField('código', max_length=20, unique=True)
    horas_semanales = models.PositiveSmallIntegerField('horas semanales')

    class Meta:
        verbose_name = 'asignatura'
        verbose_name_plural = 'asignaturas'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.codigo})'


class CursoAsignatura(models.Model):
    """Asignatura impartida en un curso por un profesor en un año escolar (N:M)."""

    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='curso_asignaturas',
        verbose_name='curso',
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.PROTECT,
        related_name='curso_asignaturas',
        verbose_name='asignatura',
    )
    profesor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='asignaturas_dictadas',
        verbose_name='profesor',
        limit_choices_to={'role': 'profesor'},
    )
    anio_escolar = models.PositiveSmallIntegerField('año escolar')

    class Meta:
        verbose_name = 'asignatura de curso'
        verbose_name_plural = 'asignaturas de curso'
        ordering = ['-anio_escolar', 'curso_id', 'asignatura__nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['curso', 'asignatura', 'anio_escolar'],
                name='unique_cursoasignatura_curso_asignatura_anio',
            ),
        ]

    def __str__(self):
        return f'{self.asignatura.nombre} — {self.curso}'


class MaterialAcademico(models.Model):
    """Material de estudio que el profesor sube para los alumnos de su clase,
    organizado por período (semestre) y unidad."""

    curso_asignatura = models.ForeignKey(
        CursoAsignatura,
        on_delete=models.CASCADE,
        related_name='materiales',
        verbose_name='asignatura de curso',
    )
    periodo = models.ForeignKey(
        'calificaciones.PeriodoEvaluacion',
        on_delete=models.PROTECT,
        related_name='materiales',
        verbose_name='período',
    )
    unidad = models.CharField(
        'unidad', max_length=100, blank=True,
        help_text='Ej: "Unidad 1: Fracciones" (opcional).',
    )
    titulo = models.CharField('título', max_length=150)
    descripcion = models.TextField('descripción', blank=True)
    archivo = models.FileField('archivo', upload_to='materiales/%Y/')
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='materiales_subidos',
        verbose_name='subido por',
    )
    creado_el = models.DateTimeField('subido el', auto_now_add=True)

    class Meta:
        verbose_name = 'material académico'
        verbose_name_plural = 'materiales académicos'
        ordering = ['-creado_el']

    def __str__(self):
        return f'{self.titulo} — {self.curso_asignatura}'
