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
    Usa el mismo diseño visual que MisNotasView (alumno)."""

    template_name = 'alumnos/pupilos_notas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        def clase_nota(n):
            if n is None:
                return 'nota-sin'
            n = float(n)
            if n >= 6.0:
                return 'nota-excelente'
            if n >= 5.0:
                return 'nota-buena'
            if n >= 4.0:
                return 'nota-suficiente'
            return 'nota-insuficiente'

        boletines = []
        for pupilo in context['pupilos']:
            matricula = (
                pupilo.matriculas
                .select_related('curso__nivel')
                .order_by('-anio_escolar')
                .first()
            )
            calificaciones = (
                Calificacion.objects.filter(matricula__alumno=pupilo)
                .select_related(
                    'evaluacion__curso_asignatura__asignatura',
                    'evaluacion__periodo',
                    'evaluacion__tipo',
                    'matricula',
                )
                .order_by(
                    'evaluacion__periodo__fecha_inicio',
                    'evaluacion__curso_asignatura__asignatura__nombre',
                    'evaluacion__fecha',
                )
            )

            # Agrupar: { periodo: { asignatura_obj: [cal, ...] } }
            agrupado = defaultdict(lambda: defaultdict(list))
            for cal in calificaciones:
                periodo = cal.evaluacion.periodo
                asignatura = cal.evaluacion.curso_asignatura.asignatura
                agrupado[periodo][asignatura].append(cal)

            todos_promedios = []
            resumen = []
            for periodo in sorted(agrupado.keys(), key=lambda p: p.fecha_inicio):
                asignaturas = []
                for asignatura, cals in sorted(
                    agrupado[periodo].items(), key=lambda x: x[0].nombre
                ):
                    notas = [float(c.nota) for c in cals]
                    promedio = round(sum(notas) / len(notas), 1) if notas else None
                    if promedio is not None:
                        todos_promedios.append(promedio)
                    asignaturas.append({
                        'asignatura': asignatura,
                        'calificaciones': [
                            {'cal': c, 'clase': clase_nota(c.nota)} for c in cals
                        ],
                        'promedio': promedio,
                        'clase_promedio': clase_nota(promedio),
                        'pct': round((promedio - 1) / 6 * 100) if promedio else 0,
                    })
                resumen.append({'periodo': periodo, 'asignaturas': asignaturas})

            promedio_general = (
                round(sum(todos_promedios) / len(todos_promedios), 1)
                if todos_promedios else None
            )
            boletines.append({
                'pupilo': pupilo,
                'matricula': matricula,
                'resumen': resumen,
                'promedio_general': promedio_general,
                'clase_promedio_general': clase_nota(promedio_general),
            })

        context['boletines'] = boletines
        return context
