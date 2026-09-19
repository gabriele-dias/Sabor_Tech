from django.contrib.auth import views as auth_views
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse


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


@login_required
def pedidos(request):
    if not request.user.is_superuser and not is_waiter(request.user):
        return redirect('core:home')
    return render(request, 'core/pedidos.html')


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
    return render(request, 'core/produtos.html', {'produtos': []})


@login_required
def relatorios(request):
    waiter_redirect = redirect_waiter(request)
    if waiter_redirect:
        return waiter_redirect
    return render(request, 'core/relatorios.html')


@login_required
def home(request):
    waiter_redirect = redirect_waiter(request)
    if waiter_redirect:
        return waiter_redirect
    return render(request, 'core/home.html')