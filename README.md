# Anka Fullstack Investment Dashboard

Plataforma full-stack para gerenciar clientes, alocações de ativos e fluxos de caixa de um escritório de investimentos. O stack combina FastAPI, PostgreSQL e Redis no backend com um dashboard Next.js 14 no frontend. Tudo está containerizado via Docker Compose.

## Estrutura

- `backend/` – serviço FastAPI com autenticação JWT, modelos SQLAlchemy, migrações Alembic, testes assíncronos e exportação CSV.
- `frontend/` – projeto Next.js 14 (App Router) com TanStack Query, UI inspirada no ShadCN, gráficos e downloads CSV.
- `docker-compose.yml` – orquestra PostgreSQL, Redis, API e interface.

## Execução com Docker

Pré-requisito: Docker Desktop (ou docker + plugin docker compose).

```bash
docker compose up --build
```

Serviços disponíveis:

- API Backend: http://localhost:8000/api
- API Docs (Swagger): http://localhost:8000/docs
- Aplicação Frontend: http://localhost:3000

## Desenvolvimento local

Backend e frontend podem rodar separados fora do Docker. Cada pasta tem instruções detalhadas (`backend/README.md`, `frontend/README.md`). Passo a passo geral:

1. Criar e ativar uma virtualenv Python.
2. `pip install -r backend/requirements-dev.txt`
3. Copiar `backend/.env.example` para `backend/.env` e ajustar segredos/URLs.
4. Rodar migrações: `alembic upgrade head` (PostgreSQL precisa estar disponível).
5. Iniciar a API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
6. No frontend, `npm install`.
7. Copiar `frontend/.env.example` para `.env.local` e definir `NEXT_PUBLIC_API_URL`.
8. Rodar `npm run dev`.

## Populando o sistema

### Seed automático

Uma base demo (usuário, clientes, ativos, alocações e movimentações) pode ser carregada quando quiser.

```bash
# Ambiente local
cd backend
python -m app.seed.sample_data

# Via Docker
docker compose exec backend python -m app.seed.sample_data
```

Credenciais geradas: `demo@anka.com` / `demo123`.

### Fluxo manual

1. **Importar ativos:** na página *Ativos* busque tickers como `PETR4.SA` ou `AAPL`. A API consulta primeiro o Yahoo Finance e, se necessário, recorre à BRAPI.
2. **Cadastrar clientes:** na tela *Clientes*, informe nome, e-mail e status.
3. **Alocações:** vincule clientes e ativos na tela *Alocações* (quantidade, preço, data).
4. **Movimentações:** registre entradas/saídas em *Movimentações* para alimentar indicadores de fluxo.
5. **Exportações:** gere CSVs (clientes, alocações, movimentações) na tela *Exportações* ou via `/api/export/*`.

## Integração de dados de mercado

- Fonte primária: Yahoo Finance (requisições autenticadas via crumb e cookie).
- Fallback: endpoint público da BRAPI para contornar limites regionais.
- Token opcional: configure `BRAPI_TOKEN` no `backend/.env` se possuir chave (maior quota para ativos brasileiros).

O serviço sempre normaliza ticker, nome, bolsa e moeda antes de salvar novos ativos.

## Testes

- Backend: `pytest`
- Frontend: `npm run lint`
