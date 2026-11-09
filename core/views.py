from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponseForbidden, JsonResponse
from django.template.loader import render_to_string
from django.db.models import Avg
from django.db import transaction
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal, InvalidOperation
import json

from .forms import (
    KitchenPreparationForm,
    RecipeCreateForm,
    RecipeIngredientFormSet,
    StaffCreateForm,
    StockMovementForm,
)
from .models import (
    Client,
    Ingredient,
    InventoryMovement,
    KitchenPreparation,
    Order,
    Product,
    Recipe,
    RecipeIngredient,
    TenantMembership,
)
from .services import InsufficientStockError, OrderPayloadError, create_order_from_payload
from .tenancy import membership_for_request


class RoleLoginView(auth_views.LoginView):
    def get_success_url(self):
        if is_cook(self.request.user):
            return reverse('core:perfil_cozinheiro')
        if is_waiter(self.request.user):
            return reverse('core:pedidos')
        if can_manage_staff(self.request.user):
            return reverse('core:perfil_administrativo')
        return super().get_success_url()


def is_waiter(user):
    return user.groups.filter(name='Garçom').exists()


def can_manage_staff(user):
    return user.is_superuser or user.groups.filter(name='Gestão').exists()


def is_kitchen_user(user):
    return user.groups.filter(name__in=('Chefe de Cozinha', 'Auxiliar de cozinha')).exists()


def is_cook(user):
    return user.groups.filter(name='Chefe de Cozinha').exists()


def can_access_kitchen(user):
    return can_manage_staff(user)


def can_access_cook_profile(user):
    return can_manage_staff(user) or is_cook(user)


def redirect_waiter(request):
    if is_waiter(request.user):
        return redirect('core:pedidos')
    return None


def logout_view(request):
    logout(request)
    return redirect('core:login')


def current_membership(request):
    return membership_for_request(request)


@login_required
def pedidos(request):
    membership = current_membership(request)
    if not is_waiter(request.user) or membership is None:
        return redirect('core:home')
    products = Product.objects.filter(tenant=membership.tenant, is_available=True)
    return render(request, 'core/pedidos.html', {
        'products': products,
        'ready_count': Order.objects.filter(tenant=membership.tenant, status=Order.STATUS_READY).count(),
        'can_manage_staff': can_manage_staff(request.user),
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
        'is_waiter': is_waiter(request.user),
    })


@login_required
@require_POST
def concluir_pedido(request):
    membership = current_membership(request)
    if not is_waiter(request.user) or membership is None:
        return JsonResponse({'error': 'Apenas garçons podem concluir pedidos.'}, status=403)

    try:
        payload = json.loads(request.body)
        order = create_order_from_payload(waiter=request.user, membership=membership, payload=payload)
    except (json.JSONDecodeError, TypeError, OrderPayloadError) as error:
        return JsonResponse({'error': str(error) or 'Dados do pedido inválidos.'}, status=400)
    except InsufficientStockError as error:
        return JsonResponse({'error': str(error)}, status=409)
    return JsonResponse({'id': order.pk, 'message': 'Pedido enviado para a administração.'}, status=201)


def waiter_ready_orders(tenant):
    orders = Order.objects.filter(
        tenant=tenant,
        status__in=(Order.STATUS_READY, Order.STATUS_OUT_FOR_DELIVERY),
    ).select_related('client', 'pickup_waiter', 'delivery_waiter').order_by('ready_at', 'created_at')
    order_rows = []
    for order in orders:
        items = []
        for item in order.items or []:
            if not isinstance(item, dict):
                continue
            name = item.get('nome') or item.get('name') or item.get('product_name') or item.get('produto') or 'Item'
            quantity = item.get('quantidade') or item.get('quantity') or 1
            items.append({'name': name, 'quantity': quantity})
        order_rows.append({
            'id': order.pk,
            'status': order.status,
            'customer_name': order.customer_name or (order.client.name if order.client else ''),
            'table_number': order.table_number,
            'items': items,
            'ready_at_label': timezone.localtime(order.ready_at).strftime('%H:%M') if order.ready_at else '—',
            'pickup_waiter_name': order.pickup_waiter.get_full_name() if order.pickup_waiter else '',
            'picked_up_at_label': timezone.localtime(order.picked_up_at).strftime('%H:%M') if order.picked_up_at else '',
            'delivery_waiter_name': order.delivery_waiter.get_full_name() if order.delivery_waiter else '',
        })
    return order_rows


