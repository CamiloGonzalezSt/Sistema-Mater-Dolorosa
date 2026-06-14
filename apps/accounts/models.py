from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validar_rut_chileno


class CustomUser(AbstractUser):
    """Usuario del sistema con rol RBAC: admin, profesor, alumno o apoderado."""

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        PROFESOR = 'profesor', 'Profesor'
        ALUMNO = 'alumno', 'Alumno'
        APODERADO = 'apoderado', 'Apoderado'

    email = models.EmailField('correo electrónico', unique=True)
    rut = models.CharField(
        'RUT', max_length=12, unique=True, validators=[validar_rut_chileno]
    )
    phone = models.CharField('teléfono', max_length=20, blank=True)
    role = models.CharField('rol', max_length=10, choices=Role.choices)
    foto = models.ImageField(
        'foto de perfil', upload_to='usuarios/fotos/', null=True, blank=True
    )

    # Login por email; username se mantiene como identificador interno
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'rut', 'role']

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'
