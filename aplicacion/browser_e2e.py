"""Recorrido de navegador de los flujos públicos principales."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from .models import Categoria


class FlujoPrincipalNavegadorTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls._directorio_medios = TemporaryDirectory(prefix="blogrecetapy-browser-")
        cls._configuracion_medios = override_settings(MEDIA_ROOT=cls._directorio_medios.name)
        cls._configuracion_medios.enable()
        super().setUpClass()

        opciones = webdriver.ChromeOptions()
        opciones.add_argument("--headless=new")
        opciones.add_argument("--no-sandbox")
        opciones.add_argument("--disable-dev-shm-usage")
        opciones.add_argument("--window-size=1440,1200")
        opciones.page_load_strategy = "eager"
        ejecutable = os.environ.get("CHROME_BIN")
        if ejecutable:
            opciones.binary_location = ejecutable
        cls.browser = webdriver.Chrome(options=opciones)
        cls.browser.set_page_load_timeout(20)
        cls.espera = WebDriverWait(cls.browser, 15)

        cls.ruta_imagen = Path(cls._directorio_medios.name) / "receta-prueba.png"
        Image.new("RGB", (20, 20), "orange").save(cls.ruta_imagen, format="PNG")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "browser"):
            cls.browser.quit()
        super().tearDownClass()
        cls._configuracion_medios.disable()
        cls._directorio_medios.cleanup()

    def abrir(self, ruta):
        self.browser.get(f"{self.live_server_url}{ruta}")

    def completar(self, nombre, valor):
        campo = self.browser.find_element(By.NAME, nombre)
        campo.clear()
        campo.send_keys(valor)

    def enviar_formulario(self):
        boton = self.browser.find_element(
            By.CSS_SELECTOR,
            "form.site-form button[type='submit']",
        )
        self.browser.execute_script("arguments[0].click();", boton)

    def escribir_en_editores(self, textos):
        editores = self.espera.until(
            lambda navegador: navegador.find_elements(
                By.CSS_SELECTOR, ".ck-editor__editable[contenteditable='true']"
            )
        )
        self.assertEqual(len(editores), len(textos))
        for editor, texto in zip(editores, textos):
            self.browser.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                editor,
            )
            editor.send_keys(texto)

    def test_registro_login_receta_comentario_portada_y_eliminacion(self):
        categoria = Categoria.objects.create(nombre="salada")

        self.abrir("/perfiles/registro/")
        self.completar("last_name", "Navegador")
        self.completar("first_name", "Prueba")
        self.completar("username", "usuario_navegador")
        self.completar("email", "navegador@example.com")
        self.completar("password1", "PruebaNavegador!2026")
        self.completar("password2", "PruebaNavegador!2026")
        self.enviar_formulario()
        self.espera.until(EC.url_contains("/perfiles/login/"))
        self.assertIn("Tu cuenta fue creada", self.browser.page_source)

        self.completar("username", "usuario_navegador")
        self.completar("password", "PruebaNavegador!2026")
        self.enviar_formulario()
        self.espera.until(EC.presence_of_element_located((By.ID, "hero-title")))
        self.assertIn("Bienvenido, usuario_navegador", self.browser.page_source)

        self.abrir("/agregar_receta/")
        self.completar("titulo", "Receta desde navegador")
        self.completar("subtitulo", "Flujo automático completo")
        Select(self.browser.find_element(By.NAME, "categoria")).select_by_value(str(categoria.pk))
        self.escribir_en_editores(["Harina, agua y sal", "Mezclar y cocinar"])
        self.browser.find_element(By.NAME, "imagen").send_keys(str(self.ruta_imagen))
        self.enviar_formulario()
        self.espera.until(EC.presence_of_element_located((By.ID, "recipe-title")))
        self.assertEqual(
            self.browser.find_element(By.ID, "recipe-title").text,
            "Receta desde navegador",
        )

        self.browser.find_element(By.LINK_TEXT, "Editar receta").click()
        self.completar("titulo", "Receta editada desde navegador")
        self.enviar_formulario()
        self.espera.until(EC.presence_of_element_located((By.ID, "recipe-title")))
        self.assertEqual(
            self.browser.find_element(By.ID, "recipe-title").text,
            "Receta editada desde navegador",
        )

        self.escribir_en_editores(["Comentario creado por el navegador"])
        self.enviar_formulario()
        self.espera.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".comments-list"),
                "Comentario creado por el navegador",
            )
        )

        self.abrir("/")
        self.espera.until(EC.presence_of_element_located((By.ID, "hero-title")))
        self.assertIn("Receta editada desde navegador", self.browser.page_source)

        enlace_detalle = self.browser.find_element(
            By.XPATH,
            "//h3[normalize-space()='Receta editada desde navegador']/following::a[1]",
        )
        self.browser.execute_script("arguments[0].click();", enlace_detalle)
        boton_eliminar = self.browser.find_element(
            By.CSS_SELECTOR,
            "form[action*='/eliminar_receta/'] button[type='submit']",
        )
        self.browser.execute_script("arguments[0].click();", boton_eliminar)
        self.espera.until(EC.alert_is_present()).accept()
        self.espera.until(EC.url_contains("/recetas/"))
        self.assertNotIn("Receta editada desde navegador", self.browser.page_source)
