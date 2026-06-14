from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from apps.core import notificaciones
from apps.core.mixins import RoleRequiredMixin

from .forms import ContactoForm, PostulacionForm
from .models import (
    EquipoConvivencia, EventoCalendario, ItemGaleria, Noticia, Postulacion,
)


class HomePublicaView(TemplateView):
    template_name = 'web_publica/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        context['noticias'] = Noticia.objects.filter(publicada=True)[:3]
        context['eventos'] = EventoCalendario.objects.filter(fecha__gte=hoy)[:4]
        return context


class HistoriaView(TemplateView):
    template_name = 'web_publica/historia.html'


class QuienesSomosView(TemplateView):
    template_name = 'web_publica/quienes_somos.html'


class NoticiasView(ListView):
    template_name = 'web_publica/noticias.html'
    context_object_name = 'noticias'
    paginate_by = 9
    queryset = Noticia.objects.filter(publicada=True)


class NoticiaDetalleView(DetailView):
    template_name = 'web_publica/noticia_detalle.html'
    context_object_name = 'noticia'
    queryset = Noticia.objects.filter(publicada=True)


class CalendarioView(TemplateView):
    template_name = 'web_publica/calendario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        desde = timezone.localdate().replace(day=1)
        context['eventos'] = EventoCalendario.objects.filter(fecha__gte=desde)
        return context


class GaleriaView(TemplateView):
    template_name = 'web_publica/galeria.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        anios = list(
            ItemGaleria.objects.values_list('anio', flat=True)
            .distinct().order_by('-anio')
        )
        anio_filtro = self.request.GET.get('anio', '')
        anio = int(anio_filtro) if anio_filtro.isdigit() else (anios[0] if anios else None)
        context['anios'] = anios
        context['anio_activo'] = anio
        context['items'] = (
            ItemGaleria.objects.filter(anio=anio) if anio else ItemGaleria.objects.none()
        )
        return context


class ConvivenciaEscolarView(TemplateView):
    template_name = 'web_publica/convivencia_escolar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipo'] = EquipoConvivencia.objects.all()
        return context


class AdmisionView(FormView):
    template_name = 'web_publica/admision.html'
    form_class = PostulacionForm
    success_url = reverse_lazy('web_publica:admision')

    def form_valid(self, form):
        postulacion = form.save()
        notificaciones.notificar_postulacion(postulacion)
        messages.success(
            self.request,
            'Recibimos tu postulación. Te contactaremos al correo indicado.',
        )
        return super().form_valid(form)


class ContactoView(FormView):
    template_name = 'web_publica/contacto.html'
    form_class = ContactoForm
    success_url = reverse_lazy('web_publica:contacto')

    def form_valid(self, form):
        form.enviar()
        messages.success(
            self.request,
            'Tu mensaje fue enviado correctamente. Te responderemos a la brevedad.',
        )
        return super().form_valid(form)


# ------------------------------------------------------------------
# Panel del administrador: revisión de postulaciones
# ------------------------------------------------------------------
class PostulacionesAdminView(RoleRequiredMixin, ListView):
    allowed_roles = ['admin']
    template_name = 'web_publica/postulaciones.html'
    context_object_name = 'postulaciones'
    paginate_by = 30

    def get_queryset(self):
        qs = Postulacion.objects.select_related('nivel')
        estado = self.request.GET.get('estado', '')
        if estado in Postulacion.Estado.values:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = Postulacion.Estado.choices
        context['filtro_estado'] = self.request.GET.get('estado', '')
        context['nuevas'] = Postulacion.objects.filter(
            estado=Postulacion.Estado.NUEVA).count()
        return context


class CambiarEstadoPostulacionView(RoleRequiredMixin, View):
    allowed_roles = ['admin']

    def post(self, request, *args, **kwargs):
        postulacion = get_object_or_404(Postulacion, pk=kwargs['pk'])
        estado = request.POST.get('estado', '')
        if estado in Postulacion.Estado.values:
            postulacion.estado = estado
            postulacion.save(update_fields=['estado'])
            messages.success(
                request,
                f'Postulación de {postulacion.nombre_postulante}: '
                f'{postulacion.get_estado_display()}.',
            )
        return redirect('postulaciones_admin')
