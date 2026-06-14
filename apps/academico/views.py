from django.contrib import messages
from django.forms import ModelForm
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, View

from apps.alumnos.models import Matricula
from apps.core.mixins import RoleRequiredMixin

from .models import CursoAsignatura, MaterialAcademico


class MaterialForm(ModelForm):
    class Meta:
        model = MaterialAcademico
        fields = ['curso_asignatura', 'periodo', 'unidad', 'titulo', 'descripcion', 'archivo']


def matricula_vigente_de(user):
    return (
        Matricula.objects.filter(
            alumno__usuario=user,
            anio_escolar=timezone.localdate().year,
            estado__in=[Matricula.Estado.REGULAR, Matricula.Estado.REPITENTE],
        )
        .select_related('curso__nivel')
        .first()
    )


class MisMaterialesView(RoleRequiredMixin, ListView):
    """Alumno: materiales del curso de su matrícula vigente."""

    allowed_roles = ['alumno']
    template_name = 'academico/materiales.html'
    context_object_name = 'materiales'

    def get_queryset(self):
        self.matricula = matricula_vigente_de(self.request.user)
        if self.matricula is None:
            return MaterialAcademico.objects.none()
        return MaterialAcademico.objects.filter(
            curso_asignatura__curso=self.matricula.curso
        ).select_related(
            'curso_asignatura__asignatura', 'periodo', 'subido_por'
        ).order_by(
            'curso_asignatura__asignatura__nombre', 'periodo_id', 'unidad', '-creado_el'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['matricula'] = self.matricula
        return context


class GestionMaterialesView(RoleRequiredMixin, CreateView):
    """Profesor: sube material a sus clases y administra los propios."""

    allowed_roles = ['profesor', 'admin']
    template_name = 'academico/materiales_gestion.html'
    form_class = MaterialForm
    success_url = reverse_lazy('academico:materiales_gestion')

    def propios(self):
        qs = MaterialAcademico.objects.select_related(
            'curso_asignatura__asignatura', 'curso_asignatura__curso__nivel', 'periodo')
        if self.request.user.role != 'admin':
            qs = qs.filter(curso_asignatura__profesor=self.request.user)
        return qs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        cas = CursoAsignatura.objects.select_related('curso__nivel', 'asignatura')
        if self.request.user.role != 'admin':
            cas = cas.filter(profesor=self.request.user)
        form.fields['curso_asignatura'].queryset = cas
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materiales'] = self.propios()
        return context

    def form_valid(self, form):
        form.instance.subido_por = self.request.user
        messages.success(self.request, 'Material publicado para el curso.')
        return super().form_valid(form)


class EliminarMaterialView(RoleRequiredMixin, View):
    allowed_roles = ['profesor', 'admin']

    def post(self, request, *args, **kwargs):
        qs = MaterialAcademico.objects.all()
        if request.user.role != 'admin':
            qs = qs.filter(curso_asignatura__profesor=request.user)
        material = get_object_or_404(qs, pk=kwargs['pk'])
        material.delete()
        messages.success(request, 'Material eliminado.')
        return redirect('academico:materiales_gestion')
