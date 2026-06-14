from django.urls import path

from .views import EliminarMaterialView, GestionMaterialesView, MisMaterialesView

app_name = 'academico'

urlpatterns = [
    path('', MisMaterialesView.as_view(), name='materiales'),
    path('gestion/', GestionMaterialesView.as_view(), name='materiales_gestion'),
    path('gestion/<int:pk>/eliminar/', EliminarMaterialView.as_view(), name='material_eliminar'),
]