@login_required
def pedidos_prontos(request):
    membership = current_membership(request)
    if not is_waiter(request.user) or membership is None:
        return redirect('core:home')
    order_rows = waiter_ready_orders(membership.tenant)
    return render(request, 'core/pedidos_prontos.html', {
        'orders': order_rows,
        'ready_count': sum(order['status'] == Order.STATUS_READY for order in order_rows),
        'can_manage_staff': can_manage_staff(request.user),
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
    })


@login_required
@require_GET
def pedidos_prontos_status(request):
    membership = current_membership(request)
    if not is_waiter(request.user) or membership is None:
        return JsonResponse({'error': 'Apenas garçons podem consultar pedidos prontos.'}, status=403)
    orders = waiter_ready_orders(membership.tenant)
    return JsonResponse({
        'ready_count': sum(order['status'] == Order.STATUS_READY for order in orders),
        'orders': orders,
        'html': render_to_string(
            'core/_pedidos_prontos_cards.html',
            {'orders': orders},
            request=request,
        ),
    })


@login_required
@require_POST
def pegar_pedido(request, order_id):
    membership = current_membership(request)
    if not is_waiter(request.user) or membership is None:
        return HttpResponseForbidden('Apenas garçons podem retirar pedidos.')

    updated = Order.objects.filter(
        pk=order_id,
        tenant=membership.tenant,
        status=Order.STATUS_READY,
        pickup_waiter__isnull=True,
        picked_up_at__isnull=True,
    ).update(
        status=Order.STATUS_OUT_FOR_DELIVERY,
        pickup_waiter=request.user,
        picked_up_at=timezone.now(),
    )
    if not updated:
        messages.warning(request, 'Este pedido já foi retirado ou não está aguardando retirada.')
    else:
        messages.success(request, f'Pedido #{order_id} retirado para entrega.')
    return redirect('core:pedidos_prontos')


@login_required
@require_POST
def entregar_pedido(request, order_id):
    membership = current_membership(request)
    if not is_waiter(request.user) or membership is None:
        return HttpResponseForbidden('Apenas garçons podem confirmar entregas.')

    updated = Order.objects.filter(
        pk=order_id,
        tenant=membership.tenant,
        status=Order.STATUS_OUT_FOR_DELIVERY,
        pickup_waiter__isnull=False,
        picked_up_at__isnull=False,
        delivered_at__isnull=True,
    ).update(
        status=Order.STATUS_DELIVERED,
        delivery_waiter=request.user,
        delivered_at=timezone.now(),
    )
    if not updated:
        messages.warning(request, 'O pedido precisa ser retirado antes de confirmar a entrega.')
    else:
        messages.success(request, f'Pedido #{order_id} marcado como entregue.')
    return redirect('core:pedidos_prontos')


