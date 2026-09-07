# Portfolio Rebalancer - Instructor Pack

One dashboard evolves over five 40-minute sessions. Students read a seeded SQLite DB via Prisma, compute weights and drift, generate an integer-share trade plan under a cash cap, edit targets/budget, and apply the plan to update holdings.

What makes this teachable:
- One page at "/" that keeps growing.
- Small JSON API with deterministic data.
- No external services, no real clock.

How to run (instructor or student):
1. cd projects/stock-tracker/app
2. npm ci
   - postinstall runs automatically: `prisma generate && prisma db push && node prisma/seed.js`
3. npm run dev (port 3000)
4. Open http://localhost:3000

Build/start (CI-style):
- npm run build
- npm start

Notes you’ll teach into:
- Targets and budget are fractions and cents, respectively.
  - Target inputs accept fractions 0..1 (0.125 means 12.5%).
  - Budget input is raw cents (e.g. 100000 == $1000.00).
- Plan includes BUY and SELL items; only BUYs count toward the budget.
- Endpoints force dynamic rendering where state mutates:
  
  ```ts
  // app/app/api/positions/route.ts
  export const dynamic = 'force-dynamic'
  ```

Session map at a glance:
- S1: Seed + GET /api/positions + table rows + weight cell
- S2: Allocation math + GET /api/allocation + drift badges + loading state
- S3: Rank and allocate + POST /api/trade-plan + plan table
- S4: Edit targets/budget + PUT /api/{targets,settings} + recompute in place
- S5: Apply plan + record trades + reconcile + notice

Repo facts:
- Stack: Next 16, React 18, TypeScript, Prisma 5, SQLite.
- Prisma schema + seed live under app/prisma/; a dev.db is committed for determinism.
- Tests exercise only DOM hooks and HTTP; no CSS assertions.
