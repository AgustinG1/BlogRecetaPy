"""Contratos de autenticación y edición exclusiva de datos propios."""

from django.contrib.auth import SESSION_KEY, get_user_model
from django.urls import reverse

from aplicacion.testing import MediosTemporalesTestCase, imagen_png
from .models import Avatar


class CuentaPerfilTests(MediosTemporalesTestCase):
    clave = "Clave-ficticia-solo-tests-982!"

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(username="cuenta_prueba", password=cls.clave)
        cls.otro = get_user_model().objects.create_user(username="otra_cuenta", first_name="Original")

    def setUp(self):
        super().setUp()
        self.client.raise_request_exception = False

    def login(self, destino):
        return self.client.post(reverse("login") + "?next=" + destino, {
            "username": self.usuario.username, "password": self.clave,
        })

    def test_login_valido_retorna_a_destino_interno(self):
        response = self.login(reverse("ver_recetas"))
        self.assertRedirects(response, reverse("ver_recetas"))
        self.assertEqual(self.client.session[SESSION_KEY], str(self.usuario.pk))

    def test_login_no_redirige_a_dominio_externo(self):
        response = self.login("https://example.org/destino")
        self.assertRedirects(response, reverse("inicio"), fetch_redirect_response=False)

    def test_login_no_acepta_destino_externo_sin_esquema(self):
        response = self.login("//example.org/destino")
        self.assertRedirects(response, reverse("inicio"), fetch_redirect_response=False)

    def test_login_invalido_no_crea_sesion(self):
        response = self.client.post(reverse("login"), {
            "username": self.usuario.username, "password": "incorrecta",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_get_logout_no_cierra_sesion(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse("logout"))
        self.assertEqual((response.status_code, SESSION_KEY in self.client.session), (405, True))

    def test_post_logout_cierra_sesion(self):
        self.client.force_login(self.usuario)
        response = self.client.post(reverse("logout"))
        self.assertIn(response.status_code, (200, 302))
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_registro_valido_guarda_hash_y_dirige_a_login(self):
        response = self.client.post(reverse("registro"), {
            "username": "nueva_cuenta", "first_name": "Prueba", "last_name": "Ficticia",
            "email": "ficticia@example.org", "password1": self.clave, "password2": self.clave,
        })
        nuevo = get_user_model().objects.get(username="nueva_cuenta")
        self.assertTrue(nuevo.check_password(self.clave))
        self.assertNotEqual(nuevo.password, self.clave)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_registro_con_passwords_distintas_no_crea_cuenta(self):
        response = self.client.post(reverse("registro"), {
            "username": "nueva_cuenta", "password1": self.clave, "password2": "Otra-982!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(get_user_model().objects.filter(username="nueva_cuenta").exists())

    def test_perfil_solo_modifica_campos_y_usuario_permitidos(self):
        self.client.force_login(self.usuario)
        response = self.client.post(reverse("editar_perfil"), {
            "first_name": "Actualizado", "last_name": "Prueba", "email": "prueba@example.org",
            "id": self.otro.pk, "is_staff": "on", "is_superuser": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.usuario.refresh_from_db()
        self.otro.refresh_from_db()
        self.assertEqual(self.usuario.first_name, "Actualizado")
        self.assertFalse(self.usuario.is_staff)
        self.assertFalse(self.usuario.is_superuser)
        self.assertEqual(self.otro.first_name, "Original")

    def test_visitante_es_redirigido_al_login_para_editar_perfil(self):
        response = self.client.get(reverse("editar_perfil"))
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("editar_perfil"))

    def test_visitante_no_puede_abrir_formulario_avatar(self):
        response = self.client.get(reverse("agregar_avatar"))
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("agregar_avatar"))

    def test_visitante_no_puede_guardar_avatar(self):
        response = self.client.post(reverse("agregar_avatar"), {"imagen": imagen_png()})
        self.assertEqual((response.status_code, Avatar.objects.count()), (302, 0))
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("agregar_avatar"))

    def test_reemplazar_avatar_mantiene_un_registro_y_usuario_de_sesion(self):
        self.client.force_login(self.usuario)
        for nombre, color in (("primera.png", "red"), ("segunda.png", "blue")):
            response = self.client.post(reverse("agregar_avatar"), {
                "imagen": imagen_png(nombre, color), "user": self.otro.pk,
            })
            self.assertEqual(response.status_code, 302)
        avatar = Avatar.objects.get()
        self.assertEqual(avatar.user_id, self.usuario.pk)
        self.assertTrue(avatar.imagen.name.endswith("segunda.png"))
        self.assertTrue(avatar.imagen.storage.exists(avatar.imagen.name))

