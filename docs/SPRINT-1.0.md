# Sprint 1.0 — Frontend protótipo (Django templates + HTMx)

Resumo
- Objetivo: criar o protótipo frontend em Django templates com interações parciais via HTMx para o TCC "Sabor e Gestão".
- Branch atual de trabalho: `feature/Versão_0.1`.
- Escopo: base visual, layout responsivo, páginas de dashboard/atendimento/clientes/produtos/relatórios/configurações, modal de login e fluxo inicial de autenticação visual.

O que foi adicionado
- Views e endpoints HTMx (mock/in-memory) em `core/views.py`:
  - `dashboard`, `atendimento`, `clientes_page`, `produtos_page`, `relatorios`, `configuracoes`.
  - Partials: `orders_partial`, `clients_partial`, `change_status`, `add_client` (usados por HTMx).
- URLs: `core/urls.py` (rotas para páginas e endpoints HTMx).
- Templates em `core/templates/core/`:
  - `base.html` (layout com sidebar, login modal e estrutura comum), `dashboard.html`, `atendimento.html`, `clientes.html`, `produtos.html`, `relatorios.html`, `configuracoes.html`.
  - Partials: `_orders.html`, `_clients_list.html`, `_time.html`.
  - Login: `login.html` como página/artefato de autenticação inicial integrada ao layout.
- Middleware/regras de autenticação visual e configuração inicial em `setup/settings.py`.
- Migração inicial de roles de acesso: `core/migrations/0002_create_roles.py`.
- Estáticos em `core/static/core/`:
  - `css/app.css` (paleta e layout responsivo), `js/app.js` (login modal + 2FA simulado).

Como rodar localmente
1. Ative o ambiente virtual do projeto:
```bash
source .venv/Scripts/activate
```
2. Rode o servidor de desenvolvimento Django:
```bash
python manage.py runserver
```
3. Acesse as páginas:
- Dashboard: `http://127.0.0.1:8000/`
- Atendimento (ex.: HTMx): `http://127.0.0.1:8000/atendimento/`
- Login/Autenticação visual: `http://127.0.0.1:8000/login/` quando a rota estiver disponível em `core/urls.py`.

Testes rápidos (HTMx)
- Buscar pedidos: use o campo de busca + botão "Buscar" — a lista de pedidos será carregada/filtrada via HTMx.
- Alterar status: no card de pedido, selecione novo status e clique em "Alterar" — a lista é atualizada via HTMx.
- Cadastro de cliente: preencha o formulário e envie — a lista de clientes é atualizada sem reload.
- Fluxo de login: o modal/visual de autenticação deve levar ao acesso inicial do sistema em template.

Notas importantes
- Os dados são *mock* mantidos em memória (variáveis `ORDERS`, `CLIENTS`) apenas para protótipo. Para persistência, implementar modelos Django e views/serializers apropriados.
- A branch atual onde foi feita a alteração: `feature/Versão_0.1`.
- O diretório `.venv` é local ao ambiente de desenvolvimento e está listado em `.gitignore`; ele não deve ser versionado no GitHub.

Próximos passos sugeridos
- Implementar CRUD simulado adicional: editar/excluir cliente, criar pedido.
- Adicionar testes básicos de integração front-back (HTMx).
- Melhorar estilos e responsividade (mobile) e adicionar ícones.
- Finalizar a modelagem de autenticação real com usuários, permissões e migrações persistentes.
