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

- **Gestão/superusuário:** após autenticar, abre o Perfil administrativo com Atendimento, Adicionar receitas, Desempenho da cozinha, Relatórios e Funcionários. O perfil administrativo não inclui Cardápio ou o painel operacional do cozinheiro.
- **Garçom:** após autenticar, abre Pedidos. Pode consultar Pedidos Prontos, retirar pedidos e confirmar a entrega. Não pode acessar o Perfil exclusivo do cozinheiro nem Desempenho da cozinha.
- **Cozinheiro:** grupo Django `Chefe de Cozinha`; após o login, abre o Perfil exclusivo do cozinheiro para confirmar pedidos, acompanhar o farol e marcá-los como prontos. Não recebe links para Home ou Desempenho.
- **Auxiliar de cozinha:** não acessa Desempenho da cozinha nem o Perfil exclusivo do cozinheiro.

As permissões são validadas nas views Django. A ocultação de links no HTML é apenas uma conveniência de navegação, não substitui autorização no servidor.

## Rotas principais

| Tela | Caminho |
|---|---|
| Login | `/login/` |
| Home | `/home/` |
| Perfil administrativo | `/perfil-administrativo/` |
| Pedidos | `/pedidos/` |
| Pedidos Prontos | `/pedidos/prontos/` |
| Atendimento | `/atendimento/` |
| Cardápio (somente Gestão/superusuário) | `/produtos/` |
| Adicionar receitas | `/receitas/` |
| Desempenho cozinha | `/desempenho-cozinha/` |
| Perfil exclusivo do cozinheiro | `/perfil-cozinheiro/` |
| Relatórios | `/relatorios/` |
| Funcionários | `/funcionarios/` |

O Perfil administrativo reúne Atendimento, Adicionar receitas, Desempenho da cozinha, Relatórios e Funcionários. Desempenho é restrito a Gestão/superusuário. O Perfil exclusivo do cozinheiro é a tela operacional de pedidos e cronômetro; administradores têm apenas consulta nessa tela.

## Pedidos Prontos

Quando a cozinha marca um pedido como pronto, ele passa a aparecer para os garçons em `/pedidos/prontos/`. O sino e o item **Pedidos Prontos** mostram a quantidade de pedidos que ainda aguardam retirada; a tela consulta o servidor a cada cinco segundos para atualizar contagem, cartões e avisos sem recarregar a página. O aviso sonoro não é usado.

O fluxo do garçom é persistente e auditável:

1. **Pronto:** o garçom usa **PEGAR PEDIDO**. A atualização condicional grava `Saiu para entrega`, o garçom que retirou e o horário. Outro garçom não consegue retirar o mesmo pedido.
2. **Saiu para entrega:** **JÁ ENTREGUE** pede confirmação antes do envio. O backend só aceita a entrega depois da retirada e grava o garçom e o horário da entrega.
3. **Entregue:** o pedido sai da lista ativa, mas permanece em `Order` para o histórico.

As rotas e consultas são limitadas à empresa ativa do garçom. A migração `0010_order_delivery_tracking` adiciona o estado `Saiu para entrega`, `pickup_waiter`, `picked_up_at`, `delivery_waiter` e `delivered_at`. Os testes cobrem contagem, escopo, retirada única, confirmação obrigatória e retenção do histórico.

O Cardápio lista os produtos da empresa ativa e oferece busca e filtro por categoria. O cadastro de um produto começa em Adicionar receitas, onde são informados os dados do produto, rendimento, tempo e ingredientes.

As telas mantêm a navegação normal por menus, sem botões Voltar. Na Home, a ação Sair encerra a sessão e retorna ao Login. O Dashboard legado continua em `/dashboard/` por compatibilidade, mas foi removido dos menus.

## Testes e verificações

```bash
python manage.py check
python manage.py test
```

Os testes cobrem autenticação, permissões, rotas, criação de funcionários, registro/filtro de preparos, persistência de pedidos, farol da cozinha, notificações e fluxo de retirada/entrega.

## Persistência atual

O banco padrão é SQLite. Pedidos são persistidos no modelo `Order`; preparos de cozinha são persistidos em `KitchenPreparation`. Produtos, clientes e receitas ainda possuem partes demonstrativas ou telas legadas sem modelos persistentes completos.

`db.sqlite3` é banco de desenvolvimento local e não deve ser incluído em novos commits.

## Documentação detalhada

Consulte [DOCUMENTACAO.md](DOCUMENTACAO.md) para o inventário arquivo a arquivo, fluxos completos, permissões, templates, estilos, scripts, migrações, testes e orientações de desenvolvimento.
