from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('aplicacion', '0014_validar_integridad_existente')]

    operations = [
        migrations.AlterField(
            model_name='categoria',
            name='nombre',
            field=models.CharField(
                choices=[('salada', 'Comida Salada'), ('dulce', 'Comida Dulce'),
                         ('vegetariana', 'Comida Vegetariana')],
                default='salada', max_length=100, unique=True,
            ),
        ),
        migrations.AlterField(
            model_name='receta', name='titulo', field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='receta', name='categoria',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to='aplicacion.categoria',
            ),
        ),
        migrations.AddIndex(
            model_name='receta',
            index=models.Index(fields=['-fecha_publicacion', '-id'], name='receta_fecha_id_idx'),
        ),
        migrations.AddIndex(
            model_name='receta',
            index=models.Index(
                fields=['categoria', '-fecha_publicacion', '-id'],
                name='receta_categoria_fecha_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='comentario',
            index=models.Index(
                fields=['receta', 'fecha_creacion', 'id'],
                name='comentario_receta_fecha_idx',
            ),
        ),
    ]
