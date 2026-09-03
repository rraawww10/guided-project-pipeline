# Session 1 - Setup, the shaft, and one tick

**Time:** the plan below runs to **47 minutes** against a 40-minute cap. That is
an overrun of seven, and it is disclosed at the bottom with what to trim. Read
that section before you teach this.

**Students start from:** the skeleton, installed, with `npm run dev` up.
`/scenarios/above` already draws the shaft - eight floors, floor 8 at the top,
the car on floor **2**, mode **moving**, tick **0**, served **0**. Pressing
**step** advances the tick readout and nothing else: the car sits on floor 2 for
ever. c-1-1, c-1-2 and c-1-6 are already green and none of them is theirs.

**Students end with:** the same page, where four presses put the car on floor 6
with the doors open and a fifth serves the caller and goes idle - `served-6`
reading **4** and `served-count` reading **1**. c-1-3, c-1-4 and c-1-5 green, so
all six of session 1's criteria pass.

## What they learn

1. **A discriminated union for a mode.** `Car` is one of three shapes, not a
   floor plus three booleans. A `doors` car has no `direction` and no `target`
   *at all* - the fields do not exist on that member - so an impossible car
   cannot be written down.
2. **One pure transition per tick.** `step(state)` takes a state and answers a
   new one. It has no side effects, no clock, no knowledge of React, and it
   never asks where the car should go next - only what happens in one tick.
3. **The declared fallback.** `step` starts by writing down the answer for the
   boring case - tick forward, car unchanged - and each branch overwrites it.
   That is why the `idle` case needs no code, and why the skeleton still
   compiles with both blocks empty.
4. **`calledAt` and `servedAt` are two different ticks**, and the tick the page
   is showing is a third one.

## Before you start

- Every student has run `npm ci` in `skeleton/` **before the session** and has
  `npm run dev` up on `http://localhost:3000/scenarios/above`. Do not spend live
  minutes on the install - it is one to two minutes each and it is the first
  thing to cut if you have to.
- Have open, in this order: `lib/types.ts`, `data/scenarios.json`,
  `lib/state.ts`, `app/scenarios/[id]/Shaft.tsx`, `lib/step.ts`. You will read
  the first four and type in the last one.
- Have the browser on `/scenarios/above`. **Only ever open `above`, `passing`
  and `quiet` today.** `/scenarios/overtake` is a live route and it misbehaves on
  the manual walk - see the warning at the end of the cut points.
- There is no `/` in this app. It is a 404. Tell the room before somebody
  reports it as a bug.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Everyone's page is up on `/scenarios/above`. Press **step** five times together. The tick climbs 0, 1, 2, 3, 4, 5 - and the car never leaves floor 2. Ask the room: the tick is moving, so *something* is running. What is missing? Do not answer yet. |
| 4-9 | Read the handed code, four files, fast. `lib/types.ts` - the `Car` union. `data/scenarios.json` - the `above` row, one call on floor 6 at tick 0. `lib/state.ts` - `manualStart` puts a moving car on floor 2 aimed at floor 6. `Shaft.tsx` - the button is `onClick={() => setState(step(state))}` and that is the whole of it. So the page is already calling their function. |
| 9-13 | Open `lib/step.ts`. Read the fallback line, then the two `TODO`s. Say what the shape means: `next` is *already* the right answer for an idle car, each branch replaces it, and there is exactly one `return`, at the bottom, outside both blocks. That is today's whole job - two blocks, nine or ten lines between them. |
| 13-25 | Live: **`cut-step-move`**. Direction first, then the landing test, then the two shapes. Reload and press four times: floor 6, mode `doors`. |
| 25-27 | Open `/scenarios/passing` and press twice: floor 3, still `moving`, even though floor 3 is a called floor. Ask why - and answer it: nothing on this page decides where the car goes, so nobody is watching for floor 3. That is next session. c-1-3 and c-1-4 are green. |
| 27-38 | Live: **`cut-step-doors`**. The two filters, then the three ticks in `{ floor, calledAt, servedAt }`, then `idle`. |
| 38-45 | Students catch up. Circulate. The symptoms under **Where students get stuck** are the ones you will actually see, in roughly that order. |
| 45-47 | Five presses on `/scenarios/above`: `served-6` reads 4, `served-count` reads 1, the car is `idle`. Say what is still missing - the car only ever goes where `manualStart` aimed it, and next session writes the thing that decides. |

