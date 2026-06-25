from django.contrib import admin
from aplicacion.models import Categoria, Receta, Comentario

# Register your models here.
admin.site.register(Categoria)
admin.site.register(Receta)
admin.site.register(Comentario)
