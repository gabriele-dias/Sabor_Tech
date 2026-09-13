# Sabor Tech

Sistema de gestão para restaurantes, com foco em operação interna, dashboard, atendimento e cálculo de custos.

## Visão geral

O Sabor Tech é uma aplicação web em Django para apoiar a gestão de restaurante com fluxos de:

- dashboard operacional;
- atendimento e pedidos;
- clientes e produtos;
- relatórios e KPIs;
- login e controles por perfil de acesso.

A solução está em evolução para se tornar uma plataforma completa de gestão, com base visual funcional e arquitetura pronta para expansão.

## Status atual

O projeto já conta com:

- aplicação principal em Django;
- login customizado com identidade visual da marca;
- controle de acesso por grupos de usuários;
- templates para dashboard, atendimento, clientes, produtos e relatórios;
- rotas autenticadas e fluxo de navegação principal;
- lógica de cálculo de receita/custo com testes automatizados;
- estrutura inicial para evolução para persistência real em banco de dados.

## Stack tecnológica

- Python 3.13
- Django
- SQLite
- Django Templates
- HTMx
- Git e GitHub

## Estrutura do projeto

```text
Sabor_e_gestao/
├── core/
│   ├── static/
│   ├── templates/
│   ├── migrations/
│   ├── calculations.py
│   ├── forms.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── docs/
├── setup/
├── manage.py
├── README.md
├── db.sqlite3
├── .gitignore
└── .venv/
```

## Branch ativa

```bash
feature/Versão_0.1
```

## Requisitos

- Python 3.10+
- Ambiente virtual
- Git
- Django instalado no ambiente

## Como configurar o ambiente

### Criar ambiente virtual

```bash
python -m venv .venv
```

### Ativar ambiente virtual

#### Git Bash / Bash

```bash
source .venv/Scripts/activate
```

#### PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

#### CMD

```cmd
.venv\Scripts\activate.bat
```

## Como rodar localmente

```bash
python -m pip install --upgrade pip
python manage.py migrate
python manage.py test
python manage.py runserver
```

Acesse:

- Dashboard: http://127.0.0.1:8000/
- Login: http://127.0.0.1:8000/login/
- Administração: http://127.0.0.1:8000/admin/

## Observações importantes

- O diretório `.venv` foi incluído em [.gitignore](.gitignore) e não deve ser versionado.
- A aplicação ainda usa dados mock para protótipo, principalmente em [core/views.py](core/views.py).
- A estrutura atual foi pensada para evoluir para persistência real com modelos de clientes, produtos e pedidos.

## Fluxo de desenvolvimento

```bash
git status
git add .
git commit -m "descreva a mudança"
git push origin feature/Versão_0.1
```

## Próximos passos

- migrar dados mock para modelos reais do Django;
- criar cadastros de produtos, clientes e pedidos persistentes;
- ampliar a lógica de relatórios e KPIs;
- melhorar autenticação e permissões por perfil;
- adicionar testes de integração para páginas e fluxos principais;
- preparar a aplicação para deploy.

## Conclusão

Este README acompanha a fase atual do projeto e será atualizado conforme a plataforma evolui para uma solução completa de gestão para restaurantes.
