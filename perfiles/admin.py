from django.contrib import admin

from perfiles.models import Avatar
from perfiles.forms import AvatarFormulario


class AvatarAdminForm(AvatarFormulario):
    class Meta(AvatarFormulario.Meta):
        fields = '__all__'


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    form = AvatarAdminForm
