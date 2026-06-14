"""Comprobante de pago en PDF."""
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer

from apps.core.pdf import ESTILO_NORMAL, construir_pdf, tabla_datos


def comprobante_pago_pdf(pago):
    cobro = pago.cobro
    alumno = cobro.matricula.alumno
    filas = [
        ['Concepto', 'Detalle'],
        ['N° de comprobante', f'{pago.pk:06d}'],
        ['Alumno(a)', f'{alumno.usuario.get_full_name()} (RUT {alumno.rut_alumno})'],
        ['Curso', str(cobro.matricula.curso)],
        ['Arancel', f'{cobro.tipo_arancel.nombre} — período {cobro.periodo}'],
        ['Monto del cobro', f'${cobro.monto:,.0f}'],
        ['Monto pagado', f'${pago.monto_pagado:,.0f}'],
        ['Saldo pendiente', f'${cobro.saldo_pendiente:,.0f}'],
        ['Fecha de pago', pago.fecha_pago.strftime('%d-%m-%Y')],
        ['Medio de pago', pago.get_medio_pago_display()],
        ['Estado del cobro', cobro.get_estado_display()],
        ['Recibido por', pago.registrado_por.get_full_name()],
    ]
    elementos = [
        tabla_datos(filas, anchos=[5 * cm, 11 * cm], fuente=10),
        Spacer(1, 0.4 * cm),
    ]
    if pago.observacion:
        elementos.append(Paragraph(f'Observación: {pago.observacion}', ESTILO_NORMAL))
    subtitulo = f'Comprobante de pago N° {pago.pk:06d}'
    return construir_pdf('Comprobante de Pago', subtitulo, elementos)
