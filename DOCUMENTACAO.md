# Manual Técnico do Sabor Tech

Este documento descreve, passo a passo, como o Sabor Tech está organizado, como executar cada fluxo, onde cada responsabilidade vive no código e como validar ou estender o sistema.

## 1. Visão geral

O Sabor Tech é uma aplicação web para operação de restaurante. O servidor é Django; as telas são renderizadas com Django Templates; os estilos e interações de interface ficam em arquivos estáticos; o banco local padrão é SQLite.

A aplicação reúne estes fluxos:

- autenticação e autorização por grupo;
- Home administrativa;
- pedidos iniciados pela equipe de atendimento;
- acompanhamento de mesas e pedidos;
- catálogo de produtos;
- fichas técnicas de receitas;
- desempenho e registros da equipe de cozinha;
- relatórios operacionais;
- cadastro de contas de funcionários.

O Dashboard legado continua disponível diretamente em `/dashboard/` para compatibilidade e testes existentes, mas foi retirado da navegação normal. As páginas operacionais voltam à Home por um botão explícito. A Home é a exceção: oferece a ação de sair, que encerra a sessão e leva ao login.

## 2. Requisitos e execução

### 2.1 Requisitos

- Python compatível com a versão declarada em `requirements.txt` e no README;
- dependências instaladas nesse ambiente;
- banco SQLite gravável;
- navegador moderno;
- acesso à rede para carregar fontes Google e Chart.js via CDN, quando permitido.

### 2.2 Preparar o ambiente

Na raiz do repositório:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

No PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2.3 Preparar banco, conferir e executar

```bash
python manage.py migrate
python manage.py check
python manage.py runserver
```

Abra `http://127.0.0.1:8000/`. A rota raiz exige autenticação e leva à Home para os usuários administrativos. O login é `/login/`.

Não use `runserver` como servidor de produção. Para produção, consulte a configuração Docker/Gunicorn do projeto e configure segredo, hosts, HTTPS e credenciais fora do repositório.

## 3. Mapa de diretórios

```text
manage.py                         Entrada dos comandos Django
backend/                           Configurações e roteamento raiz do projeto
core/
  admin.py                         Registro do Django Admin
  apps.py                          Configuração do app
  calculations.py                  Funções puras de cálculos de receita/pedidos
  forms.py                         Formulários de login, funcionário e preparo
  models.py                        Modelos persistentes Order e KitchenPreparation
  urls.py                          URLs nomeadas do app
  views.py                         Regras de acesso, leitura e gravação das telas
  migrations/                      Histórico versionado do banco
  templates/core/                  Telas e fragmentos HTML do app
  tests.py                         Testes Django de views, permissões e cálculos
  tests/blackbox/                  Testes de caixa preta adicionais
frontend/
  static/css/                      Folhas de estilo das telas
  static/js/                       JavaScript compartilhado ou por tela
  templates/                       Templates legados/localizados fora do app
DOCUMENTACAO.md                    Manual técnico detalhado
README.md                          Introdução e comandos rápidos
requirements.txt                   Dependências Python
 db.sqlite3                        Banco local de desenvolvimento; não versionar dados locais
```

O Django encontra templates de `core/templates/` por `APP_DIRS=True` e arquivos estáticos em `frontend/static/` via `STATICFILES_DIRS`.

## 4. Inicialização e configurações Django

### `manage.py`

Ponto de entrada para comandos administrativos Django, como `runserver`, `migrate`, `makemigrations`, `check` e `test`. Define o módulo de settings padrão do projeto.

### `backend/settings.py`

Configura:

- aplicações Django instaladas, incluindo `core`;
- middleware de sessão, autenticação, CSRF e mensagens;
- templates e context processors, que tornam `request`, usuário e mensagens disponíveis;
- banco SQLite em `db.sqlite3`;
- `STATIC_URL` e `STATICFILES_DIRS`;
- idioma, fuso horário e política de senhas;
- URL de login e URL padrão após autenticação.

