from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation
import json

from .models import Order


class RoleLoginView(auth_views.LoginView):
    def get_success_url(self):
        if is_waiter(self.request.user):
            return reverse('core:pedidos')
        return super().get_success_url()


def is_waiter(user):
    return user.groups.filter(name='Garçom').exists()


def redirect_waiter(request):
    if is_waiter(request.user):
        return redirect('core:pedidos')
    return None


def logout_view(request):
    logout(request)
    return redirect('core:login')


@login_required
def pedidos(request):
    if not request.user.is_superuser and not is_waiter(request.user):
        return redirect('core:home')
    return render(request, 'core/pedidos.html')


@login_required
@require_POST
def concluir_pedido(request):
    if not is_waiter(request.user) and not request.user.is_superuser:
        return JsonResponse({'error': 'Apenas garçons podem concluir pedidos.'}, status=403)

    try:
        payload = json.loads(request.body)
        items = payload.get('items', [])
        subtotal = Decimal(str(payload.get('subtotal', '0')))
        service_fee = Decimal(str(payload.get('service_fee', '0')))
        total = Decimal(str(payload.get('total', '0')))
    except (json.JSONDecodeError, InvalidOperation, TypeError, ValueError):
        return JsonResponse({'error': 'Dados do pedido inválidos.'}, status=400)

    if not items or subtotal <= 0 or total <= 0:
        return JsonResponse({'error': 'Adicione pelo menos um item ao pedido.'}, status=400)

    order = Order.objects.create(
        waiter=request.user,
        items=items,
        subtotal=subtotal,
        service_fee=service_fee,
        total=total,
    )
    return JsonResponse({'id': order.pk, 'message': 'Pedido enviado para a administração.'}, status=201)


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
    produtos = [
        {'nome': 'Pizza Marguerita', 'categoria': 'Pizzas', 'descricao': 'Molho de tomate, mozzarella e manjericão.', 'preco': '54,90', 'emoji': '🍕', 'disponivel': True},
        {'nome': 'Pizza Calabresa', 'categoria': 'Pizzas', 'descricao': 'Calabresa artesanal, cebola e mozzarella.', 'preco': '59,90', 'emoji': '🍕', 'disponivel': True},
        {'nome': 'X-Bacon', 'categoria': 'Lanches', 'descricao': 'Hambúrguer, bacon crocante e queijo.', 'preco': '34,90', 'emoji': '🍔', 'disponivel': True},
        {'nome': 'Lasanha da Casa', 'categoria': 'Massas', 'descricao': 'Camadas de massa, molho e queijo gratinado.', 'preco': '42,90', 'emoji': '🍝', 'disponivel': True},
        {'nome': 'Suco Natural', 'categoria': 'Bebidas', 'descricao': 'Escolha o sabor do dia, servido bem gelado.', 'preco': '9,90', 'emoji': '🥤', 'disponivel': True},
        {'nome': 'Brownie com Sorvete', 'categoria': 'Sobremesas', 'descricao': 'Brownie quente, sorvete e calda de chocolate.', 'preco': '18,90', 'emoji': '🍰', 'disponivel': False},
    ]
    return render(request, 'core/produtos.html', {'produtos': produtos})


@login_required
def receitas(request):
    waiter_redirect = redirect_waiter(request)
    if waiter_redirect:
        return waiter_redirect
    return render(request, 'core/receitas.html')


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
    })


@login_required
def home(request):
    waiter_redirect = redirect_waiter(request)
    if waiter_redirect:
        return waiter_redirect
    return render(request, 'core/home.html')