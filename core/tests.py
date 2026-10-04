from decimal import Decimal
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
import json

from .models import KitchenPreparation, Order
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

    def test_waiter_orders_page_links_to_atendimento(self):
        user = User.objects.create_user(username='garcom_atendimento', password='senha123')
        group, _ = Group.objects.get_or_create(name='Garçom')
        user.groups.add(group)
        self.client.force_login(user)

        response = self.client.get(reverse('core:pedidos'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('core:atendimento'))

    def test_management_user_cannot_open_orders(self):
        user = User.objects.create_user(username='gestao', password='senha123')
        self.client.force_login(user)

        response = self.client.get(reverse('core:pedidos'))

        self.assertRedirects(response, reverse('core:home'))

    def test_waiter_can_return_to_limited_home_but_not_management_pages(self):
        user = User.objects.create_user(username='garcom_limitado', password='senha123')
        group, _ = Group.objects.get_or_create(name='Garçom')
        user.groups.add(group)
        self.client.force_login(user)

        home = self.client.get(reverse('core:home'))
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, reverse('core:pedidos'))
        self.assertContains(home, reverse('core:atendimento'))
        self.assertNotContains(home, reverse('core:produtos'))
        self.assertNotContains(home, reverse('core:dashboard'))

        for route_name in ('dashboard', 'produtos', 'relatorios'):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(f'core:{route_name}'))
                self.assertRedirects(response, reverse('core:pedidos'))

    def test_logout_redirects_to_login(self):
        user = User.objects.create_user(username='logout_user', password='senha123')
        self.client.force_login(user)

        response = self.client.get(reverse('core:logout'))

        self.assertRedirects(response, reverse('core:login'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_waiter_order_is_saved_for_management(self):
        user = User.objects.create_user(username='garcom_pedido', password='senha123')
        group, _ = Group.objects.get_or_create(name='Garçom')
        user.groups.add(group)
        self.client.force_login(user)

        response = self.client.post(
            reverse('core:concluir_pedido'),
            data=json.dumps({
                'items': [{'nome': 'Pizza Calabresa', 'preco': 59.9, 'quantidade': 1}],
                'subtotal': 59.9,
                'service_fee': 5.99,
                'total': 65.89,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.client.logout()
        admin_user = User.objects.create_user(username='gestor_pedido', password='senha123')
        self.client.force_login(admin_user)
        dashboard = self.client.get(reverse('core:dashboard'))
        self.assertContains(dashboard, 'Pizza Calabresa')
        self.assertContains(dashboard, 'garcom_pedido')

    def test_concluir_pedido_rejects_invalid_items_shape(self):
        waiter = User.objects.create_user(username="garcom_payload", password="senha123")
        group, _ = Group.objects.get_or_create(name="Garçom")
        waiter.groups.add(group)
        self.client.force_login(waiter)

        response = self.client.post(
            reverse("core:concluir_pedido"),
            data=json.dumps({"items": {"nome": "Pizza"}, "subtotal": 50, "service_fee": 5, "total": 55}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)


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


class ServiceAndStaffViewTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username="manager@sabor.test", password="senha123")
        management_group, _ = Group.objects.get_or_create(name="Gestão")
        self.manager.groups.add(management_group)
        self.client.force_login(self.manager)

    def test_atendimento_displays_orders_and_tables(self):
        Order.objects.create(
            waiter=self.manager,
            items=[{"cliente": "Ana Souza", "mesa": 3, "canal": "Presencial"}],
            subtotal=Decimal("64.80"),
            service_fee=Decimal("6.48"),
            total=Decimal("71.28"),
            status="Em preparo",
        )

        response = self.client.get(reverse("core:atendimento"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Atendimento")
        self.assertContains(response, "Ana Souza")
        self.assertContains(response, "Mesa 03")
        self.assertEqual(response.context["occupied_count"], 1)
        self.assertEqual(response.context["table_count"], 12)

    def test_staff_form_creates_user_with_selected_group(self):
        response = self.client.post(
            reverse("core:funcionarios"),
            {
                "full_name": "Ana Souza",
                "email": "ana.souza@sabor.test",
                "password": "N0v0-Acesso!Sabor2026",
                "profile": "garcom",
            },
            follow=True,
        )

        employee = User.objects.get(email="ana.souza@sabor.test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(employee.get_full_name(), "Ana Souza")
        self.assertTrue(employee.groups.filter(name="Garçom").exists())
        self.assertContains(response, "Funcionário Ana Souza cadastrado com sucesso.")

    def test_staff_form_shows_role_descriptions(self):
        response = self.client.get(reverse("core:funcionarios"))

        self.assertContains(response, "Acessa somente Atendimento e Pedidos.")
        self.assertContains(response, "Acessa toda a gestão do restaurante.")
        self.assertContains(response, "Acompanha a operação da cozinha.")
        self.assertContains(response, "Apoia os preparos e tarefas da cozinha.")

    def test_non_management_user_cannot_open_staff_form(self):
        waiter = User.objects.create_user(username="waiter@sabor.test", password="senha123")
        waiter_group, _ = Group.objects.get_or_create(name="Garçom")
        waiter.groups.add(waiter_group)
        self.client.force_login(waiter)

        response = self.client.get(reverse("core:funcionarios"))

        self.assertRedirects(response, reverse("core:pedidos"))

    def test_legacy_client_and_settings_routes_render(self):
        for route_name in ("clientes", "configuracoes"):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(f"core:{route_name}"))
                self.assertEqual(response.status_code, 200)

    def test_management_menus_hide_orders_without_order_permission(self):
        for route_name in ("home", "atendimento", "produtos", "receitas", "relatorios", "funcionarios"):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(f"core:{route_name}"))
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, f'href="{reverse("core:pedidos")}"')

    def test_main_pages_remain_available_to_superuser(self):
        administrator = User.objects.create_superuser(
            username="administrator@sabor.test",
            email="administrator@sabor.test",
            password="senha123",
        )
        self.client.force_login(administrator)

        for route_name in (
            "home", "dashboard", "atendimento", "pedidos", "produtos",
            "receitas", "relatorios", "funcionarios", "clientes", "configuracoes",
            "desempenho_cozinha",
        ):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(f"core:{route_name}"))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, reverse("core:home"))
                self.assertNotContains(response, f'href="{reverse("core:dashboard")}"')


class KitchenPerformanceTests(TestCase):
    def setUp(self):
        self.cook = User.objects.create_user(
            username="cook@sabor.test",
            email="cook@sabor.test",
            password="senha123",
            first_name="Carlos",
            last_name="Lima",
        )
        self.cook_group, _ = Group.objects.get_or_create(name="Chefe de Cozinha")
        self.cook.groups.add(self.cook_group)
        self.auxiliary = User.objects.create_user(
            username="auxiliary@sabor.test",
            email="auxiliary@sabor.test",
            password="senha123",
            first_name="Beatriz",
            last_name="Alves",
        )
        self.auxiliary_group, _ = Group.objects.get_or_create(name="Auxiliar de cozinha")
        self.auxiliary.groups.add(self.auxiliary_group)
        self.client.force_login(self.cook)

    def test_kitchen_view_shows_real_records_and_metrics(self):
        KitchenPreparation.objects.create(
            dish_name="Pizza Marguerita",
            responsible=self.cook,
            status=KitchenPreparation.STATUS_COMPLETED,
            duration_minutes=18,
        )
        KitchenPreparation.objects.create(
            dish_name="Molho de tomate",
            responsible=self.auxiliary,
            status=KitchenPreparation.STATUS_IN_PROGRESS,
        )

        response = self.client.get(reverse("core:desempenho_cozinha"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pizza Marguerita")
        self.assertContains(response, "Carlos Lima")
        self.assertContains(response, "Auxiliar de cozinha")
        self.assertEqual(response.context["preparation_count"], 2)
        self.assertEqual(response.context["average_duration"], 18)
        self.assertEqual(response.context["active_cooks"], 1)
        self.assertEqual(response.context["active_assistants"], 1)

    def test_kitchen_member_can_register_a_completed_preparation(self):
        response = self.client.post(
            reverse("core:desempenho_cozinha"),
            {"dish_name": "Lasanha da Casa", "status": "Concluído", "duration_minutes": 32},
            follow=True,
        )

        preparation = KitchenPreparation.objects.get(dish_name="Lasanha da Casa")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(preparation.responsible, self.cook)
        self.assertEqual(preparation.duration_minutes, 32)

    def test_completed_preparation_requires_duration(self):
        response = self.client.post(
            reverse("core:desempenho_cozinha"),
            {"dish_name": "Caldo", "status": "Concluído", "duration_minutes": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(KitchenPreparation.objects.exists())
        self.assertContains(response, "Informe a duração do preparo concluído.")

    def test_kitchen_profile_filter_limits_records(self):
        KitchenPreparation.objects.create(
            dish_name="Pizza Marguerita",
            responsible=self.cook,
            status=KitchenPreparation.STATUS_COMPLETED,
            duration_minutes=18,
        )
        KitchenPreparation.objects.create(
            dish_name="Molho de tomate",
            responsible=self.auxiliary,
            status=KitchenPreparation.STATUS_COMPLETED,
            duration_minutes=12,
        )

        response = self.client.get(reverse("core:desempenho_cozinha"), {"perfil": "auxiliares"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [preparation.dish_name for preparation in response.context["preparations"]],
            ["Molho de tomate"],
        )

    def test_non_kitchen_user_is_redirected(self):
        waiter = User.objects.create_user(username="kitchen_waiter", password="senha123")
        waiter_group, _ = Group.objects.get_or_create(name="Garçom")
        waiter.groups.add(waiter_group)
        self.client.force_login(waiter)

        response = self.client.get(reverse("core:desempenho_cozinha"))

        self.assertRedirects(response, reverse("core:pedidos"))

    def test_home_and_kitchen_menus_omit_dashboard_and_expose_routes(self):
        home = self.client.get(reverse("core:home"))
        kitchen = self.client.get(reverse("core:desempenho_cozinha"))

        self.assertEqual(home.status_code, 200)
        self.assertEqual(kitchen.status_code, 200)
        self.assertNotContains(home, ">Dashboard<")
        self.assertNotContains(kitchen, ">Dashboard<")
        for route_name in ("atendimento", "produtos", "receitas", "desempenho_cozinha", "relatorios"):
            with self.subTest(route_name=route_name):
                self.assertContains(home, reverse(f"core:{route_name}"))
                self.assertContains(kitchen, reverse(f"core:{route_name}"))
        self.assertContains(kitchen, "Voltar à Home")

    def test_staff_pages_have_home_return(self):
        manager = User.objects.create_user(username="staff_manager@sabor.test", password="senha123")
        management_group, _ = Group.objects.get_or_create(name="Gestão")
        manager.groups.add(management_group)
        self.client.force_login(manager)
        response = self.client.get(reverse("core:funcionarios"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("core:home"))
        self.assertContains(response, "Voltar à Home")