`DEBUG=True` e a chave de desenvolvimento são adequados apenas ao ambiente local. Antes da publicação, mova segredos para variáveis de ambiente, defina `ALLOWED_HOSTS` e execute a checklist de segurança do Django.

### `backend/urls.py`

Registra o Admin Django e inclui as rotas do app `core` na raiz do site. A partir desse ponto os padrões em `core/urls.py` ficam disponíveis.

### `core/apps.py`

Declara a configuração do app Django. O app concentra dados, formulários, views, templates, URLs, testes e migrações do domínio do restaurante.

## 5. Navegação e mapa de rotas

As rotas usam nomes Django. Templates devem preferir `{% url 'core:nome' %}` a caminhos escritos manualmente: renomear ou reorganizar uma rota assim gera erro detectável, em vez de deixar um link quebrado silenciosamente.

| Nome da rota | Caminho | Uso e controle |
|---|---|---|
| `core:login` | `/login/` | Formulário de autenticação |
| `core:logout` | `/logout/` | Encerra sessão e volta ao login |
| `core:home` | `/home/` | Home administrativa ou Home limitada para garçons |
| `core:home-root` | `/` | Alias da Home |
| `core:dashboard` | `/dashboard/` | Dashboard legado, fora da navegação normal |
| `core:pedidos` | `/pedidos/` | Catálogo para montar pedidos; superusuário e garçons |
| `core:concluir_pedido` | `/pedidos/concluir/` | Recebe JSON via POST e persiste um pedido |
| `core:atendimento` | `/atendimento/` | Acompanhamento de pedidos e mesas |
| `core:desempenho_cozinha` | `/desempenho-cozinha/` | Registro e indicadores da produção da cozinha |
| `core:produtos` | `/produtos/` | Catálogo administrativo de produtos |
| `core:receitas` | `/receitas/` | Formulário de ficha técnica |
| `core:relatorios` | `/relatorios/` | Gráficos e análises operacionais |
| `core:funcionarios` | `/funcionarios/` | Cadastro de contas e perfis de funcionários |
| `core:funcionarios_novo` | `/funcionarios/novo/` | Alias do cadastro de funcionário |
| `core:clientes` | `/clientes/` | Tela legada de clientes |
| `core:configuracoes` | `/configuracoes/` | Tela legada de configurações |

O item Dashboard foi removido dos menus e dos atalhos da Home. A rota permanece para compatibilidade enquanto telas, testes ou links antigos ainda possam referenciá-la. Não é um item da navegação cotidiana.

### Regra de retorno

- As telas internas expõem um botão `Voltar à Home` ou um link Home claramente visível.
- A Home não precisa de botão de retorno; ela oferece `Sair` por formulário POST com token CSRF.
- Pedidos mantém seu menu próprio por categorias. O cabeçalho inclui `Voltar à Home` e a sidebar oferece destinos compatíveis com o perfil.
- A Home é acessível a garçons, mas mostra apenas Home, Atendimento, Pedidos e Sair; as views administrativas continuam protegidas.

| Tela | Retorno esperado |
|---|---|
| Home | `Sair`, encerra sessão e abre Login |
| Pedidos | `Voltar à Home` |
| Atendimento | `Voltar à Home` |
| Cardápio | `Voltar à Home` junto de Novo produto |
| Adicionar receitas | `Voltar à Home` |
| Desempenho cozinha | `Voltar à Home` |
| Relatórios | `Voltar à Home` |
| Novo funcionário | `Voltar à Home` |
| Dashboard legado | `Voltar à Home` pelo layout compartilhado |
| Clientes e Configurações | `Voltar à Home` pelo layout compartilhado |
| Login | Não oferece Home autenticada; o redirect após login depende do perfil |

## 6. Autenticação, grupos e permissões

### 6.1 Login