## The code they are handed, and that you read on screen

These are the pieces you point at, not the pieces they type.

The `Car` union - the one type worth four minutes:

```ts
export type Car =
  | { mode: 'moving'; floor: number; direction: Direction; target: number }
  | { mode: 'doors'; floor: number }
  | { mode: 'idle'; floor: number }
```

The two seeds, `lib/state.ts`. Session 1's page uses the second one:

```ts
export function seed(scenario: Scenario): SimState {
  return {
    tick: 0,
    car: { mode: 'idle', floor: scenario.start },
    pending: scenario.calls.map((call) => ({ floor: call.floor, tick: call.tick })),
    served: [],
  }
}

/**
 * Tick 0, a `moving` car at `scenario.start` aimed at `calls[0].floor` with the
 * direction that points at it, or an `idle` car for a scenario with no calls.
 *
 * This reads `calls[0]` straight out of the data: it computes no nearest floor
 * and no direction rule, so no part of session 2's policy is visible in session
 * 1's shipped code for a student to copy.
 */
export function manualStart(scenario: Scenario): SimState {
  const base = seed(scenario)
  const first = scenario.calls[0]
  if (first === undefined) return base
  const direction: Direction = first.floor < scenario.start ? 'down' : 'up'
  return { ...base, car: { mode: 'moving', floor: scenario.start, direction, target: first.floor } }
}
```

Say what `manualStart` is and is not: it reads `calls[0]` straight out of the
data and aims at it. It computes no nearest floor and applies no direction rule,
because deciding *which* call to go for is next session's whole subject. Today
the car has one destination, handed to it, and `step` only has to get there.

The shaft rows, from `Shaft.tsx`. `floors` is built high-to-low, which is why
floor 8 is at the top:

```tsx
  const floors = Array.from({ length: scenario.floors }, (_, index) => scenario.floors - index)
```

```tsx
      <ol className="plain shaft">
        {floors.map((floor) => (
          <li className={floor === state.car.floor ? 'here' : undefined} key={floor} data-testid={`floor-${floor}`}>
            {floor}
            <span className="marker">{floor === state.car.floor ? state.car.mode : null}</span>
          </li>
        ))}
      </ol>
```

The four readouts. Every one of them is `state.<something>` - there is no
derived display value anywhere on this page:

```tsx
      <div className="readouts">
        <span>
          <span className="label">floor</span>
          <span className="value" data-testid="car-floor">{state.car.floor}</span>
        </span>
        <span>
          <span className="label">mode</span>
          <span className="value" data-testid="car-mode">{state.car.mode}</span>
        </span>
        <span>
          <span className="label">tick</span>
          <span className="value" data-testid="tick">{state.tick}</span>
        </span>
        <span>
          <span className="label">served</span>
          <span className="value" data-testid="served-count">{state.served.length}</span>
        </span>
      </div>
```

The button. Read this line out loud twice:

```tsx
      <button type="button" data-testid="step-button" onClick={() => setState(step(state))}>
        step
      </button>
```

"Set the state to one step on from the state we have." All the learning is
inside `step`. Nothing about a lift is in the click.

The served list, so they know where `served-6` comes from:

```tsx
      <h2>served</h2>
      <ul className="plain served">
        {state.served.map((entry) => (
          <li key={entry.floor}>
            {`floor ${entry.floor} served at tick `}
            <span data-testid={`served-${entry.floor}`}>{entry.servedAt}</span>
          </li>
        ))}
      </ul>
```

And if anyone asks how the page got its scenario - it is resolved on the server
before anything renders, so the first frame already holds the seeded state:

```tsx
export default async function ScenarioPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const scenarios = await readScenarios()
  const scenario = scenarios.find((entry) => entry.id === id)

  if (scenario === undefined) {
    return (
      <main className="page">
        <h1>Lift</h1>
        <p className="missing" data-testid="no-scenario">{`No scenario with id ${id}`}</p>
      </main>
    )
  }

  return <Shaft scenario={scenario} />
}
```

## Cut points in this session

Both are in `lib/step.ts`. This is the whole file the student opens, below its
comment block - the two `TODO` lines are the session:

