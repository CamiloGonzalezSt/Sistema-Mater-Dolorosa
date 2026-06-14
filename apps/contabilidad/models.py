from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from apps.alumnos.models import Matricula


class TipoArancel(models.Model):
    """Concepto cobrable: 'Matrícula', 'Mensualidad', 'Taller'."""

    nombre = models.CharField('nombre', max_length=100, unique=True)
    monto_base = models.DecimalField(
        'monto base', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    descripcion = models.TextField('descripción', blank=True)

    class Meta:
        verbose_name = 'tipo de arancel'
        verbose_name_plural = 'tipos de arancel'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} (${self.monto_base:,.0f})'


class Cobro(models.Model):
    """Obligación de pago de una matrícula por un concepto y período."""

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        PAGADO = 'pagado', 'Pagado'
        VENCIDO = 'vencido', 'Vencido'
        CONDONADO = 'condonado', 'Condonado'

    matricula = models.ForeignKey(
        Matricula,
        on_delete=models.PROTECT,
        related_name='cobros',
        verbose_name='matrícula',
    )
    tipo_arancel = models.ForeignKey(
        TipoArancel,
        on_delete=models.PROTECT,
        related_name='cobros',
        verbose_name='tipo de arancel',
    )
    periodo = models.CharField(
        'período', max_length=20,
        help_text='Ej: "2026-03" para mensualidad de marzo, "2026-matricula".',
    )
    monto = models.DecimalField(
        'monto', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    fecha_vencimiento = models.DateField('fecha de vencimiento')
    estado = models.CharField(
        'estado', max_length=10, choices=Estado.choices, default=Estado.PENDIENTE
    )
    created_at = models.DateTimeField('creado el', auto_now_add=True)

    class Meta:
        verbose_name = 'cobro'
        verbose_name_plural = 'cobros'
        ordering = ['-fecha_vencimiento']
        constraints = [
            models.UniqueConstraint(
                fields=['matricula', 'tipo_arancel', 'periodo'],
                name='unique_cobro_matricula_arancel_periodo',
            ),
        ]
        indexes = [models.Index(fields=['matricula', 'estado'])]

    @property
    def total_pagado(self):
        return self.pagos.aggregate(
            total=models.Sum('monto_pagado')
        )['total'] or Decimal('0')

    @property
    def saldo_pendiente(self):
        return self.monto - self.total_pagado

    def refrescar_estado(self):
        """Recalcula el estado según pagos y vencimiento. Condonado es terminal."""
        if self.estado == self.Estado.CONDONADO:
            return
        if self.saldo_pendiente <= 0:
            nuevo = self.Estado.PAGADO
        elif self.fecha_vencimiento < timezone.localdate():
            nuevo = self.Estado.VENCIDO
        else:
            nuevo = self.Estado.PENDIENTE
        if nuevo != self.estado:
            self.estado = nuevo
            self.save(update_fields=['estado'])

    def __str__(self):
        return (
            f'{self.tipo_arancel.nombre} {self.periodo} — '
            f'{self.matricula.alumno} (${self.monto:,.0f})'
        )


class Pago(models.Model):
    """Abono (total o parcial) a un cobro. Auditado con historial completo."""

    class MedioPago(models.TextChoices):
        EFECTIVO = 'efectivo', 'Efectivo'
        TRANSFERENCIA = 'transferencia', 'Transferencia'
        CHEQUE = 'cheque', 'Cheque'
        OTRO = 'otro', 'Otro'

    cobro = models.ForeignKey(
        Cobro,
        on_delete=models.PROTECT,
        related_name='pagos',
        verbose_name='cobro',
    )
    monto_pagado = models.DecimalField(
        'monto pagado', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    fecha_pago = models.DateField('fecha de pago', default=timezone.localdate)
    medio_pago = models.CharField(
        'medio de pago', max_length=15, choices=MedioPago.choices
    )
    comprobante = models.FileField(
        'comprobante adjunto', upload_to='comprobantes/%Y/%m/', null=True, blank=True
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pagos_registrados',
        verbose_name='registrado por',
    )
    observacion = models.TextField('observación', blank=True)

    history = HistoricalRecords(verbose_name='historial de pago')

    class Meta:
        verbose_name = 'pago'
        verbose_name_plural = 'pagos'
        ordering = ['-fecha_pago', '-id']

    def clean(self):
        if self.cobro_id is None or self.monto_pagado is None:
            return
        if self.cobro.estado == Cobro.Estado.CONDONADO:
            raise ValidationError('No se pueden registrar pagos en un cobro condonado.')
        pagado_otros = self.cobro.pagos.exclude(pk=self.pk).aggregate(
            total=models.Sum('monto_pagado')
        )['total'] or Decimal('0')
        if self.monto_pagado > self.cobro.monto - pagado_otros:
            raise ValidationError(
                f'El pago excede el saldo pendiente '
                f'(${self.cobro.monto - pagado_otros:,.0f}).'
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.cobro.refrescar_estado()

    def __str__(self):
        return f'Pago ${self.monto_pagado:,.0f} — {self.cobro}'
