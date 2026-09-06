# Dependency Planner: Topological Order with Cycle Reports

**One line:** A one-screen planner that turns a small set of tasks with dependencies into an execution plan, reporting parallelizable stages and a concrete cycle when one exists.

## Theme
Many real workflows are DAGs, not lists. This project takes a tiny task set and teaches Kahn’s algorithm for topological ordering, plus a human-friendly cycle diagnostic when the graph is not a DAG. It’s valuable because expressing “what can run now” and proving “why it cannot” are everyday engineering skills.

## Sessions
1. Setup + order: seed 6–10 tasks with deps in JSON, build a small graph, implement topoSort(tasks) to produce one valid total order, and render it at "/". It runs end-to-end with a simple list.
2. Cycles and API: detect cycles and reconstruct one exact cycle path (e.g. A → C → D → A). Add POST /api/schedule that returns { order } or { error } with the cycle string; the page shows either.
3. Stages: compute execution levels (wavefronts) where tasks with indegree 0 at each step share a stage. Render a rows-by-stage view so parallelism is visible; editing deps in-memory recomputes deterministically.

## What the student types
- buildGraph(tasks): adjacency and indegree maps from the seed.
- topoSort(graph): Kahn’s queue-based walk that emits a total order and leftover nodes when blocked.
- findCycle(graph): when blocked, backtrack one concrete cycle to report in the error payload.

## What this teaches that the shipped projects do not
- No shipped project computes a DAG topological order or reports a concrete cycle. Minesweeper’s flood fill and Elevator’s dispatch traverse grids/states, not dependency graphs with indegree and cycle detection.
- Ledger parsing validates line shape; this validates global consistency and emits a minimal witness cycle, which is a different class of diagnostic.

## Out of scope
- Weighted scheduling, critical-path duration math, Gantt charts, or persistence. One screen, one POST endpoint, small seeded DAG only.

## Risks
- Cycle reconstruction can overrun if over-designed. Keep it to parent pointers captured when nodes enter the queue, and cap the seed size so tests stay small.