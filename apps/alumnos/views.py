"""Portal del apoderado: vistas de solo lectura sobre sus pupilos."""
from collections import defaultdict
from decimal import Decimal

from django.views.generic import TemplateView

from apps.calificaciones.models import Calificacion
from apps.convivencia.models import Anotacion, Citacion
from apps.core.mixins import RoleRequiredMixin

from .models import PerfilAlumno

UMBRAL_APROBACION = Decimal('4.0')


def pupilos_de(user):
    return PerfilAlumno.objects.filter(
        vinculos_apoderados__apoderado__usuario=user
    ).select_related('usuario').distinct()


class PortalApoderadoMixin(RoleRequiredMixin):
    allowed_roles = ['apoderado']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pupilos'] = pupilos_de(self.request.user)
        return context


class PupilosCitacionesView(PortalApoderadoMixin, TemplateView):
    template_name = 'alumnos/pupilos_citaciones.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        citaciones = Citacion.objects.filter(
            matricula__alumno__in=context['pupilos']
        ).select_related(
            'matricula__alumno__usuario', 'apoderado__usuario', 'registrado_por'
        )
        context['programadas'] = citaciones.filter(estado=Citacion.Estado.PROGRAMADA)
        context['historicas'] = citaciones.exclude(estado=Citacion.Estado.PROGRAMADA)
        return context


class PupilosAnotacionesView(PortalApoderadoMixin, TemplateView):
    template_name = 'alumnos/pupilos_anotaciones.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['anotaciones'] = Anotacion.objects.filter(
            matricula__alumno__in=context['pupilos']
        ).select_related('matricula__alumno__usuario', 'registrado_por')
        return context


class PupilosNotasView(PortalApoderadoMixin, TemplateView):
    """Notas por asignatura con promedio por asignatura y promedio general.
    Bajo 4.0 → Reprobado (rojo); desde 4.0 → Aprobado."""

    template_name = 'alumnos/pupilos_notas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        boletines = []
        for pupilo in context['pupilos']:
            calificaciones = (
                Calificacion.objects.filter(matricula__alumno=pupilo)
                .select_related(
                    'evaluacion__curso_asignatura__asignatura',
                    'evaluacion__periodo', 'evaluacion__tipo', 'matricula',
                )
                .order_by('evaluacion__fecha')
            )
            por_asignatura = defaultdict(list)
            for cal in calificaciones:
                nombre = cal.evaluacion.curso_asignatura.asignatura.nombre
                por_asignatura[nombre].append(cal)

            ramos = []
            for nombre, cals in sorted(por_asignatura.items()):
                promedio = sum(c.nota for c in cals) / len(cals)
                ramos.append({
                    'asignatura': nombre,
                    'calificaciones': cals,
                    'promedio': promedio,
                    'aprobado': promedio >= UMBRAL_APROBACION,
                })
            promedio_general = (
                sum(r['promedio'] for r in ramos) / len(ramos) if ramos else None
            )
            boletines.append({
                'pupilo': pupilo,
                'ramos': ramos,
                'promedio_general': promedio_general,
                'aprobado_general': (
                    promedio_general is not None
                    and promedio_general >= UMBRAL_APROBACION
                ),
            })
        context['boletines'] = boletines
        return context
