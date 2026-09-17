from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class MigracionesIntegridadTests(TransactionTestCase):
    anteriores = [
        ('aplicacion', '0013_remove_message_chat_delete_chat_delete_message'),
        ('perfiles', '0001_initial'),
    ]
    nuevas = [
        ('aplicacion', '0015_restricciones_e_indices'),
        ('perfiles', '0002_avatar_usuario_obligatorio'),
    ]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        self.ultimas = executor.loader.graph.leaf_nodes()
        self.addCleanup(self.restaurar_esquema)
        executor.migrate(self.anteriores)
        apps = executor.loader.project_state(self.anteriores).apps
        self.Categoria = apps.get_model('aplicacion', 'Categoria')
        self.Receta = apps.get_model('aplicacion', 'Receta')
        self.Comentario = apps.get_model('aplicacion', 'Comentario')
        self.Avatar = apps.get_model('perfiles', 'Avatar')
        self.usuario = apps.get_model('auth', 'User').objects.create(username='anterior')
        self.categoria = self.Categoria.objects.create(nombre='salada')
        self.receta = self.Receta.objects.create(
            titulo='Receta existente', categoria_id=self.categoria.pk,
            creador_id=self.usuario.pk, ingredientes='<p>Agua</p>',
            instrucciones='<p>Cocinar</p>', imagen='images/existente.png',
        )
        self.comentario = self.Comentario.objects.create(
            receta_id=self.receta.pk, autor_id=self.usuario.pk, contenido='Conservar',
        )
        self.avatar = self.Avatar.objects.create(
            user_id=self.usuario.pk, imagen='avatares/existente.png',
        )

    def restaurar_esquema(self):
        # Solo la base desechable de TransactionTestCase; elimina fixtures inválidas.
        call_command('flush', verbosity=0, interactive=False)
        MigrationExecutor(connection).migrate(self.ultimas)

    def test_migracion_conserva_datos_y_crea_indices(self):
        antes = {
            modelo: list(modelo.objects.order_by('pk').values())
            for modelo in (self.Categoria, self.Receta, self.Comentario, self.Avatar)
        }
        MigrationExecutor(connection).migrate(self.nuevas)
        for modelo, filas in antes.items():
            self.assertEqual(list(modelo.objects.order_by('pk').values()), filas)

        with connection.cursor() as cursor:
            recetas = connection.introspection.get_constraints(cursor, 'aplicacion_receta')
            comentarios = connection.introspection.get_constraints(cursor, 'aplicacion_comentario')
        self.assertEqual(recetas['receta_fecha_id_idx']['columns'], ['fecha_publicacion', 'id'])
        self.assertEqual(
            recetas['receta_categoria_fecha_idx']['columns'],
            ['categoria_id', 'fecha_publicacion', 'id'],
        )
        self.assertEqual(
            comentarios['comentario_receta_fecha_idx']['columns'],
            ['receta_id', 'fecha_creacion', 'id'],
        )

    def comprobar_bloqueo(self, mensaje):
        with self.assertRaisesRegex(RuntimeError, mensaje):
            MigrationExecutor(connection).migrate(self.nuevas)
        aplicadas = MigrationExecutor(connection).loader.applied_migrations
        self.assertNotIn(('aplicacion', '0014_validar_integridad_existente'), aplicadas)
        for migracion in self.nuevas:
            self.assertNotIn(migracion, aplicadas)
        self.assertTrue(self.Receta.objects.filter(pk=self.receta.pk).exists())
        self.assertTrue(self.Comentario.objects.filter(pk=self.comentario.pk).exists())

    def test_duplicadas_detienen_migracion_sin_borrar_recetas(self):
        duplicada = self.Categoria.objects.create(nombre='salada')
        self.Receta.objects.filter(pk=self.receta.pk).update(categoria_id=duplicada.pk)
        self.comprobar_bloqueo('categorías con nombre duplicado: 1')
        self.assertEqual(self.Categoria.objects.count(), 2)
        self.receta.refresh_from_db()
        self.assertEqual(self.receta.categoria_id, duplicada.pk)

    def test_titulo_nulo_detiene_migracion_sin_inventar_titulo(self):
        self.Receta.objects.filter(pk=self.receta.pk).update(titulo=None)
        self.comprobar_bloqueo('recetas con título nulo: 1')
        self.receta.refresh_from_db()
        self.assertIsNone(self.receta.titulo)

    def test_avatar_huerfano_detiene_migracion_sin_reasignar_usuario(self):
        self.Avatar.objects.filter(pk=self.avatar.pk).update(user_id=None)
        self.comprobar_bloqueo('avatares sin usuario: 1')
        self.avatar.refresh_from_db()
        self.assertIsNone(self.avatar.user_id)
