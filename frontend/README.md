# Anka Investment Frontend

Next.js 14 dashboard for the Anka investment office. Implements authentication, client insights, and interactive charts inspired by the provided Figma direction.

## Setup

```bash
npm install
npm run dev
```

Create a `.env.local` file with:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Available Scripts

- `npm run dev` ? start the local development server
- `npm run build` ? create an optimized production build
- `npm run start` ? serve the build output
- `npm run lint` ? run ESLint

## Tech Stack

- Next.js 14 (App Router) + TypeScript
- TailwindCSS + ShadCN-inspired components
- TanStack Query for server state
- React Hook Form + Zod validation
- Axios for API requests
- Recharts for data visualizations
- react-hot-toast for feedback messages
