from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from perfiles.models import Avatar
from aplicacion.imagenes import validar_imagen


class UserRegisterForm(UserCreationForm):
    # Esto es un ModelForm
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repetir contraseña', widget=forms.PasswordInput)

    class Meta:
       model = User
       fields = ['last_name', 'first_name', 'username', 'email', 'password1', 'password2']
       help_texts = {k: '' for k in ('username',)}

class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'email']

    def save(self, commit=True):
        user = super(UserUpdateForm, self).save(commit=False)
        if commit:
            user.save()
        return user


class AvatarFormulario(forms.ModelForm):
    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if not imagen:
            raise forms.ValidationError('Selecciona una imagen para tu avatar.')
        if 'imagen' in self.files:
            validar_imagen(imagen)
        return imagen

    class Meta:
        model = Avatar
        fields = ['imagen']
