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

    def test_login_redirects_to_home(self):
        user = User.objects.create_user(username='chef', email='chef@sabor.com', password='senha123')

        response = self.client.post(
            reverse('core:login'),
            {'username': 'chef', 'password': 'senha123'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('core:home'))

    def test_waiter_login_redirects_to_orders(self):
        user = User.objects.create_user(username='garcom', password='senha123')
        group, _ = Group.objects.get_or_create(name='Garçom')
        user.groups.add(group)

        response = self.client.post(
            reverse('core:login'),
            {'username': 'garcom', 'password': 'senha123'},
        )

        self.assertRedirects(response, reverse('core:pedidos'))

    def test_management_user_cannot_open_orders(self):
        user = User.objects.create_user(username='gestao', password='senha123')
        self.client.force_login(user)

        response = self.client.get(reverse('core:pedidos'))

        self.assertRedirects(response, reverse('core:home'))

    def test_waiter_is_limited_to_orders(self):
        user = User.objects.create_user(username='garcom_limitado', password='senha123')
        group, _ = Group.objects.get_or_create(name='Garçom')
        user.groups.add(group)
        self.client.force_login(user)

        for route_name in ('home', 'dashboard', 'produtos', 'relatorios'):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(f'core:{route_name}'))
                self.assertRedirects(response, reverse('core:pedidos'))


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

    def test_dashboard_hides_recipe_tools(self):
        user = User.objects.create_user(username="gestor", password="123456")
        group, _ = Group.objects.get_or_create(name="Gestão")
        user.groups.add(group)
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Adicionar receita")
        self.assertNotContains(response, "Calcular custo")

    def test_dashboard_filters_orders_by_selected_date(self):
        user = User.objects.create_user(username="gestor2", password="123456")
        group, _ = Group.objects.get_or_create(name="Gestão")
        user.groups.add(group)
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"), {"date_start": "2026-09-12", "date_end": "2026-09-12"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pedidos do período")
        self.assertContains(response, "Maria Costa")
        self.assertContains(response, "Precificação por pedido")

    def test_dashboard_calculates_period_averages(self):
        user = User.objects.create_user(username="gestor3", password="123456")
        group, _ = Group.objects.get_or_create(name="Gestão")
        user.groups.add(group)
        self.client.force_login(user)

        response = self.client.get(
            reverse("core:dashboard"),
            {"date_start": "2026-09-12", "date_end": "2026-09-13"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["period_days"], 2)
        self.assertEqual(response.context["total_vendas"], 144.5)
        self.assertEqual(response.context["media_vendas"], 72.25)
        self.assertContains(response, "Pizza Marguerita")
        self.assertContains(response, "farinha de trigo")
