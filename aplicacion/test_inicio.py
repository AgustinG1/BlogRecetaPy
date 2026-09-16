"""Regresiones del contrato INI-01: últimas seis recetas públicas."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Receta


class UltimasRecetasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(nombre="salada")
        cls.usuario = get_user_model().objects.create_user(username="lector_prueba")

    def crear_receta(self, titulo, fecha=None):
        receta = Receta.objects.create(
            titulo=titulo,
            subtitulo="Una receta de prueba",
            categoria=self.categoria,
            ingredientes="<p>Ingredientes</p>",
            instrucciones="<p>Preparación</p>",
        )
        if fecha is not None:
            Receta.objects.filter(pk=receta.pk).update(fecha_publicacion=fecha)
        return receta

    def test_inicio_vacio_invita_al_visitante_a_registrarse(self):
        response = self.client.get(reverse("inicio"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aún no hay recetas")
        self.assertContains(response, 'href="{}"'.format(reverse("registro")))

    def test_inicio_vacio_invita_al_usuario_a_publicar(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse("inicio"))
        self.assertContains(response, "Aún no hay recetas")
        self.assertContains(response, 'href="{}"'.format(reverse("agregar_receta")))

    def test_muestra_solo_las_seis_mas_recientes_por_fecha(self):
        ahora = timezone.now()
        # El orden de creación difiere del de publicación intencionalmente.
        recetas = {
            dias: self.crear_receta(f"Plato-{dias}-prueba", ahora - timedelta(days=dias))
            for dias in (3, 0, 7, 2, 6, 1, 5, 4)
        }
        response = self.client.get(reverse("inicio"))
        self.assertEqual(
            [r.pk for r in response.context["recetas_destacadas"]],
            [recetas[dias].pk for dias in range(6)],
        )
        for dias in range(6):
            self.assertContains(response, recetas[dias].titulo)
            self.assertContains(
                response,
                'href="{}"'.format(reverse("detalle_receta", args=[recetas[dias].pk])),
            )
        for dias in (6, 7):
            self.assertNotContains(response, recetas[dias].titulo)
        self.assertNotContains(response, "Aún no hay recetas")

    def test_fechas_iguales_se_desempatan_por_id_descendente(self):
        fecha = timezone.now()
        primera = self.crear_receta("Primera", fecha)
        segunda = self.crear_receta("Segunda", fecha)
        response = self.client.get(reverse("inicio"))
        self.assertEqual(
            [r.pk for r in response.context["recetas_destacadas"]],
            [segunda.pk, primera.pk],
        )

    def test_portada_anonima_carga_tarjetas_y_categorias_en_una_consulta(self):
        for indice in range(8):
            self.crear_receta(f"Receta {indice}")
        with self.assertNumQueries(1):
            response = self.client.get(reverse("inicio"))
        self.assertContains(response, "Comida Salada")

