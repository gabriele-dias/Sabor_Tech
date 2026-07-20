# Sabor e Gestão

Projeto inicial em Django para a gestão de produtos e operações do restaurante/empresa Sabor e Gestão.

## Visão geral

Este repositório contém a base inicial de um sistema web desenvolvido com Django, com foco na organização e gestão de produtos. O objetivo é evoluir para uma solução completa de gestão com painel administrativo e funcionalidades para cadastro, consulta e controle de itens.

## Status atual

Até o momento, foram implementados os seguintes pontos:

- Estrutura inicial do projeto Django criada.
- Aplicativo principal configurado em `core`.
- Modelo `Produto` criado com os campos `nome` e `preco`.
- Registro do modelo no painel administrativo.
- Configuração inicial das rotas do projeto.
- Migrações iniciais já disponibilizadas no repositório.
- Correção de um erro de importação no painel administrativo, permitindo a execução do projeto.

## Tecnologias utilizadas

- Python
- Django
- SQLite
- Git / GitHub

## Requisitos

- Python 3.10 ou superior
- Django
- Ambiente virtual (recomendado)
- Git Bash no Windows (para uso recomendado no terminal)

## Configuração do ambiente

### 1. Clonar o repositório

```bash
git clone https://github.com/gabriele-dias/Sabor_e_gestao.git
cd Sabor_e_gestao
```

### 2. Criar e ativar o ambiente virtual

No Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

### 3. Instalar dependências

```bash
python -m pip install --upgrade pip
django
```

### 4. Aplicar migrações

```bash
python manage.py migrate
```

### 5. Criar superusuário

```bash
python manage.py createsuperuser
```

## Como executar o projeto

No Git Bash, execute:

```bash
cd /c/Users/taboo/Sabor_e_gestao
source .venv/Scripts/activate
python manage.py runserver
```

Acesse:

- Aplicação: http://127.0.0.1:8000/
- Painel administrativo: http://127.0.0.1:8000/admin/

## Estrutura do projeto

- `core/` - aplicação principal do sistema
- `core/models.py` - definição dos modelos
- `core/admin.py` - configuração do painel administrativo
- `core/views.py` - implementação das views
- `setup/` - configuração geral do projeto Django
- `manage.py` - ponto de entrada do projeto Django

## Fluxo de desenvolvimento

### Commits e branch principal

O projeto utiliza a branch `main` como branch principal para desenvolvimento e entrega.

Exemplos de comandos úteis:

```bash
git status
git add .
git commit -m "mensagem do commit"
git push origin main
```

## Próximos passos

- Implementar o CRUD de produtos.
- Criar telas de cadastro e listagem.
- Melhorar a experiência no painel administrativo.
- Expandir as funcionalidades de gestão.
- Adicionar autenticação e permissões.

## Observações importantes

- O projeto já está rodando corretamente após a correção do erro de importação no painel administrativo.
- Para desenvolvimento local, recomenda-se o uso do terminal Git Bash no Windows.

## Como contribuir

1. Crie uma branch a partir da `main`.
2. Faça as alterações necessárias.
3. Teste localmente.
4. Realize o commit com mensagem clara.
5. Envie para o repositório remoto.

Exemplo:

```bash
git checkout -b feature/nova-funcionalidade
git add .
git commit -m "feat: adicionar nova funcionalidade"
git push origin feature/nova-funcionalidade
```

## Checklist para deploy

- [x] Projeto executando localmente
- [x] Banco de dados configurado
- [x] Migrações aplicadas
- [x] Branch `main` atualizada
- [ ] Ambiente de produção configurado
- [ ] Variáveis sensíveis definidas corretamente
- [ ] Testes finais realizados

Este README será atualizado conforme o projeto evoluir.
