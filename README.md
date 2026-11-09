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

- **Gestão/superusuário:** Home, atendimento, cardápio, receitas, relatórios, desempenho da cozinha e administração de funcionários. Pode consultar o perfil exclusivo do cozinheiro, sem operar pedidos.
- **Garçom:** após autenticar, abre diretamente a página Pedidos. Essa página não aparece como link em nenhuma outra tela e usuários de outros perfis não podem abri-la por URL.
- **Cozinheiro:** grupo Django `Chefe de Cozinha`; após o login, abre diretamente o Perfil exclusivo do cozinheiro e pode confirmar/finalizar pedidos.
- **Auxiliar de cozinha:** consulta Desempenho da cozinha e pode registrar preparos; não acessa o perfil operacional exclusivo.
- **Garçom:** não acessa o Perfil exclusivo do cozinheiro.

As permissões são validadas nas views Django. A ocultação de links no HTML é apenas uma conveniência de navegação, não substitui autorização no servidor.

## Rotas principais

| Tela | Caminho |
|---|---|
| Login | `/login/` |
| Home | `/home/` |
| Pedidos | `/pedidos/` |
| Atendimento | `/atendimento/` |
| Cardápio (somente Gestão/superusuário) | `/produtos/` |
| Adicionar receitas | `/receitas/` |
| Desempenho cozinha | `/desempenho-cozinha/` |
| Perfil exclusivo do cozinheiro | `/perfil-cozinheiro/` |
| Relatórios | `/relatorios/` |
| Funcionários | `/funcionarios/` |

Desempenho da cozinha é a tela de indicadores e histórico de preparos. O Perfil exclusivo do cozinheiro é a tela operacional de pedidos e cronômetro; o administrador, incluindo `gabriele@gmail.com` no banco local, tem somente consulta.

O Cardápio lista os produtos da empresa ativa e oferece busca e filtro por categoria. O cadastro de um produto começa em Adicionar receitas, onde são informados os dados do produto, rendimento, tempo e ingredientes.

As telas mantêm a navegação normal por menus, sem botões Voltar. Na Home, a ação Sair encerra a sessão e retorna ao Login. O Dashboard legado continua em `/dashboard/` por compatibilidade, mas foi removido dos menus.

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
