from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from .forms import ComentarioForm, RecetaForm
from .models import Comentario, Receta


def _receta_del_autor(receta_id, usuario):
    receta = get_object_or_404(Receta, pk=receta_id)
    if receta.creador_id != usuario.pk:
        raise PermissionDenied("No tienes permiso para modificar esta receta.")
    return receta


def _contexto_detalle(receta, form=None):
    return {
        "receta": receta,
        "comentarios": receta.comentario_set.select_related("autor").order_by("fecha_creacion", "pk"),
        "form": form if form is not None else ComentarioForm(),
    }


@require_safe
def pagina_inicio(request):
    recetas_destacadas = (
        Receta.objects.select_related("categoria")
        .order_by("-fecha_publicacion", "-pk")[:6]
    )
    return render(request, "inicio.html", {"recetas_destacadas": recetas_destacadas})


@login_required
@require_http_methods(["GET", "POST"])
def agregar_receta(request):
    form = RecetaForm(request.POST, request.FILES) if request.method == "POST" else RecetaForm()
    if request.method == "POST" and form.is_valid():
        receta = form.save(commit=False)
        receta.creador = request.user
        receta.save()
        messages.success(request, "Tu receta fue publicada.")
        return redirect("detalle_receta", receta_id=receta.pk)
    return render(request, "agregar_receta.html", {"form": form})


@require_safe
def detalle_receta(request, receta_id):
    receta = get_object_or_404(Receta.objects.select_related("categoria", "creador"), pk=receta_id)
    return render(request, "detalle_receta.html", _contexto_detalle(receta))


@require_safe
def ver_recetas(request):
    query = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "")
    recetas = Receta.objects.select_related("categoria", "creador").order_by("-fecha_publicacion", "-pk")
    if query:
        recetas = recetas.filter(titulo__icontains=query)
    if categoria:
        recetas = recetas.filter(categoria__nombre=categoria)
    return render(request, "recetas.html", {
        "recetas": recetas, "query": query, "categoria_activa": categoria,
    })


@login_required
@require_POST
def eliminar_receta(request, receta_id):
    receta = _receta_del_autor(receta_id, request.user)
    receta.delete()
    messages.success(request, "La receta fue eliminada.")
    return redirect("ver_recetas")


@login_required
@require_http_methods(["GET", "POST"])
def editar_receta(request, receta_id):
    receta = _receta_del_autor(receta_id, request.user)
    form = (
        RecetaForm(request.POST, request.FILES, instance=receta)
        if request.method == "POST" else RecetaForm(instance=receta)
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Los cambios fueron guardados.")
        return redirect("detalle_receta", receta_id=receta.pk)
    return render(request, "agregar_receta.html", {"form": form, "edit_mode": True, "receta": receta})


@login_required
@require_POST
def agregar_comentario(request, receta_id):
    receta = get_object_or_404(Receta.objects.select_related("categoria", "creador"), pk=receta_id)
    form = ComentarioForm(request.POST)
    if form.is_valid():
        comentario = form.save(commit=False)
        comentario.receta = receta
        comentario.autor = request.user
        comentario.save()
        messages.success(request, "Tu comentario fue publicado.")
        return redirect("detalle_receta", receta_id=receta.pk)
    return render(request, "detalle_receta.html", _contexto_detalle(receta, form))


@require_safe
def about(request):
    return render(request, "about.html")


@login_required
@require_POST
def eliminar_comentario(request, comentario_id):
    comentario = get_object_or_404(Comentario, pk=comentario_id)
    if comentario.autor_id != request.user.pk:
        raise PermissionDenied("No tienes permiso para eliminar este comentario.")
    receta_id = comentario.receta_id
    comentario.delete()
    messages.success(request, "El comentario fue eliminado.")
    return redirect("detalle_receta", receta_id=receta_id)
