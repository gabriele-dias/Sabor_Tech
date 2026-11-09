from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from .forms import CardapioLoginForm

app_name = "core"

urlpatterns = [
    path(
        "login/",
        views.RoleLoginView.as_view(
            template_name="core/login.html",
            authentication_form=CardapioLoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
    path("home/", views.home, name="home"),
    path("perfil-administrativo/", views.perfil_administrativo, name="perfil_administrativo"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("", views.home, name="home-root"),
    path("pedidos/", views.pedidos, name="pedidos"),
    path("pedidos/concluir/", views.concluir_pedido, name="concluir_pedido"),
    path("pedidos/prontos/", views.pedidos_prontos, name="pedidos_prontos"),
    path("pedidos/prontos/status/", views.pedidos_prontos_status, name="pedidos_prontos_status"),
    path("pedidos/<int:order_id>/retirar/", views.pegar_pedido, name="pegar_pedido"),
    path("pedidos/<int:order_id>/entregar/", views.entregar_pedido, name="entregar_pedido"),
    path("atendimento/", views.atendimento, name="atendimento"),
    path("desempenho-cozinha/", views.desempenho_cozinha, name="desempenho_cozinha"),
    path("perfil-cozinheiro/", views.perfil_cozinheiro, name="perfil_cozinheiro"),
    path("funcionarios/", views.funcionarios, name="funcionarios"),
    path("funcionarios/novo/", views.funcionarios, name="funcionarios_novo"),
    path("produtos/", views.produtos, name="produtos"),
    path("receitas/", views.receitas, name="receitas"),
    path("relatorios/", views.relatorios, name="relatorios"),
    path("clientes/", views.clientes, name="clientes"),
    path("configuracoes/", views.configuracoes, name="configuracoes"),
]
