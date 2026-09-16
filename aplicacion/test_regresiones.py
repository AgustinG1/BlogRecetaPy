"""Contratos de seguridad y funcionamiento. Los fallos NO se omiten."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import Client
from django.urls import reverse

from .models import Categoria, Comentario, Receta
from .testing import MediosTemporalesTestCase, imagen_png


class RecetasComentariosTests(MediosTemporalesTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autor = get_user_model().objects.create_user(username="autor_ficticio")
        cls.otro = get_user_model().objects.create_user(username="otro_ficticio")
        cls.categoria = Categoria.objects.create(nombre="salada")
        cls.receta = Receta.objects.create(
            titulo="Receta original", subtitulo="Subtítulo", categoria=cls.categoria,
            creador=cls.autor, ingredientes="<p>Arroz</p>", instrucciones="<p>Cocinar</p>",
        )
        cls.comentario = Comentario.objects.create(
            receta=cls.receta, autor=cls.otro, contenido="Comentario existente",
        )

    def setUp(self):
        super().setUp()
        # Así un 500 se informa como respuesta incorrecta, conservando el traceback
        # en los logs, en lugar de abortar la solicitud con una excepción del cliente.
        self.client.raise_request_exception = False

    def datos_receta(self, **cambios):
        datos = {
            "titulo": "Receta actualizada", "subtitulo": "Subtítulo actualizado",
            "categoria": self.categoria.pk, "ingredientes": "<p>Arroz y sal</p>",
            "instrucciones": "<p>Cocinar lentamente</p>",
        }
        datos.update(cambios)
        return datos

    def url(self, nombre):
        return reverse(nombre, args=[self.receta.pk])

    def test_visitante_no_puede_publicar_receta(self):
        response = self.client.post(reverse("agregar_receta"), self.datos_receta())
        self.assertEqual(Receta.objects.count(), 1)
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("agregar_receta"),
            fetch_redirect_response=False,
        )

    def test_publicacion_asigna_creador_de_sesion(self):
        self.client.force_login(self.autor)
        response = self.client.post(reverse("agregar_receta"), self.datos_receta(creador=self.otro.pk))
        self.assertEqual(response.status_code, 302)
        nueva = Receta.objects.exclude(pk=self.receta.pk).get()
        self.assertEqual(nueva.creador_id, self.autor.pk)
        self.assertRedirects(response, reverse("detalle_receta", args=[nueva.pk]))

    def test_formulario_invalido_no_crea_receta(self):
        self.client.force_login(self.autor)
        response = self.client.post(reverse("agregar_receta"), self.datos_receta(titulo=""))
        self.assertEqual((response.status_code, Receta.objects.count()), (200, 1))
        self.assertIn("titulo", response.context["form"].errors)

    def test_otro_usuario_no_puede_abrir_edicion(self):
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(self.url("editar_receta")).status_code, 403)

    def test_otro_usuario_no_puede_modificar_receta(self):
        self.client.force_login(self.otro)
        response = self.client.post(self.url("editar_receta"), self.datos_receta())
        self.receta.refresh_from_db()
        self.assertEqual((response.status_code, self.receta.titulo), (403, "Receta original"))

    def test_otro_usuario_no_puede_eliminar_receta_ni_comentarios(self):
        self.client.force_login(self.otro)
        response = self.client.post(self.url("eliminar_receta"))
        self.assertEqual(
            (response.status_code, Receta.objects.count(), Comentario.objects.count()),
            (403, 1, 1),
        )

    def test_dueno_puede_editar_sin_cambiar_autor_ni_fecha(self):
        self.client.force_login(self.autor)
        fecha = self.receta.fecha_publicacion
        response = self.client.post(self.url("editar_receta"), self.datos_receta(creador=self.otro.pk))
        self.receta.refresh_from_db()
        self.assertRedirects(response, self.url("detalle_receta"))
        self.assertEqual(self.receta.titulo, "Receta actualizada")
        self.assertEqual(self.receta.creador_id, self.autor.pk)
        self.assertEqual(self.receta.fecha_publicacion, fecha)

    def test_dueno_puede_borrar_receta_y_sus_comentarios(self):
        self.client.force_login(self.autor)
        response = self.client.post(self.url("eliminar_receta"))
        self.assertRedirects(response, reverse("ver_recetas"))
        self.assertEqual((Receta.objects.count(), Comentario.objects.count()), (0, 0))

    def test_get_no_borra_receta_y_responde_405(self):
        self.client.force_login(self.autor)
        response = self.client.get(self.url("eliminar_receta"))
        self.assertEqual((response.status_code, Receta.objects.count()), (405, 1))

    def test_edicion_guarda_imagen_nueva(self):
        self.client.force_login(self.autor)
        response = self.client.post(self.url("editar_receta"), self.datos_receta(imagen=imagen_png()))
        self.receta.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.receta.imagen.name, "images/receta_default.jpg")
        self.assertTrue(self.receta.imagen.storage.exists(self.receta.imagen.name))

    def test_edicion_sin_archivo_conserva_imagen(self):
        self.client.force_login(self.autor)
        self.receta.imagen.save("anterior.png", imagen_png(), save=True)
        nombre = self.receta.imagen.name
        response = self.client.post(self.url("editar_receta"), self.datos_receta())
        self.receta.refresh_from_db()
        self.assertEqual((response.status_code, self.receta.imagen.name), (302, nombre))
        self.assertTrue(self.receta.imagen.storage.exists(nombre))

    def test_detalle_inexistente_responde_404(self):
        self.assertEqual(self.client.get(reverse("detalle_receta", args=[999999])).status_code, 404)

    def test_detalle_no_acepta_post_de_comentarios(self):
        self.client.force_login(self.autor)
        # El código actual intenta insertar sin autor: un savepoint permite
        # comprobar los datos incluso después del IntegrityError que produce.
        with transaction.atomic():
            response = self.client.post(self.url("detalle_receta"), {"contenido": "Comentario nuevo"})
        self.assertEqual((response.status_code, Comentario.objects.count()), (405, 1))

    def test_comentario_asigna_autor_de_sesion(self):
        self.client.force_login(self.autor)
        response = self.client.post(self.url("agregar_comentario"), {
            "contenido": "Nuevo comentario", "autor": self.otro.pk,
        })
        self.assertRedirects(response, self.url("detalle_receta"))
        self.assertEqual(Comentario.objects.get(contenido="Nuevo comentario").autor_id, self.autor.pk)

    def test_comentario_invalido_conserva_lista_y_muestra_error(self):
        self.client.force_login(self.autor)
        response = self.client.post(self.url("agregar_comentario"), {"contenido": ""})
        self.assertEqual((response.status_code, Comentario.objects.count()), (200, 1))
        self.assertIn("contenido", response.context["form"].errors)
        self.assertContains(response, "Comentario existente")

    def test_comentar_receta_inexistente_responde_404(self):
        self.client.force_login(self.autor)
        response = self.client.post(reverse("agregar_comentario", args=[999999]), {"contenido": "Prueba"})
        self.assertEqual((response.status_code, Comentario.objects.count()), (404, 1))

    def test_get_no_elimina_comentario(self):
        self.client.force_login(self.otro)
        response = self.client.get(reverse("eliminar_comentario", args=[self.comentario.pk]))
        self.assertEqual((response.status_code, Comentario.objects.count()), (405, 1))

    def test_dueno_de_receta_no_puede_borrar_comentario_ajeno(self):
        self.client.force_login(self.autor)
        response = self.client.post(reverse("eliminar_comentario", args=[self.comentario.pk]))
        self.assertEqual((response.status_code, Comentario.objects.count()), (403, 1))

    def test_autor_puede_borrar_su_comentario(self):
        self.client.force_login(self.otro)
        response = self.client.post(reverse("eliminar_comentario", args=[self.comentario.pk]))
        self.assertRedirects(response, self.url("detalle_receta"))
        self.assertEqual(Comentario.objects.count(), 0)

    def test_post_directo_no_guarda_ni_renderiza_script_en_comentario(self):
        self.client.force_login(self.otro)
        contenido = '<p>Comentario seguro</p><script>window.__prueba__=1</script>'
        response = self.client.post(self.url("agregar_comentario"), {"contenido": contenido})
        self.assertEqual(response.status_code, 302)
        comentario = Comentario.objects.exclude(pk=self.comentario.pk).get()
        detalle = self.client.get(self.url("detalle_receta"))
        for origen, html in (("base", comentario.contenido), ("respuesta", detalle.content.decode())):
            with self.subTest(origen=origen):
                self.assertNotIn('<script>window.__prueba__', html)
                self.assertIn("Comentario seguro", html)

    def test_post_directo_sanitiza_html_de_receta(self):
        self.client.force_login(self.autor)
        response = self.client.post(self.url("editar_receta"), self.datos_receta(
            ingredientes='<p>Arroz</p><img src="x" onerror="window.__prueba__=1">',
            instrucciones='<p>Cocinar</p><a href="javascript:alert(1)">Enlace</a>',
        ))
        self.assertEqual(response.status_code, 302)
        self.receta.refresh_from_db()
        detalle = self.client.get(self.url("detalle_receta")).content.decode()
        for origen, html in (("ingredientes", self.receta.ingredientes),
                             ("instrucciones", self.receta.instrucciones), ("respuesta", detalle)):
            with self.subTest(origen=origen):
                self.assertNotIn("onerror=", html.lower())
                self.assertNotIn("javascript:", html.lower())

    def test_borrado_sin_csrf_es_rechazado(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.autor)
        response = cliente.post(self.url("eliminar_receta"))
        self.assertEqual((response.status_code, Receta.objects.count()), (403, 1))

    def test_borrado_con_csrf_y_propiedad_es_aceptado(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.autor)
        cliente.get(self.url("detalle_receta"))
        response = cliente.post(self.url("eliminar_receta"), {
            "csrfmiddlewaretoken": cliente.cookies["csrftoken"].value,
        })
        self.assertEqual((response.status_code, Receta.objects.count()), (302, 0))

    def test_editor_rechaza_upload_anonimo_incluso_con_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.get(reverse("login"))
        # Simula únicamente el almacenamiento externo; permisos, CSRF y validación
        # del endpoint siguen siendo reales. No se sube nada a Cloudinary.
        with patch("django_ckeditor_5.views.handle_uploaded_file", return_value="/images/simulada.png") as guardar:
            response = cliente.post(reverse("ck_editor_5_upload_file"), {
                "upload": imagen_png(), "csrfmiddlewaretoken": cliente.cookies["csrftoken"].value,
            })
        self.assertEqual((response.status_code, guardar.called), (403, False))
