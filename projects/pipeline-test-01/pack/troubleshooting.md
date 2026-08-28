# Troubleshooting

Errors students in this project actually hit, in the order they hit them. Each
one: what they see, why, what you say.

## Getting the app running

**`sh: next: not found` / `'next' is not recognized`**
`node_modules` is missing. Run `npm install` (or `npm ci`, since the tree ships
a `package-lock.json`) in the folder that holds `package.json`. Do this before
the session, never in it.

**`Error: listen EADDRINUSE: address already in use :::3000`**
Something else is on port 3000, usually yesterday's dev server.

```bash
npm run dev -- -p 3001
```

If they move the port, the test command has to move with it - `BASE_URL` must
point at the port the app is actually on.

**`npm error code ENOENT ... package.json`**
Wrong directory. `package.json`, `lib/` and `app/` sit side by side in the
project root; that is where every command runs.

**`npm install` printed a vulnerability advisory.**
Read the line, do not just look at the exit code. It does not stop the class,
but it is worth a note to whoever maintains the pack.

**The server starts but every route 404s.**
They are on the wrong URL. The three that exist are `/boards/intro`,
`/boards/field` and `/boards/corner`, each with a `/solved` variant, plus
`/api/boards`.

## The page looks wrong

**Every non-mine square reads `undefined`.**
`counts` is still the empty fallback in `lib/board.ts`. `counts[index]` on an
empty array is `undefined`, and the text rule turns that into the word. Finish
`cut-neighbour-counts`. Sessions 1 to 3.

**The grid is empty - 0 cells - and the loop looks right.**
Either `cells` is never filled (`cut-solved-cells` still open), or they looped
over `counts`, which is empty until the neighbour scan is written. Both grids
must iterate `board.width * board.height`.

**Every square shows `0`.**
The text rule: a cell that is not a mine and whose count is 0 shows *empty*
text. The 0 still belongs in `data-count`.

**The whole grid is one long row.**
They edited the `board-grid` element or its `gridTemplateColumns` style. That
markup is given; restore it from the original tree.

**`Board not found` on a board that exists.**
The id in the URL is not one of the three, or `findBoard` was edited. That
screen is the given not-found state and `c-1-6` and `c-2-4` grade it.

**A blank white page and a console error about hooks or `useParams`.**
Both screens are client components. The `'use client'` line at the top of the
file is load-bearing - `useParams`, `useState` and `useEffect` all need it.

**The board flashes empty for a moment on load.**
Correct and expected. Before the first `GET /api/boards/[id]` answers, the page
draws no cells. Nothing grades that moment.

## Clicks and state

**Nothing happens when I click a cell, session 2.**
Two causes, in this order: flag mode is on (the button says `Flag mode: on` -
its branch is session 3's work and is empty until then), or `cut-play-click` is
still open.

**The first click does nothing, the second click opens both.**
The state array was mutated - `push`, `splice`, or sorting in place - and then
handed back to React, which sees the same array and does not re-render. Build a
new array every time.

**The tab freezes and the fan spins up.**
The flood fill never ends: no `visited` set, or cells marked visited when they
come off the queue instead of when they go on. Kill the tab, fix the walk, and
say the rule - visited means queued, not finished.

**One click opens the entire board.**
The fill walks out of numbered cells. On `field` that is 54 cells instead of 14.
The numbered cell is added to the set and then the walk stops there.

**Clicking a mine opens a region.**
The mine test comes after the count test. `intro` index 9 is a mine no mine
touches, so its count is 0 and a count-first fill floods out of it.

**A flagged cell opens anyway, or an open cell takes a flag.**
The two branches of `onCellClick` each guard the other's state, and one of the
guards is missing. `c-3-5` drives both on purpose.

**`Mines left` never goes below 0.**
Someone clamped it. It is `board.mines.length` minus the number of flags, and
`c-3-5` expects `Mines left: -1`.

## TypeScript and the build

**`TS2355: A function whose declared type is neither 'undefined' nor 'any' must
return a value`**
They deleted the fallback above the TODO, or the `return` below it. Both are
there so the file keeps compiling with the block empty. Put it back.

**`Cannot find module '@/lib/reveal'`**
The `@/` alias maps to the project root, so it is `@/lib/reveal`, not
`@/app/lib/reveal` and not a relative climb out of `app/`.

**`Property 'id' does not exist on type 'Promise<...>'` in a route handler.**
In Next 15 the route's `params` is a Promise: the given handlers do
`const { id } = await params`. Nothing in this project asks a student to write a
route handler, so this only appears when given code has been edited.

**The dev server compiles but the criteria fail in a fresh checkout.**
`npm run build` is stricter than `npm run dev`. The pipeline's test command
builds first, so a type error that `dev` tolerated will surface there.

## Running the tests

**How to run one criterion, against the dev server the class already has:**

```bash
cd projects/pipeline-test-01
BASE_URL=http://localhost:3000 .pipeline/venv/bin/python -m pytest skeleton/verify -q -k c_2_1
# Windows: .pipeline\venv\Scripts\python.exe -m pytest skeleton\verify -q -k c_2_1
```

**How to run all 18, the way the pipeline does** - installs, builds, starts the
app on a free port, writes `skeleton-results.json`:

```bash
python3 -m pipeline test pipeline-test-01 --target skeleton
```

**`RuntimeError: BASE_URL is not set`**

```text
BASE_URL is not set. This suite never starts a server - it talks to an app that
is already running. Start the app, then point BASE_URL at it, or let the
pipeline do both: python3 -m pipeline test <slug>
```

Exactly what it says. The suite never boots anything.

**`Executable doesn't exist ... playwright install`**
The browser is missing. Once per machine:

```bash
.pipeline/venv/bin/playwright install chromium
```

**A UI test fails with `Locator expected to have count '25' / Actual value: 0`
after waiting 20 seconds.**
The page rendered no cells for the whole timeout. Either the app under test is
not the tree they edited, or the cut is still open. Open the same URL in a
browser before believing the test.

**A criterion that was green has gone red.**
Five of the 18 grade handed-over code and are green before anyone writes a
line: `c-1-3`, `c-1-6`, `c-2-3`, `c-2-4` and `c-3-1`. If one of those breaks,
given code was edited - look there first, not at the TODO.

**The test names look nothing like the criteria.**
Every test is named after the criterion it grades: `-k c_1_1` selects the test
for `c-1-1`, `-k c_3_6` for `c-3-6`. The full map is in `results.json`.

## Two things that are correct even though they look wrong

- **A mine has a neighbour count too.** `field` index 63 is a mine with a count
  of 0; `corner` index 15 is a mine with a count of 2. The glyph is the visible
  text, the count is the attribute.
- **The board does not lock when the game ends.** A click after `Won` or `Lost`
  opens or flags its cell exactly as before. `c-3-6` clicks once more after
  `Lost` and expects the next cell to open.
