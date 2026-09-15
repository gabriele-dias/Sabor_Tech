# Ambiente Azure simulado

Esta pasta reserva o espaço para os arquivos de infraestrutura do Azure.

O ambiente local equivalente é executado pelo `docker-compose.yml` na raiz:

- uma aplicação web Django em um container;
- um volume nomeado para simular armazenamento persistente do SQLite;
- variáveis de ambiente semelhantes às usadas no Azure Container Apps.

Próximas peças de infraestrutura:

- Azure Container Registry;
- Azure Container Apps Environment;
- Azure Container App;
- Azure Database for PostgreSQL para substituir o SQLite.

Nenhuma credencial ou recurso real do Azure deve ser armazenado neste diretório.