from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from perfiles.models import Avatar
from .models import Categoria, Comentario, Receta


class IntegridadDatosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(username='integridad')
        cls.categoria = Categoria.objects.create(nombre='salada')
        cls.receta = Receta.objects.create(
            titulo='Sopa', categoria=cls.categoria, creador=cls.usuario,
            ingredientes='Agua y verduras', instrucciones='Cocinar',
        )
        cls.comentario = Comentario.objects.create(
            receta=cls.receta, autor=cls.usuario, contenido='Excelente',
        )

    def test_base_rechaza_categoria_duplicada(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Categoria.objects.bulk_create([Categoria(nombre='salada')])
        self.assertEqual(Categoria.objects.filter(nombre='salada').count(), 1)

    def test_categoria_en_uso_protege_recetas_y_comentarios(self):
        for borrar in (self.categoria.delete, Categoria.objects.all().delete):
            with self.assertRaises(ProtectedError):
                borrar()
            self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())
            self.assertTrue(Receta.objects.filter(pk=self.receta.pk).exists())
            self.assertTrue(Comentario.objects.filter(pk=self.comentario.pk).exists())

    def test_categoria_vacia_se_puede_eliminar(self):
        categoria = Categoria.objects.create(nombre='dulce')
        pk = categoria.pk
        categoria.delete()
        self.assertFalse(Categoria.objects.filter(pk=pk).exists())

    def test_base_rechaza_titulo_nulo_en_actualizacion_directa(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Receta.objects.filter(pk=self.receta.pk).update(titulo=None)
        self.receta.refresh_from_db()
        self.assertEqual(self.receta.titulo, 'Sopa')

    def test_base_rechaza_avatar_sin_usuario(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Avatar.objects.create(user=None, imagen='avatares/prueba.png')
        self.assertFalse(Avatar.objects.exists())

    def test_avatar_sigue_siendo_unico_por_usuario(self):
        Avatar.objects.create(user=self.usuario, imagen='avatares/primero.png')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Avatar.objects.create(user=self.usuario, imagen='avatares/segundo.png')
        self.assertEqual(Avatar.objects.get(user=self.usuario).imagen.name, 'avatares/primero.png')

    def test_borrar_usuario_conserva_receta_sin_autor(self):
        Avatar.objects.create(user=self.usuario, imagen='avatares/prueba.png')
        self.usuario.delete()
        self.receta.refresh_from_db()
        self.assertIsNone(self.receta.creador_id)
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())
        self.assertFalse(Avatar.objects.exists())
        self.assertFalse(Comentario.objects.exists())

    def test_borrar_receta_conserva_categoria_y_usuario(self):
        self.receta.delete()
        self.assertFalse(Comentario.objects.exists())
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())
        self.assertTrue(get_user_model().objects.filter(pk=self.usuario.pk).exists())
