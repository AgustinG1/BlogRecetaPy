from django.shortcuts import render, redirect, get_object_or_404
from .models import Categoria, Receta
from .forms import RecetaForm, ComentarioForm
from django.contrib.auth.decorators import login_required
from .models import Comentario
from django.core.exceptions import PermissionDenied



# Create your views here.

def pagina_inicio(request):
    return render(request, 'inicio.html')



@login_required
def agregar_receta(request):
    if request.method == 'POST':
        form = RecetaForm(request.POST, request.FILES)
        if form.is_valid():
            nueva_receta = form.save(commit=False)
            nueva_receta.creador = request.user
            nueva_receta.imagen = form.cleaned_data['imagen']
            nueva_receta.save()
            return redirect('detalle_receta', receta_id=nueva_receta.id)
    else:
        form = RecetaForm()

    return render(request, 'agregar_receta.html', {'form': form})


def detalle_receta(request, receta_id):
    receta = Receta.objects.get(pk=receta_id)

    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            nuevo_comentario = form.save(commit=False)
            nuevo_comentario.receta = receta
            nuevo_comentario.save()
            return redirect('detalle_receta', receta_id=receta.id)

    else:
        form = ComentarioForm()

    comentarios = receta.comentario_set.all()
    
    return render(request, 'detalle_receta.html', {'receta': receta, 'comentarios': comentarios, 'form': form})

def ver_recetas(request):
    query = request.GET.get('q', '')  
    recetas = Receta.objects.filter(titulo__icontains=query) if query else Receta.objects.all()
    return render(request, 'recetas.html', {'recetas': recetas, 'query': query})

@login_required
def eliminar_receta(request, receta_id):
    receta = get_object_or_404(Receta, pk=receta_id)

    if request.method == 'POST':
        receta.delete()
        return redirect('ver_recetas')  

    return render(request, 'eliminar_receta.html', {'receta': receta})

@login_required
def editar_receta(request, receta_id):
    receta = get_object_or_404(Receta, pk=receta_id)
    
    if request.method == 'POST':
        form = RecetaForm(request.POST, instance=receta)
        if form.is_valid():
            form.save()
            return redirect('detalle_receta', receta_id=receta.id)
    else:
        form = RecetaForm(instance=receta)
    
    return render(request, 'agregar_receta.html', {'form': form, 'edit_mode': True, 'receta': receta})

@login_required
def agregar_comentario(request, receta_id):
    receta = Receta.objects.get(id=receta_id)

    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.receta = receta
            comentario.autor = request.user
            comentario.save()
            return redirect('detalle_receta', receta_id=receta_id)
    else:
        form = ComentarioForm()

    return render(request, 'detalle_receta.html', {'form': form, 'receta': receta})

def about(request):
    return render(request, 'about.html')


def eliminar_comentario(request, comentario_id):
    comentario = get_object_or_404(Comentario, id=comentario_id)
    
    # Verificar si el usuario actual es el autor del comentario
    if request.user == comentario.autor:
        # Si el usuario actual es el autor, eliminar el comentario
        comentario.delete()
        # Redirigir a la página de detalle de la receta o a donde sea apropiado
        return redirect('detalle_receta', receta_id=comentario.receta.id)
    else:
        # Manejar el caso en que el usuario no esté autorizado para eliminar el comentario
        # Puedes mostrar un mensaje de error o redirigir a otra página
        # Por ejemplo, podrías lanzar una excepción de permisos insuficientes
        raise PermissionDenied("No tienes permiso para eliminar este comentario")