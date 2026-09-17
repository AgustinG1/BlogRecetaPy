from django.db import migrations
from django.db.models import Count


def validar_datos(apps, schema_editor):
    alias = schema_editor.connection.alias
    Categoria = apps.get_model('aplicacion', 'Categoria')
    Receta = apps.get_model('aplicacion', 'Receta')
    Avatar = apps.get_model('perfiles', 'Avatar')

    duplicadas = (
        Categoria.objects.using(alias).order_by().values('nombre')
        .annotate(total=Count('pk')).filter(total__gt=1).count()
    )
    sin_titulo = Receta.objects.using(alias).filter(titulo__isnull=True).count()
    sin_usuario = Avatar.objects.using(alias).filter(user__isnull=True).count()
    problemas = []
    if duplicadas:
        problemas.append(f'categorías con nombre duplicado: {duplicadas}')
    if sin_titulo:
        problemas.append(f'recetas con título nulo: {sin_titulo}')
    if sin_usuario:
        problemas.append(f'avatares sin usuario: {sin_usuario}')
    if problemas:
        raise RuntimeError(
            'Migración detenida antes de modificar las tablas. Revisar y corregir: '
            + '; '.join(problemas)
            + '. No se borraron ni reasignaron registros. Luego ejecutar migrate nuevamente.'
        )


class Migration(migrations.Migration):
    dependencies = [
        ('aplicacion', '0013_remove_message_chat_delete_chat_delete_message'),
        ('perfiles', '0001_initial'),
    ]

    operations = [migrations.RunPython(validar_datos, migrations.RunPython.noop)]
