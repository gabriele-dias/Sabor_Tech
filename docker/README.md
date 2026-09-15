# Ambiente Docker local

O Compose simula localmente a execução da aplicação em um Azure Container App.

```bash
cp .env.example .env
docker compose up --build
```

A aplicação ficará disponível em `http://localhost:8000`.

O container executa as migrações antes de iniciar o Gunicorn. O volume
`sqlite_data` é apenas para desenvolvimento e testes; não substitui um banco
gerenciado em produção.