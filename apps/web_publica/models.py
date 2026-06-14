from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.academico.models import NivelEducacional


class Noticia(models.Model):
    titulo = models.CharField('título', max_length=200)
    bajada = models.CharField(
        'bajada', max_length=300,
        help_text='Resumen corto que se muestra en los listados.',
    )
    cuerpo = models.TextField('cuerpo')
    imagen = models.ImageField(
        'imagen', upload_to='noticias/%Y/', null=True, blank=True
    )
    publicada = models.BooleanField('publicada', default=True)
    fecha = models.DateField('fecha', default=timezone.localdate)

    class Meta:
        verbose_name = 'noticia'
        verbose_name_plural = 'noticias'
        ordering = ['-fecha', '-id']

    def __str__(self):
        return self.titulo


class EventoCalendario(models.Model):
    titulo = models.CharField('título', max_length=200)
    descripcion = models.TextField('descripción', blank=True)
    fecha = models.DateField('fecha')
    hora = models.TimeField('hora', null=True, blank=True)
    lugar = models.CharField('lugar', max_length=150, blank=True)

    class Meta:
        verbose_name = 'evento del calendario'
        verbose_name_plural = 'eventos del calendario'
        ordering = ['fecha', 'hora']

    def __str__(self):
        return f'{self.titulo} ({self.fecha:%d-%m-%Y})'


class ItemGaleria(models.Model):
    """Foto o video de la galería. Para videos, pegar la URL embebible
    (ej: https://www.youtube.com/embed/ID)."""

    titulo = models.CharField('título', max_length=150)
    anio = models.PositiveSmallIntegerField('año', default=timezone.localdate().year)
    imagen = models.ImageField('imagen', upload_to='galeria/%Y/', null=True, blank=True)
    video_url = models.URLField(
        'URL de video (embed)', blank=True,
        help_text='Ej: https://www.youtube.com/embed/XXXXXXX',
    )
    creado_el = models.DateTimeField('subido el', auto_now_add=True)

    class Meta:
        verbose_name = 'ítem de galería'
        verbose_name_plural = 'galería'
        ordering = ['-anio', '-creado_el']

    def clean(self):
        if not self.imagen and not self.video_url:
            raise ValidationError('Debes subir una imagen o indicar la URL de un video.')

    @property
    def es_video(self):
        return bool(self.video_url)

    def __str__(self):
        return f'{self.titulo} ({self.anio})'


class EquipoConvivencia(models.Model):
    """Integrante del equipo profesional de convivencia escolar
    (encargada, orientadora, psicóloga, etc.). No está asociado a un curso."""

    nombre = models.CharField('nombre', max_length=150)
    cargo = models.CharField('cargo', max_length=120)
    descripcion = models.CharField('descripción', max_length=250, blank=True)
    orden = models.PositiveSmallIntegerField(
        'orden', default=0, help_text='Menor número aparece primero.'
    )

    class Meta:
        verbose_name = 'integrante del equipo de convivencia'
        verbose_name_plural = 'equipo de convivencia'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return f'{self.nombre} — {self.cargo}'


class Postulacion(models.Model):
    """Postulación de admisión enviada desde el sitio público."""

    class Estado(models.TextChoices):
        NUEVA = 'nueva', 'Nueva'
        EN_REVISION = 'en_revision', 'En revisión'
        ACEPTADA = 'aceptada', 'Aceptada'
        RECHAZADA = 'rechazada', 'Rechazada'

    nombre_postulante = models.CharField('nombre del postulante', max_length=150)
    fecha_nacimiento = models.DateField('fecha de nacimiento')
    nivel = models.ForeignKey(
        NivelEducacional,
        on_delete=models.PROTECT,
        related_name='postulaciones',
        verbose_name='nivel al que postula',
    )
    nombre_apoderado = models.CharField('nombre del apoderado', max_length=150)
    email = models.EmailField('correo electrónico de contacto')
    telefono = models.CharField('teléfono', max_length=20)
    mensaje = models.TextField('mensaje', blank=True)
    estado = models.CharField(
        'estado', max_length=12, choices=Estado.choices, default=Estado.NUEVA
    )
    creado_el = models.DateTimeField('recibida el', auto_now_add=True)

    class Meta:
        verbose_name = 'postulación'
        verbose_name_plural = 'postulaciones'
        ordering = ['-creado_el']

    def clean(self):
        if self.fecha_nacimiento and self.fecha_nacimiento >= timezone.localdate():
            raise ValidationError('La fecha de nacimiento debe ser pasada.')

    def __str__(self):
        return f'{self.nombre_postulante} → {self.nivel} [{self.get_estado_display()}]'
