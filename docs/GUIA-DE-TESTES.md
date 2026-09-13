# Guia de testes

Este documento define a base de testes do projeto Sabor Tech. O primeiro foco será o dashboard e o cálculo dos pedidos.

## Objetivo

Os testes devem verificar se o sistema:

- protege o dashboard contra acesso sem autenticação;
- exibe os pedidos corretamente;
- calcula o total dos pedidos sem perder casas decimais;
- trata listas vazias e valores inválidos;
- mantém a interface funcionando depois das alterações.

## Tipos de teste

### Teste de caixa-preta

O teste de caixa-preta observa o sistema pelo ponto de vista do usuário. Ele verifica entradas e resultados sem depender da implementação interna.

Exemplo: um usuário autenticado acessa o dashboard e visualiza o total dos pedidos.

### Teste de caixa-branca

O teste de caixa-branca conhece a implementação interna. Ele verifica funções, condições e caminhos específicos do código.

Exemplo: testar diretamente uma função responsável por somar os valores dos pedidos.

## Escopo inicial: dashboard

O dashboard atual apresenta pedidos e clientes. A próxima funcionalidade será calcular o valor total dos pedidos exibidos.

Antes da implementação, usaremos esta regra:

```text
Total dos pedidos = soma do valor de cada pedido
```

Exemplo:

```text
Pedido 1: R$ 45,50
Pedido 2: R$ 67,00
Pedido 3: R$ 32,00
Total: R$ 144,50
```

## Cenários de caixa-preta

| ID | Cenário | Entrada | Resultado esperado |
|---|---|---|---|
| CP-01 | Acesso sem login | Usuário acessa `/` sem autenticação | Usuário é redirecionado para `/login/` |
| CP-02 | Dashboard autenticado | Usuário autenticado acessa `/` | Dashboard é exibido com status HTTP 200 |
| CP-03 | Exibição de pedidos | Dashboard recebe uma lista de pedidos | Cada pedido aparece na tela |
| CP-04 | Total de pedidos | Dashboard recebe pedidos com valores | Total correto aparece no dashboard |
| CP-05 | Nenhum pedido | Dashboard recebe uma lista vazia | Sistema exibe um estado vazio sem quebrar |
| CP-06 | Valor inválido | Pedido possui valor ausente ou inválido | Sistema trata o problema de forma controlada |
| CP-07 | Valor decimal | Pedido possui valor como `45.50` | Total mantém o valor correto, sem erro de arredondamento visível |

## Cenários de caixa-branca

| ID | Parte testada | Situação | Resultado esperado |
|---|---|---|---|
| CB-01 | Função de cálculo | Lista com um pedido | Retorna o valor do pedido |
| CB-02 | Função de cálculo | Lista com vários pedidos | Retorna a soma de todos os valores |
| CB-03 | Função de cálculo | Lista vazia | Retorna zero |
| CB-04 | Função de cálculo | Valor decimal | Mantém o resultado correto |
| CB-05 | Validação | Valor inválido | Rejeita ou trata a entrada conforme a regra definida |
| CB-06 | View do dashboard | Usuário sem permissão | Impede o acesso ou redireciona |
| CB-07 | View do dashboard | Usuário com permissão | Monta o contexto esperado para o template |

## Plano de implementação

A funcionalidade será construída em etapas pequenas:

1. Definir a regra para valores inválidos.
2. Criar uma função isolada para calcular o total.
3. Criar testes de caixa-branca para essa função.
4. Usar o resultado da função na view do dashboard.
5. Exibir o total no template do dashboard.
6. Criar testes de caixa-preta para a página.
7. Adicionar ou ajustar o estilo visual.
8. Validar a interação no navegador, caso exista uma calculadora com botões.

## Arquivos que poderão ser alterados

- `core/views.py`: preparar os dados do cálculo para o dashboard.
- `core/templates/core/dashboard.html`: exibir o total ou a calculadora.
- `core/static/core/css/app.css`: estilizar o novo componente.
- `core/tests.py`: adicionar testes automatizados.

As alterações não devem ser feitas em todos esses arquivos de uma vez. Cada etapa deve ser pequena e validada antes da próxima.

## Checklist

- [x] Definir comportamento para valor inválido.
- [x] Criar função de cálculo.
- [x] Criar testes da função.
- [ ] Executar os testes de caixa-branca.
- [ ] Integrar o cálculo à view.
- [ ] Exibir o resultado no dashboard.
- [ ] Criar testes de caixa-preta da página.
- [ ] Adicionar a interface da calculadora.
- [ ] Testar a interface no navegador.
- [ ] Registrar a alteração em um commit.

## Comandos de validação

Executar todos os testes do projeto:

```bash
./.venv/Scripts/python.exe manage.py test
```

Verificar problemas gerais do Django:

```bash
./.venv/Scripts/python.exe manage.py check
```

Verificar se o Git detecta espaços inválidos:

```bash
git diff --check
```
