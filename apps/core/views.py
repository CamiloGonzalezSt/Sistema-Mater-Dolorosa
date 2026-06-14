from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView, View

from apps.asistencia.models import RegistroAsistencia
from apps.asistencia.views import ROLES_DOCENTES, cursos_asignatura_de
from apps.calificaciones.models import Calificacion
from apps.convivencia.models import Anotacion, Citacion
from apps.core.mixins import RoleRequiredMixin


class HomeView(LoginRequiredMixin, TemplateView):
    """Panel de inicio: módulos + dashboard para roles docentes."""

    template_name = 'core/home.html'


class DashboardDataView(RoleRequiredMixin, View):
    """Datos agregados del dashboard en JSON. Mismo alcance que el resto del
    panel: el profesor ve sus asignaturas, el admin todo el colegio."""

    allowed_roles = ROLES_DOCENTES

    def get(self, request, *args, **kwargs):
        hoy = timezone.localdate()
        anio = hoy.year
        cas = cursos_asignatura_de(request.user).filter(anio_escolar=anio)
        cursos_ids = list(cas.values_list('curso_id', flat=True).distinct())

        # --- Asistencia de hoy ---
        por_estado = dict(
            RegistroAsistencia.objects.filter(curso_asignatura__in=cas, fecha=hoy)
            .values_list('estado')
            .annotate(n=Count('id'))
        )
        total_hoy = sum(por_estado.values())
        pct_presentes_hoy = (
            round(100 * por_estado.get('presente', 0) / total_hoy, 1) if total_hoy else None
        )

        # --- Serie de asistencia: últimos 30 días con registros ---
        desde = hoy - timedelta(days=29)
        serie = list(
            RegistroAsistencia.objects.filter(
                curso_asignatura__in=cas, fecha__gte=desde, fecha__lte=hoy
            )
            .values('fecha')
            .annotate(
                total=Count('id'),
                presentes=Count('id', filter=Q(estado='presente')),
            )
            .order_by('fecha')
        )
        asistencia_serie = {
            'fechas': [s['fecha'].strftime('%d-%m') for s in serie],
            'porcentajes': [round(100 * s['presentes'] / s['total'], 1) for s in serie],
        }

        # --- Promedio de notas por asignatura (año en curso) ---
        notas_qs = Calificacion.objects.filter(evaluacion__curso_asignatura__in=cas)
        promedios = list(
            notas_qs.values('evaluacion__curso_asignatura__asignatura__nombre')
            .annotate(promedio=Avg('nota'))
            .order_by('evaluacion__curso_asignatura__asignatura__nombre')
        )
        promedios_data = {
            'asignaturas': [p['evaluacion__curso_asignatura__asignatura__nombre'] for p in promedios],
            'promedios': [round(float(p['promedio']), 2) for p in promedios],
        }

        # --- Distribución de notas (histograma 1-7) ---
        tramos = [0] * 6  # [1-2), [2-3), ... [6-7]
        for (nota,) in notas_qs.values_list('nota'):
            indice = min(int(float(nota)) - 1, 5)
            tramos[max(indice, 0)] += 1

        # --- Convivencia del mes ---
        anotaciones_mes = dict(
            Anotacion.objects.filter(
                matricula__curso_id__in=cursos_ids,
                fecha__year=anio,
                fecha__month=hoy.month,
            )
            .values_list('tipo')
            .annotate(n=Count('id'))
        )
        citaciones_pendientes = Citacion.objects.filter(
            matricula__curso_id__in=cursos_ids,
            estado=Citacion.Estado.PROGRAMADA,
        ).count()

        return JsonResponse({
            'anio': anio,
            'asistencia_hoy': {
                'porcentaje_presentes': pct_presentes_hoy,
                'total_registros': total_hoy,
                'por_estado': por_estado,
            },
            'asistencia_serie': asistencia_serie,
            'promedios': promedios_data,
            'distribucion_notas': {
                'tramos': ['1-1.9', '2-2.9', '3-3.9', '4-4.9', '5-5.9', '6-7'],
                'cantidades': tramos,
            },
            'anotaciones_mes': {
                'positivas': anotaciones_mes.get('positiva', 0),
                'negativas': anotaciones_mes.get('negativa', 0),
                'observaciones': anotaciones_mes.get('observacion', 0),
            },
            'citaciones_pendientes': citaciones_pendientes,
        })
