# Plano Sabor_Tech: Docker, GitHub Actions e Azure

Este documento registra o plano de infraestrutura para executar o Sabor_Tech em Docker, validar o projeto no GitHub Actions e publicar a aplicação no Microsoft Azure. A implementação fica para uma etapa posterior.

## Objetivo

Preparar uma entrega repetível que:

1. construa a imagem Docker;
2. aplique as migrações em um ambiente isolado;
3. execute `django check` e todos os testes;
4. publique a imagem no Azure Container Registry;
5. atualize o Azure Container Apps somente depois da aprovação dos testes.

## Etapas planejadas

### 1. Containerização

- Criar `Dockerfile` com Python 3.13.
- Adicionar `requirements.txt` com Django, Gunicorn e WhiteNoise.
- Adicionar `.dockerignore` para excluir `.git`, `.venv`, cache Python e SQLite local.
- Executar Gunicorn na porta `8000`.
- Executar `migrate` no início do container.
- Configurar `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` por variáveis de ambiente.

### 2. GitHub Actions

Criar `.github/workflows/docker-azure.yml` com dois jobs:

- `docker-test`: build da imagem, migrações, `python manage.py check` e `python manage.py test`.
- `push-and-deploy`: executado somente em push na branch `main`; publica a imagem no Azure Container Registry e atualiza o Azure Container Apps.

Pull Requests devem executar somente a validação Docker.

### 3. Azure

Criar os seguintes recursos:

- Resource Group;
- Azure Container Registry;
- Container Apps Environment;
- Azure Container App com ingress externo e porta `8000`.

Configurar no ambiente `production` do GitHub:

- `AZURE_CREDENTIALS`;
- `AZURE_RESOURCE_GROUP`;
- `AZURE_CONTAINER_APP_NAME`;
- `ACR_LOGIN_SERVER`;
- `ACR_USERNAME`;
- `ACR_PASSWORD`.

As credenciais nunca devem entrar no código ou no YAML.

## Plano de testes caixa-preta

Os testes de caixa-preta observam o comportamento pelo ponto de vista do usuário, sem depender da implementação interna.

| ID | Cenário | Resultado esperado |
|---|---|---|
| CP-01 | Abrir o sistema sem autenticação | Redireciona para `/login/` |
| CP-02 | Entrar com usuário autorizado | Abre o cardápio e seus valores |
| CP-03 | Informar data inicial e final | Exibe somente pedidos do intervalo |
| CP-04 | Informar datas invertidas | Normaliza o intervalo sem quebrar a tela |
| CP-05 | Consultar intervalo sem pedidos | Exibe valores zerados e mantém a página funcional |
| CP-06 | Abrir a aplicação em container | Responde pela porta `8000` |
| CP-07 | Acessar a URL publicada no Azure | Container App responde externamente |

## Plano de testes caixa-branca

Os testes de caixa-branca verificam funções, condições, contexto e caminhos internos.

| ID | Parte testada | Resultado esperado |
|---|---|---|
| CB-01 | `calculate_orders_total` com vários pedidos | Retorna a soma decimal correta |
| CB-02 | `calculate_orders_total` com lista vazia | Retorna `Decimal("0.00")` |
| CB-03 | Valor inválido ou negativo | Levanta `ValueError` |
| CB-04 | View sem grupo `Gestão` | Bloqueia o acesso e redireciona |
| CB-05 | View com intervalo de datas | Filtra o intervalo de forma inclusiva |
| CB-06 | Contexto da view | Contém pedidos, vendas, custo, lucro e quantidade de dias |
| CB-07 | Pipeline Docker | Executa migrações, `check` e testes antes do deploy |

## Comandos de validação local

Depois da implementação do plano:

```bash
python manage.py check
python manage.py test

docker build -t sabor-tech:test .
docker run --rm sabor-tech:test sh -c "python manage.py migrate --noinput && python manage.py check && python manage.py test"
```

## Limitação atual

O projeto usa SQLite e dados mockados. SQLite em Container Apps não deve ser tratado como armazenamento persistente. Antes de usar o Azure como ambiente definitivo, migrar o banco para Azure Database for PostgreSQL e transformar pedidos, clientes e produtos em modelos persistentes.
