"""Utilidades comunes para reportes PDF institucionales (ReportLab)."""
from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

AZUL = colors.HexColor('#010D61')
AZUL_CLARO = colors.HexColor('#E8F2FE')
GRIS = colors.HexColor('#e6e9ee')

_base = getSampleStyleSheet()
ESTILO_TITULO = ParagraphStyle('TituloMD', parent=_base['Title'], textColor=AZUL, fontSize=16)
ESTILO_SUBTITULO = ParagraphStyle('SubtituloMD', parent=_base['Normal'], fontSize=10.5, leading=14)
ESTILO_SECCION = ParagraphStyle('SeccionMD', parent=_base['Heading2'], textColor=AZUL, fontSize=12)
ESTILO_PIE = ParagraphStyle('PieMD', parent=_base['Normal'], fontSize=8, textColor=colors.grey)
ESTILO_NORMAL = _base['Normal']


def construir_pdf(titulo, subtitulo, elementos, apaisado=False):
    """Arma el documento con encabezado institucional y devuelve los bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4) if apaisado else A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        title=titulo,
    )
    contenido = [
        Paragraph('Colegio Mater Dolorosa', ESTILO_TITULO),
        Paragraph(titulo, ESTILO_SECCION),
        Paragraph(subtitulo, ESTILO_SUBTITULO),
        Spacer(1, 0.5 * cm),
        *elementos,
        Spacer(1, 0.7 * cm),
        Paragraph(
            f'Documento emitido el {timezone.localtime():%d-%m-%Y %H:%M}. '
            'Uso interno — contiene datos personales protegidos (Ley 19.628).',
            ESTILO_PIE,
        ),
    ]
    doc.build(contenido)
    return buffer.getvalue()


def tabla_datos(filas, anchos=None, fuente=9):
    """Tabla con encabezado azul institucional y filas alternadas."""
    tabla = Table(filas, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), fuente),
        ('GRID', (0, 0), (-1, -1), 0.4, GRIS),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, AZUL_CLARO]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return tabla
