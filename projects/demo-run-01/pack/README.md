Shortlist Scorer — Instructor Pack

What this project is
- A small Next + React + TypeScript app that ranks a fixed seed of 10 candidates by a couple of signals and explains the score.
- 3 sessions x 40 minutes. Session 1: seed + list + toggles. Session 2: pure scorer + /api/rank + UI scores. Session 3: stable comparator + min filter.

How to run it locally
- Requirements: Node 18+.
- From projects/demo-run-01/app:
  - npm install
  - npm run dev
  - Open http://localhost:3000 (App Router at app/app).
- To run the test suite the pipeline uses (optional for teaching):
  - From the project root, the harness runs pytest against verify/; instructors can read tests for intent but do not need to run them in class.

Files to keep open while teaching
- Session 1
  - app/app/api/candidates/route.ts
  - app/app/page.tsx
  - app/data/candidates.ts (seed)
- Session 2
  - app/lib/score.ts
  - app/app/api/rank/route.ts
  - app/app/page.tsx
- Session 3
  - app/lib/sort.ts
  - app/app/api/rank/route.ts

What “done” looks like per session
- End of Session 1: GET /api/candidates returns 200 with 10 items; "/" renders 10 cards; both toggles visible and start unchecked.
- End of Session 2: Toggling “years” shows scores to two decimals and a reasons line containing “years”; /api/rank accepts active=years and returns 10 RankItem.
- End of Session 3: /api/rank ordering is stable under ties (see spec); /api/rank?active=years&min=100 returns [].