```ts
export function step(state: SimState): SimState {
  let next: SimState = { ...state, tick: state.tick + 1 }

  if (state.car.mode === 'moving') {
    const car = state.car
    // TODO(cut-step-move): The car is `moving`, so put into `next` a car one floor along `car.direction`: `'up'` adds one to `car.floor` and `'down'` takes one away. `car.target` decides only where the doors open, never which way the car travels. Landing on `car.target` gives the pair `{ mode: 'doors', floor: car.target }`, and otherwise a `moving` car at the new floor keeping the same `direction` and `target`. Leave `pending` and `served` as they are.
  } else if (state.car.mode === 'doors') {
    const car = state.car
    // TODO(cut-step-doors): The doors are open at `car.floor`, so put into `next` the state one tick on: each call in `state.pending` for that floor with a `tick` at or below `state.tick` joins `served` as `{ floor, calledAt: the call's own tick, servedAt: state.tick }` and leaves `pending`, and the car becomes `{ mode: 'idle', floor: car.floor }`.
  }

  return next
}
```

### cut-step-move - `lib/step.ts:27`

**What students see** (the skeleton, exactly):

```ts
  if (state.car.mode === 'moving') {
    const car = state.car
    // TODO(cut-step-move): The car is `moving`, so put into `next` a car one floor along `car.direction`: `'up'` adds one to `car.floor` and `'down'` takes one away. `car.target` decides only where the doors open, never which way the car travels. Landing on `car.target` gives the pair `{ mode: 'doors', floor: car.target }`, and otherwise a `moving` car at the new floor keeping the same `direction` and `target`. Leave `pending` and `served` as they are.
  } else if (state.car.mode === 'doors') {
```

**What they write.** One local for the new floor: one above `car.floor` when
`car.direction` is `'up'`, one below when it is `'down'`. Then one assignment to
`next` that spreads `next` and replaces `car` with one of two shapes - if the
new floor equals `car.target`, `{ mode: 'doors', floor: car.target }`; if not, a
`moving` car at the new floor carrying the *same* `direction` and the *same*
`target`. Nothing else. `pending` and `served` are not mentioned, so the spread
carries them through untouched. Eight lines.

**Teach it like this.** "The car does not steer. It travels the way its
`direction` field says, one floor per tick, and `target` is only the floor it is
allowed to stop at. Move first, then ask 'am I there?'"

Then say the same thing as a warning, because it is the mistake half the room is
about to make: **do not compute the direction from the target.**
`car.target - car.floor` would give you the right answer today and it makes
`direction` a decoration - a field the trace prints and the simulation ignores.
Next session writes the code that *sets* `direction`, and if `step` does not
move on it, that code cannot be wrong, which means it cannot be taught. (Being
straight with the room: no test in this project catches that. `ambiguity.md` W4
is exactly this, and it is owned by nothing. Teach it anyway.)

Then the landing test, and make sure they hear which floor is compared. It is
the **new** floor against `car.target`, not `car.floor`. Comparing `car.floor`
means the doors open on the floor the car is leaving, one tick early, and the
car never reaches 6.

Two small things worth ten seconds each, because they show up as red squiggles:

- Inside the branch, use `car`, not `state.car`. The line `const car =
  state.car` above the `TODO` is what narrows the union to the `moving` member,
  and it ships written for exactly that reason. `state.car.direction` will not
  compile.
- The `doors` shape takes **only** `mode` and `floor`. Adding `direction` to it
  is a type error, and that is the union doing its job.

**Reference solution** - your copy, from `app/lib/step.ts`. Build it on screen;
do not project it before they have tried:

```ts
    const floor = car.direction === 'up' ? car.floor + 1 : car.floor - 1
    next = {
      ...next,
      car:
        floor === car.target
          ? { mode: 'doors', floor: car.target }
          : { mode: 'moving', floor, direction: car.direction, target: car.target },
    }
```

**Passes when:** c-1-3 and c-1-4 both go green, and this cut alone turns them.
c-1-3 is `above` after four presses - floor 6, mode `doors`. c-1-4 is `passing`
after two presses - floor 3, mode `moving`, which is the fixture that fails a
block that opens its doors at every called floor. c-1-5 needs the second cut too.

### cut-step-doors - `lib/step.ts:30`

**What students see** (the skeleton, exactly):

```ts
  } else if (state.car.mode === 'doors') {
    const car = state.car
    // TODO(cut-step-doors): The doors are open at `car.floor`, so put into `next` the state one tick on: each call in `state.pending` for that floor with a `tick` at or below `state.tick` joins `served` as `{ floor, calledAt: the call's own tick, servedAt: state.tick }` and leaves `pending`, and the car becomes `{ mode: 'idle', floor: car.floor }`.
  }
