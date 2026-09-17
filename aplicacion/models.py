from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field
from .contenido import sanear_html

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
        default='salada',
        unique=True,
    )

    def __str__(self):
        return self.get_nombre_display()




class Receta(models.Model):
    titulo = models.CharField(max_length=200)
    subtitulo = models.CharField(max_length=200, null=True)  
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    ingredientes = CKEditor5Field('Ingredientes', config_name='extends')  
    instrucciones = CKEditor5Field('Instrucciones', config_name='extends')  
 
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    imagen = models.ImageField(upload_to='images', default='images/receta_default.jpg')  
    creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['-fecha_publicacion', '-id'], name='receta_fecha_id_idx'),
            models.Index(
                fields=['categoria', '-fecha_publicacion', '-id'],
                name='receta_categoria_fecha_idx',
            ),
        ]
    
    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        # También protege guardados que no pasan por los formularios públicos.
        campos = kwargs.get('update_fields')
        for campo in ('ingredientes', 'instrucciones'):
            if campos is None or campo in campos:
                setattr(self, campo, sanear_html(getattr(self, campo)))
        return super().save(*args, **kwargs)


class Comentario(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['receta', 'fecha_creacion', 'id'],
                name='comentario_receta_fecha_idx',
            ),
        ]

    def save(self, *args, **kwargs):
        campos = kwargs.get('update_fields')
        if campos is None or 'contenido' in campos:
            self.contenido = sanear_html(self.contenido, comentario=True)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Comentario de {self.autor.username} en {self.receta.titulo}"
    
