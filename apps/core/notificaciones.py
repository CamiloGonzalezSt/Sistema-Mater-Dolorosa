"""Notificaciones por email a apoderados.

Funciones síncronas y aisladas a propósito: en la Fase 4 (deploy) se convierten
en tareas Celery anteponiendo @shared_task, sin cambiar a quienes las llaman.
Usan fail_silently: un problema de correo nunca debe romper el registro académico.
"""
from django.conf import settings
from django.core.mail import send_mail

FIRMA = '\n\nAtentamente,\nColegio Mater Dolorosa\n(Mensaje automático, no responder)'


def _emails_apoderados(alumno):
    return [
        v.apoderado.usuario.email
        for v in alumno.vinculos_apoderados.select_related('apoderado__usuario')
        if v.apoderado.usuario.email
    ]


def _enviar(asunto, cuerpo, destinatarios):
    if destinatarios:
        send_mail(
            subject=asunto,
            message=cuerpo + FIRMA,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinatarios,
            fail_silently=True,
        )


def notificar_anotacion_negativa(anotacion):
    alumno = anotacion.matricula.alumno
    _enviar(
        f'[Mater Dolorosa] Anotación en la hoja de vida de {alumno.usuario.get_full_name()}',
        (
            f'Estimado(a) apoderado(a):\n\n'
            f'Se ha registrado una anotación negativa para '
            f'{alumno.usuario.get_full_name()} ({anotacion.matricula.curso}) '
            f'con fecha {anotacion.fecha:%d-%m-%Y}:\n\n'
            f'"{anotacion.descripcion}"\n\n'
            f'Registrada por: {anotacion.registrado_por.get_full_name()}.\n'
            f'Le pedimos tomar conocimiento y conversar la situación en familia.'
        ),
        _emails_apoderados(alumno),
    )


def notificar_citacion(citacion, creada=True):
    email = citacion.apoderado.usuario.email
    alumno = citacion.matricula.alumno
    if creada:
        asunto = f'[Mater Dolorosa] Citación de apoderado — {alumno.usuario.get_full_name()}'
        cuerpo = (
            f'Estimado(a) {citacion.apoderado.usuario.get_full_name()}:\n\n'
            f'Usted ha sido citado(a) al colegio por el/la alumno(a) '
            f'{alumno.usuario.get_full_name()} ({citacion.matricula.curso}).\n\n'
            f'Fecha y hora: {citacion.fecha_hora:%d-%m-%Y a las %H:%M} hrs.\n'
            f'Motivo: {citacion.motivo}\n\n'
            f'Cita: {citacion.registrado_por.get_full_name()}.'
        )
    else:
        asunto = f'[Mater Dolorosa] Resultado de citación — {alumno.usuario.get_full_name()}'
        cuerpo = (
            f'Estimado(a) {citacion.apoderado.usuario.get_full_name()}:\n\n'
            f'La citación del {citacion.fecha_hora:%d-%m-%Y} quedó registrada como '
            f'"{citacion.get_estado_display()}".\n'
            + (f'\nAcuerdos:\n{citacion.acuerdos}' if citacion.acuerdos else '')
        )
    _enviar(asunto, cuerpo, [email] if email else [])


def notificar_mensaje(mensaje):
    """Copia por email al profesor cuando un alumno o apoderado le escribe."""
    email = mensaje.destinatario.email
    pupilo = (
        f'\nAlumno relacionado: {mensaje.pupilo.usuario.get_full_name()}'
        if mensaje.pupilo else ''
    )
    _enviar(
        f'[Mater Dolorosa] {mensaje.get_tipo_display()}: {mensaje.asunto}',
        (
            f'Estimado(a) {mensaje.destinatario.get_full_name()}:\n\n'
            f'Ha recibido un(a) {mensaje.get_tipo_display().lower()} de '
            f'{mensaje.remitente.get_full_name()} '
            f'({mensaje.remitente.get_role_display().lower()}).{pupilo}\n\n'
            f'{mensaje.cuerpo}\n\n'
            f'Puede responder desde su bandeja en el panel del colegio.'
        ),
        [email] if email else [],
    )


def notificar_postulacion(postulacion):
    """Aviso a secretaría cuando llega una postulación desde el sitio público."""
    _enviar(
        f'[Mater Dolorosa] Nueva postulación: {postulacion.nombre_postulante}',
        (
            f'Se recibió una nueva postulación de admisión:\n\n'
            f'Postulante: {postulacion.nombre_postulante}\n'
            f'Nivel: {postulacion.nivel}\n'
            f'Apoderado: {postulacion.nombre_apoderado}\n'
            f'Email: {postulacion.email} · Teléfono: {postulacion.telefono}\n\n'
            f'{postulacion.mensaje or "(sin mensaje)"}\n\n'
            f'Revísala en el panel: /panel/postulaciones/'
        ),
        [settings.CONTACT_EMAIL],
    )


def alertar_inasistencias(matricula, cantidad, dias=30):
    alumno = matricula.alumno
    _enviar(
        f'[Mater Dolorosa] Alerta de inasistencias — {alumno.usuario.get_full_name()}',
        (
            f'Estimado(a) apoderado(a):\n\n'
            f'{alumno.usuario.get_full_name()} ({matricula.curso}) acumula '
            f'{cantidad} ausencias sin justificar en los últimos {dias} días.\n\n'
            f'Le recordamos que puede justificar las inasistencias en secretaría. '
            f'La asistencia regular es fundamental para el proceso de aprendizaje.'
        ),
        _emails_apoderados(alumno),
    )
