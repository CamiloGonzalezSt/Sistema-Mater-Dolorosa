from datetime import date, timedelta

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from apps.academico.models import CursoAsignatura
from apps.alumnos.models import Matricula
from apps.core import notificaciones
from apps.core.mixins import RoleRequiredMixin

UMBRAL_AUSENCIAS = 3  # ausencias sin justificar en 30 días que gatillan alerta

from .forms import RegistroAsistenciaForm, SeleccionAsistenciaForm
from .models import RegistroAsistencia

ROLES_DOCENTES = ['profesor', 'admin']


def cursos_asignatura_de(user):
    """Asignaturas que el usuario puede operar: las suyas, o todas si es admin."""
    qs = CursoAsignatura.objects.select_related('curso__nivel', 'asignatura', 'profesor')
    if user.role != 'admin':
        qs = qs.filter(profesor=user)
    return qs


class SeleccionAsistenciaView(RoleRequiredMixin, FormView):
    allowed_roles = ROLES_DOCENTES
    template_name = 'asistencia/seleccionar.html'
    form_class = SeleccionAsistenciaForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['curso_asignatura'].queryset = cursos_asignatura_de(self.request.user)
        return form

    def form_valid(self, form):
        ca = form.cleaned_data['curso_asignatura']
        fecha = form.cleaned_data['fecha']
        url = reverse('asistencia:registrar', args=[ca.pk])
        return redirect(f'{url}?fecha={fecha.isoformat()}')


class RegistrarAsistenciaView(RoleRequiredMixin, TemplateView):
    allowed_roles = ROLES_DOCENTES
    template_name = 'asistencia/registrar.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)  # mixin resuelve login/403
        # Propiedad: 404 si la asignatura no pertenece al profesor
        self.curso_asignatura = get_object_or_404(
            cursos_asignatura_de(request.user), pk=kwargs['pk']
        )
        try:
            self.fecha = date.fromisoformat(
                request.POST.get('fecha') or request.GET.get('fecha') or ''
            )
        except ValueError:
            self.fecha = date.today()
        return super().dispatch(request, *args, **kwargs)

    def get_forms(self, data=None):
        matriculas = (
            Matricula.objects.filter(
                curso=self.curso_asignatura.curso,
                estado__in=[Matricula.Estado.REGULAR, Matricula.Estado.REPITENTE],
            )
            .select_related('alumno__usuario')
            .order_by('alumno__usuario__last_name', 'alumno__usuario__first_name')
        )
        existentes = {
            r.matricula_id: r
            for r in RegistroAsistencia.objects.filter(
                curso_asignatura=self.curso_asignatura,
                fecha=self.fecha,
                matricula__in=matriculas,
            )
        }
        forms = []
        for m in matriculas:
            instancia = existentes.get(m.pk) or RegistroAsistencia(
                matricula=m,
                curso_asignatura=self.curso_asignatura,
                fecha=self.fecha,
                registrado_por=self.request.user,
            )
            inicial = {} if instancia.pk else {'estado': RegistroAsistencia.Estado.PRESENTE}
            forms.append(
                (m, RegistroAsistenciaForm(data, instance=instancia, prefix=f'm{m.pk}', initial=inicial))
            )
        return forms

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('filas', self.get_forms())
        context['curso_asignatura'] = self.curso_asignatura
        context['fecha'] = self.fecha
        return context

    def post(self, request, *args, **kwargs):
        filas = self.get_forms(request.POST)
        if all(form.is_valid() for _, form in filas):
            with transaction.atomic():
                for _, form in filas:
                    registro = form.save(commit=False)
                    registro.registrado_por = request.user  # último en editar
                    registro.save()
            self._alertar_inasistencias(filas)
            messages.success(
                request,
                f'Asistencia del {self.fecha.strftime("%d-%m-%Y")} guardada '
                f'({len(filas)} alumnos).',
            )
            url = reverse('asistencia:registrar', args=[self.curso_asignatura.pk])
            return redirect(f'{url}?fecha={self.fecha.isoformat()}')
        context = self.get_context_data(filas=filas)
        return self.render_to_response(context)

    def _alertar_inasistencias(self, filas):
        """Alerta al apoderado cuando el alumno alcanza el umbral de ausencias
        sin justificar en los últimos 30 días (solo al cruzarlo, evita spam)."""
        desde = self.fecha - timedelta(days=30)
        for matricula, form in filas:
            if form.instance.estado != RegistroAsistencia.Estado.AUSENTE:
                continue
            ausencias = RegistroAsistencia.objects.filter(
                matricula=matricula,
                estado=RegistroAsistencia.Estado.AUSENTE,
                fecha__gte=desde,
                fecha__lte=self.fecha,
            ).count()
            if ausencias == UMBRAL_AUSENCIAS:
                notificaciones.alertar_inasistencias(matricula, ausencias)
