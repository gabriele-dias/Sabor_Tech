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
    path("dashboard/", views.dashboard, name="dashboard"),
    path("", views.home, name="home-root"),
    path("pedidos/", views.pedidos, name="pedidos"),
    path("pedidos/concluir/", views.concluir_pedido, name="concluir_pedido"),
    path("produtos/", views.produtos, name="produtos"),
    path("relatorios/", views.relatorios, name="relatorios"),
]
