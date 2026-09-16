"""Verifica la política nueva y vías que evitan los formularios públicos."""

from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse
from PIL import Image

from .admin import ComentarioAdminForm, RecetaAdminForm
from .contenido import sanear_html, validar_contenido
from .imagenes import MAX_BYTES, validar_imagen
from .models import Categoria, Comentario, Receta
from .testing import MediosTemporalesTestCase, imagen_png


class SanitizacionTests(SimpleTestCase):
    def test_elimina_eventos_protocolos_y_contenido_activo(self):
        for html in (
            '<p onclick="alert(1)">Texto</p>',
            '<a href="jav&#x61;script:alert(1)">Texto</a>',
            '<a href="java\nscript:alert(1)">Texto</a>',
            '<svg><script>alert(1)</script></svg><p>Texto</p>',
            '<math><mtext><img src=x onerror=alert(1)></mtext></math><p>Texto</p>',
            '<iframe srcdoc="<script>alert(1)</script>"></iframe><p>Texto</p>',
        ):
            with self.subTest(html=html):
                limpio = sanear_html(html)
                self.assertIn('Texto', limpio)
                for fragmento in ('onclick', 'onerror', 'javascript:', 'alert(1)', '<svg', '<math', '<iframe'):
                    self.assertNotIn(fragmento, limpio.lower())

    def test_saneado_es_idempotente_y_conserva_enlace_y_formato(self):
        limpio = sanear_html('<p><strong>Texto</strong><a href="https://example.org/">Referencia</a></p>')
        self.assertEqual(sanear_html(limpio), limpio)
        self.assertIn('<strong>Texto</strong>', limpio)
        self.assertIn('href="https://example.org/"', limpio)

    @override_settings(MEDIA_URL='/images/', HTML_IMAGE_URL_PREFIXES=['https://res.cloudinary.com/propio/'])
    def test_imagenes_solo_desde_medios_permitidos(self):
        for url in ('/images/foto.png', 'https://res.cloudinary.com/propio/image/upload/foto.png'):
            with self.subTest(url=url):
                self.assertIn('src=', sanear_html(f'<img src="{url}" alt="Foto">'))
        for url in ('https://otro.example/foto.png', '//otro.example/foto.png',
                    '/images/../admin/', '/images/%2e%2e/admin/',
                    'https://res.cloudinary.com/otro/foto.png',
                    'https://res.cloudinary.com/propio/../otro/foto.png',
                    'data:image/svg+xml;base64,AAAA', 'http://res.cloudinary.com/propio/foto.png'):
            with self.subTest(url=url):
                self.assertNotIn('src=', sanear_html(f'<img src="{url}" alt="Foto">'))

    def test_comentarios_no_admiten_imagenes_ni_estilos(self):
        limpio = sanear_html('<p style="color:red">Texto</p><img src="/images/foto.png">', comentario=True)
        self.assertEqual(limpio, '<p>Texto</p>')

    def test_limites_y_vacio_despues_de_sanear(self):
        for valor, comentario in (('a' * 5001, True), ('a' * 50001, False),
                                   ('<script>texto</script>', True), ('<p>\u200b</p>', False)):
            with self.subTest(comentario=comentario, longitud=len(valor)):
                with self.assertRaises(ValidationError):
                    validar_contenido(valor, comentario=comentario)

    def test_imagen_valida_y_falsa_extension(self):
        archivo = imagen_png()
        self.assertIs(validar_imagen(archivo), archivo)
        self.assertEqual(archivo.tell(), 0)
        for falso in (SimpleUploadedFile('foto.jpg', b'<script>invalido</script>'), imagen_png('foto.svg')):
            with self.subTest(nombre=falso.name):
                with self.assertRaises(ValidationError):
                    validar_imagen(falso)

    def test_imagen_supera_limite_de_bytes(self):
        with self.assertRaises(ValidationError):
            validar_imagen(SimpleUploadedFile('grande.png', b'x' * (MAX_BYTES + 1)))

    def test_imagen_supera_dimensiones(self):
        contenido = BytesIO()
        Image.new('RGB', (4097, 1)).save(contenido, format='PNG')
        with self.assertRaises(ValidationError):
            validar_imagen(SimpleUploadedFile('ancha.png', contenido.getvalue()))


