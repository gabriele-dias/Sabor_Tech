from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .calculations import (
    calculate_custo_por_pessoa,
    calculate_custo_total,
    calculate_orders_total,
    calculate_receita,
    calculate_total_insumo,
)


class CoreAccessTests(TestCase):
    def test_login_page_is_rendered(self):
        response = self.client.get(reverse('core:login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Entrar')
        self.assertContains(response, 'form method="post" class="login-form"')
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')

    def test_root_requires_login(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login/?next=/')


class OrderCalculationTests(TestCase):
    def test_calculates_total_for_multiple_orders(self):
        orders = [{"valor": "45.50"}, {"valor": "67.00"}, {"valor": "32.00"}]

        result = calculate_orders_total(orders)

        self.assertEqual(result, Decimal("144.50"))

    def test_empty_order_list_returns_zero(self):
        self.assertEqual(calculate_orders_total([]), Decimal("0.00"))

    def test_invalid_order_value_raises_error(self):
        with self.assertRaises(ValueError):
            calculate_orders_total([{"valor": "invalido"}])

    def test_negative_order_value_raises_error(self):
        with self.assertRaises(ValueError):
            calculate_orders_total([{"valor": "-10.00"}])

    def test_total_insumo(self):
        self.assertEqual(calculate_total_insumo(Decimal("0.40"), 30), Decimal("12.00"))

    def test_custo_total(self):
        self.assertEqual(calculate_custo_total(Decimal("12.00"), Decimal("8.50")), Decimal("102.00"))

    def test_custo_por_pessoa(self):
        self.assertEqual(calculate_custo_por_pessoa(Decimal("102.00"), 30), Decimal("3.40"))

    def test_calcular_receita_completo(self):
        dados = calculate_receita(
            quantidade_por_pessoa=Decimal("0.40"),
            pessoas=30,
            custo_unitario=Decimal("8.50"),
        )

        self.assertEqual(dados["total_insumo"], Decimal("12.00"))
        self.assertEqual(dados["custo_total"], Decimal("102.00"))
        self.assertEqual(dados["custo_por_pessoa"], Decimal("3.40"))

    def test_dashboard_calculator_returns_recipe_total(self):
        user = User.objects.create_user(username="gestor", password="123456")
        group, _ = Group.objects.get_or_create(name="Gestão")
        user.groups.add(group)
        self.client.force_login(user)

        response = self.client.post(
            reverse("core:dashboard"),
            {"quantidade_por_pessoa": "0.40", "pessoas": "30", "custo_unitario": "8.50"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Custo total")
        self.assertContains(response, "R$ 102,00")
