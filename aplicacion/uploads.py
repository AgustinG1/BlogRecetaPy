from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django_ckeditor_5 import views as editor_views

from .imagenes import validar_imagen


@require_POST
def subir_imagen_editor(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": {"message": "Inicia sesión para subir imágenes."}}, status=403)
    archivo = request.FILES.get("upload")
    if archivo is None:
        return JsonResponse({"error": {"message": "Selecciona una imagen."}}, status=400)
    try:
        validar_imagen(archivo)
    except ValidationError as error:
        return JsonResponse({"error": {"message": " ".join(error.messages)}}, status=400)
    return editor_views.upload_file(request)

