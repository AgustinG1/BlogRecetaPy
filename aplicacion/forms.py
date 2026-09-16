from django import forms
from .models import Receta, Comentario
from django_ckeditor_5.widgets import CKEditor5Widget
from .contenido import validar_contenido
from .imagenes import validar_imagen

class RecetaForm(forms.ModelForm):
    def clean_ingredientes(self):
        return validar_contenido(self.cleaned_data['ingredientes'])

    def clean_instrucciones(self):
        return validar_contenido(self.cleaned_data['instrucciones'])

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if 'imagen' in self.files and imagen:
            validar_imagen(imagen)
        return imagen

    class Meta:
        model = Receta
        fields = ['titulo', 'subtitulo', 'categoria', 'ingredientes', 'instrucciones', 'imagen']
        widgets = {
            'ingredientes': CKEditor5Widget(config_name='extends'),  
            'instrucciones': CKEditor5Widget(config_name='extends'),  
        }



class ComentarioForm(forms.ModelForm):
    def clean_contenido(self):
        return validar_contenido(self.cleaned_data['contenido'], comentario=True)

    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': CKEditor5Widget(config_name='comentarios'),
        }
