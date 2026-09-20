# Sabor Tech

Sistema web de gestão para restaurantes, desenvolvido com Django. A aplicação separa as rotinas de administração, atendimento, Cardápio, fichas técnicas e análise operacional.

## Executar o projeto

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

No PowerShell, a ativação do ambiente virtual é:

```powershell
.\.venv\Scripts\Activate.ps1
```

A aplicação fica disponível em `http://127.0.0.1:8000/`.

## Acessos

O login usa o grupo do usuário para decidir a tela inicial:

- **Administrativo:** entra em `/home/` e acessa dashboard, Cardápio, receitas e relatórios.
- **Garçom:** entra diretamente em `/pedidos/` e não acessa as telas administrativas.

Para criar um garçom, acesse `/admin/`, crie o usuário e associe-o ao grupo `Garçom`.

## Telas

### Home

É a entrada administrativa do sistema. Apresenta os atalhos para atendimento, métricas, Cardápio e cadastro de receitas.

### Pedidos

É a tela exclusiva do garçom. Ela contém:

- categorias do cardápio;
- busca de produtos;
- montagem do pedido da mesa;
- subtotal e taxa de serviço;
- conclusão do pedido.

Ao concluir, o pedido é salvo no banco pela rota `POST /pedidos/concluir/`. O administrativo visualiza os pedidos recebidos no dashboard.

### Cardápio

O Cardápio é diferente de uma receita. Ele representa os produtos vendidos ao cliente, com:

- nome;
- categoria;
- preço;
- disponibilidade;
- descrição;
- busca e filtro por categoria.

Rota: `/produtos/`.

### Adicionar receitas

Receitas são fichas técnicas internas do restaurante. A tela permite informar:

- nome e categoria;
- rendimento;
- tempo de preparo;
- ingredientes;
- quantidade, unidade e custo;
- custo estimado da preparação.

Rota: `/receitas/`.

### Relatórios

Rota: `/relatorios/`.

O painel de Relatórios foi criado para leitura rápida da operação.

#### Indicadores

- Receita total;
- Custo dos insumos;
- Lucro líquido;
- Percentual de desperdício;
- Tempo médio de atendimento.

As cores ajudam a identificar cada grupo: azul para vendas, vermelho para custos, verde para lucro, amarelo para desperdício e lilás para tempo.

#### Gráficos

- **Linha:** acompanha vendas, custos e lucro ao longo dos dias.
- **Barras:** compara os pratos mais vendidos.
- **Rosca:** mostra a distribuição de uso dos insumos.
- **Heatmap:** indica os horários com maior movimento.

Os gráficos usam Chart.js e se adaptam a desktop e celular.

#### Filtros

Os filtros da tela permitem selecionar:

- período: dia, semana, mês ou ano;
- categoria: todas, pizzas, massas ou bebidas;
- perfil: todos, delivery ou presencial.

Os controles estão preparados para receber séries históricas reais conforme os módulos de vendas e clientes forem persistidos.

#### Análises preditivas

A seção de análises apresenta o espaço de decisão para:

- previsão de demanda;
- previsão de compra de insumos;
- detecção de anomalias;
- simulação de impacto de promoções e preços.

No protótipo atual, essas recomendações são demonstrativas. A base para modelos estatísticos será formada pelos pedidos persistidos, custos e desperdícios registrados ao longo do uso.

#### Exportação

- **Exportar Excel:** baixa um CSV que abre no Excel e em outras planilhas.
- **Exportar PDF:** abre a impressão do navegador com uma versão própria para salvar como PDF.

## Dados e persistência

O banco padrão é SQLite. Os pedidos concluídos são armazenados no modelo `Order`, com garçom, itens, subtotal, taxa, total, status e data de criação.

As telas de Cardápio e Receitas ainda usam dados de protótipo para apresentação. A próxima evolução natural é criar cadastros persistentes para produtos, ingredientes e fichas técnicas.

## Testes

Execute:

```bash
python manage.py check
python manage.py test
```

Os testes cobrem autenticação, separação entre garçom e administrativo, pedidos persistidos, cálculos e acesso às telas protegidas.

## Estrutura principal

```text
backend/                 Configurações do projeto Django
core/                    Rotas, views, modelos, migrações e templates
frontend/static/css/     Estilos das telas
frontend/static/js/      Comportamentos JavaScript compartilhados
docker/                  Arquivos de execução em container
infra/azure/             Arquivos de infraestrutura
manage.py                Entrada dos comandos Django
db.sqlite3               Banco local de desenvolvimento
```

## Publicação

A branch principal do fork é:

`https://github.com/taboomgabyy333367-hue/Sabor-Tech`

Para publicar alterações:

```bash
git add .
git commit -m "descreva a alteração"
git push fork main
```