from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.alumnos.models import Matricula, PerfilApoderado
from apps.asistencia.views import ROLES_DOCENTES
from apps.core import notificaciones
from apps.core.mixins import RoleRequiredMixin

from .forms import AnotacionForm, CitacionForm, CitacionResultadoForm
from .models import Anotacion, Citacion


def matriculas_de(user):
    """Matrículas vigentes que el usuario puede operar: alumnos de cursos donde
    dicta clases, o todas si es admin."""
    qs = (
        Matricula.objects.filter(
            estado__in=[Matricula.Estado.REGULAR, Matricula.Estado.REPITENTE]
        )
        .select_related('alumno__usuario', 'curso__nivel')
        .order_by('curso__nivel_id', 'curso__letra', 'alumno__usuario__last_name')
    )
    if user.role != 'admin':
        qs = qs.filter(curso__curso_asignaturas__profesor=user).distinct()
    return qs


class MatriculaContextMixin(RoleRequiredMixin):
    """Carga self.matricula con control de propiedad (404 si no corresponde)."""

    allowed_roles = ROLES_DOCENTES

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role in self.allowed_roles:
            self.matricula = get_object_or_404(
                matriculas_de(request.user), pk=kwargs['pk']
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['matricula'] = self.matricula
        return context


class SeleccionAlumnoView(RoleRequiredMixin, ListView):
    allowed_roles = ROLES_DOCENTES
    template_name = 'convivencia/alumnos.html'
    context_object_name = 'matriculas'

    def get_queryset(self):
        qs = matriculas_de(self.request.user)
        busqueda = self.request.GET.get('q', '').strip()
        if busqueda:
            qs = qs.filter(
                Q(alumno__usuario__first_name__icontains=busqueda)
                | Q(alumno__usuario__last_name__icontains=busqueda)
                | Q(alumno__rut_alumno__icontains=busqueda)
            )
        curso_id = self.request.GET.get('curso', '')
        if curso_id.isdigit():
            qs = qs.filter(curso_id=curso_id)
        return qs

    def get_context_data(self, **kwargs):
        from apps.academico.models import Curso

        context = super().get_context_data(**kwargs)
        context['busqueda'] = self.request.GET.get('q', '')
        context['filtro_curso'] = self.request.GET.get('curso', '')
        cursos = Curso.objects.select_related('nivel')
        if self.request.user.role != 'admin':
            cursos = cursos.filter(
                curso_asignaturas__profesor=self.request.user
            ).distinct()
        context['cursos'] = cursos
        return context


class HojaVidaView(MatriculaContextMixin, TemplateView):
    template_name = 'convivencia/hoja_vida.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['anotaciones'] = self.matricula.anotaciones.select_related(
            'registrado_por'
        )
        context['citaciones'] = self.matricula.citaciones.select_related(
            'apoderado__usuario', 'registrado_por'
        )
        return context


class CrearAnotacionView(MatriculaContextMixin, CreateView):
    form_class = AnotacionForm
    template_name = 'convivencia/anotacion_form.html'

    def form_valid(self, form):
        form.instance.matricula = self.matricula
        form.instance.registrado_por = self.request.user
        respuesta = super().form_valid(form)
        if self.object.tipo == Anotacion.Tipo.NEGATIVA:
            notificaciones.notificar_anotacion_negativa(self.object)
        messages.success(self.request, 'Anotación registrada en la hoja de vida.')
        return respuesta

    def get_success_url(self):
        return reverse('convivencia:hoja_vida', args=[self.matricula.pk])


class CrearCitacionView(MatriculaContextMixin, CreateView):
    form_class = CitacionForm
    template_name = 'convivencia/citacion_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['apoderado'].queryset = PerfilApoderado.objects.filter(
            vinculos_alumnos__alumno=self.matricula.alumno
        ).select_related('usuario')
        return form

    def form_valid(self, form):
        form.instance.matricula = self.matricula
        form.instance.registrado_por = self.request.user
        respuesta = super().form_valid(form)
        notificaciones.notificar_citacion(self.object, creada=True)
        messages.success(self.request, 'Citación programada y notificada al apoderado.')
        return respuesta

    def get_success_url(self):
        return reverse('convivencia:hoja_vida', args=[self.matricula.pk])


class CerrarCitacionView(RoleRequiredMixin, UpdateView):
    """Registrar el resultado de la citación (estado y acuerdos)."""

    allowed_roles = ROLES_DOCENTES
    form_class = CitacionResultadoForm
    template_name = 'convivencia/citacion_form.html'
    context_object_name = 'citacion'

    def get_queryset(self):
        return Citacion.objects.filter(
            matricula__in=matriculas_de(self.request.user)
        ).select_related('matricula__alumno__usuario', 'apoderado__usuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['matricula'] = self.object.matricula
        context['es_cierre'] = True
        return context

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        notificaciones.notificar_citacion(self.object, creada=False)
        messages.success(self.request, 'Resultado de la citación registrado y notificado.')
        return respuesta

    def get_success_url(self):
        return reverse('convivencia:hoja_vida', args=[self.object.matricula_id])
