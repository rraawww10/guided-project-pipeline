# Three-Step Wizard with a Finite State Machine

**One line:** A multi-step form (Profile → Preferences → Confirm) powered by an explicit state machine with guards and a disk-backed draft.

## Theme
Many UIs are wizards in disguise. This project encodes the flow as a tiny finite state machine rather than ad-hoc booleans. It practices pure transition logic, guarded moves (can’t proceed until valid), and a small save/resume flow via local file routes.

## Sessions
1. Flow skeleton: scaffold three pages or a single page with 3 steps, add Next + TS, and seed a draft file. Implement basic Next/Back that moves through steps in-order with placeholder validity. End: users can move Next/Back and see the current step reflected in the UI.
2. Guards and validation: write pure validators for each step (required fields, simple shape checks) and a `nextStateFor(state, event)` that refuses invalid transitions. Add a server route to save/load a draft JSON. End: invalid steps block Next and a refresh reloads the draft.
3. Review and edits: implement a Confirm step that summarizes inputs, supports Edit on any prior step, and disables Finish until all steps are valid. Persist final submission to a separate JSON file. End: a complete, resumable wizard with a deterministic FSM.

## What the student types
- `nextStateFor(state: State, event: Event): State` – the FSM transition function with guard checks.
- `validateStep(id: StepId, data: unknown): Validation` – per-step input validation, pure and unit-testable.
- `persist(kind: "draft"|"final", data: WizardData): Promise<void>` – server route logic writing to local JSON files.

## What this teaches that the shipped projects do not
- An explicit state machine with guards and refusal paths; existing projects focus on lists, searches, or numeric calculations, not FSM design.
- Save/resume semantics without a database, kept small and deterministic for tests.

## Out of scope
- Auth, multi-user conflict handling, or cloud storage.
- Date pickers, time-based steps, or async validation against third parties.
- Drag-and-drop or complex form libraries.

## Risks
- Overbuilding form plumbing; keep inputs minimal so the FSM and guards carry the session.