`core/forms.py` define `CardapioLoginForm`, que altera rótulos e placeholders do formulário padrão Django. `RoleLoginView` em `core/views.py` usa esse formulário e direciona garçons para a tela de Pedidos. Outros usuários seguem o redirect padrão da autenticação.

O usuário precisa estar autenticado para acessar as views protegidas por `@login_required`.

### 6.2 Grupos

O app utiliza grupos Django em vez de um campo de perfil novo no usuário:

- `Gestão`: acesso às funções administrativas e cadastro de funcionários;
- `Garçom`: monta/conclui pedidos e acompanha o atendimento;
- `Chefe de Cozinha`: registra preparos como cozinheiro;
- `Auxiliar de cozinha`: registra preparos como auxiliar.

A migration `0002_create_roles.py` cria os grupos administrativos históricos. A migration `0005_create_waiter_role.py` cria `Garçom`. Ao criar funcionário pela tela, a view cria o grupo de destino se ainda não existir. O perfil `Cozinheiro` é associado ao grupo histórico `Chefe de Cozinha`.

### 6.3 Funções de autorização

Em `core/views.py`:

- `is_waiter(user)` verifica o grupo `Garçom`;
- `can_access_orders(user)` permite a rota Pedidos a superusuário ou garçom;
- `can_manage_staff(user)` autoriza superusuário ou membro de `Gestão`;
- `is_kitchen_user(user)` verifica `Chefe de Cozinha` ou `Auxiliar de cozinha`;
- `can_access_kitchen(user)` permite Gestão/superusuário e equipe da cozinha;
- `redirect_waiter(request)` centraliza o destino seguro do garçom.

As mesmas regras controlam a view e a apresentação dos links. Esconder um link no template não substitui a autorização na view: cada view protegida deve validar o perfil no servidor.

## 7. Dados e persistência

### 7.1 `Order`

Definido em `core/models.py` e criado originalmente pela migration `0006_order.py`:

- `waiter`: usuário que enviou o pedido;
- `items`: lista JSON com itens e metadados do pedido;
- `subtotal`, `service_fee`, `total`: valores monetários decimais;
- `status`: estado do atendimento;
- `created_at`: data e hora de criação;
- ordenação padrão do mais recente para o mais antigo.

O JSON de itens pode conter nome, preço, quantidade e, quando a tela fornece, cliente, mesa ou canal. Views tratam campos opcionais para não pressupor metadados que o formulário de pedidos ainda não coleta.

### 7.2 `KitchenPreparation`

Criado pela migration `0007_kitchenpreparation_remove_ingrediente_receita_and_more.py` (o arquivo conserva esse identificador histórico; suas operações foram limitadas à criação deste modelo):

- `dish_name`: nome do preparo;
- `responsible`: funcionário responsável, protegido contra exclusão enquanto houver preparos;
- `status`: `Em preparo` ou `Concluído`;
- `duration_minutes`: duração positiva opcional, exigida pelo formulário para conclusão;
- `created_at`: instante em que o registro foi feito.

A migration 0007 cria uma tabela e um índice de responsável. Ela não apaga `Receita`, `Ingrediente` ou `Produto`, que aparecem no estado histórico do projeto, mas não estão representados no `models.py` atual.

### 7.3 Banco local

`db.sqlite3` contém dados da máquina de desenvolvimento. Migrações e alterações de schema são versionadas; o arquivo de banco não deve ser enviado em commits, pois pode conter contas, hashes de senha e dados reais de teste.

## 8. Formulários

### `CardapioLoginForm`

Especializa `AuthenticationForm` para apresentar o usuário como e-mail e usar campos com preenchimento automático apropriado.

### `StaffCreateForm`

- normaliza espaços no nome;
- converte e-mail a minúsculas;
- impede duplicação de username ou e-mail;
- valida a senha com os validadores Django;
- oferece quatro perfis: Garçom, Administrador, Cozinheiro e Auxiliar de cozinha.

