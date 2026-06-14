from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from apps.asistencia.views import ROLES_DOCENTES
from apps.convivencia.views import matriculas_de
from apps.core.mixins import RoleRequiredMixin

from .reportes import informe_notas_pdf


class InformeNotasPDFView(RoleRequiredMixin, View):
    allowed_roles = ROLES_DOCENTES

    def get(self, request, *args, **kwargs):
        matricula = get_object_or_404(matriculas_de(request.user), pk=kwargs['pk'])
        pdf = informe_notas_pdf(matricula)
        respuesta = HttpResponse(pdf, content_type='application/pdf')
        respuesta['Content-Disposition'] = (
            f'attachment; filename="informe_notas_{matricula.alumno.rut_alumno}'
            f'_{matricula.anio_escolar}.pdf"'
        )
        return respuesta
