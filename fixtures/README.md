# Integration fixture

`runner-check` is a minimal but real Next.js 15 app used to prove the scripts
against a live build, not a mock. The selftest covers the deterministic core in
a second; this covers the parts that need npm, a browser and a booted server.

```bash
python3 -m pipeline.test_runner fixtures/runner-check --target app       # 3/3 criteria pass
python3 -m pipeline.cutter     cut fixtures/runner-check                 # skeleton + typecheck
python3 -m pipeline.test_runner fixtures/runner-check --target skeleton  # 2 fail, 1 pass
python3 -m pipeline.cutter     verify fixtures/runner-check              # ok, no mismatches
```

It is deliberately shaped to exercise the two things that broke first:

- `app/api/health/route.ts` keeps its `return` **outside** the cut markers, with
  a typed fallback inside. Move the return inside the markers and the cutter
  fails with TS2355 - that is the check working.
- `app/page.tsx` cuts a JSX block, so the `{/* ... */}` comment style is covered.

Not a guided project. It lives outside `projects/` so the watchdog and the
orchestrator never see it.