```

**What they write.** Two filters over `state.pending` on the same condition -
`call.floor === car.floor && call.tick <= state.tick` - one keeping the matches
and one keeping everything else. The matches become `served` entries appended to
`state.served`, each `{ floor, calledAt: the call's own tick, servedAt:
state.tick }`. The car becomes `{ mode: 'idle', floor: car.floor }`. Ten lines.

**Teach it like this.** "The tick is spent standing still with the doors open.
Everybody who is waiting on this floor, and who has actually pressed the button
by now, gets on. Then the doors close and the car has nowhere to be."

Three points, in this order:

1. **`<=`, not `===`.** A call registered at tick 0 is still waiting at tick 4.
   `===` serves only the callers who pressed the button on the exact tick the
   doors opened, which on `above` is nobody, and c-1-5 goes red with an empty
   served list.
2. **Three different ticks, and they are all in play.** `calledAt` is the tick
   on the call - when they pressed. `servedAt` is `state.tick` - when the doors
   were open. And the page is about to show tick `state.tick + 1`, because
   `next` already advanced it. On `above` those are 0, 4 and 5. c-1-5 pins
   `served-6` at **4**, so it separates all three: 0 is the swap, 5 is
   `next.tick`.
3. **A call that boards must leave `pending`.** Today you cannot see the
   difference - the car goes idle and this branch never runs again - but next
   session folds this function in a loop, and a caller who is served without
   being removed is served for ever and the run never ends. Say that now; you
   will be glad you did in session 2.

**Reference solution** - your copy, from `app/lib/step.ts`:

```ts
    const arriving = state.pending.filter((call) => call.floor === car.floor && call.tick <= state.tick)
    next = {
      ...next,
      car: { mode: 'idle', floor: car.floor },
      pending: state.pending.filter((call) => !(call.floor === car.floor && call.tick <= state.tick)),
      served: [
        ...state.served,
        ...arriving.map((call) => ({ floor: call.floor, calledAt: call.tick, servedAt: state.tick })),
      ],
    }