A senha é salva por `User.objects.create_user`, que usa o hash de senha do Django. Não é armazenada em texto simples.

### `KitchenPreparationForm`

- aceita nome, estado e duração;
- impede duração menor que um minuto;
- exige duração para `Concluído`;
- permite deixar a duração em branco enquanto o preparo está em andamento.

## 9. Views e fluxo de cada tela

As regras e coordenação de páginas estão em `core/views.py`.

### 9.1 `pedidos`

Valida se o usuário é superusuário ou garçom. Renderiza catálogo, busca, filtros de categoria, carrinho e resumo. Passa flags de permissão para o menu de navegação.

### 9.2 `concluir_pedido`

Aceita apenas POST e verifica perfil antes de processar. Decodifica JSON, converte valores para `Decimal`, exige uma lista não vazia de objetos e totais positivos e salva um `Order`. Responde JSON com `201` ao salvar, `400` para payload inválido e `403` para papel não autorizado.

### 9.3 `home`

Redireciona garçons para Pedidos. Para os demais usuários, renderiza a Home e flags de permissão para os menus. Os números demonstrativos exibidos no hero ainda são texto de protótipo, não agregados de pedidos.

### 9.4 `dashboard`

É a página administrativa histórica com métricas/dados de demonstração e pedidos persistidos recebidos. Continua acessível em URL para compatibilidade, porém não é anunciada nos menus. Garçons são redirecionados.

### 9.5 `atendimento`

Permite Gestão, superusuário, garçom e equipe de cozinha. Lê os pedidos recentes, transforma os itens JSON em linhas apresentáveis, filtra por nome/número/status e calcula ocupação a partir dos metadados de mesa recebidos. Cria doze espaços visuais para o salão; somente mesas inferidas de pedidos ativos são marcadas ocupadas.

Pedidos sem metadados de cliente são exibidos com o nome do garçom associado. Isso é um fallback de apresentação, não uma afirmação de que o garçom seja o cliente.

### 9.6 `desempenho_cozinha`

Permite Gestão, superusuários, `Chefe de Cozinha` e `Auxiliar de cozinha`. Usuário sem acesso vai à Home; garçom vai diretamente a Pedidos.

Um membro da cozinha pode enviar POST para registrar preparo. O responsável é sempre `request.user`, não um campo livre, impedindo atribuição a outra conta pela interface. O filtro restringe a tabela por grupo. Indicadores usam registros reais da data local atual, média apenas de durações concluídas e contagens de contas ativas nos grupos.

Gestores podem consultar e filtrar os registros, mas não podem registrar pela view: somente membros dos grupos de cozinha executam o POST.

### 9.7 `funcionarios`

Restrita a Gestão e superusuário. Valida `StaffCreateForm`, cria uma conta com e-mail como username, divide nome em primeiro nome/sobrenome, associa a conta ao grupo correspondente e mostra mensagem de sucesso. Garçons sem permissão são encaminhados a Pedidos.

### 9.8 `produtos` e `receitas`

Protegidas contra garçons. Atualmente o catálogo e a ficha de receita ainda usam dados/protótipos de interface; o envio do formulário de receita exibe uma confirmação, mas não persiste uma entidade `Receita` no modelo atual.

### 9.9 `relatorios`

Protegida contra garçons. Compõe dados para Chart.js e passa flags de menu. Uma parte das séries e das análises preditivas ainda é demonstrativa, com o último valor de venda atualizado a partir dos pedidos persistidos.

### 9.10 `clientes` e `configuracoes`

Views de compatibilidade do layout legado. Clientes ainda não tem modelo persistente e recebe lista vazia; Configurações renderiza o esqueleto existente. As duas rotas usam autenticação e recusam garçons.

## 10. Templates e comportamento de interface

Os templates em `core/templates/core/` definem o HTML e usam tags Django:

