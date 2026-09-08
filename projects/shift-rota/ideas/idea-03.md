# Shift Bidding Allocator: Points → Assignments

**One line:** Staff bid points on desired shifts; an allocator assigns each slot to the highest effective bid under fairness caps and rest rules.

## Theme
Many teams “bid” on unpopular shifts with points. Turning that into code forces careful ordering, tie‑breaks and constraints. This project delivers a visible allocation from compact numeric input and explains the result with a fairness/readout panel.

## Sessions
1. Setup + bids: seed staff with a per‑week cap (max shifts) and render a small week/slot grid. UI to enter bids (name, slot, points). Runs with a bids table persisted to a JSON file.
2. Allocator v1: implement a deterministic assignment pass that sorts bids by points, then by fewest assigned so far, then by name. Assign a bid if it does not exceed the person’s cap and does not clash same‑day. Show the computed assignment grid.
3. Fairness audit: implement a score panel (e.g., total points won per person vs. bids placed; variance of load). Add a single‑pass “rebalance” that tries one swap when it reduces variance without breaking constraints. Persist the final plan.

## What the student types
- Stable sort with multi‑key tie‑break (points DESC, assigned ASC, name ASC).
- Assignment engine that scans bids and commits if constraints pass.
- Fairness/audit functions: per‑person won‑points, load variance, and a safe one‑swap improvement.

## What this teaches that the shipped projects do not
Unlike list/filter or simple calculators, this is a constrained optimization with explicit, testable tie‑breaks and a post‑hoc audit. It stays small enough to seed by hand and is fully deterministic for grading.

## Out of scope
- Global optimal allocation (ILP/flow). We keep a single greedy pass plus at most one improving swap.
- Real calendars, authentication, or drag/drop.

## Risks
Choosing too many slots or bids can make tests flaky on order; keep seeds intentionally non‑alphabetic and non‑numeric to prove sorting without coincidence.