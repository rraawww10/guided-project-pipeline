# Game of Life Stepper

**One line:** A grid-based Conway’s Game of Life with a manual step button, pattern loader, and clear, deterministic rules.

## Theme
A classic cellular automaton is a perfect vehicle for pure, deterministic state transitions over a grid. It is worth a session because the neighbor-count rule is small but rich, and the UI immediately shows whether the transition logic is correct.

## Sessions
1. Scaffold grid UI: render a small 20×20 board with clickable cells to toggle alive/dead; wire a disabled Step button and a placeholder `next(board)` that echoes the board so the page runs.
2. Implement the rules: pure `next(board)` that counts neighbors and applies the 2/3 survive, 3 born rules. Enable Step to apply `next` once, and allow multi-step.
3. Add a tiny pattern library and controls: load a few seeded patterns (block, blinker, glider) from JSON and center them; add clear/fill; optional torus mode toggle (wrap vs. clamp) as a pure variant.

## What the student types
- Neighbor counting with bounds or wrap handling.
- The transition function `next(board)` returning a fresh board (no mutation-in-place).
- Pattern placement logic that merges a small mask into the board safely.

## What this teaches that the shipped projects do not
None of the shipped projects implement a 2D grid automaton or explicit neighborhood-based transitions. This teaches pure step functions and grid reasoning, different from lists, forms, or aggregates.

## Out of scope
- Animation/timers or real-time ticks (manual Step only keeps tests deterministic).
- Infinite boards or performance tuning.

## Risks
Accidental mutation of the current board causing step-by-step divergence. Emphasize returning new arrays and test for identity changes.