- `{% load static %}` referencia CSS/JavaScript;
- `{% url %}` monta links a partir dos nomes de rota;
- `{% csrf_token %}` protege formulários POST;
- `{% if %}` limita links por permissão;
- `{% for %}` apresenta registros e cria estados vazios;
- `json_script` incorpora dados para gráficos sem concatenar JSON manualmente em HTML executável.

### Telas principais

- `home.html`: entrada por perfil, navegação, cartões permitidos e botão Sair por POST;
- `pedidos.html`: catálogo para montar pedidos; comportamento do carrinho e POST para concluir pedido;
- `atendimento.html`: resumo, busca/filtro, lista de pedidos e grade de mesas;
- `produtos.html`: lista, busca e filtro de produtos; botão Novo produto encaminha ao formulário de receitas;
- `receitas.html`: formulário de ficha e cálculo visual de custo;
- `desempenho_cozinha.html`: indicadores, filtro de equipe, tabela e formulário de preparo recolhível;
- `funcionarios.html`: criação de conta e seleção de grupo;
- `relatorios.html`: filtros, métricas, gráficos, mapa de movimento e exportação;
- `base.html`: casca histórica compartilhada por Dashboard, Clientes e Configurações;
- `_orders.html` e `_clients_list.html`: fragmentos legados de lista.

A navegação pode variar por papel, mas cada página interna oferece retorno à Home. A tela especial de Pedidos mantém atalhos próprios sem expor links administrativos aos garçons.

## 11. CSS e responsividade

Os estilos estão em `frontend/static/css/`:

- `home.css`: Home administrativa e shell visual;
- `pedidos.css`: catálogo/carrinho específico da tela Pedidos;
- `cardapio.css`: catálogo administrativo;
- `receitas.css`: formulário de receita;
- `relatorios.css`: dashboard de indicadores e gráficos;
- `operacao.css`: componentes comuns de Atendimento e Funcionários;
- `desempenho.css`: produção da cozinha, tabela e formulário de preparo;
- `base.css`: layout legado.

Os arquivos utilizam breakpoints para substituir sidebars por navegação horizontal e reorganizar grids em telas estreitas. Em grades CSS, elementos sem conteúdo precisam de dimensões de linha/coluna explícitas quando necessário; a grade do mapa de movimento de Relatórios possui doze linhas definidas para tornar as células visíveis.

## 12. JavaScript e integrações de navegador

- `pedidos.html` adiciona/remove itens do carrinho, calcula subtotal e taxa de serviço, envia JSON com token CSRF e mostra o resultado;
- `produtos.html` filtra o catálogo por texto e categoria e direciona o botão de novo produto à tela de receitas;
- `receitas.html` duplica/remove linhas de ingrediente e atualiza o custo estimado no navegador; o salvamento ainda é demonstrativo;
- `relatorios.html` lê o JSON seguro produzido pela view, constrói gráficos Chart.js, cria o mapa de horários e oferece CSV/impressão.

O caminho nominal do script comum é `frontend/static/js/main.js`. Scripts específicos estão em `pedidos.js`, `produtos.js` e `relatorios.js`; parte do comportamento está inline nos templates históricos.

## 13. Migrações

Migrações importantes:

- `0001_initial.py`: estado inicial do app;
- `0002_create_roles.py`: grupos administrativos históricos;
- `0003_receita.py` e `0004_alter_receita_quantidade_kg_ingrediente.py`: estado histórico de fichas e ingredientes;
- `0005_create_waiter_role.py`: grupo Garçom;
- `0006_order.py`: pedidos persistidos;
- `0007_kitchenpreparation_remove_ingrediente_receita_and_more.py`: tabela `KitchenPreparation` usada pela tela de desempenho.

Antes de editar modelos:

1. altere `core/models.py`;
2. rode `python manage.py makemigrations core`;
3. revise todas as operações geradas, sobretudo `DeleteModel` e `RemoveField`;
4. rode `python manage.py sqlmigrate core <numero>`;
5. rode `python manage.py migrate`;
6. rode testes e `python manage.py check`.

Não aplique ao banco de produção uma migration que proponha apagar dados sem decisão explícita e backup verificado.

## 14. Testes

Executar toda a suíte:

```bash
python manage.py check
python manage.py test
```

Os testes em `core/tests.py` cobrem:

- página de login e redirect por perfil;
- acesso de garçons às rotas permitidas;
- proteção de áreas administrativas;
- conclusão e persistência de pedidos;
- rejeição de payload de pedido malformado;
- cálculos puros;
- renderização e filtros do Dashboard legado;
- registro, métricas, duração e filtro da cozinha;
- permissões de cadastro de funcionários;
- links e retorno às telas.

Testes usam banco temporário criado pelo Django; não gravam registros de validação no SQLite local.

## 15. Adicionar uma nova página, passo a passo

1. Criar a view em `core/views.py` com `@login_required` e autorização de servidor.
2. Se houver entrada de dados, criar um formulário em `core/forms.py` e um modelo em `core/models.py` quando a informação precisar persistir.
3. Criar/revisar migration e inspecionar seu SQL antes de aplicar.
4. Registrar caminho e nome em `core/urls.py`.
5. Criar o template em `core/templates/core/` e referenciar estáticos com `{% static %}`.
6. Criar/atualizar CSS em `frontend/static/css/` seguindo o shell comum.
7. Adicionar links condicionais nos menus relevantes, sempre com `{% url %}`.
8. Incluir botão de retorno à Home nas telas internas; conservar Sair na Home.
9. Criar testes de acesso, sucesso, validação, estado vazio e caminhos do menu.
10. Executar `manage.py check`, os testes afetados e a suíte completa.
11. Inspecionar diff e status para garantir que arquivos locais como `db.sqlite3` não entrem no commit.

## 16. Publicação GitHub

A branch de trabalho é `feature/Versao-1.0`, rastreada por `origin/feature/Versao-1.0`. Há também o remoto `fork`, configurado para o repositório GitHub pessoal. Antes de publicar:

```bash
git status --short --branch
git diff --check
git diff
```

Adicionar arquivos selecionados explicitamente, excluindo banco e segredos:

```bash
git add README.md DOCUMENTACAO.md core frontend

git status --short
git diff --cached --check
git commit -m "documenta navegação e gestão operacional"
git push origin feature/Versao-1.0
```

O push publica a branch de trabalho. Não use `git add .` sem verificar o status, pois `db.sqlite3`, uploads, credenciais ou outros artefatos locais não devem ser publicados.

## 17. Limites conhecidos e próximos passos

- Produtos, clientes e receitas precisam de modelos e formulários persistentes;
- metadados de cliente, mesa e canal devem ser validados/normalizados no envio do pedido;
- relatórios e Home têm números demonstrativos que devem ser substituídos por agregações do banco;
- falta implementar atualização de status de pedido com autorização e histórico auditável;
- recomenda-se criar auditoria de alterações administrativas e fluxo de redefinição de senha;
- o conteúdo da equipe da cozinha depende de funcionários criados nos grupos apropriados;
- proteja o Admin e as rotas com políticas de senha, limites de tentativas, HTTPS e segredo externo ao código.

## 18. Inventário arquivo a arquivo

Este inventário explica a responsabilidade dos arquivos de código atualmente presentes, inclusive os pontos legados. Uma rota ou arquivo legado pode continuar no repositório para compatibilidade sem aparecer na navegação normal.

### Raiz e projeto

