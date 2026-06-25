from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Receta, Comentario, Categoria

class AgregarComentarioViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        # Crear una categoría para asociarla a la receta
        self.categoria = Categoria.objects.create(nombre='Categoría de prueba')
        self.recipe = Receta.objects.create(titulo='Receta de prueba', categoria=self.categoria)


    def test_vista_requiere_inicio_sesion(self):
        url = reverse('agregar_comentario', kwargs={'receta_id': self.recipe.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Debería redirigir a la página de inicio de sesión

    def test_agregar_comentario(self):
        self.client.login(username='testuser', password='password')
        url = reverse('agregar_comentario', kwargs={'receta_id': self.recipe.id})
        data = {'contenido': '¡Este es un comentario de prueba!'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Debería redirigir después de agregar el comentario

        # Verificar si el comentario se agregó correctamente a la base de datos
        comentario_agregado = Comentario.objects.get(autor=self.user, receta=self.recipe)
        self.assertEqual(comentario_agregado.contenido, '¡Este es un comentario de prueba!')
        
class DetalleRecetaViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        # Crear una categoría para asociar a la receta
        self.categoria = Categoria.objects.create(nombre='Categoria de prueba')

        # Crear una receta y asociarla a la categoría creada
        self.recipe = Receta.objects.create(titulo='Receta de prueba', categoria=self.categoria)