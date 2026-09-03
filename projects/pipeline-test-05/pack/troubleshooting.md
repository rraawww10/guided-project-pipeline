# Troubleshooting

Every entry has a cause and a sentence you can say. Ordered by when in the two
sessions you will hit it.

## Getting it running

**`npm ci` fails with `EUSAGE` or complains about the lock file.** Use
`npm install` in that tree instead. `skeleton/` and `app/` each have their own
`package-lock.json` and their own `node_modules`; installing in one does nothing
for the other.

**`Cannot find module 'next'`.** No `node_modules` in *this* tree. Install here,
not one level up.

**`Module not found: Can't resolve '@/lib/step'`.** `@/*` is mapped to the
project root in `tsconfig.json`, so it only resolves when the dev server was
started from the directory holding `package.json`. Somebody ran `npm run dev` a
level up, or opened the editor on the repository root and the language server
guessed. Restart the server from `skeleton/`.

**`Error: listen EADDRINUSE :::3000`.** Something is already on 3000, very often
a `next` server left behind by a run that was closed with the window rather than
with Ctrl-C. On Windows, `npm run start` spawns `next` as a child, so killing the
npm window can leave the child holding the port. Kill it properly, or
`npm run dev -- -p 3001` and tell the room the new port.

**`http://localhost:3000/` is a 404.** Correct. There is no index route in this
project. Every URL is `/scenarios/<id>` or an `/api/` path. Say so before
somebody debugs it.

**The page never changes, whatever is saved.** Look at the terminal running
`npm run dev`, not at the browser. A TypeScript error stops the rebuild and the
last good bundle keeps being served, so the browser is telling you the truth
about two minutes ago.

**An edit to `lib/` does nothing.** You are on `npm run start` against a build
made before the edit. Use `npm run dev`; the page and both routes are
`force-dynamic` and re-read on every request.

**`npm install` prints a security advisory.** Read it and carry on for the
session - it does not stop the build. Worth noting because a green deploy check
has hidden a CVE line in this pipeline before. On this project's `deploy.json`
the advisory list is empty for `next@15.5.24`.

## Running the graded suite

**Always let the pipeline boot the app.** It installs, builds, starts the server
on a free port, exports `BASE_URL`, runs pytest with Playwright and writes the
report:

```text
python3 -m pipeline test pipeline-test-05 --target skeleton
python3 -m pipeline test pipeline-test-05 --target app
```

**`RuntimeError: BASE_URL is not set`.** Somebody ran `pytest` inside `verify/`
by hand. The suite never starts a server; the message says what to do:

```text
        raise RuntimeError(
            "BASE_URL is not set. This suite never starts a server: point it at "
            "an app that is already running, e.g. BASE_URL=http://127.0.0.1:3000"
        )
```

**Every criterion reports `missing`.** The app never booted, so no test ran.
Read `.pipeline/server-<target>.log` in the project directory - it holds the
`npm run build` output, and a build that failed is the usual answer.

**A student's own `pytest` run needs Playwright browsers.** The pipeline's venv
has them. A hand-rolled venv will need `playwright install chromium`. It is not
worth doing in class - the page is the faster feedback loop in session 1, and the
console `fetch` is the faster one in session 2.

**Playwright reports a timeout on the first click.** The shaft page is a client
component, so the first press can race hydration. The suite already re-sends
only the first press, and only while the `tick` readout still reads `0`. If it
still times out, the page is not rendering at all - open it in a browser and look
for a server error.

## Session 1 - one tick

**"Press step and the tick goes up but the car never moves."** The correct
starting state of the skeleton, with both `TODO`s empty. It stays correct
*between* the two cuts, too. Say so before you reload anything, or half the room
will undo work that was right.

**The doors open one floor early - floor 5 instead of floor 6.** The landing test
compares `car.floor === car.target`, the floor the car is leaving. Compare the
new floor. "You put the new floor in a variable. Ask *that* whether it has
arrived."

**The car reaches floor 6 and `car-mode` still reads `moving`.** The two shapes
in the ternary are the wrong way round, or the `moving` shape is written on both
branches.

**`car-mode` reads `doors` after two presses on `/scenarios/passing`.** The block
opens the doors at any floor somebody has called from, rather than at
`car.target`. c-1-4 exists for this. "Only `target` may stop this car, and
`target` is 5."

