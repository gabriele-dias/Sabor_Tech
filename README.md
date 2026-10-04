# Sabor Tech

Sistema de gestão de restaurante desenvolvido com Django. O sistema reúne atendimento, pedidos, cardápio, receitas, controle de cozinha, funcionários e relatórios.

## Requisitos

- Python instalado;
- dependências de `requirements.txt`;
- SQLite local, criado pelo Django;
- navegador moderno.

## Instalação local

Na raiz do projeto:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver
```

No PowerShell, ative o ambiente com:

```powershell
.\.venv\Scripts\Activate.ps1
```

Abra `http://127.0.0.1:8000/`. Não há configuração Docker no repositório atual; `runserver` é somente para desenvolvimento local.

Para criar o primeiro administrador, execute `python manage.py createsuperuser`. Não armazene senhas no README, na documentação ou no Git.

## Perfis

- **Gestão/superusuário:** Home, atendimento, cardápio, receitas, relatórios e administração de funcionários. Algumas páginas legadas permanecem acessíveis por URL.
- **Garçom:** entra inicialmente em Pedidos e pode voltar à Home limitada, que oferece somente Atendimento, Pedidos e Sair.
- **Cozinheiro:** grupo Django `Chefe de Cozinha`; pode registrar preparos e consultar desempenho da cozinha.
- **Auxiliar de cozinha:** pode registrar preparos e consultar desempenho da cozinha.

As permissões são validadas nas views Django. A ocultação de links no HTML é apenas uma conveniência de navegação, não substitui autorização no servidor.

## Rotas principais

| Tela | Caminho |
|---|---|
| Login | `/login/` |
| Home | `/home/` |
| Pedidos | `/pedidos/` |
| Atendimento | `/atendimento/` |
| Cardápio | `/produtos/` |
| Adicionar receitas | `/receitas/` |
| Desempenho cozinha | `/desempenho-cozinha/` |
| Relatórios | `/relatorios/` |
| Funcionários | `/funcionarios/` |

As páginas internas têm um retorno à Home. Na Home, a ação Sair encerra a sessão e retorna ao Login. O Dashboard legado continua em `/dashboard/` por compatibilidade, mas foi removido dos menus.

## Testes e verificações

```bash
python manage.py check
python manage.py test
```

Os testes cobrem autenticação, permissões, rotas, criação de funcionários, registro/filtro de preparos, persistência de pedidos e cálculos.

## Persistência atual

O banco padrão é SQLite. Pedidos são persistidos no modelo `Order`; preparos de cozinha são persistidos em `KitchenPreparation`. Produtos, clientes e receitas ainda possuem partes demonstrativas ou telas legadas sem modelos persistentes completos.

`db.sqlite3` é banco de desenvolvimento local e não deve ser incluído em novos commits.

## Documentação detalhada

Consulte [DOCUMENTACAO.md](DOCUMENTACAO.md) para o inventário arquivo a arquivo, fluxos completos, permissões, templates, estilos, scripts, migrações, testes e orientações de desenvolvimento.