```

**Passes when:** c-1-5 goes green - `above` after five presses, `served-6`
reading `4`, `served-count` reading `1`, `car-mode` reading `idle`. It is the
only criterion in the session that needs this cut, and it needs `cut-step-move`
as well.

### The one route not to open today

`/scenarios/overtake` works, renders, and does the wrong thing on this page.
`manualStart` aims at `calls[0].floor`, and `overtake`'s first call is floor 5
**registered for tick 2**. So: one press lands the car on floor 5 at tick 1, the
doors open, the doors branch looks for live calls and finds none - the floor-5
caller has not pressed the button yet - `served-count` stays `0`, and the car
goes idle for ever with the call still pending.

That is correct code doing something that teaches the opposite of the lesson. It
is `ambiguity.md` W1, filed against this pack, and the reason session 1 walks
`above`, `passing` and `quiet` only. If a student finds it, the answer is the
honest one and it is a good answer: "the doors opened because `manualStart`
pointed the car at a call that has not been made yet. Nothing on this page
re-checks the destination. Next session that re-check is the first thing we
write."

## Where students get stuck

- **"The tick goes up and the car never moves."** - Nothing is written yet.
  This is the correct starting state, before and *between* the two cuts, and it
  is worth saying out loud before you reload anything - otherwise half the room
  will start undoing work that was right.
- **"The doors open on floor 5 instead of 6."** - The landing test compares
  `car.floor === car.target` instead of the new floor. They are asking "was I
  there?" rather than "am I there now?" - "You moved the car into a local
  variable. Compare that, not the floor you came from."
- **"The car gets to 6 and the mode still says `moving`."** - The `moving`
  shape is being written on both paths, or the ternary's branches are the wrong
  way round. Have them read the two shapes out loud.
- **"`car-mode` says `doors` after two presses on `passing`."** - The block
  opens the doors whenever the car is on a floor somebody called from, instead
  of on `car.target`. c-1-4 exists for exactly this. - "Who told the car it may
  stop here? Only `target` may stop it, and `target` is 5."
- **"The car goes down instead of up" / "floor 0, floor -1".** - `'up'` was
  wired to `car.floor - 1`. Watch for it on `passing`, which starts on floor 1
  and immediately underflows.
- **"TypeScript: Property 'direction' does not exist on type 'Car'."** - They
  wrote `state.car.direction`. Inside the branch, the narrowed local is `car`.
  Do not let anyone delete or move the `const car = state.car` line; it is
  above the `TODO` on purpose.
- **"TypeScript: Object literal may only specify known properties, and
  'direction' does not exist in type '{ mode: "doors"; floor: number; }'."** -
  They added `direction` to the doors shape. That is the union refusing an
  impossible car, and it is the best error message in the session. Read it out.
- **"`served-6` says 5."** - `servedAt` was taken from `next.tick`, which has
  already advanced. It is `state.tick` - the tick the doors were open on.
- **"`served-6` says 0."** - `calledAt` and `servedAt` are swapped. The page
  prints `servedAt`, and the call's own tick is `calledAt`.
- **"`served-count` says 0 and there is no served line at all."** - Either the
  filter used `===` on the tick instead of `<=`, or `served` was replaced with
  just the new entries and the spread of `state.served` was left out - on `above`
  those look the same, because there is only one call. Check the filter first.
- **"Nothing changed when I saved."** - Look at the terminal running
  `npm run dev`, not the browser. A TypeScript error stops the rebuild and the
  last good page keeps being served. The browser is telling you the truth about
  two minutes ago.
- **"It works but I hardcoded the served entry."** - It really does pass c-1-5;
  all three numbers are printed in the criterion. Say it straight: "that answers
  this one page. Next session runs this same function nine times on a scenario
  you have not seen, and there is no number to copy."

## Check before moving on

On `/scenarios/above`, five presses give: `car-floor` **6**, `car-mode`
**idle**, `served-count` **1**, and the served line reading *floor 6 served at
tick* **4**. On `/scenarios/passing`, two presses leave the car **moving** at
floor **3**.

If a student is still on a car that does not move, session 2 will not start for
them. Every session-2 criterion except c-2-5 folds their own `step`, so
`cut-step-move` and `cut-step-doors` have to be right before the fold can be.
`mutation.json` records this directly: removing either session-1 cut turns
c-2-1, c-2-2 and c-2-3 red as collateral.

## Timing - the overrun and what to trim

The plan above is **47 minutes**. `lint.json` says 39.3. The seven extra minutes
are mostly in one place: `cut-step-move`'s hint states three outcomes, a
preservation rule and a prohibition, and that is twelve live minutes, not the
8.3 the estimator charges. This session also carries the whole project setup and
the only new type in the project.

`ambiguity.md` W12 predicted this before any code existed, and named the
structural reason: the 45% largest-cut check does not fire on a two-cut session,
because two cuts always split at least 50/50, so `cut-step-move` at 58% of the
session's cut minutes raised no warning.

Trim in this order and stop as soon as you are inside the cap.

1. **`npm ci` and the first `npm run dev` are pre-work, not session work.**
   Saves 2-4 if you were going to do them live. The plan above already assumes
   this; doing it live adds those minutes back on top of the 47.
2. **Hand `cut-step-doors` over already written.** This is `spec.md`'s own drop
   candidate, it is a real block a student types, and it is the only trim here
   that gets the session inside 40. **Saves 11, bringing the plan to 36.** It
   costs c-1-5, the only session-1 criterion that grades it. Two things make
   that a fair trade: the doors transition is still *taught* - you read it out
   in two minutes as handed code - and session 2's folds still exercise it four
   times over. What you lose is a student writing it with their own hands.
3. **Put `lib/types.ts` and `manualStart` on one slide, already written, and
   read them in two minutes instead of five.** Saves 3. Do this before trim 2 if
   you would rather keep both cuts and land at 44 - over the cap, but with
   nothing dropped.
4. **Move the `/scenarios/passing` detour into the catch-up window.** Students
   read it off their own screens while you circulate, instead of you driving it.
   Saves 2.

Trims 3 and 4 together give 42. Only trim 2 gets you to 40 or under. If you take
trim 2, take it *before* the session and hand the file out written - discovering
at minute 38 that there is no time left is worse than a session with one cut in
it.
