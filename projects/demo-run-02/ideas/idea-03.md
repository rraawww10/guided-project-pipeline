# PathQuiz: A Branching Quiz Engine

**One line:** A finite-state quiz where answers traverse a JSON-defined graph to an outcome, with a summary of the path taken.

## Theme
Many apps are state machines at heart. This project makes that explicit: a tiny quiz engine whose nodes and edges live in a seed JSON, with the UI rendering the current node and choices. It’s valuable because students practice explicit state modeling and safe transitions.

## Sessions
1. App boots and renders a first question: seed quiz.json (nodes, choices, outcomes), GET /api/quiz?id=<node> returns a node, and the UI renders text and buttons to choose an edge.
2. Navigation and validation: implement nextNode(currentId, choiceId) as a pure function with guards (no missing edges, no cycles allowed by policy); track the path and render an outcome view when reaching a leaf.
3. Scoring and summary: implement computeScore(path) from accumulated tags or weights, show a summary component, and add a restart button that resets to the initial node.

## What the student types
- nextNodeWithValidation(graph, currentId, choiceId): computes the next node or a well-typed error.
- isLeaf(node): guard that decides when to show the outcome screen.
- computeScore(path): folds tags/weights along the taken edges into a category or total.

## What this teaches that the shipped projects do not
- An explicit finite-state model and safe transitions instead of another CRUD list.
- Defensive validation at the API boundary with deterministic error shapes the UI can test.
- Representing and inspecting a path for derived results without relying on time or external services.

## Out of scope
- Timers, persistence beyond in-memory React state, or user accounts.

## Risks
Graph validation rules (e.g., forbidding cycles) need crisp wording and fixtures so tests are stable and the engine remains small enough for the minutes budget.