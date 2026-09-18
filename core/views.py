from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def pedidos(request):
    return render(request, 'pedidos.html')


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


def login_view(request):

    if request.method == 'POST':

        email = request.POST.get('email')
        senha = request.POST.get('senha')

        try:
            usuario = User.objects.get(email=email)

            user = authenticate(
                request,
                username=usuario.username,
                password=senha
            )

        except User.DoesNotExist:
            user = None

        if user is not None:

            login(request, user)

            return redirect('pedidos')

        else:

            messages.error(
                request,
                'E-mail ou senha inválidos.'
            )

    return render(request, 'login.html')


@login_required
def produtos(request):
    return render(request, 'produtos.html')


@login_required
def relatorios(request):
    return render(request, 'relatorios.html')


@login_required
def home(request):
    return render(request, 'home.html')