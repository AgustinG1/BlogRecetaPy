"""Validación común para imágenes de recetas, avatares y editor."""

import warnings
from pathlib import Path

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

MAX_BYTES = 5 * 1024 * 1024
MAX_DIMENSION = 4096
FORMATOS = {"JPEG": {".jpg", ".jpeg"}, "PNG": {".png"}, "WEBP": {".webp"}}


def validar_imagen(archivo):
    if archivo.size > MAX_BYTES:
        raise ValidationError("La imagen no puede superar 5 MiB.")
    try:
        archivo.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(archivo) as imagen:
                if imagen.format not in FORMATOS or Path(archivo.name).suffix.lower() not in FORMATOS[imagen.format]:
                    raise ValidationError("Selecciona una imagen JPEG, PNG o WebP con extensión correcta.")
                if max(imagen.size) > MAX_DIMENSION:
                    raise ValidationError("La imagen no puede superar 4096 píxeles de ancho o alto.")
                imagen.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValidationError("El archivo no es una imagen válida.")
    finally:
        archivo.seek(0)
    return archivo

