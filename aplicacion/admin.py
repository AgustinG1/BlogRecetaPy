from django.contrib import admin
from aplicacion.models import Categoria, Receta, Comentario
from aplicacion.forms import RecetaForm, ComentarioForm

# Register your models here.
admin.site.register(Categoria)


class RecetaAdminForm(RecetaForm):
    class Meta(RecetaForm.Meta):
        fields = '__all__'


class ComentarioAdminForm(ComentarioForm):
    class Meta(ComentarioForm.Meta):
        fields = '__all__'


@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    form = RecetaAdminForm


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    form = ComentarioAdminForm
