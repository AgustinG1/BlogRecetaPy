"""Contratos unitarios de contenido, sin base ni navegador (U-01/U-02)."""

from django.test import SimpleTestCase

from .forms import ComentarioForm


class ContenidoComentarioTests(SimpleTestCase):
    def test_rechaza_texto_vacio(self):
        for contenido in ("", "   ", "\n\t"):
            with self.subTest(contenido=repr(contenido)):
                form = ComentarioForm(data={"contenido": contenido})
                self.assertFalse(form.is_valid())
                self.assertIn("contenido", form.errors)

    def test_rechaza_html_sin_texto_util(self):
        for contenido in ("<p>&nbsp;</p>", "<p><br></p>"):
            with self.subTest(contenido=contenido):
                form = ComentarioForm(data={"contenido": contenido})
                self.assertFalse(form.is_valid())
                self.assertIn("contenido", form.errors)

    def test_conserva_texto_y_formato_permitidos(self):
        form = ComentarioForm(data={"contenido": "<p>Muy <strong>rica</strong>.</p>"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn("<strong>rica</strong>", form.cleaned_data["contenido"])

    def test_elimina_script_conservando_el_comentario(self):
        form = ComentarioForm(data={
            "contenido": "<p>Comentario válido</p><script>window.__prueba__=1</script>"
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn("Comentario válido", form.cleaned_data["contenido"])
        self.assertNotIn("<script", form.cleaned_data["contenido"].lower())

