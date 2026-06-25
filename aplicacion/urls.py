from django.urls import path, include
from . import views
from .views import agregar_receta, detalle_receta, eliminar_receta, editar_receta


urlpatterns = [
    path('', views.pagina_inicio, name='inicio'),
    path('agregar_receta/', agregar_receta, name='agregar_receta'),
    path('detalle_receta/<int:receta_id>/', detalle_receta, name='detalle_receta'),
    path('recetas/', views.ver_recetas, name='ver_recetas'),
    path('eliminar_receta/<int:receta_id>/', views.eliminar_receta, name='eliminar_receta'),
    path('editar_receta/<int:receta_id>/', views.editar_receta, name='editar_receta'),
    path('perfiles/', include('perfiles.urls')),
    path('agregar_comentario/<int:receta_id>/', views.agregar_comentario, name='agregar_comentario'),
    path('about/', views.about, name='about'),
    path('eliminar_comentario/<int:comentario_id>/', views.eliminar_comentario, name='eliminar_comentario'),
]