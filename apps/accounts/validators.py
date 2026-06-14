import re

from django.core.exceptions import ValidationError


def validar_rut_chileno(rut: str) -> None:
    """Valida formato y dígito verificador de un RUT chileno (módulo 11)."""
    rut = rut.replace('.', '').replace('-', '').upper()
    if not re.fullmatch(r'\d{7,8}[0-9K]', rut):
        raise ValidationError('RUT inválido.')
    cuerpo, dv = rut[:-1], rut[-1]
    suma, mult = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * mult
        mult = mult + 1 if mult < 7 else 2
    resto = 11 - suma % 11
    if resto == 11:
        dv_calc = '0'
    elif resto == 10:
        dv_calc = 'K'
    else:
        dv_calc = str(resto)
    if dv != dv_calc:
        raise ValidationError('RUT inválido (dígito verificador incorrecto).')
