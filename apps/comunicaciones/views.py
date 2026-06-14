from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView, View

from apps.alumnos.models import Matricula, PerfilAlumno
from apps.core import notificaciones
from apps.core.mixins import RoleRequiredMixin

from .forms import MensajeAlumnoForm, MensajeApoderadoForm
from .models import Mensaje

User = get_user_model()


def pupilos_de(user):
    return PerfilAlumno.objects.filter(
        vinculos_apoderados__apoderado__usuario=user
    ).select_related('usuario').distinct()


def profesores_para(user):
    """Profesores a los que el usuario puede escribir: los que hacen clases en
    el curso vigente del alumno, o en los cursos vigentes de sus pupilos."""
    anio = timezone.localdate().year
    if user.role == 'alumno':
        alumnos = PerfilAlumno.objects.filter(usuario=user)
    else:
        alumnos = pupilos_de(user)
    cursos = Matricula.objects.filter(
        alumno__in=alumnos, anio_escolar=anio,
        estado__in=[Matricula.Estado.REGULAR, Matricula.Estado.REPITENTE],
    ).values_list('curso_id', flat=True)
    return User.objects.filter(
        role='profesor', asignaturas_dictadas__curso_id__in=list(cursos)
    ).distinct().order_by('last_name')


class MensajesView(RoleRequiredMixin, TemplateView):
    """Bandeja según rol: profesor ve recibidos; alumno/apoderado ven enviados."""

    allowed_roles = ['profesor', 'alumno', 'apoderado', 'admin']

    def get_template_names(self):
        if self.request.user.role in ('profesor', 'admin'):
            return ['comunicaciones/bandeja.html']
        return ['comunicaciones/enviados.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.role in ('profesor', 'admin'):
            recibidos = Mensaje.objects.select_related(
                'remitente', 'pupilo__usuario')
            if user.role == 'profesor':
                recibidos = recibidos.filter(destinatario=user)
            context['mensajes'] = recibidos
            context['no_leidos'] = recibidos.filter(leido=False).count()
        else:
            context['mensajes'] = Mensaje.objects.filter(
                remitente=user).select_related('destinatario', 'pupilo__usuario')
        return context


class EnviarMensajeView(RoleRequiredMixin, CreateView):
    allowed_roles = ['alumno', 'apoderado']
    template_name = 'comunicaciones/enviar.html'
    success_url = reverse_lazy('comunicaciones:mensajes')

    def get_form_class(self):
        if self.request.user.role == 'alumno':
            return MensajeAlumnoForm
        return MensajeApoderadoForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['destinatario'].queryset = profesores_para(self.request.user)
        if 'pupilo' in form.fields:
            form.fields['pupilo'].queryset = pupilos_de(self.request.user)
        return form

    def form_valid(self, form):
        form.instance.remitente = self.request.user
        if self.request.user.role == 'alumno':
            form.instance.pupilo = PerfilAlumno.objects.filter(
                usuario=self.request.user).first()
        respuesta = super().form_valid(form)
        notificaciones.notificar_mensaje(self.object)
        messages.success(
            self.request,
            'Mensaje enviado. El profesor recibió una copia por correo.',
        )
        return respuesta


class MarcarLeidoView(RoleRequiredMixin, View):
    allowed_roles = ['profesor', 'admin']

    def post(self, request, *args, **kwargs):
        qs = Mensaje.objects.all()
        if request.user.role == 'profesor':
            qs = qs.filter(destinatario=request.user)
        mensaje = get_object_or_404(qs, pk=kwargs['pk'])
        mensaje.leido = True
        mensaje.save(update_fields=['leido'])
        return redirect('comunicaciones:mensajes')
