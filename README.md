# Sabor e Gestão

Sistema de gestão web para o restaurante/empresa Sabor e Gestão, desenvolvido com Django, templates e HTMx para fluxo de dashboard/atendimento.

## Visão geral

Este repositório está em evolução para uma aplicação de operações internas com áreas como dashboard de gestão, atendimento, cadastro de clientes, filtros de pedidos, relatórios e administração de acesso.

## Status atual

A base atual do projeto já está organizada com:

- Aplicação principal `core` com templates e views de navegação.
- Login visual em [core/templates/core/login.html](core/templates/core/login.html).
- Regras de acesso por grupo com `@role_required(...)` em [core/views.py](core/views.py).
- Rotas autenticadas e de login em [core/urls.py](core/urls.py).
- Migração de criação de grupos de acesso em [core/migrations/0002_create_roles.py](core/migrations/0002_create_roles.py).
- Configuração inicial do Django em [setup/settings.py](setup/settings.py).
- Testes básicos de regressão em [core/tests.py](core/tests.py).

## Branch ativa

O trabalho atual está sendo realizado na branch:

```bash
feature/Versão_0.1
```

Também já existe o tracking com o remoto:

```bash
git push -u origin feature/Versão_0.1
```

## Tecnologias

- Python 3.13
- Django
- SQLite
- Django Templates
- HTMx
- Git / GitHub

## Requisitos

- Python 3.10+ (recomendado 3.13)
- Ambiente virtual
- Projeto no GitHub
- Django instalado no ambiente

## Como abrir o ambiente virtual

### Git Bash / Bash

```bash
source .venv/Scripts/activate
```

### PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

### CMD

```cmd
.venv\Scripts\activate.bat
```

Se o ambiente virtual ainda não existir, crie-o com:

```bash
python -m venv .venv
```

## Configuração local

```bash
python -m pip install --upgrade pip
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Como executar

No projeto, com o `.venv` ativado:

```bash
python manage.py runserver
```

Acesse:

- Aplicação principal: http://127.0.0.1:8000/
- Login: http://127.0.0.1:8000/login/
- Administração: http://127.0.0.1:8000/admin/

## Observações importantes

- O diretório `.venv` é local e não deve ser enviado para o GitHub.
- Ele está listado em [.gitignore](.gitignore).
- A aplicação ainda usa dados mock para protótipo em [core/views.py](core/views.py).

## Fluxo de desenvolvimento

```bash
git status
git add .
git commit -m "descreva a mudança"
git push origin feature/Versão_0.1
```

## Próximos passos

- Implementar persistência de pedidos/clientes/produtos com modelos reais.
- Expandir o painel com autenticação e grupos/funções de negócio.
- Criar testes de integração para as páginas principais.
- Preparar estrutura final de deployment.

Este README acompanha o estado atual da branch de desenvolvimento e será atualizado conforme os próximos ciclos forem concluídos.
