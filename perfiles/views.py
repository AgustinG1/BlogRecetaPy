
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LogoutView
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from .models import Avatar


from perfiles.forms import UserRegisterForm, UserUpdateForm, AvatarFormulario


def registro(request):
    if request.method == "POST":
       
        formulario = UserRegisterForm(request.POST)

        if formulario.is_valid():
            formulario.save() 
            url_exitosa = reverse('inicio')
            return redirect(url_exitosa)
    else:  # GET
       
        formulario = UserRegisterForm()
    return render(
        request=request,
        template_name='perfiles/registro.html',
        context={'form': formulario},
    )


def login_view(request):
    next_url = request.GET.get('next')
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            data = form.cleaned_data  
            usuario = data.get('username')
            password = data.get('password')
            user = authenticate(username=usuario, password=password)
            
            if user: 
                login(request=request, user=user) 
                if next_url:
                    return redirect(next_url)
                url_exitosa = reverse('inicio')
                return redirect(url_exitosa)
    else: 
        form = AuthenticationForm()
    return render(
        request=request,
        template_name='perfiles/login.html',
        context={'form': form},
    )


class CustomLogoutView(LogoutView):
    template_name = 'perfiles/logout.html'


class MiPerfilUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserUpdateForm
    success_url = reverse_lazy('inicio')
    template_name = 'perfiles/formulario_perfil.html'

    def get_object(self, queryset=None):
        return self.request.user



def agregar_avatar(request):
    if request.method == "POST":
        formulario = AvatarFormulario(request.POST, request.FILES)
        if formulario.is_valid():
            # Verificar si el usuario ya tiene un avatar
            avatar_existente = Avatar.objects.filter(user=request.user).first()
            if avatar_existente:
                # Si el usuario ya tiene un avatar, actualiza los detalles en lugar de crear uno nuevo
                avatar_existente.imagen = formulario.cleaned_data['imagen']
                avatar_existente.save()
            else:
                # Si el usuario no tiene un avatar, crea uno nuevo
                avatar = formulario.save(commit=False)
                avatar.user = request.user
                avatar.save()

            url_exitosa = reverse('inicio')
            return redirect(url_exitosa)
    else:  
        formulario = AvatarFormulario()
    return render(
        request=request,
        template_name="perfiles/formulario_avatar.html",
        context={'form': formulario},
    )

