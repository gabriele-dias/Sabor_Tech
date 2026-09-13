from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from .forms import SaborTechLoginForm

app_name = "core"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="core/login.html", authentication_form=SaborTechLoginForm),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/"), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("atendimento/orders/", views.orders_partial, name="orders_partial"),
    path("atendimento/change_status/", views.change_status, name="change_status"),
    path("atendimento/clients/", views.clients_partial, name="clients_partial"),
    path("atendimento/clients/add/", views.add_client, name="add_client"),
    path("atendimento/", views.atendimento, name="atendimento"),
    path("clientes/", views.clientes_page, name="clientes"),
    path("produtos/", views.produtos_page, name="produtos"),
    path("relatorios/", views.relatorios, name="relatorios"),
    path("configuracoes/", views.configuracoes, name="configuracoes"),
]
