from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, TemplateView

from apps.alumnos.models import Matricula
from apps.asistencia.views import ROLES_DOCENTES, cursos_asignatura_de
from apps.core.mixins import RoleRequiredMixin

from .forms import CalificacionForm
from .models import Calificacion, Evaluacion


def evaluaciones_de(user):
    """Evaluaciones que el usuario puede operar: las de sus asignaturas, o todas si es admin."""
    return (
        Evaluacion.objects.filter(curso_asignatura__in=cursos_asignatura_de(user))
        .select_related(
            'curso_asignatura__curso__nivel',
            'curso_asignatura__asignatura',
            'periodo',
            'tipo',
        )
        .order_by('-fecha')
    )


class SeleccionEvaluacionView(RoleRequiredMixin, ListView):
    """La tabla de evaluaciones solo aparece con los 3 filtros completos
    (curso + profesor + período). El profesor queda fijado a sí mismo."""

    allowed_roles = ROLES_DOCENTES
    template_name = 'calificaciones/seleccionar.html'
    context_object_name = 'evaluaciones'

    def get_filtro(self):
        from django.contrib.auth import get_user_model

        from apps.academico.models import Curso

        from .forms import FiltroEvaluacionesForm

        form = FiltroEvaluacionesForm(self.request.GET or None)
        user = self.request.user
        if user.role != 'admin':
            # Propiedad: solo él mismo y sus cursos
            form.fields['profesor'].queryset = get_user_model().objects.filter(pk=user.pk)
            form.fields['profesor'].initial = user.pk
            form.fields['curso'].queryset = Curso.objects.filter(
                curso_asignaturas__profesor=user
            ).select_related('nivel').distinct()
        return form

    def get_queryset(self):
        self.form_filtro = self.get_filtro()
        if not self.form_filtro.is_bound or not self.form_filtro.is_valid():
            return evaluaciones_de(self.request.user).none()
        datos = self.form_filtro.cleaned_data
        return evaluaciones_de(self.request.user).filter(
            curso_asignatura__curso=datos['curso'],
            curso_asignatura__profesor=datos['profesor'],
            periodo=datos['periodo'],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_filtro'] = self.form_filtro
        context['filtros_aplicados'] = (
            self.form_filtro.is_bound and self.form_filtro.is_valid()
        )
        return context


class IngresarNotasView(RoleRequiredMixin, TemplateView):
    allowed_roles = ROLES_DOCENTES
    template_name = 'calificaciones/ingresar.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)  # mixin resuelve login/403
        # Propiedad: 404 si la evaluación no es de una asignatura del profesor
        self.evaluacion = get_object_or_404(
            evaluaciones_de(request.user), pk=kwargs['pk']
        )
        return super().dispatch(request, *args, **kwargs)

    def get_forms(self, data=None):
        matriculas = (
            Matricula.objects.filter(
                curso=self.evaluacion.curso_asignatura.curso,
                estado__in=[Matricula.Estado.REGULAR, Matricula.Estado.REPITENTE],
            )
            .select_related('alumno__usuario')
            .order_by('alumno__usuario__last_name', 'alumno__usuario__first_name')
        )
        existentes = {
            c.matricula_id: c
            for c in Calificacion.objects.filter(
                evaluacion=self.evaluacion, matricula__in=matriculas
            )
        }
        forms = []
        for m in matriculas:
            instancia = existentes.get(m.pk) or Calificacion(
                evaluacion=self.evaluacion, matricula=m
            )
            # Filas nuevas dejadas en blanco son válidas y se omiten al guardar:
            # no se obliga a calificar a todo el curso de una vez.
            forms.append(
                (m, CalificacionForm(
                    data,
                    instance=instancia,
                    prefix=f'm{m.pk}',
                    empty_permitted=instancia.pk is None,
                    use_required_attribute=False,
                ))
            )
        return forms

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('filas', self.get_forms())
        context['evaluacion'] = self.evaluacion
        return context

    def post(self, request, *args, **kwargs):
        filas = self.get_forms(request.POST)
        if all(form.is_valid() for _, form in filas):
            guardadas = 0
            with transaction.atomic():
                for _, form in filas:
                    # Fila nueva sin datos → no se crea calificación
                    if form.instance.pk is None and not form.has_changed():
                        continue
                    form.save()  # el middleware de simple-history registra al usuario
                    guardadas += 1
            messages.success(
                request, f'Notas guardadas: {guardadas} de {len(filas)} alumnos.'
            )
            return redirect('calificaciones:ingresar', pk=self.evaluacion.pk)
        context = self.get_context_data(filas=filas)
        return self.render_to_response(context)
