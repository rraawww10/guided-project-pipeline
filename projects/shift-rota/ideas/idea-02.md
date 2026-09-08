# PTO Gatekeeper: Keep Coverage While Approving Time‑Off

**One line:** An approval tool that accepts/denies staff PTO requests only when per‑slot minimum coverage stays satisfied, with clear reasons for each decision.

## Theme
Rota quality depends as much on what you decline as on what you schedule. This project models coverage as numbers over a small grid (days × shift types) and teaches reasoning about feasibility. It is valuable because each approval is a decision backed by a check the browser can demonstrate end‑to‑end.

## Sessions
1. Setup + inputs: seed staff, define shift slots, and set per‑slot minimum coverage. UI to submit PTO requests (name, day index, slot). Runs with a pending requests list and a coverage dashboard.
2. Feasibility checks: implement a coverage calculator from the current rota and a safety test that predicts whether approving a given request would violate any minimum. Approving one request updates both the dashboard and the JSON store.
3. Resolver: implement a batch “Resolve All” that orders requests by declared priority (text or number) and greedily approves safe ones; produce a per‑request reason string (Approved, or Denied: breaks Mon‑D1 min 2). Persist the decisions and render an audit table.

## What the student types
- Coverage tally by slot and day, derived from assignments minus approved PTO.
- Safety predicate: would‑approve(request, state) that returns a structured reason.
- Greedy resolver that iterates pending in priority order and commits safe approvals.

## What this teaches that the shipped projects do not
The shipped set leans on filtering, toggles and arithmetic. This idea adds feasibility reasoning over a grid with explicit safety proofs (reasons), making cause/effect visible. It also demonstrates how to encode policy decisions as pure functions, not UI wiring.

## Out of scope
- Real calendar dates; days are D1…D7 labels.
- Optimizing for maximum approvals globally; we use a simple greedy pass with a stable order and reasons.
- Notifications or user accounts.

## Risks
Edge cases where multiple requests hit the same tight slot can make reasoning unclear. Keep seed small and order deterministic so tests can assert the exact approved/denied set and the reason strings.