"""Datos ficticios y medios desechables para las pruebas del proyecto."""

from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image


def imagen_png(nombre="prueba.png", color="blue"):
    contenido = BytesIO()
    Image.new("RGB", (3, 3), color).save(contenido, format="PNG")
    return SimpleUploadedFile(nombre, contenido.getvalue(), content_type="image/png")


class MediosTemporalesTestCase(TestCase):
    def setUp(self):
        super().setUp()
        directorio = TemporaryDirectory(prefix="blogrecetapy-tests-")
        self.addCleanup(directorio.cleanup)
        configuracion = override_settings(
            MEDIA_ROOT=directorio.name,
            DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",
        )
        configuracion.enable()
        self.addCleanup(configuracion.disable)