class ProteccionIntegradaTests(MediosTemporalesTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(username='seguridad_prueba')
        cls.categoria = Categoria.objects.create(nombre='salada')
        cls.receta = Receta.objects.create(
            titulo='Receta segura', subtitulo='Ejemplo', categoria=cls.categoria, creador=cls.usuario,
            ingredientes='<p>Arroz</p>', instrucciones='<p>Cocinar</p>',
        )

    def test_guardado_directo_del_modelo_sanea_html(self):
        self.receta.ingredientes = '<p>Arroz</p><script>peligro()</script>'
        self.receta.save(update_fields=['ingredientes'])
        comentario = Comentario.objects.create(
            receta=self.receta, autor=self.usuario, contenido='<p>Bien</p><script>peligro()</script>',
        )
        self.receta.refresh_from_db()
        self.assertEqual(self.receta.ingredientes, '<p>Arroz</p>')
        self.assertEqual(comentario.contenido, '<p>Bien</p>')

    def test_imagen_por_defecto_se_sirve_desde_estaticos(self):
        for url in (reverse('inicio'), reverse('ver_recetas'), reverse('detalle_receta', args=[self.receta.pk])):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'src="/static/images/receta_default.jpg"')
                self.assertNotContains(response, '/images/images/receta_default.jpg')

    def test_contenido_antiguo_se_sanea_al_renderizar(self):
        # update() evita save(): simula registros previos al arreglo.
        Receta.objects.filter(pk=self.receta.pk).update(ingredientes='<p>Arroz</p><script>peligro()</script>')
        comentario = Comentario.objects.create(receta=self.receta, autor=self.usuario, contenido='Bien')
        Comentario.objects.filter(pk=comentario.pk).update(contenido='<p>Bien</p><img src=x onerror=peligro()>')
        response = self.client.get(reverse('detalle_receta', args=[self.receta.pk]))
        self.assertContains(response, '<p>Arroz</p>')
        self.assertContains(response, '<p>Bien</p>')
        self.assertNotContains(response, 'peligro()')
        self.assertNotContains(response, 'onerror=')

    def test_admin_conserva_relaciones_y_valida_contenido(self):
        form = ComentarioAdminForm(data={
            'receta': self.receta.pk, 'autor': self.usuario.pk,
            'contenido': '<p>Bien</p><script>peligro()</script>',
        })
        self.assertTrue(form.is_valid(), form.errors)
        comentario = form.save()
        self.assertEqual((comentario.receta_id, comentario.autor_id), (self.receta.pk, self.usuario.pk))
        self.assertEqual(comentario.contenido, '<p>Bien</p>')
        self.assertIn('creador', RecetaAdminForm().fields)

    def test_imagen_invalida_no_modifica_receta(self):
        self.client.force_login(self.usuario)
        response = self.client.post(reverse('editar_receta', args=[self.receta.pk]), {
            'titulo': 'Cambio que no debe guardarse', 'subtitulo': 'Subtítulo', 'categoria': self.categoria.pk,
            'ingredientes': '<p>Arroz</p>', 'instrucciones': '<p>Cocinar</p>',
            'imagen': SimpleUploadedFile('foto.png', b'no-es-imagen'),
        })
        self.receta.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertIn('imagen', response.context['form'].errors)
        self.assertEqual(self.receta.titulo, 'Receta segura')

    def test_editor_autenticado_sube_imagen_valida(self):
        self.client.force_login(self.usuario)
        response = self.client.post(reverse('ck_editor_5_upload_file'), {'upload': imagen_png()})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['url'].startswith('/images/'))

    def test_editor_rechaza_archivo_ausente_o_invalido(self):
        self.client.force_login(self.usuario)
        for datos in ({}, {'upload': SimpleUploadedFile('foto.png', b'invalido')}):
            with self.subTest(datos=list(datos)):
                with patch('django_ckeditor_5.views.handle_uploaded_file') as guardar:
                    response = self.client.post(reverse('ck_editor_5_upload_file'), datos)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(guardar.called)

    def test_logout_en_interfaz_es_post_y_exige_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        response = cliente.get(reverse('inicio'))
        self.assertContains(response, f'method="post" action="{reverse("logout")}"')
        self.assertNotContains(response, f'href="{reverse("logout")}"')
        self.assertEqual(cliente.post(reverse('logout')).status_code, 403)
        self.assertIn('_auth_user_id', cliente.session)
        cliente.post(reverse('logout'), {'csrfmiddlewaretoken': cliente.cookies['csrftoken'].value})
        self.assertNotIn('_auth_user_id', cliente.session)
