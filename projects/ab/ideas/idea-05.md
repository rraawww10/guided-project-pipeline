# Shortest Path Explorer

**One line:** A seeded graph visualizer that finds and steps through the shortest path between two nodes using breadth-first search (BFS).

## Theme
Graph search is a foundational algorithm. This project makes it tangible with a tiny, fixed graph and a stepper that reveals BFS layers. It is worth a session because the algorithm is small, deterministic, and entirely local.

## Sessions
1. Scaffold: render a list or simple grid of nodes and edges from a small JSON seed; allow selecting source and target; placeholder `findPath()` returns none so the page runs.
2. Implement BFS: frontier queue, visited set, parent map; return the shortest path as a node sequence when it exists. Highlight the path in the UI.
3. Add a stepper and edits: expose the BFS layers step-by-step (frontier expansions) on button clicks; allow toggling an edge on/off in-memory and recomputing.

## What the student types
- BFS core: queue pop/push loop, mark-visited, parent backtrack to a path.
- Deterministic layer-by-layer stepper that advances the frontier on each click.
- Safe edge toggle that preserves graph invariants and re-runs BFS.

## What this teaches that the shipped projects do not
None of the shipped projects teach graph traversal or reconstructing paths from parent pointers. This adds algorithmic thinking distinct from sorting or list UIs.

## Out of scope
- Weighted graphs or Dijkstra/A*.
- Large or dynamic layouts; keep a simple layout so logic stays center-stage.

## Risks
UI complexity creep from visualization. Keep the visual minimal (lists and highlighting) so the core BFS remains the focus and fully testable.
