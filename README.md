# Anka Fullstack Investment Dashboard

Aplicação full-stack para um escritório de investimentos gerenciar clientes, ativos, alocações e fluxos de caixa. Backend em FastAPI + PostgreSQL + Redis, frontend em Next.js 14. Todo o ambiente sobe via Docker Compose.

## Estrutura do projeto

- `backend/` - API FastAPI com autenticação JWT, ORM SQLAlchemy 2, Redis para cache, auditoria, exportação CSV/Excel e testes automatizados `pytest`.
- `frontend/` - Next.js 14 (App Router) com TypeScript, TanStack Query, componentes baseados em ShadCN, gráficos e exportação de dados.
- `docker-compose.yml` - orquestra Postgres 15, Redis 7, backend e frontend.

## Executando com Docker

Pré-requisito: Docker Desktop (ou Docker Engine + plugin compose).

```bash
docker compose up --build
```

Serviços após o build:

- Backend: http://localhost:8000/api
- Docs Swagger: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Desenvolvimento local (sem Docker)

Cada pasta possui README próprio com mais detalhes. Resumo rápido:

1. Criar virtualenv Python e instalar dependências: `pip install -r backend/requirements-dev.txt`.
2. Copiar `backend/.env.example` para `backend/.env` e ajustar segredos (`DATABASE_URL`, `SECRET_KEY`, etc.).
3. Rodar migraões: `alembic upgrade head` (Postgres precisa estar ativo).
4. Iniciar API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
5. No frontend: `npm install` e `cp frontend/.env.example frontend/.env.local` definindo `NEXT_PUBLIC_API_URL`.
6. Rodar `npm run dev`.

## Seed de dados

Há um seed opcional com usuário demo, clientes, ativos, alocações e movimentações.

```bash
# Ambiente local
cd backend
python -m app.seed.sample_data

# Usando Docker
docker compose exec backend python -m app.seed.sample_data
```

Credenciais geradas: `demo@anka.com` / `demo123`.

Para resetar completamente o banco em Docker:

```bash
docker compose down
docker volume rm ankafullstack_db_data
docker compose up -d
# aplicar migrações antes do seed
docker compose exec backend alembic upgrade head
```

## Funcionalidades-chave

- Autenticação JWT com login, registro e CRUD de usuários (administradores).
- Cadastro e listagem de clientes com paginação, busca e filtro por status.
- Importação de ativos via Yahoo Finance (fallback BRAPI) + cadastro manual.
- Gestão de alocações (cliente x ativo) com paginação e exportação.
- Registro de movimentações (depósito/retirada) com filtros de período e indicadores.
- Dashboard consolidado com cache Redis, exportação Excel/CSV.
- Auditoria completa: toda ação CRUD relevante grava evento em `audit_logs` com metadados e usuário.

## Integrações externas

- Yahoo Finance para cotações (crumb + cookie automáticos).
- BRAPI como fallback opcional. Configure `BRAPI_TOKEN` em `backend/.env` para ampliar limites.

## Testes

- Backend: `pytest`
- Frontend: `npm run lint`

Os testes backend rodam 100% assíncronos usando banco SQLite em memória. Antes de entregar, execute:

```bash
# backend
cd backend && python -m pytest

# frontend
cd frontend && npm run lint
```

## Auditoria e cache

- `audit_logs` registra ação, entidade, IDs, usuário e payload complementar.
- Redis guarda snapshots do dashboard e quotes de mercado, com invalidação automática após mutações.

## Deploy

- Ajustar variáveis em `backend/.env` para ambiente (secret, DB, Redis, tokens).
- Rodar migrações `alembic upgrade head` após subir containers.
- Opcional: executar seed para dados demo.
