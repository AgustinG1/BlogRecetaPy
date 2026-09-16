from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from aplicacion.contenido import sanear_html

register = template.Library()


@register.filter
def receta_html(valor):
    return mark_safe(sanear_html(valor))


@register.filter
def comentario_html(valor):
    return mark_safe(sanear_html(valor, comentario=True))


@register.filter
def imagen_receta(imagen):
    if not imagen or imagen.name == 'images/receta_default.jpg':
        return static('images/receta_default.jpg')
    return imagen.url
