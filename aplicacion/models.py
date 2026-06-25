from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field

# Create your models here.


class Categoria(models.Model):
    CATEGORIAS_CHOICES = (
        ('salada', 'Comida Salada'),
        ('dulce', 'Comida Dulce'),
        ('vegetariana', 'Comida Vegetariana'),
    )

    nombre = models.CharField(
        max_length=100,
        choices=CATEGORIAS_CHOICES,
        default='salada'
    )

    def __str__(self):
        return self.get_nombre_display()




class Receta(models.Model):
    titulo = models.CharField(max_length=200, null=True)
    subtitulo = models.CharField(max_length=200, null=True)  
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    ingredientes = CKEditor5Field('Ingredientes', config_name='extends')  
    instrucciones = CKEditor5Field('Instrucciones', config_name='extends')  
 
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    imagen = models.ImageField(upload_to='images', default='images/receta_default.jpg')  
    creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return self.titulo


class Comentario(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.autor.username} en {self.receta.titulo}"
    

