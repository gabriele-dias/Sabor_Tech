# Sprint 1.0 — Frontend protótipo (Django templates + HTMx)

## Resumo

- Objetivo: criar a base visual e a estrutura de acesso da plataforma Sabor Tech.
- Branch ativa: `feature/Versão_0.1`.
- Escopo atual: dashboard, atendimento, clientes, produtos, relatórios, configurações, login e proteção por permissões por grupo.

## O que foi adicionado

- Views e endpoints HTMx em [core/views.py](core/views.py): `dashboard`, `atendimento`, `clientes_page`, `produtos_page`, `relatorios`, `configuracoes`, `orders_partial`, `clients_partial`, `change_status` e `add_client`.
- URLs em [core/urls.py](core/urls.py): rotas HTML e endpoints parcialmente interactivos.
- Templates em [core/templates/core](core/templates/core): `base.html`, `dashboard.html`, `atendimento.html`, `clientes.html`, `produtos.html`, `relatorios.html`, `configuracoes.html`, `_orders.html`, `_clients_list.html` e `login.html`.
- Regras de controle de acesso com `role_required` em [core/views.py](core/views.py).
- Migração de grupos de acesso em [core/migrations/0002_create_roles.py](core/migrations/0002_create_roles.py).
- Estáticos em [core/static/core](core/static/core).

## Como rodar localmente

1. Ative o ambiente virtual:

```bash
source .venv/Scripts/activate
```

No PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

2. Rode o servidor de desenvolvimento Django:

```bash
python manage.py runserver
```

3. Acesse:

- Dashboard: `http://127.0.0.1:8000/`
- Atendimento: `http://127.0.0.1:8000/atendimento/`
- Login: `http://127.0.0.1:8000/login/`

## Testes

Os testes básicos de acesso foram adicionados em [core/tests.py](core/tests.py) e validam:

- renderização da página de login
- redirecionamento da rota principal para o login quando o navegador entra sem autenticação

Comando para validar:

```bash
python manage.py test
```

## Observações importantes

- Os dados de pedidos/clientes continuam sendo `mock` em memória para o protótipo.
- A branch ativa é `feature/Versão_0.1`.
- O diretório `.venv` é local ao desenvolvimento e fica ignorado no GitHub por [.gitignore](.gitignore).
- A arquitetura ainda está em fase de protótipo e deve evoluir para persistência real com modelos e migrations de negócio.
