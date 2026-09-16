"""Política común de HTML para formularios, modelos y salida de contenido antiguo."""

from html import unescape
from posixpath import normpath
from urllib.parse import unquote, urlsplit

import nh3
from django.conf import settings
from django.core.exceptions import ValidationError


ETIQUETAS_COMENTARIO = {"p", "br", "strong", "em", "b", "i", "ul", "ol", "li", "a"}
ETIQUETAS_RECETA = ETIQUETAS_COMENTARIO | {"h2", "h3", "blockquote", "figure", "figcaption", "img"}
CONTENIDO_PROHIBIDO = {"script", "style", "iframe", "object", "embed", "svg", "math"}


def _imagen_permitida(valor):
    # Rechaza ambigüedades que los navegadores normalizan al resolver una URL.
    if any(ord(c) <= 32 for c in valor) or "\\" in valor:
        return False
    try:
        url = urlsplit(valor)
        ruta = normpath(unquote(url.path))
        prefijos = [settings.MEDIA_URL, *getattr(settings, "HTML_IMAGE_URL_PREFIXES", [])]
        for prefijo in prefijos:
            base = urlsplit(prefijo)
            if url.username or url.password:
                continue
            if base.scheme:
                if url.scheme != "https" or url.netloc.lower() != base.netloc.lower():
                    continue
            elif url.scheme or url.netloc or not valor.startswith("/") or valor.startswith("//"):
                continue
            raiz = normpath(unquote(base.path)).rstrip("/") + "/"
            if raiz != "/" and ruta.startswith(raiz):
                return True
    except ValueError:
        return False
    return False


def _atributo_seguro(etiqueta, atributo, valor):
    if etiqueta == "img" and atributo == "src" and not _imagen_permitida(valor):
        return None
    return valor


def sanear_html(valor, *, comentario=False):
    atributos = {"a": {"href", "title"}}
    if not comentario:
        atributos["img"] = {"src", "alt"}
    return nh3.clean(
        valor or "",
        tags=ETIQUETAS_COMENTARIO if comentario else ETIQUETAS_RECETA,
        attributes=atributos,
        attribute_filter=_atributo_seguro,
        clean_content_tags=CONTENIDO_PROHIBIDO,
        allowed_classes={} if comentario else {"figure": {"image"}},
        url_schemes={"http", "https"},
        link_rel="noopener noreferrer nofollow",
        strip_comments=True,
    )


def validar_contenido(valor, *, comentario=False):
    limite = 5000 if comentario else 50000
    if len(valor) > limite:
        raise ValidationError(f"El contenido no puede superar {limite} caracteres.")
    limpio = sanear_html(valor, comentario=comentario)
    if len(limpio) > limite:
        raise ValidationError(f"El contenido no puede superar {limite} caracteres.")
    texto = unescape(nh3.clean(limpio, tags=set(), attributes={}, link_rel=None))
    if not texto.replace("\u200b", "").replace("\ufeff", "").strip():
        raise ValidationError("Escribe contenido; el campo no puede quedar vacío.")
    return limpio