- `manage.py`: despacha comandos Django e seleciona `backend.settings` como configuração ativa.
- `requirements.txt`: fixa Django e lista Gunicorn/WhiteNoise para execução servida; pacotes Python novos devem ser declarados aqui.
- `backend/__init__.py`: marca o pacote Python do projeto.
- `backend/settings.py`: configuração ativa do projeto; caminhos de template, estáticos, banco, middleware, autenticação e segurança.
- `backend/urls.py`: inclui Admin e as rotas nomeadas de `core`.
- `backend/asgi.py`: ponto de entrada ASGI para servidores assíncronos.
- `backend/wsgi.py`: ponto de entrada WSGI para Gunicorn/servidores síncronos.
- `setup/__init__.py`, `setup/settings.py`, `setup/urls.py`, `setup/asgi.py`, `setup/wsgi.py`: outro pacote de configuração presente no repositório. Os comandos normais via `manage.py` usam `backend.settings`; não altere `setup/` presumindo que seja a configuração ativa. Antes de reutilizá-lo, compare os settings e confirme referências.
- `LICENSE`: termos de distribuição do projeto.
- `README.md`: apresentação, instalação curta, acesso e visão resumida de telas.
- `DOCUMENTACAO.md`: este manual operacional/técnico aprofundado.
- `db.sqlite3`: banco local versionado historicamente; contém estado mutável local e não deve receber novas alterações de dados em commits.

### Código Python de `core`

- `core/__init__.py`: inicializador do pacote.
- `core/apps.py`: metadados e configuração do app Django.
- `core/admin.py`: ponto de registro dos modelos no Admin; atualmente não personaliza registros.
- `core/calculations.py`: lógica independente de banco para quantidade total de insumo, custo total, custo por pessoa, composição de custos da receita e soma de pedidos. Usa `Decimal` para valores monetários e lança `ValueError` quando os dados são inválidos.
- `core/forms.py`: apresentação/validação de autenticação, criação de funcionário e registro de preparo. Formulários não persistem sozinhos; as views executam as gravações após `is_valid()`.
- `core/models.py`: schema ORM atual. `Order` guarda pedidos; `KitchenPreparation` guarda preparos da cozinha.
- `core/urls.py`: tabela que associa cada caminho HTTP a uma view e um nome `core:*` usado pelos templates e testes.
- `core/views.py`: autenticação, autorização, redirects por grupo, composição dos contextos, validação de JSON, consultas e persistência. Evite colocar regras de domínio complexas nos templates.
- `core/tests.py`: testes Django de acesso, navegação, views, persistência e formulários.
- `core/tests/blackbox/test_receita.py`: testes externos às views para as funções puras de cálculo, com pytest.
- `core/analytics/`: pacote reservado a análises; não há implementação Python atualmente.
- `core/management/commands/`: diretório reservado a comandos Django próprios; não contém comandos implementados atualmente.

### Migrações

- `core/migrations/__init__.py`: inicializa o pacote de migrações.
- `0001_initial.py`: schema inicial registrado para o app.
- `0002_create_roles.py`: cria grupos administrativos históricos.
- `0003_receita.py`: estado histórico de Receita.
- `0004_alter_receita_quantidade_kg_ingrediente.py`: alteração histórica de unidade/quantidade de ingrediente.
- `0005_create_waiter_role.py`: cria o grupo `Garçom`.
- `0006_order.py`: cria a tabela de pedidos e o vínculo com usuário.
- `0007_kitchenpreparation_remove_ingrediente_receita_and_more.py`: apesar do sufixo longo herdado do autogerador, contém somente a criação de `KitchenPreparation` e seu índice de responsável. Seu SQL foi conferido para garantir que não elimina tabelas.

### Templates de `core/templates/core`

