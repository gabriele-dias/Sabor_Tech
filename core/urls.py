from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("time/", views.time_partial, name="time_partial"),
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