@login_required
def dashboard(request):
    waiter_redirect = redirect_waiter(request)
    if waiter_redirect:
        return waiter_redirect
    pedidos_mock = [
        {
            'id': 101,
            'cliente': 'Maria Costa',
            'data': '2026-09-12',
            'valor': 45.5,
            'status': 'Pendente',
            'atraso_min': 12,
            'custo_receita': 20.0,
            'lucro': 25.5,
        },
        {
            'id': 102,
            'cliente': 'João Pereira',
            'data': '2026-09-13',
            'valor': 99.0,
            'status': 'Entregue',
            'atraso_min': 0,
            'custo_receita': 45.0,
            'lucro': 54.0,
        },
    ]
    clientes = [
        {'nome': 'Maria Costa', 'mais_pedido': 'Pizza Marguerita', 'tempo_medio': '18 min'},
        {'nome': 'João Pereira', 'mais_pedido': 'Lasanha', 'tempo_medio': '22 min'},
    ]
    receita = {
        'nome': 'Pizza Marguerita',
        'sabor': 'Tradicional',
        'ingredientes': [
            {'quantidade': 500, 'unidade': 'g', 'nome': 'farinha de trigo'},
            {'quantidade': 300, 'unidade': 'g', 'nome': 'molho de tomate'},
        ],
    }
    total_vendas = sum(item['valor'] for item in pedidos_mock)
    valor_custo = sum(item['custo_receita'] for item in pedidos_mock)
    lucro_total = total_vendas - valor_custo
    period_days = 2
    date_start = request.GET.get('date_start', '2026-09-12')
    date_end = request.GET.get('date_end', '2026-09-13')

    context = {
        'can_manage_staff': can_manage_staff(request.user),
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
        'date_start': date_start,
        'date_end': date_end,
        'period_days': period_days,
        'total_vendas': total_vendas,
        'valor_custo': valor_custo,
        'lucro_total': lucro_total,
        'media_vendas': total_vendas / period_days,
        'pedidos': pedidos_mock,
        'clientes': clientes,
        'receita': receita,
        'orders_received': Order.objects.select_related('waiter')[:20],
    }
    return render(request, 'core/dashboard.html', context)


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        try:
            usuario = User.objects.get(email=email)
            user = authenticate(request, username=usuario.username, password=senha)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect('core:home')

        messages.error(request, 'E-mail ou senha inválidos.')

    return render(request, 'core/login.html', {'form': None})


@login_required
def produtos(request):
    waiter_redirect = redirect_waiter(request)
    if waiter_redirect:
        return waiter_redirect
    if not can_manage_staff(request.user):
        return redirect('core:home')
    membership = current_membership(request)
    if membership is None:
        return redirect('core:home')
    produtos = Product.objects.filter(tenant=membership.tenant).order_by('category', 'name')
    return render(request, 'core/produtos.html', {
        'produtos': produtos,
        'can_manage_staff': can_manage_staff(request.user),
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
    })


@login_required
def receitas(request):
    waiter_redirect = redirect_waiter(request)
    if waiter_redirect:
        return waiter_redirect
    membership = current_membership(request)
    if membership is None:
        return redirect('core:home')

    form = RecipeCreateForm(request.POST or None)
    ingredient_formset = RecipeIngredientFormSet(request.POST or None, prefix='ingredients')
    if request.method == 'POST' and form.is_valid() and ingredient_formset.is_valid():
        active_lines = [
            line for line in ingredient_formset.forms
            if line.cleaned_data and not line.cleaned_data.get('DELETE', False)
        ]
        if not active_lines:
            ingredient_formset.forms[0].add_error(None, 'Inclua pelo menos um ingrediente na ficha.')

        if Product.objects.filter(tenant=membership.tenant, name__iexact=form.cleaned_data['name']).exists():
            form.add_error('name', 'Já existe um produto com esse nome nesta empresa.')

        for line in active_lines:
            existing = Ingredient.objects.filter(
                tenant=membership.tenant,
                name__iexact=line.cleaned_data['name'],
            ).first()
            if existing and existing.unit != line.cleaned_data['unit']:
                line.add_error('unit', f'Este insumo já está cadastrado em {existing.unit}.')

        if form.is_valid() and ingredient_formset.is_valid() and active_lines:
            with transaction.atomic():
                product = Product.objects.create(
                    tenant=membership.tenant,
                    name=form.cleaned_data['name'],
                    category=form.cleaned_data['category'],
                    description=form.cleaned_data['description'],
                    sale_price=form.cleaned_data['sale_price'],
                )
                recipe = Recipe.objects.create(
                    tenant=membership.tenant,
                    product=product,
                    yield_quantity=form.cleaned_data['yield_quantity'],
                    prep_time_minutes=form.cleaned_data['prep_time_minutes'],
                )
                for line in active_lines:
                    ingredient, created = Ingredient.objects.get_or_create(
                        tenant=membership.tenant,
                        name=line.cleaned_data['name'],
                        defaults={
                            'unit': line.cleaned_data['unit'],
                            'unit_cost': line.cleaned_data['unit_cost'],
                        },
                    )
                    if not created and ingredient.unit_cost != line.cleaned_data['unit_cost']:
                        ingredient.unit_cost = line.cleaned_data['unit_cost']
                        ingredient.save(update_fields=['unit_cost'])
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient,
                        quantity=line.cleaned_data['quantity'],
                    )
            messages.success(request, f'Receita {product.name} cadastrada e salva no cardápio.')
            return redirect('core:produtos')

    return render(request, 'core/receitas.html', {
        'form': form,
        'ingredient_formset': ingredient_formset,
        'can_manage_staff': can_manage_staff(request.user),
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
    })


