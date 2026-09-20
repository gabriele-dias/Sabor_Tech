# Sabor Tech

## Versão 1.0

O Sabor Tech é um sistema web de gestão para restaurantes. A versão 1.0 organiza o atendimento, o Cardápio, as fichas técnicas de receitas, os relatórios operacionais e os acessos por perfil.

O projeto foi desenvolvido em Django e utiliza templates HTML, CSS, JavaScript e SQLite no ambiente local. A execução em produção ou homologação pode ser feita com Docker e Gunicorn.

## Sumário

- [Objetivo](#objetivo)
- [Tecnologias](#tecnologias)
- [Como executar](#como-executar)
- [Docker](#docker)
- [Perfis de acesso](#perfis-de-acesso)
- [Telas do sistema](#telas-do-sistema)
- [Fluxo do garçom](#fluxo-do-garçom)
- [Relatórios](#relatórios)
- [Testes](#testes)
- [Testes de caixa branca](#testes-de-caixa-branca)
- [Testes de caixa preta](#testes-de-caixa-preta)
- [Atualizações da versão 1.0](#atualizações-da-versão-10)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Próximas evoluções](#próximas-evoluções)

## Objetivo

O sistema foi criado para centralizar tarefas comuns de um restaurante:

- controlar produtos e preços do Cardápio;
- cadastrar fichas técnicas de receitas;
- receber pedidos feitos pelo garçom;
- enviar pedidos concluídos para a administração;
- acompanhar custos, vendas, lucro e desperdício;
- separar as funções administrativas das funções de atendimento.

## Tecnologias

- Python 3.13;
- Django 5.2.7;
- SQLite;
- Django Templates;
- JavaScript no navegador;
- Chart.js para gráficos dos Relatórios;
- Gunicorn para servir a aplicação;
- WhiteNoise para arquivos estáticos;
- Docker e Docker Compose;
- Git e GitHub.

## Como executar

### 1. Criar o ambiente virtual

No terminal, dentro da pasta do projeto:

```bash
python -m venv .venv
```

### 2. Ativar o ambiente virtual

Git Bash:

```bash
source .venv/Scripts/activate
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar dependências

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Aplicar as migrações

```bash
python manage.py migrate
```

As migrações criam os grupos de acesso e a tabela de pedidos concluídos.

### 5. Verificar o projeto

```bash
python manage.py check
```

### 6. Executar localmente

```bash
python manage.py runserver
```

A aplicação estará em:

```text
http://127.0.0.1:8000/
```

## Docker

O projeto possui uma configuração Docker no diretório `docker/`.

### Construir e iniciar

A partir da raiz do projeto:

```bash
docker compose -f docker/docker-compose.yml up --build
```

O serviço web será exposto na porta `8000`:

```text
http://127.0.0.1:8000/
```

### O que o Docker faz

1. Usa uma imagem leve de Python 3.13.
2. Instala as dependências do `requirements.txt`.
3. Copia o projeto para `/app`.
4. Executa `collectstatic` durante a construção da imagem.
5. Cria um usuário do sistema chamado `app`.
6. Mantém o SQLite em um volume chamado `sqlite_data`.
7. Inicia o Django usando Gunicorn.
8. Usa o script `docker/entrypoint.sh` para preparar o ambiente antes da aplicação iniciar.

### Parar os serviços

```bash
docker compose -f docker/docker-compose.yml down
```

Para remover também o volume local do banco:

```bash
docker compose -f docker/docker-compose.yml down -v
```

## Perfis de acesso

O login usa grupos do Django para definir o destino do usuário.

### Administrativo

Usuários administrativos acessam:

- Home;
- Dashboard;
- Pedidos recebidos;
- Cardápio;
- Adicionar receitas;
- Relatórios.

A conta administrativa criada para o ambiente local é:

```text
Login: gabriele@gmail.com
Senha: 1234
```

Em um ambiente real, a senha deve ser trocada antes da publicação.

### Garçom

Usuários do grupo `Garçom` são enviados automaticamente para `/pedidos/`.

O garçom não acessa as telas administrativas. Se tentar abrir diretamente a Home, o Dashboard, o Cardápio ou os Relatórios, será redirecionado para os Pedidos.

Para criar um garçom:

1. Acesse `/admin/` com uma conta administrativa.
2. Crie um usuário.
3. Marque o grupo `Garçom`.
4. Salve o usuário.
5. Faça login com esse usuário.

A conta de teste do ambiente local é:

```text
Login: garçom@gmail.com
Senha: 1234
```

## Telas do sistema

### Login

A tela de login autentica o usuário pelo formulário do Django. Depois da autenticação, o sistema consulta o grupo do usuário e decide a tela de entrada.

- Administrativo: `/home/`;
- Garçom: `/pedidos/`.

O botão de saída encerra a sessão e retorna para `/login/`.

### Home administrativa

A Home apresenta atalhos para as principais áreas do sistema:

- abrir Pedidos;
- abrir Dashboard;
- abrir Cardápio;
- adicionar receitas;
- abrir Relatórios.

### Pedidos

A tela de Pedidos é voltada ao atendimento do garçom. Ela possui:

- categorias de produtos;
- pesquisa de produtos;
- cardápio de itens disponíveis;
- carrinho da Mesa 05;
- quantidades e remoção de itens;
- subtotal;
- taxa de serviço de 10%;
- total do pedido;
- botão `Concluir Pedido`.

Quando o pedido é concluído, o navegador envia os itens e valores para:

```text
POST /pedidos/concluir/
```

A aplicação salva o pedido no modelo `Order`, vinculado ao usuário garçom. O pedido passa a aparecer no Dashboard administrativo.

### Cardápio

Cardápio e Receita são conceitos diferentes.

O Cardápio representa os produtos vendidos ao cliente. A tela `/produtos/` apresenta:

- nome do produto;
- categoria;
- descrição;
- preço;
- disponibilidade;
- pesquisa;
- filtros por categoria.

As categorias disponíveis na versão 1.0 são Pizzas, Lanches, Massas, Bebidas e Sobremesas.

### Adicionar receitas

A tela `/receitas/` representa a ficha técnica interna do restaurante. Ela permite informar:

- nome da receita;
- categoria;
- rendimento em porções;
- tempo de preparo;
- ingredientes;
- quantidade;
- unidade de medida;
- custo de cada ingrediente;
- custo estimado da receita.

O botão de adicionar ingrediente cria novas linhas no formulário. O custo estimado é atualizado no navegador conforme os valores são preenchidos.

### Relatórios

A tela `/relatorios/` é o painel de análise operacional da versão 1.0.

## Relatórios em detalhes

### Indicadores principais

Os cards do topo mostram uma leitura rápida da operação:

- **Receita total:** valor vendido no período selecionado;
- **Custo dos insumos:** estimativa gasta com ingredientes;
- **Lucro líquido:** diferença entre vendas e custos;
- **Desperdício:** percentual estimado de perdas;
- **Tempo médio:** tempo médio de atendimento.

As cores dos indicadores foram separadas para facilitar a leitura:

- azul: vendas;
- vermelho: custos;
- verde: lucro;
- amarelo: desperdício;
- lilás: tempo de atendimento.

### Gráfico de linhas

O gráfico de linhas apresenta a evolução de três séries:

- vendas;
- custos;
- lucro.

O eixo horizontal representa os dias e o eixo vertical representa os valores em reais. Quando existem pedidos persistidos, a série mais recente considera os dados gravados no banco.

### Gráfico de barras

O gráfico de barras compara os pratos mais vendidos. Ele ajuda a identificar os produtos que devem receber maior atenção no estoque, na produção e nas promoções.

### Gráfico de distribuição de insumos

O gráfico em formato de rosca mostra a participação relativa dos principais grupos de insumos, como farinha, queijo, tomate, carnes e bebidas.

### Heatmap de movimento

O heatmap distribui a movimentação por horário. Quanto mais forte a cor, maior a quantidade estimada de pedidos naquele horário.

Esse recurso ajuda a decidir:

- quantos funcionários colocar em cada turno;
- quando iniciar o preparo;
- qual horário exige mais estoque disponível;
- quando criar promoções de menor movimento.

### Filtros

Os filtros da tela são:

- período: hoje, semana, mês ou ano;
- categoria: todas, pizzas, massas ou bebidas;
- perfil de cliente: todos, delivery ou presencial.

A interface já possui os controles preparados para receber filtros baseados em dados históricos completos.

### Análises preditivas

A versão 1.0 apresenta uma área inicial para análises preditivas. As recomendações atuais são demonstrativas e organizam a experiência para a futura camada estatística.

As análises previstas são:

- **Previsão de demanda:** estimar a quantidade de pratos por dia e horário;
- **Previsão de insumos:** recomendar compras para evitar falta ou excesso;
- **Detecção de anomalias:** identificar quedas de vendas ou aumentos de desperdício;
- **Simulação de lucro:** estimar o impacto de promoções e reajustes de preço.

Para transformar essas previsões em modelos reais, será necessário acumular histórico suficiente de vendas, custos, estoque e desperdício.

### Exportação

O botão `Exportar Excel` gera um arquivo CSV compatível com Excel e outras planilhas.

O botão `Exportar PDF` abre a impressão do navegador. Na janela de impressão, selecione `Salvar como PDF`.

## Testes

A versão 1.0 possui testes automatizados em `core/tests.py`.

Executar todos os testes:

```bash
python manage.py test --verbosity 1
```

Executar a verificação de configuração:

```bash
python manage.py check
```

A suíte atual cobre 19 cenários e verifica:

- renderização da tela de login;
- redirecionamento da raiz para login;
- login administrativo;
- login de garçom;
- bloqueio de telas administrativas para garçom;
- logout;
- conclusão de pedido;
- exibição do pedido no Dashboard;
- cálculos de custo;
- cálculos de pedidos;
- filtros e métricas do Dashboard.

## Testes de caixa branca

Teste de caixa branca avalia a implementação interna. O teste conhece o código, as funções e os caminhos de execução.

No Sabor Tech, os testes de caixa branca verificam principalmente:

- funções matemáticas em `core/calculations.py`;
- cálculo de custo total;
- cálculo de custo por pessoa;
- cálculo de quantidade de insumo;
- cálculo do total de pedidos;
- validação de valores inválidos;
- criação do modelo `Order`;
- associação do pedido ao usuário garçom;
- redirecionamento condicionado ao grupo `Garçom`.

Exemplos de comandos:

```bash
python manage.py test core.tests.OrderCalculationTests
python manage.py test core.tests.CoreAccessTests.test_waiter_order_is_saved_for_management
```

O objetivo é verificar se cada decisão interna funciona corretamente e se valores incorretos são rejeitados.

## Testes de caixa preta

Teste de caixa preta avalia o sistema pela perspectiva do usuário, sem depender de como o código foi escrito.

Na versão 1.0, os principais fluxos de caixa preta são:

1. Abrir `/login/`.
2. Entrar como administrativo.
3. Confirmar a abertura da Home.
4. Abrir Cardápio.
5. Abrir Adicionar receitas.
6. Abrir Relatórios.
7. Sair e confirmar o retorno para login.
8. Entrar como garçom.
9. Confirmar a abertura automática de Pedidos.
10. Adicionar produtos ao carrinho.
11. Concluir pedido.
12. Entrar como administrativo.
13. Confirmar que o pedido aparece no Dashboard.

Também devem ser conferidos:

- busca do Cardápio;
- filtros de categoria;
- inclusão e remoção de ingredientes;
- cálculo do custo da receita;
- filtros de período dos Relatórios;
- gráfico em desktop;
- gráfico em celular;
- exportação CSV;
- impressão em PDF.

## Testes em Docker

A validação Docker deve ser feita com:

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

Depois, verificar a aplicação:

```bash
curl http://127.0.0.1:8000/login/
```

Executar os testes dentro do container:

```bash
docker compose -f docker/docker-compose.yml exec web python manage.py check
docker compose -f docker/docker-compose.yml exec web python manage.py test --verbosity 1
```

Verificar os logs:

```bash
docker compose -f docker/docker-compose.yml logs -f web
```

Finalizar:

```bash
docker compose -f docker/docker-compose.yml down
```

A validação Docker confirma que a aplicação instala suas dependências, coleta arquivos estáticos, executa as migrações, inicia com Gunicorn e responde pela porta 8000.

## Estrutura de pastas

```text
backend/                    Configurações, URLs e WSGI/ASGI
core/                       Views, modelos, formulários e migrações
core/templates/core/       Telas Django da aplicação
frontend/static/css/       Estilos das telas
frontend/static/js/        JavaScript compartilhado
 docker/                    Dockerfile, Compose e entrypoint
infra/                      Arquivos de infraestrutura
manage.py                   Comandos do Django
requirements.txt            Dependências Python
DOCUMENTACAO.md             Documentação funcional complementar
README.md                   Documentação principal da versão 1.0
db.sqlite3                  Banco local de desenvolvimento
```

## Atualizações da versão 1.0

A versão 1.0 consolidou as seguintes entregas:

1. Login com redirecionamento por perfil.
2. Grupo de acesso `Garçom`.
3. Restrição do garçom à tela de Pedidos.
4. Logout com retorno ao login.
5. Tela de pedidos com cardápio e carrinho.
6. Persistência de pedidos concluídos.
7. Exibição de pedidos no Dashboard administrativo.
8. Tela própria de Cardápio.
9. Separação explícita entre Cardápio e Receitas.
10. Tela de cadastro de receitas.
11. Tela analítica de Relatórios.
12. KPIs, gráficos, heatmap e filtros.
13. Exportação CSV e impressão em PDF.
14. Layout responsivo para desktop e celular.
15. Documentação de testes de caixa branca, caixa preta e Docker.

## Próximas evoluções

- persistir produtos e receitas em modelos próprios;
- persistir estoque e desperdício;
- conectar os filtros dos Relatórios ao banco;
- substituir dados demonstrativos por séries históricas;
- implementar modelos estatísticos de previsão;
- criar permissões mais detalhadas além dos grupos;
- adicionar testes automatizados de navegador;
- configurar pipeline de integração contínua.
