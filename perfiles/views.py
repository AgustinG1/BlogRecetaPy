from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods
from django.views.generic import UpdateView

from .forms import AvatarFormulario, UserRegisterForm, UserUpdateForm
from .models import Avatar


@require_http_methods(["GET", "POST"])
def registro(request):
    form = UserRegisterForm(request.POST) if request.method == "POST" else UserRegisterForm()
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tu cuenta fue creada. Ahora puedes iniciar sesión.")
        return redirect("login")
    return render(request, "perfiles/registro.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    next_url = request.POST.get("next", request.GET.get("next", ""))
    form = AuthenticationForm(request, data=request.POST) if request.method == "POST" else AuthenticationForm(request)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        if url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect("inicio")
    return render(request, "perfiles/login.html", {"form": form, "next": next_url})


class CustomLogoutView(LogoutView):
    http_method_names = ["post", "options"]
    template_name = "perfiles/logout.html"


class MiPerfilUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserUpdateForm
    success_url = reverse_lazy("inicio")
    template_name = "perfiles/formulario_perfil.html"

    def get_object(self, queryset=None):
        return self.request.user


@login_required
@require_http_methods(["GET", "POST"])
def agregar_avatar(request):
    avatar = Avatar.objects.filter(user=request.user).first()
    form = (
        AvatarFormulario(request.POST, request.FILES, instance=avatar)
        if request.method == "POST" else AvatarFormulario(instance=avatar)
    )
    if request.method == "POST" and form.is_valid():
        avatar = form.save(commit=False)
        avatar.user = request.user
        avatar.save()
        messages.success(request, "Tu avatar fue actualizado.")
        return redirect("inicio")
    return render(request, "perfiles/formulario_avatar.html", {"form": form})