@login_required
def atendimento(request):
    staff_admin = can_manage_staff(request.user)
    allowed = staff_admin or is_waiter(request.user) or is_kitchen_user(request.user)
    if not allowed:
        return redirect('core:home')

    orders = list(Order.objects.select_related('waiter').order_by('-created_at')[:30])
    order_rows = []
    occupied_tables = set()
    active_statuses = {'pendente', 'em preparo', 'saiu para entrega', 'atrasado'}
    delivery_statuses = {'Saiu para entrega', 'Em rota'}
    prep_count = 0
    delivery_count = 0
    active_age_minutes = []

    for order in orders:
        order_items = order.items if isinstance(order.items, list) else []
        item = next((entry for entry in order_items if isinstance(entry, dict)), {})
        table_number = item.get('mesa')
        try:
            table_number = int(table_number) if table_number not in (None, '') else None
        except (TypeError, ValueError):
            table_number = None

        status = order.status or 'Pendente'
        status_key = status.casefold()
        channel = item.get('canal') or item.get('origem') or 'Presencial'
        customer = item.get('cliente') or order.waiter.get_full_name() or order.waiter.username
        created_at = timezone.localtime(order.created_at)
        order_rows.append({
            'id': order.pk,
            'customer': customer,
            'table_number': table_number,
            'channel': channel,
            'created_label': created_at.strftime('%H:%M'),
            'total_label': f"R$ {order.total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'status': status,
            'status_class': slugify(status),
        })

        if status_key in active_statuses:
            if table_number:
                occupied_tables.add(table_number)
            active_age_minutes.append(max(0, int((timezone.now() - order.created_at).total_seconds() // 60)))
        if status_key == 'em preparo':
            prep_count += 1
        if status in delivery_statuses or str(channel).casefold() == 'delivery':
            delivery_count += 1

    search_term = request.GET.get('q', '').strip().casefold()
    status_filter = request.GET.get('status', '').strip()
    filtered_orders = order_rows
    if status_filter:
        filtered_orders = [row for row in filtered_orders if row['status'] == status_filter]
    if search_term:
        filtered_orders = [
            row for row in filtered_orders
            if search_term in row['customer'].casefold() or search_term in str(row['id'])
        ]

    tables = [
        {'number': number, 'occupied': number in occupied_tables}
        for number in range(1, 13)
    ]
    return render(request, 'core/atendimento.html', {
        'orders': filtered_orders,
        'orders_count': len(filtered_orders),
        'status_filter': status_filter,
        'search_term': request.GET.get('q', ''),
        'status_options': ('Pendente', 'Em preparo', 'Saiu para entrega', 'Entregue', 'Atrasado', 'Cancelado'),
        'occupied_count': len(occupied_tables),
        'table_count': len(tables),
        'tables': tables,
        'can_manage_staff': staff_admin,
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
        'prep_count': prep_count,
        'delivery_count': delivery_count,
        'average_minutes': round(sum(active_age_minutes) / len(active_age_minutes)) if active_age_minutes else 0,
    })


@login_required
def perfil_cozinheiro(request):
    cook_user = is_cook(request.user)
    if not can_access_cook_profile(request.user):
        waiter_redirect = redirect_waiter(request)
        if waiter_redirect:
            return waiter_redirect
        return redirect('core:home')

    if request.method == 'POST':
        if not cook_user:
            return HttpResponseForbidden('Somente o perfil de cozinheiro pode operar este painel.')

        action = request.POST.get('action')
        order_id = request.POST.get('order_id')
        if action in {'confirm_order', 'ready_order'} and order_id:
            order = get_object_or_404(Order, pk=order_id, tenant=current_membership(request).tenant)
            if action == 'confirm_order':
                if order.confirmed_at is None:
                    order.confirmed_at = timezone.now()
                if order.status in (Order.STATUS_PENDING, 'Pendente'):
                    order.status = Order.STATUS_PREPARING
                order.save(update_fields=['confirmed_at', 'status'])
                messages.success(request, f'Pedido #{order.pk} confirmado. Cronômetro iniciado.')
            elif action == 'ready_order':
                order.status = Order.STATUS_READY
                order.ready_at = order.ready_at or timezone.now()
                order.save(update_fields=['status', 'ready_at'])
                messages.success(request, f'Pedido #{order.pk} marcado como pronto. Cronômetro finalizado.')
            return redirect('core:perfil_cozinheiro')

        return HttpResponseForbidden('Ação inválida para o painel do cozinheiro.')

    membership = current_membership(request)
    orders = Order.objects.filter(tenant=membership.tenant).exclude(status__in=(Order.STATUS_CANCELLED, 'Entregue')).order_by('created_at') if membership else Order.objects.none()
    kitchen_orders = []
    server_now = timezone.now()
    server_now_ms = int(server_now.timestamp() * 1000)
    for order in orders:
        is_demo_order = order.customer_name.startswith('DEMO -')
        yellow_after_seconds = 10 if is_demo_order else 20 * 60
        red_after_seconds = 20 if is_demo_order else 30 * 60
        confirmed_at_ms = int(order.confirmed_at.timestamp() * 1000) if order.confirmed_at else None
        ready_at = order.ready_at or (server_now if order.status == Order.STATUS_READY else None)
        ready_at_ms = int(ready_at.timestamp() * 1000) if ready_at else None
        if not order.confirmed_at:
            traffic_light = 'pending'
            elapsed_label = ''
            trend_label = 'Aguardando confirmação'
        else:
            reference = ready_at or server_now
            total_seconds = max(0, int((reference - order.confirmed_at).total_seconds()))
            display_minutes, remainder = divmod(total_seconds, 60)
            elapsed_label = f'{display_minutes:02d}:{remainder:02d}'
            if order.status == Order.STATUS_READY:
                traffic_light = 'done'
                trend_label = 'Pedido concluído'
            elif total_seconds < yellow_after_seconds:
                traffic_light = 'green'
                trend_label = 'Tempo dentro do esperado'
            elif total_seconds < red_after_seconds:
                traffic_light = 'yellow'
                trend_label = 'Atenção ao tempo'
            else:
                traffic_light = 'red'
                trend_label = 'Pedido atrasado · prioridade'

        if traffic_light == 'red':
            priority = 0
        elif traffic_light == 'yellow':
            priority = 1
        elif traffic_light == 'green':
            priority = 2
        elif traffic_light == 'pending':
            priority = 3
        else:
            priority = 4

        item_lines = []
        for item in order.items or []:
            if not isinstance(item, dict):
                continue
            name = item.get('name') or item.get('product_name') or item.get('nome') or item.get('produto') or item.get('item') or 'Item'
            quantity = item.get('quantity') or item.get('quantidade') or 1
            item_lines.append(f'{quantity}x {name}')
        if not item_lines:
            item_lines.append('Pedido em andamento')

        kitchen_orders.append({
            'id': order.pk,
            'status': order.status,
            'status_class': slugify(order.status),
            'traffic_light': traffic_light,
            'elapsed_label': elapsed_label,
            'trend_label': trend_label,
            'confirmed_at_ms': confirmed_at_ms,
            'ready_at_ms': ready_at_ms,
            'yellow_after_seconds': yellow_after_seconds,
            'red_after_seconds': red_after_seconds,
            'priority': priority,
            'customer': order.customer_name or order.waiter.get_full_name() or order.waiter.username,
            'table_number': order.table_number,
            'responsible': order.waiter.get_full_name() or order.waiter.username,
            'items': item_lines,
            'observation': order.items[0].get('observacao') if order.items and isinstance(order.items[0], dict) else '',
        })

    kitchen_orders.sort(key=lambda order: order['priority'])

    return render(request, 'core/desempenho_cozinha.html', {
        'can_manage_staff': can_manage_staff(request.user),
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
        'can_record_preparation': cook_user,
        'kitchen_orders': kitchen_orders,
        'server_now_ms': server_now_ms,
    })


@login_required
def desempenho_cozinha(request):
    if not can_manage_staff(request.user):
        waiter_redirect = redirect_waiter(request)
        if waiter_redirect:
            return waiter_redirect
        return redirect('core:home')

    form = KitchenPreparationForm(request.POST or None)
    if request.method == 'POST':
        if not can_manage_staff(request.user):
            return HttpResponseForbidden('Somente o perfil administrativo pode registrar preparos nesta tela.')
        if form.is_valid():
            KitchenPreparation.objects.create(
                responsible=request.user,
                dish_name=form.cleaned_data['dish_name'],
                status=form.cleaned_data['status'],
                duration_minutes=form.cleaned_data['duration_minutes'],
            )
            messages.success(request, 'Preparo registrado com sucesso.')
            return redirect('core:desempenho_cozinha')

    today = timezone.localdate()
    today_preparations = KitchenPreparation.objects.filter(created_at__date=today)
    completed_today = today_preparations.filter(status=KitchenPreparation.STATUS_COMPLETED)
    average_duration = completed_today.aggregate(value=Avg('duration_minutes'))['value'] or 0

    profile_filter = request.GET.get('perfil', 'todos')
    preparations = KitchenPreparation.objects.select_related('responsible').prefetch_related('responsible__groups')
    if profile_filter == 'cozinheiros':
        preparations = preparations.filter(responsible__groups__name='Chefe de Cozinha')
    elif profile_filter == 'auxiliares':
        preparations = preparations.filter(responsible__groups__name='Auxiliar de cozinha')

    preparation_rows = list(preparations[:50])
    for preparation in preparation_rows:
        groups = {group.name for group in preparation.responsible.groups.all()}
        preparation.profile_label = 'Cozinheiro' if 'Chefe de Cozinha' in groups else 'Auxiliar de cozinha'
        preparation.created_label = timezone.localtime(preparation.created_at).strftime('%H:%M')
        preparation.duration_label = (
            f'{preparation.duration_minutes} min' if preparation.duration_minutes else 'Em andamento'
        )
        preparation.status_class = slugify(preparation.status)

    return render(request, 'core/desempenho_metricas.html', {
        'can_manage_staff': can_manage_staff(request.user),
        'can_access_kitchen': True,
        'can_access_cook_profile': can_access_cook_profile(request.user),
        'can_record_preparation': can_manage_staff(request.user),
        'form': form,
        'preparations': preparation_rows,
        'preparation_count': today_preparations.count(),
        'average_duration': round(average_duration),
        'active_cooks': User.objects.filter(is_active=True, groups__name='Chefe de Cozinha').distinct().count(),
        'active_assistants': User.objects.filter(is_active=True, groups__name='Auxiliar de cozinha').distinct().count(),
        'profile_filter': profile_filter,
    })


@login_required
def perfil_administrativo(request):
    if not can_manage_staff(request.user):
        waiter_redirect = redirect_waiter(request)
        if waiter_redirect:
            return waiter_redirect
        return redirect('core:home')

    return render(request, 'core/perfil_administrativo.html', {
        'can_manage_staff': True,
        'can_access_kitchen': True,
        'can_access_cook_profile': True,
    })


@login_required
def funcionarios(request):
    if not can_manage_staff(request.user):
        waiter_redirect = redirect_waiter(request)
        if waiter_redirect:
            return waiter_redirect
        return redirect('core:home')

    form = StaffCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        full_name = form.cleaned_data['full_name']
        first_name, _, last_name = full_name.partition(' ')
        email = form.cleaned_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=form.cleaned_data['password'],
            first_name=first_name,
            last_name=last_name,
        )
        group_name = {
            'garcom': 'Garçom',
            'administrador': 'Gestão',
            'cozinheiro': 'Chefe de Cozinha',
            'auxiliar': 'Auxiliar de cozinha',
        }[form.cleaned_data['profile']]
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        messages.success(request, f'Funcionário {full_name} cadastrado com sucesso.')
        return redirect('core:funcionarios')

    return render(request, 'core/funcionarios.html', {
        'form': form,
        'can_manage_staff': True,
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
    })


@login_required
def clientes(request):
    waiter_redirect = redirect_waiter(request)
    if waiter_redirect:
        return waiter_redirect
    return render(request, 'core/clientes.html', {
        'clientes': [],
        'can_manage_staff': can_manage_staff(request.user),
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
    })


@login_required
def configuracoes(request):
    waiter_redirect = redirect_waiter(request)
    if waiter_redirect:
        return waiter_redirect
    return render(request, 'core/configuracoes.html', {
        'can_manage_staff': can_manage_staff(request.user),
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
    })


@login_required
def relatorios(request):
    waiter_redirect = redirect_waiter(request)
    if waiter_redirect:
        return waiter_redirect
    orders = list(Order.objects.order_by('created_at')[:30])
    report_data = {
        'labels': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
        'sales': [4200, 5100, 4800, 6300, 7200, 8400, 7900],
        'costs': [1700, 2100, 1950, 2600, 3050, 3520, 3300],
        'profits': [2500, 3000, 2850, 3700, 4150, 4880, 4600],
        'dishes': ['Pizza Marguerita', 'Lasanha', 'X-Bacon', 'Pizza Calabresa', 'Suco Natural'],
        'dish_values': [142, 118, 96, 84, 71],
        'ingredients': ['Farinha', 'Queijo', 'Tomate', 'Carne', 'Bebidas'],
        'ingredient_values': [31, 25, 18, 15, 11],
        'heatmap': [2, 4, 7, 11, 15, 22, 28, 25, 18, 12, 7, 4],
    }
    if orders:
        total = sum(float(order.total) for order in orders)
        report_data['sales'][-1] = round(total, 2)
        report_data['costs'][-1] = round(total * 0.38, 2)
        report_data['profits'][-1] = round(total * 0.62, 2)
    return render(request, 'core/relatorios.html', {
        'report_data': report_data,
        'orders_count': len(orders) or 148,
        'orders_received': orders,
        'can_manage_staff': can_manage_staff(request.user),
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
    })


@login_required
def home(request):
    return render(request, 'core/home.html', {
        'can_manage_staff': can_manage_staff(request.user),
        'can_access_kitchen': can_access_kitchen(request.user),
        'can_access_cook_profile': can_access_cook_profile(request.user),
        'is_waiter': is_waiter(request.user),
    })