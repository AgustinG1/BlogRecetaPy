from django import forms
from .models import Receta, Comentario
from django_ckeditor_5.widgets import CKEditor5Widget

class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['titulo', 'subtitulo', 'categoria', 'ingredientes', 'instrucciones', 'imagen']
        widgets = {
            'ingredientes': CKEditor5Widget(config_name='extends'),  
            'instrucciones': CKEditor5Widget(config_name='extends'),  
        }



class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': CKEditor5Widget(config_name='extends'),
        }