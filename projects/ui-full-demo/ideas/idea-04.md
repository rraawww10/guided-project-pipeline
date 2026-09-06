# Shortest Path on a Tiny Grid

**One line:** A 9×9 obstacle grid where you place walls and the app computes and draws one shortest path from start to goal, deterministically.

## Theme
Pathfinding is a classic, and a small grid makes it teachable. This project focuses on BFS plus predecessor backtracking to recover a specific path, with a fixed neighbour order so the answer is reproducible. It’s a clean way to practice queues, visited sets and backtracking.

## Sessions
1. Grid and distance: draw a 9×9 grid at "/", toggle walls in local state, and implement bfsDistance(grid, start, goal) that returns a number or null. Show the distance label; no path drawing yet.
2. Path reconstruction: record parents during BFS and backtrack to one shortest path with a fixed neighbour order (e.g. up, right, down, left). Draw the path cells. Add POST /api/path returning { distance, path } from the same seed.
3. Waypoints: accept an ordered list of 0–3 checkpoints and chain BFS legs (start → w1 → w2 → goal), stopping at the first break with a clear message. Show per-leg distances in a small panel.

## What the student types
- neighbours(p): in-bounds, not-a-wall cardinal neighbours in a pinned order.
- bfs(grid, start, goal): queue + visited + parent map returning distance and parents.
- backtrack(parents, goal): recover a path by following parents to start and reversing.

## What this teaches that the shipped projects do not
- Minesweeper teaches an 8-neighbour flood fill but never reconstructs a path; this adds predecessor backtracking and a tie-break by neighbour order so one path is fixed.
- None of Nonogram, Ledger, Bowling or Elevator deal with spatial paths or per-leg concatenation through waypoints.

## Out of scope
- Diagonals, weighted costs, heuristics (A*), or live animation. One page, one POST endpoint, tiny in-memory grid.

## Risks
- Without a fixed neighbour order, the chosen path can vary; pin it. Large grids would make the DP heavy; we keep it 9×9 with hand-seeded walls.