from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import View

from apps.core.mixins import RoleRequiredMixin

from .reportes import libro_asistencia_pdf
from .views import ROLES_DOCENTES, cursos_asignatura_de


class LibroAsistenciaPDFView(RoleRequiredMixin, View):
    allowed_roles = ROLES_DOCENTES

    def get(self, request, *args, **kwargs):
        ca = get_object_or_404(cursos_asignatura_de(request.user), pk=kwargs['pk'])
        hoy = timezone.localdate()
        try:
            anio, mes = map(int, request.GET.get('mes', '').split('-'))
            assert 1 <= mes <= 12
        except (ValueError, AssertionError):
            anio, mes = hoy.year, hoy.month
        pdf = libro_asistencia_pdf(ca, anio, mes)
        respuesta = HttpResponse(pdf, content_type='application/pdf')
        respuesta['Content-Disposition'] = (
            f'attachment; filename="libro_asistencia_{ca.pk}_{anio}-{mes:02d}.pdf"'
        )
        return respuesta
