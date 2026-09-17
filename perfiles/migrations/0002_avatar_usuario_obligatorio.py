from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('perfiles', '0001_initial'),
        ('aplicacion', '0014_validar_integridad_existente'),
    ]

    operations = [
        migrations.AlterField(
            model_name='avatar', name='user',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