**The car goes down when it should go up, or reaches floor 0.** `'up'` is wired
to `car.floor - 1`. Watch `passing`, which starts on floor 1 and underflows
immediately.

**`Property 'direction' does not exist on type 'Car'`.** They wrote
`state.car.direction`. Inside the branch the narrowed local is `car`, from the
shipped line `const car = state.car` above the `TODO`. Do not let anyone delete
or move that line.

**`Object literal may only specify known properties, and 'direction' does not
exist in type '{ mode: "doors"; floor: number; }'`.** They added `direction` to
the doors shape. That is the discriminated union refusing an impossible car - the
best error message in session 1. Read it out.

**`Property 'target' does not exist on type '{ mode: "doors"; floor: number; }'`
in the doors branch.** They reached for `car.target` while the doors are open.
The doors car does not have one; the floor it is standing on is `car.floor`.

**`served-6` reads `5`.** `servedAt` was taken from `next.tick`, which has
already advanced. It is `state.tick` - the tick the doors were open on. On
`above` the three ticks in play are 0 (`calledAt`), 4 (`servedAt`) and 5 (what
the page now shows).

**`served-6` reads `0`.** `calledAt` and `servedAt` are swapped. The page prints
`servedAt`.

**`served-count` stays `0` and no served line appears.** Either the pending
filter used `call.tick === state.tick` instead of `<=` - so only callers who
pressed the button on this exact tick board, which on `above` is nobody - or
`state.served` was not spread into the new list. Check the filter first.

**`served-count` reads `1` but the line says "served at tick 0".** The same swap,
seen on the page instead of in a test.

**`/scenarios/overtake` opens its doors on an empty landing and then sits idle
for ever.** Not a bug, and not something to fix. `manualStart` aims at
`calls[0].floor`, and `overtake`'s first call is floor 5 registered for **tick
2**, so the car arrives at tick 1 before the caller has pressed the button.
`ambiguity.md` W1. Session 1 walks `above`, `passing` and `quiet` only. If a
student finds it: "the doors opened because the car was pointed at a call that
has not been made yet, and nothing on this page re-checks the destination. Next
session, that re-check is the first thing we write."

**"No scenario with id above" on a page that used to work.** The id was edited in
`data/scenarios.json`, or the file no longer parses as JSON. Check the terminal.

**c-1-5 passes with a hardcoded `served` entry.** It really does - all three
numbers are printed in the criterion (`ambiguity.md` W8). Session 2's folds
separate it on four different floors, and `mutation.json` records that removing
`cut-step-doors` turns c-2-1, c-2-2 and c-2-3 red as collateral. "That answers
this one page. Next session runs the same function nine times on a scenario you
have not seen."

## Session 2 - dispatch and the fold

**`{"rows":[],"served":[],"complete":false}`.** `cut-run-until` is still open.
This is also what you get with both dispatch cuts finished and the fold empty, so
say it before anyone blames their comparator.

**A valid-looking POST answers 400.** The body is an envelope. It is
`{"scenario": { ... }}` and `maxTicks` is a sibling of `scenario`, not a field
inside it. This is the most common hand-testing mistake of the session and it has
nothing to do with the student's code.

**Still 400 with a `scenario` key.** A call names a floor outside 1 to `floors` -
the other half of c-2-5's single predicate. Check the `calls` array against
`floors: 8`. The message is the same either way, on purpose: one predicate, one
message.

**400 for a body that is not valid JSON.** Also correct, also c-2-5, also the
same message. A trailing comma in a pasted `fetch` body will do it.

**`both-sides` serves floor 6 at tick 2 and floor 2 at tick 7 - the right ticks
on the wrong floors.** The distance tie is being broken by the higher floor, or
`ahead` is not sorted at all and the seed's insertion order is deciding. The seed
lists floor 6 first for exactly this reason. "Both callers are two floors away.
Which one does your comparator hand back first?"

**`ahead` sorted by floor number instead of distance.** Right on `both-sides`
going up, wrong the moment the car is above a caller. The key is
`Math.abs(call.floor - state.car.floor)`.

**`overtake`'s tick-2 row reads `down`.** No direction filter - usually
`ahead = live`. The car sees the nearer caller behind it and turns round.
c-2-2 is the criterion. "Read rule 3 off the board: can the car reach floor 5
without turning round?"

