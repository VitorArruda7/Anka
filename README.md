# Anka Fullstack Investment Dashboard

Aplicacao full-stack para um escritorio de investimentos gerenciar clientes, ativos, alocacoes e fluxos de caixa. Backend em FastAPI + PostgreSQL + Redis, frontend em Next.js 14. Todo o ambiente sobe via Docker Compose.

## Estrutura do projeto

- `backend/` - API FastAPI com autenticacao JWT, ORM SQLAlchemy 2, Redis para cache, auditoria, exportacao CSV/Excel e testes automatizados `pytest`.
- `frontend/` - Next.js 14 (App Router) com TypeScript, TanStack Query, componentes baseados em ShadCN, graficos e exportacao de dados.
- `docker-compose.yml` - orquestra Postgres 15, Redis 7, backend e frontend.

## Executando com Docker

Prerequisito: Docker Desktop (ou Docker Engine + plugin compose).

```bash
docker compose up --build
```

Servicos apos o build:

- Backend: http://localhost:8000/api
- Docs Swagger: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Desenvolvimento local (sem Docker)

Cada pasta possui README proprio com mais detalhes. Resumo:

1. Criar virtualenv Python e instalar deps: `pip install -r backend/requirements-dev.txt`.
2. Copiar `backend/.env.example` para `backend/.env` e ajustar segredos (`DATABASE_URL`, `SECRET_KEY`, etc.).
3. Rodar migracoes: `alembic upgrade head` (Postgres precisa estar ativo).
4. Iniciar API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
5. No frontend: `npm install` e `cp frontend/.env.example frontend/.env.local` definindo `NEXT_PUBLIC_API_URL`.
6. Rodar `npm run dev`.

## Seed de dados

Existe um seed opcional com usuario demo, clientes, ativos, alocacoes e movimentacoes.

```bash
# Ambiente local
cd backend
python -m app.seed.sample_data

# Usando Docker
docker compose exec backend python -m app.seed.sample_data
```

Credenciais geradas: `demo@anka.com` / `demo123`.

Caso precise resetar completamente o banco em Docker:

```bash
docker compose down
docker volume rm ankafullstack_db_data
docker compose up -d
# aplicar migracoes antes do seed
docker compose exec backend alembic upgrade head
```

## Funcionalidades chave

- Autenticacao JWT com login, registro e CRUD de usuarios (administradores).
- Cadastro e listagem de clientes com paginacao, busca e filtro por status.
- Importacao de ativos via Yahoo Finance (fallback BRAPI) + cadastro manual.
- Gestao de alocacoes (cliente x ativo) com paginacao e exportacao.
- Registro de movimentacoes (deposito/retirada) com filtros de periodo e indicadores.
- Dashboard consolidado com cache Redis, exportacao Excel/CSV.
- Auditoria completa: toda acao CRUD relevante grava evento em `audit_logs` com metadados e user.

## Integracoes externas

- Yahoo Finance para quotes (crumb + cookie automaticos).
- BRAPI como fallback opcional. Configure `BRAPI_TOKEN` em `backend/.env` para ampliar limites.

## Testes

- Backend: `pytest`
- Frontend: `npm run lint`

Os testes backend rodam 100% assincronos usando banco SQLite em memoria. Antes de entregar, execute:

```bash
# backend
dotenv -f backend/.env pytest  # ou simplesmente python -m pytest dentro da venv

# frontend
npm run lint
```

## Auditoria e cache

- `audit_logs` registra acao, entidade, IDs, usuario e payload complementar.
- Redis guarda snapshots do dashboard e quotes de mercado, com invalidacao automatica apos mutacoes.

## Deploy

- Ajustar variaveis em `backend/.env` para ambiente (secret, DB, Redis, tokens).
- Rodar migracoes `alembic upgrade head` apos subir containers.
- Opcional: executar seed para dados demo.
