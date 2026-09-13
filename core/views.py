from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.utils import timezone

from .calculations import calculate_receita


def user_has_role(user, roles):
	if not user.is_active:
		return False
	return user.groups.filter(name__in=roles).exists()


def role_required(roles):
	return user_passes_test(lambda u: user_has_role(u, roles), login_url='/login/')


# Mock data stores (in-memory, for prototype only)
ORDERS = [
	{"id": 101, "cliente": "João Silva", "status": "Pendente", "atraso_min": 12, "valor": 45.50},
	{"id": 102, "cliente": "Maria Costa", "status": "Saiu para entrega", "atraso_min": 3, "valor": 67.00},
	{"id": 103, "cliente": "Pedro Alves", "status": "Atrasado", "atraso_min": 27, "valor": 32.00},
]

CLIENTS = [
	{"id": 1, "nome": "João Silva", "telefone": "(11) 99999-0001"},
	{"id": 2, "nome": "Maria Costa", "telefone": "(11) 98888-1111"},
]


@role_required(['Gestão'])
def index(request):
	"""Página inicial que mostra exemplo de HTMx."""
	now = timezone.now()
	return render(request, "core/index.html", {"now": now})


@role_required(['Gestão'])
def time_partial(request):
	"""Retorna apenas o fragmento de hora — usado por HTMx."""
	now = timezone.now()
	return render(request, "core/_time.html", {"now": now})


@role_required(['Gestão'])
def dashboard(request):
	"""Dashboard principal com lista de pedidos, clientes e cálculo de receita."""
	pedidos = ORDERS
	clientes = [
		{"nome": c["nome"], "mais_pedido": "Margherita", "tempo_medio": "30m"} for c in CLIENTS
	]

	calculo = None
	form_data = {"quantidade_por_pessoa": "0.40", "pessoas": "30", "custo_unitario": "8.50"}
	error_message = None

	if request.method == "POST":
		form_data = {
			"quantidade_por_pessoa": request.POST.get("quantidade_por_pessoa", "0.40"),
			"pessoas": request.POST.get("pessoas", "30"),
			"custo_unitario": request.POST.get("custo_unitario", "8.50"),
		}
		try:
			calculo = calculate_receita(
				Decimal(form_data["quantidade_por_pessoa"]),
				int(form_data["pessoas"]),
				Decimal(form_data["custo_unitario"]),
			)
		except (InvalidOperation, TypeError, ValueError):
			error_message = "Informe valores válidos para quantidade, pessoas e custo unitário."

	return render(request, "core/dashboard.html", {
		"pedidos": pedidos,
		"clientes": clientes,
		"calculo": calculo,
		"form_data": form_data,
		"error_message": error_message,
	})


@role_required(['Gestão', 'Chefe de Cozinha'])
def atendimento(request):
	"""Página de atendimento (esqueleto)."""
	return render(request, "core/atendimento.html", {"orders": ORDERS, "clients": CLIENTS})


@role_required(['Gestão', 'Chefe de Cozinha'])
def orders_partial(request):
	"""Retorna o fragmento com a lista de pedidos, possivelmente filtrada."""
	q = request.GET.get('q', '').lower()
	status = request.GET.get('status', '')
	filtered = ORDERS
	if q:
		filtered = [o for o in filtered if q in o['cliente'].lower() or q in str(o['id'])]
	if status:
		filtered = [o for o in filtered if o['status'] == status]
	return render(request, "core/_orders.html", {"orders": filtered})


@role_required(['Gestão', 'Chefe de Cozinha'])
def change_status(request):
	"""Altera o status de um pedido (POST via HTMx) e retorna o fragmento atualizado."""
	if request.method == 'POST':
		oid = int(request.POST.get('order_id'))
		new_status = request.POST.get('new_status')
		for o in ORDERS:
			if o['id'] == oid:
				o['status'] = new_status
				break
	return render(request, "core/_orders.html", {"orders": ORDERS})


@role_required(['Gestão', 'Chefe de Cozinha'])
def clients_partial(request):
	return render(request, "core/_clients_list.html", {"clients": CLIENTS})


@role_required(['Gestão', 'Chefe de Cozinha'])
def add_client(request):
	"""Adiciona cliente (POST via HTMx) e retorna a lista atualizada."""
	if request.method == 'POST':
		nome = request.POST.get('nome')
		telefone = request.POST.get('telefone')
		nid = max([c['id'] for c in CLIENTS]) + 1 if CLIENTS else 1
		CLIENTS.append({"id": nid, "nome": nome, "telefone": telefone})
	return render(request, "core/_clients_list.html", {"clients": CLIENTS})


@role_required(['Gestão'])
def clientes_page(request):
	"""Lista de clientes (esqueleto)."""
	clientes = [
		{"nome": "João Silva", "telefone": "(11) 99999-0001"},
		{"nome": "Maria Costa", "telefone": "(11) 98888-1111"},
	]
	return render(request, "core/clientes.html", {"clientes": clientes})


@role_required(['Gestão'])
def produtos_page(request):
	"""Lista de produtos (esqueleto)."""
	produtos = [
		{"nome": "Margherita", "preco": 32.0},
		{"nome": "Calabresa", "preco": 36.5},
	]
	return render(request, "core/produtos.html", {"produtos": produtos})


@role_required(['Gestão'])
def relatorios(request):
	"""Página de relatórios (esqueleto)."""
	return render(request, "core/relatorios.html")


@role_required(['Gestão'])
def configuracoes(request):
	"""Página de configurações/admin (esqueleto)."""
	return render(request, "core/configuracoes.html")