**`TypeError: Cannot read properties of undefined (reading 'floor')`** in the
server log. `ahead[0]` on an empty `ahead`, with the fallback missing. Note what
this really tells you: with a correct filter that branch is unreachable on all
five fixtures (`ambiguity.md` W6), so the error is a message about the *filter* -
an inverted `dir` case, or `>=` where `>` was meant.

**The car reaches floor 9, then 10.** `direction` is the constant `'up'`. `step`
moves on that field, so the car climbs out of the building. c-2-2's tick-5 row is
the only place a criterion watches a downward car, and it is there for this.
"Compare the target to the floor you are standing on."

**`rows` has as many entries as `maxTicks` and `complete` is false on a scenario
that should finish.** Two causes, and check them in this order. First, session
1's `cut-step-doors`: a caller who boards without being removed from `pending` is
served for ever, so the run can never complete. Second, the completion exit -
`idle` *and* `pending` empty, tested on the dispatched state.

**The request never comes back and the dev server pins a core.** The `while`
condition does not test `trace.rows.length < maxTicks`. Stop the server. The
bound is not a safety net here, it is part of the specification.

**`maxTicks` 4 returns 5 rows.** The bound is tested after the push instead of in
the `while` condition. c-2-4.

**`quiet` returns 0 rows.** The completion check runs before the row is pushed.
The final row is part of the trace: `quiet` is one `idle` row and `complete`
true. c-2-6.

**`quiet` returns `complete` false.** The exit tested only `idle`, or only
`pending`, or the run ended by exhausting the bound rather than by completing.

**Rows carry `direction: "up"` on `doors` and `idle` rows.** No `null` mapping.
`TraceRow.direction` is `Direction | null` for exactly this, and c-2-6 pins
`null` on `quiet`'s single row.

**`rows` is right and `served` is empty.** `trace.served` was never assigned, or
was read from `seed(scenario)`, whose `served` is always `[]`. The state moves
twice per turn of the loop - once at dispatch, once through `step` - so record it
after both.

**`Type 'string' is not assignable to type 'Direction'`.** The direction was
computed into a separate `let`, which TypeScript widened to `string`. Put the
ternary directly in the object literal, or annotate the local as `Direction`.

**`Property 'direction' does not exist on type 'Car'` inside the fold.** The row
reads the dispatched car's `direction` without narrowing. The check
`car.mode === 'moving'` is what makes the field visible, which is why the row's
`direction` is a conditional and not a plain read.

**The trace is right and one row is missing at the end.** The `break` fires
before the push. Push, then decide whether to stop.

**Everything passes but `step` moves by `Math.sign(car.target - car.floor)`.**
It really does pass all twelve criteria. `spec.md` forbids it and nothing
enforces that - `ambiguity.md` W4, owner `nothing`. Argue it on the merits:
`direction` is the field the simulation runs on, and if `step` recomputes it then
`cut-dispatch-target` cannot be wrong, and code that cannot be wrong cannot be
checked.

## For whoever maintains this project

**Never normalise `data/scenarios.json`.** The order of the objects inside each
`calls` array is load-bearing and no criterion pins it: `overtake` must list its
tick-2 floor-5 call before its tick-0 floor-8 call, and `both-sides` must list
floor 6 before floor 2. Sorting either into registration order leaves all twelve
criteria green and silently stops grading both the direction filter and the tie
rule. This was hand-checked at Gate 2 and it is the one defect in this project
that no script can see.

**Two ungraded display rules.** The shaft's document order and the `tick` readout
past its seeded `0` are asserted by nothing (`ambiguity.md` W10). An upside-down
shaft, and a tick display frozen at 0, both satisfy `spec.json`. The shipped
markup is correct; the suite is not what is holding it there.

**The skeleton's `tsconfig.json` does not set `noUnusedLocals`.** That is what
keeps `ambiguity.md` W7 inert: with the cuts open, `const car`, `const dir` and
`let ahead` have no readers, and under `noUnusedLocals` the student's tree would
stop compiling with TS6133. `skeleton-check.json` records `typecheck.ran` true,
`ok` true, `typecheck_fail_open` false - so the check really ran, which is the
thing to confirm rather than assume. If anyone ever tightens that tsconfig, read
W7 first.
