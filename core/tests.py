from decimal import Decimal
from datetime import timedelta
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
import json

from .models import KitchenPreparation, Order, Tenant, TenantMembership
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

    def test_waiter_orders_page_links_to_ready_orders(self):
        user = User.objects.create_user(username='garcom_atendimento', password='senha123')
        group, _ = Group.objects.get_or_create(name='Garçom')
        user.groups.add(group)
        self.client.force_login(user)

        response = self.client.get(reverse('core:pedidos'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('core:pedidos_prontos'))
        self.assertContains(response, 'aria-label="Pedidos prontos aguardando retirada"')
        self.assertNotContains(response, 'Navegação do sistema')
        self.assertNotContains(response, f'href="{reverse("core:pedidos")}"')

    def test_management_user_cannot_open_orders(self):
        user = User.objects.create_user(username='gestao', password='senha123')
        self.client.force_login(user)

        response = self.client.get(reverse('core:pedidos'))

        self.assertRedirects(response, reverse('core:home'))

    def test_non_management_user_cannot_open_products(self):
        user = User.objects.create_user(username='funcionario', password='senha123')
        self.client.force_login(user)

        response = self.client.get(reverse('core:produtos'))

        self.assertRedirects(response, reverse('core:home'))

    def test_management_user_can_open_products(self):
        user = User.objects.create_user(username='gestao_produtos', password='senha123')
        management_group, _ = Group.objects.get_or_create(name='Gestão')
        user.groups.add(management_group)
        tenant = Tenant.objects.create(name='Restaurante Teste', slug='restaurante-teste')
        TenantMembership.objects.create(tenant=tenant, user=user, role=TenantMembership.Role.MANAGER)
        self.client.force_login(user)

        response = self.client.get(reverse('core:produtos'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cardápio')

    def test_superuser_cannot_open_waiter_orders_page(self):
        user = User.objects.create_superuser(
            username='admin_sem_pedidos',
            email='admin_sem_pedidos@sabor.test',
            password='senha123',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('core:pedidos'))

        self.assertRedirects(response, reverse('core:home'))

    def test_waiter_home_is_limited_and_management_pages_remain_blocked(self):
        user = User.objects.create_user(username='garcom_limitado', password='senha123')
        group, _ = Group.objects.get_or_create(name='Garçom')
        user.groups.add(group)
        self.client.force_login(user)

        home = self.client.get(reverse('core:home'))
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, reverse('core:atendimento'))
        self.assertNotContains(home, f'href="{reverse("core:pedidos")}"')
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
        self.assertContains(response, "Acessa exclusivamente o painel da cozinha e opera pedidos e preparos.")
        self.assertContains(response, "Perfil exclusivo do cozinheiro")
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
            "home", "perfil_administrativo", "dashboard", "atendimento", "produtos",
            "receitas", "desempenho_cozinha", "perfil_cozinheiro", "relatorios",
            "funcionarios", "clientes", "configuracoes",
        ):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(f"core:{route_name}"))
                self.assertEqual(response.status_code, 200)
                if route_name not in ("perfil_administrativo", "desempenho_cozinha", "perfil_cozinheiro"):
                    self.assertContains(response, reverse("core:home"))
                self.assertNotContains(response, f'href="{reverse("core:dashboard")}"')
                self.assertNotContains(response, f'href="{reverse("core:clientes")}"')
                self.assertNotContains(response, f'href="{reverse("core:configuracoes")}"')
                self.assertNotContains(response, "Voltar")

    def test_administrative_profile_has_requested_screens(self):
        administrator = User.objects.create_superuser(
            username="admin_profile@sabor.test",
            email="admin_profile@sabor.test",
            password="senha123",
        )
        self.client.force_login(administrator)

        response = self.client.get(reverse("core:perfil_administrativo"))

        self.assertEqual(response.status_code, 200)
        for route_name in ("atendimento", "receitas", "desempenho_cozinha", "relatorios", "funcionarios"):
            self.assertContains(response, reverse(f"core:{route_name}"))
        for route_name in ("home", "produtos", "perfil_cozinheiro"):
            self.assertNotContains(response, f'href="{reverse(f"core:{route_name}")}"')

    def test_administrator_login_redirects_to_administrative_profile(self):
        self.client.logout()
        administrator = User.objects.create_superuser(
            username="admin_login@sabor.test",
            email="admin_login@sabor.test",
            password="senha123",
        )

        response = self.client.post(
            reverse("core:login"),
            {"username": administrator.email, "password": "senha123"},
        )

        self.assertRedirects(response, reverse("core:perfil_administrativo"))


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
        self.administrator = User.objects.create_superuser(
            username="kitchen_admin@sabor.test",
            email="kitchen_admin@sabor.test",
            password="senha123",
        )
        self.client.force_login(self.cook)

    def create_kitchen_order(self, **overrides):
        membership = self.cook.tenant_memberships.filter(is_active=True, tenant__is_active=True).first()
        self.assertIsNotNone(membership)
        order_data = {
            "waiter": self.cook,
            "tenant": membership.tenant,
            "items": [{"name": "Pizza Calabresa", "quantity": 2}],
            "subtotal": Decimal("40.00"),
            "service_fee": Decimal("0.00"),
            "total": Decimal("40.00"),
        }
        order_data.update(overrides)
        return Order.objects.create(**order_data)

    def test_pending_order_has_no_traffic_light_or_timer(self):
        order = self.create_kitchen_order()

        response = self.client.get(reverse("core:perfil_cozinheiro"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "O cronômetro e o farol iniciam após a confirmação.")
        self.assertNotContains(response, f'data-kitchen-timer="{order.pk}"')
        self.assertNotContains(response, f'data-kitchen-light="{order.pk}"')

    def test_confirm_action_starts_order_timer_and_reports_feedback(self):
        order = self.create_kitchen_order()

        response = self.client.post(
            reverse("core:perfil_cozinheiro"),
            {"order_id": order.pk, "action": "confirm_order"},
            follow=True,
        )

        order.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(order.status, Order.STATUS_PREPARING)
        self.assertIsNotNone(order.confirmed_at)
        self.assertContains(response, f"Pedido #{order.pk} confirmado. Cronômetro iniciado.")
        self.assertContains(response, f'data-kitchen-timer="{order.pk}"')
        self.assertContains(response, "Marcar como pronto")
        self.assertContains(response, f"Garçom: {self.cook.get_full_name()}")

    def test_ready_action_finishes_timer_and_reports_feedback(self):
        order = self.create_kitchen_order(
            status=Order.STATUS_PREPARING,
            confirmed_at=timezone.now() - timedelta(minutes=5),
        )

        response = self.client.post(
            reverse("core:perfil_cozinheiro"),
            {"order_id": order.pk, "action": "ready_order"},
            follow=True,
        )

        order.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(order.status, Order.STATUS_READY)
        self.assertIsNotNone(order.ready_at)
        self.assertContains(response, f"Pedido #{order.pk} marcado como pronto. Cronômetro finalizado.")
        self.assertContains(response, 'data-light="done"')
        self.assertNotContains(response, "Marcar como pronto")

    def test_confirmed_order_uses_server_timestamp_and_live_farol_threshold(self):
        green_order = self.create_kitchen_order(
            status=Order.STATUS_PREPARING,
            confirmed_at=timezone.now() - timedelta(minutes=19, seconds=59),
        )
        yellow_order = self.create_kitchen_order(
            status=Order.STATUS_PREPARING,
            confirmed_at=timezone.now() - timedelta(minutes=20),
        )
        red_order = self.create_kitchen_order(
            status=Order.STATUS_PREPARING,
            confirmed_at=timezone.now() - timedelta(minutes=30),
        )

        response = self.client.get(reverse("core:perfil_cozinheiro"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-kitchen-timer="{green_order.pk}"')
        self.assertContains(response, f'data-kitchen-timer="{yellow_order.pk}"')
        self.assertContains(response, f'data-kitchen-timer="{red_order.pk}"')
        self.assertContains(response, 'data-light="green"')
        self.assertContains(response, 'data-light="yellow"')
        self.assertContains(response, 'data-light="red"')
        self.assertContains(response, "data-confirmed-at-ms=")
        self.assertContains(response, "setInterval(updateKitchenTimers, 1000)")
        response_body = response.content.decode()
        self.assertLess(
            response_body.index(f'data-kitchen-timer="{red_order.pk}"'),
            response_body.index(f'data-kitchen-timer="{yellow_order.pk}"'),
        )

    def test_ready_order_timer_uses_saved_ready_timestamp(self):
        confirmed_at = timezone.now() - timedelta(minutes=35)
        ready_at = timezone.now() - timedelta(minutes=5)
        order = self.create_kitchen_order(
            status=Order.STATUS_READY,
            confirmed_at=confirmed_at,
            ready_at=ready_at,
        )

        response = self.client.get(reverse("core:perfil_cozinheiro"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-kitchen-timer="{order.pk}"')
        self.assertContains(response, 'data-light="done"')
        self.assertContains(response, f'data-ready-at-ms="{int(ready_at.timestamp() * 1000)}"')

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
        self.client.force_login(self.administrator)

        response = self.client.get(reverse("core:desempenho_cozinha"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Desempenho da cozinha")
        self.assertContains(response, "Pizza Marguerita")
        self.assertContains(response, "Carlos Lima")
        self.assertContains(response, "Auxiliar de cozinha")
        self.assertEqual(response.context["preparation_count"], 2)
        self.assertEqual(response.context["average_duration"], 18)
        self.assertEqual(response.context["active_cooks"], 1)
        self.assertEqual(response.context["active_assistants"], 1)

    def test_administrator_can_register_a_completed_preparation(self):
        self.client.force_login(self.administrator)
        response = self.client.post(
            reverse("core:desempenho_cozinha"),
            {"dish_name": "Lasanha da Casa", "status": "Concluído", "duration_minutes": 32},
            follow=True,
        )

        preparation = KitchenPreparation.objects.get(dish_name="Lasanha da Casa")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(preparation.responsible, self.administrator)
        self.assertEqual(preparation.duration_minutes, 32)

    def test_completed_preparation_requires_duration(self):
        self.client.force_login(self.administrator)
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
        self.client.force_login(self.administrator)

        response = self.client.get(reverse("core:desempenho_cozinha"), {"perfil": "auxiliares"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [preparation.dish_name for preparation in response.context["preparations"]],
            ["Molho de tomate"],
        )

    def test_cook_login_redirects_to_kitchen_dashboard(self):
        self.client.logout()
        response = self.client.post(
            reverse("core:login"),
            {"username": self.cook.email, "password": "senha123"},
            follow=True,
        )

        self.assertRedirects(response, reverse("core:perfil_cozinheiro"))

    def test_non_kitchen_user_is_redirected(self):
        waiter = User.objects.create_user(username="kitchen_waiter", password="senha123")
        waiter_group, _ = Group.objects.get_or_create(name="Garçom")
        waiter.groups.add(waiter_group)
        self.client.force_login(waiter)

        response = self.client.get(reverse("core:perfil_cozinheiro"))

        self.assertRedirects(response, reverse("core:pedidos"))

    def test_auxiliary_cannot_open_cook_profile(self):
        self.client.force_login(self.auxiliary)

        response = self.client.get(reverse("core:perfil_cozinheiro"))

        self.assertRedirects(response, reverse("core:home"))

    def test_admin_can_view_cook_dashboard_without_kitchen_actions(self):
        order = self.create_kitchen_order()
        administrator = User.objects.create_superuser(
            username="admin_cook_blocked@sabor.test",
            email="admin_cook_blocked@sabor.test",
            password="senha123",
        )
        self.client.force_login(administrator)

        response = self.client.get(reverse("core:perfil_cozinheiro"))

        self.assertEqual(response.status_code, 200)
        home = self.client.get(reverse("core:home"))
        self.assertContains(home, reverse("core:perfil_cozinheiro"))
        self.assertFalse(response.context["can_record_preparation"])
        self.assertContains(response, "Perfil exclusivo do cozinheiro")
        self.assertNotContains(response, "Perfil ativo")
        self.assertNotContains(response, "Perfil visualizado")
        self.assertNotContains(response, f'data-kitchen-light="{order.pk}"')
        self.assertNotContains(response, "Confirmar pedido")
        self.assertEqual(self.client.get(reverse("core:desempenho_cozinha")).status_code, 200)

    def test_admin_cannot_register_kitchen_preparation(self):
        administrator = User.objects.create_superuser(
            username="admin_kitchen_post@sabor.test",
            email="admin_kitchen_post@sabor.test",
            password="senha123",
        )
        self.client.force_login(administrator)

        response = self.client.post(
            reverse("core:perfil_cozinheiro"),
            {"dish_name": "Preparo administrativo", "status": "Concluído", "duration_minutes": 10},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(KitchenPreparation.objects.filter(dish_name="Preparo administrativo").exists())

    def test_home_and_kitchen_menus_omit_dashboard_and_expose_routes(self):
        home = self.client.get(reverse("core:home"))
        kitchen = self.client.get(reverse("core:perfil_cozinheiro"))

        self.assertEqual(home.status_code, 200)
        self.assertEqual(kitchen.status_code, 200)
        self.assertNotContains(home, ">Dashboard<")
        self.assertNotContains(kitchen, ">Dashboard<")
        for route_name in ("atendimento", "receitas", "perfil_cozinheiro", "relatorios"):
            with self.subTest(route_name=route_name):
                self.assertContains(home, reverse(f"core:{route_name}"))
        self.assertContains(kitchen, reverse("core:perfil_cozinheiro"))
        self.assertNotContains(kitchen, reverse("core:home"))
        self.assertNotContains(kitchen, reverse("core:desempenho_cozinha"))
        self.assertNotContains(home, reverse("core:produtos"))
        self.assertNotContains(kitchen, reverse("core:produtos"))
        for route_name in ("atendimento", "receitas", "relatorios", "funcionarios"):
            self.assertNotContains(kitchen, reverse(f"core:{route_name}"))
        self.assertNotContains(kitchen, "Voltar")

    def test_staff_page_has_home_navigation_without_back_button(self):
        manager = User.objects.create_user(username="staff_manager@sabor.test", password="senha123")
        management_group, _ = Group.objects.get_or_create(name="Gestão")
        manager.groups.add(management_group)
        self.client.force_login(manager)
        response = self.client.get(reverse("core:funcionarios"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("core:home"))
        self.assertNotContains(response, "Voltar")


class ReadyOrdersWorkflowTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Pedidos Prontos Teste", slug="pedidos-prontos-teste")
        self.waiter = self.create_waiter("garcom.principal@sabor.test")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.waiter,
            role=TenantMembership.Role.WAITER,
        )
        self.client.force_login(self.waiter)

    def create_waiter(self, username):
        waiter = User.objects.create_user(username=username, password="senha123")
        group, _ = Group.objects.get_or_create(name="Garçom")
        waiter.groups.add(group)
        return waiter

    def create_order(self, status, **overrides):
        data = {
            "waiter": self.waiter,
            "tenant": self.tenant,
            "customer_name": "Cliente Teste",
            "table_number": 4,
            "items": [{"nome": "Pizza Calabresa", "quantidade": 2}],
            "subtotal": Decimal("40.00"),
            "service_fee": Decimal("0.00"),
            "total": Decimal("40.00"),
            "status": status,
        }
        data.update(overrides)
        return Order.objects.create(**data)

    def test_ready_queue_and_notification_count_include_only_waiting_pickup(self):
        ready = self.create_order(Order.STATUS_READY, ready_at=timezone.now())
        out_for_delivery = self.create_order(
            Order.STATUS_OUT_FOR_DELIVERY,
            ready_at=timezone.now(),
            pickup_waiter=self.waiter,
            picked_up_at=timezone.now(),
        )
        delivered = self.create_order(
            Order.STATUS_DELIVERED,
            ready_at=timezone.now(),
            pickup_waiter=self.waiter,
            picked_up_at=timezone.now(),
            delivery_waiter=self.waiter,
            delivered_at=timezone.now(),
        )

        page = self.client.get(reverse("core:pedidos_prontos"))
        status = self.client.get(reverse("core:pedidos_prontos_status"))

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, f"{ready.pk:03d}")
        self.assertContains(page, f"{out_for_delivery.pk:03d}")
        self.assertNotContains(page, f"{delivered.pk:03d}")
        self.assertContains(page, "PEGAR PEDIDO")
        self.assertContains(page, "JÁ ENTREGUE")
        self.assertIn("confirm(", page.content.decode())
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["ready_count"], 1)
        self.assertEqual({row["id"] for row in status.json()["orders"]}, {ready.pk, out_for_delivery.pk})

    def test_pickup_is_claimed_once_and_records_waiter_and_time(self):
        order = self.create_order(Order.STATUS_READY, ready_at=timezone.now())
        other_waiter = self.create_waiter("garcom.segundo@sabor.test")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=other_waiter,
            role=TenantMembership.Role.WAITER,
        )

        first_response = self.client.post(reverse("core:pegar_pedido", args=[order.pk]))
        order.refresh_from_db()
        picked_up_at = order.picked_up_at
        second_client = self.client_class()
        second_client.force_login(other_waiter)
        second_response = second_client.post(reverse("core:pegar_pedido", args=[order.pk]))
        order.refresh_from_db()

        self.assertRedirects(first_response, reverse("core:pedidos_prontos"))
        self.assertEqual(order.status, Order.STATUS_OUT_FOR_DELIVERY)
        self.assertEqual(order.pickup_waiter, self.waiter)
        self.assertIsNotNone(picked_up_at)
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(order.pickup_waiter, self.waiter)
        self.assertEqual(order.picked_up_at, picked_up_at)

    def test_delivery_requires_pickup_and_preserves_order_history(self):
        order = self.create_order(Order.STATUS_READY, ready_at=timezone.now())

        premature_response = self.client.post(reverse("core:entregar_pedido", args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_READY)
        self.assertIsNone(order.delivered_at)

        self.client.post(reverse("core:pegar_pedido", args=[order.pk]))
        delivery_response = self.client.post(reverse("core:entregar_pedido", args=[order.pk]))
        order.refresh_from_db()

        self.assertEqual(premature_response.status_code, 302)
        self.assertEqual(delivery_response.status_code, 302)
        self.assertEqual(order.status, Order.STATUS_DELIVERED)
        self.assertEqual(order.delivery_waiter, self.waiter)
        self.assertIsNotNone(order.delivered_at)
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())
        self.assertNotContains(self.client.get(reverse("core:pedidos_prontos")), f"{order.pk:03d}")

    def test_non_waiter_cannot_access_queue_or_actions(self):
        administrator = User.objects.create_superuser(
            username="ready_orders_admin@sabor.test",
            email="ready_orders_admin@sabor.test",
            password="senha123",
        )
        order = self.create_order(Order.STATUS_READY)
        self.client.force_login(administrator)

        page = self.client.get(reverse("core:pedidos_prontos"))
        status = self.client.get(reverse("core:pedidos_prontos_status"))
        pickup = self.client.post(reverse("core:pegar_pedido", args=[order.pk]))

        self.assertRedirects(page, reverse("core:home"))
        self.assertEqual(status.status_code, 403)
        self.assertEqual(pickup.status_code, 403)