- `base.html`: layout legado compartilhado, navegação por URLs nomeadas, botão Home e formulário POST de logout.
- `login.html`: formulário visual de login; recebe campos e erros da autenticação Django.
- `home.html`: Home por perfil, navegação, cartões e logout POST. Para garçons apresenta apenas rotas de atendimento autorizadas.
- `dashboard.html`: Dashboard administrativo histórico, acessível diretamente mas removido dos menus; ainda é usado por testes e por compatibilidade de pedidos recebidos.
- `pedidos.html`: categorias, produtos, carrinho, taxa, total, POST JSON com CSRF, retorno Home e navegação recolhível.
- `atendimento.html`: indicadores e filtros dos pedidos, linhas da operação, mapa de mesas e links por grupo.
- `produtos.html`: catálogo administrativo, pesquisa, filtro e ação Novo produto, além de retorno à Home.
- `receitas.html`: formulário visual da ficha técnica, linhas dinâmicas de ingrediente e custo estimado; o cadastro ainda não grava modelo de receita.
- `desempenho_cozinha.html`: resumo da produção, filtro por perfil, tabela persistida, retorno Home e formulário de preparo para cozinheiros/auxiliares.
- `funcionarios.html`: formulário de criação de usuário, senha, e-mail e seleção de grupo; apresenta validação e mensagens.
- `relatorios.html`: filtros, indicadores demonstrativos, gráficos Chart.js, mapa horário, análises demonstrativas e exportação/impressão.
- `clientes.html`: tela legada com lista vazia porque não há modelo de Cliente ativo.
- `configuracoes.html`: tela legada de esqueleto para configurações.
- `_orders.html`: fragmento antigo de pedidos para renderização parcial; referencia endpoints históricos que não compõem o fluxo atual de Atendimento.
- `_clients_list.html`: fragmento antigo de lista de clientes; permanece sem modelo de Cliente ativo.

### Templates legados em `frontend/templates`

O settings ativo adiciona essa pasta a `TEMPLATES[0]['DIRS']`. Ela contém `base.html`, `home.html`, `dashboard.html`, `login.html`, `pedidos.html`, `produtos.html` e `relatorios.html`, versões sem o namespace `core/`. O fluxo atual usa predominantemente `core/templates/core/`; ao editar uma tela, confira o nome solicitado no `render()` ou no `LoginView` para não editar uma cópia que não está sendo usada.

### CSS em `frontend/static/css`

- `base.css`: reset e pequenas regras do layout legado; não substitui os estilos específicos.
- `login.css`: tela de autenticação.
- `home.css`: shell e cartões da Home.
- `dashboard.css`: estilos do Dashboard legado.
- `pedidos.css`: layout de pedidos, categorias, catálogo e resumo lateral.
- `cardapio.css`: catálogo administrativo e botão de retorno.
- `receitas.css`: ficha técnica e linhas de ingredientes.
- `operacao.css`: sidebar e componentes comuns de Atendimento/Funcionários.
- `desempenho.css`: tabela, filtros e formulário da equipe de cozinha.
- `relatorios.css`: cartões, gráficos, indicadores e regras de impressão dos relatórios.

### JavaScript em `frontend/static/js`

- `main.js`: inicialização visual da tela de login (mostrar/ocultar senha e estado de envio) e atraso de animação dos cartões da Home; seleciona elementos somente quando eles existem.
- `pedidos.js`: arquivo presente, atualmente vazio. A lógica ativa de carrinho está inline em `core/templates/core/pedidos.html`.
- `produtos.js`: arquivo presente, atualmente vazio. Busca, categorias e navegação do botão estão inline em `core/templates/core/produtos.html`.
- `relatorios.js`: arquivo presente, atualmente vazio. Chart.js, heatmap e exportação estão inline em `core/templates/core/relatorios.html`.

### Recursos estáticos e terceiros

- Chart.js é carregado por CDN na página de Relatórios.
- DM Sans, Space Grotesk e demais fontes são carregadas por CSS via Google Fonts.
- O template legado `base.html` referencia HTMX por CDN; a nova tela Atendimento não depende de HTMX e consulta os dados no render Django.
- Sem rede externa, a página continua com fallback de fontes; gráficos dependem do carregamento de Chart.js.
