# Ambiguity report - tip-split

**Verdict:** 3 blocking, 6 worth a look

The money arithmetic checks out: every worked value in `spec.md` and every
`worked_values` entry in `spec.json` recomputes correctly (12400/136400, 6129/93679,
2250/47250, 28005/261380, 2985/22885, 24800/334800; `[45467, 45467, 45466]`,
`[34100 x4]`, `[136400]`). Click counts are right: 4 Fewer clicks reach the lower clamp,
17 More clicks reach the upper one. Counts are under the house caps (4/4/3 cuts,
5/6/6 criteria), every cut is referenced by a criterion, every endpoint and screen is
built by a session, and both declared departures from `idea.md` are argued in the spec.

The three blocking findings are all about grading integrity rather than wording: two
criteria go green while a cut they name is still open, and the route-handler skeleton
rule contradicts the pattern proven in `fixtures/runner-check`.

## Blocking

### B1 - The route-handler fallback puts the only `return` before the cut, not after it

- **Where:** spec.md, Sessions, rule 2; spec.json `notes.skeleton_rules[1]`
- **The line:** "A cut that would otherwise remove its function's only `return` keeps a
  typed fallback return outside the markers, as the last statement of the function:
  ... and `return NextResponse.json({ error: 'not implemented' }, { status: 501 })` in
  each of the two route handlers."
- **Reading one:** the handler follows the house pattern proven in
  `fixtures/runner-check/app/app/api/health/route.ts` - `let body`, `let status = 501`
  declared above the marker, the cut block assigns to both, and one
  `return Response.json(body, { status })` sits below. But then the last statement is
  not the literal the spec names, so this reading contradicts the sentence.
- **Reading two:** the cut block contains its own `return NextResponse.json(bills)` and
  the literal 501 return sits after it as the last statement, exactly as written. The
  finished `app/` then has an unreachable statement in both handlers - `no-unreachable`
  under `next lint`, and dead code in the reference implementation the student
  eventually reads.
- **Why it matters:** this is the one rule `lessons.md` was written for ("Never put a
  typed function's only `return` inside the markers", recipe-box, six cuts, TS2355).
  Reading two re-introduces a `return` inside the markers for the two route handlers -
  the skeleton still typechecks because the fallback follows, but the Builder is now
  writing a shape the fixture does not endorse, and the lint failure lands at build
  time, not at Gate 1. The two handlers are also the only cuts in the spec whose hints
  ("Send every bill ... back to the browser", "Reply with the bill as JSON and status
  200") describe returning rather than assigning, so the hints have to move with the
  rule.
- **Suggested wording:** "In each route handler the fallback is
  `let body: unknown = { error: 'not implemented' }` and `let status = 501` declared
  above the opening marker, with `return NextResponse.json(body, { status })` as the
  last statement of the function; the cut block assigns to `body` and `status`. Restate
  `cut-api-bills-list` as 'Put every bill the store holds into the response body and set
  the status to 200' and `cut-api-bill-get` as 'Put the bill into the response body with
  status 200 when the store finds it, and an object holding an error field with status
  404 when it finds nothing.'"

### B2 - `c-3-4` is green with `cut-bill-people` still open, and the spec says nothing about it

- **Where:** spec.md and spec.json, Session 3, criterion `c-3-4`
- **The line:** "sc-bill renders 4 share-row elements each reading ₹341.00 after the
  Fewer people control is clicked 1 time and the More people control is then clicked 1
  time at the route /bills/anand-bhavan"
- **Reading one:** the criterion grades the clamped setter, because it names
  `cut-bill-people` in its cut list.
- **Reading two:** the criterion grades nothing about the stepper. With
  `cut-bill-people` open, `setPeopleClamped` does nothing, `people` stays on the stored
  4 for both clicks, and the screen renders 4 rows of ₹341.00 the whole time - which is
  exactly what the assertion checks. Every other listed cut filled plus this one open
  is a green `c-3-4`.
- **Why it matters:** `c-3-4` is the round-trip criterion, the one that backs the
  outcome sentence "moving it back to 4 restores the bill exactly as it was saved". Any
  criterion phrased as "return to the starting value" is satisfied by a stepper that
  never moves. The spec's own rule 3 quietly admits it - "a `setPeopleClamped` that does
  nothing leaves `people-count` on the stored value, which fails `c-3-2`, `c-3-5` and
  `c-3-6`" lists neither `c-3-3` (which fails for a different reason) nor `c-3-4` (which
  does not fail) - while the subset paragraph claims "No other criterion in the spec is
  satisfied by a proper subset of its cuts." `cutter.py` will not catch this:
  `expected_skeleton_results` only checks the all-cuts-open skeleton, where `shares` is
  `[]` and `c-3-4` fails for want of rows. At a per-cut checkpoint it reads as proof of
  a cut it does not exercise.
- **Suggested wording:** make the criterion assert the intermediate state in the same
  run: "`c-3-4` sc-bill displays 3 in its people-count element after the Fewer people
  control is clicked 1 time, then displays 4 in its people-count element and renders 4
  share-row elements each reading ₹341.00 after the More people control is then clicked
  1 time, at the route /bills/anand-bhavan."

### B3 - `c-1-2` passes vacuously on the empty array the open `cut-store-read-all` produces

- **Where:** spec.md and spec.json, Session 1, criterion `c-1-2`
- **The line:** "GET /api/bills returns each bill with an id, a place, a date, a
  totalPaise integer, a tipPercent integer and a people integer"
- **Reading one:** the test fetches, asserts the array holds 6 bills, and then checks
  the fields of each.
- **Reading two:** the test loops over whatever the endpoint returned and checks the
  fields of each element - the literal reading of "each bill". With
  `cut-store-read-all` open and `cut-api-bills-list` filled, the endpoint answers 200
  with `[]`, the loop runs zero times, and the criterion is green.
- **Why it matters:** same class as the recipe-box lesson ("Where a criterion has more
  than one cut, check by hand that no proper subset satisfies it") and it breaks the
  same claim as B2. `c-1-1` pins the count and so fails correctly on `[]`, which is why
  rule 3 only mentions `c-1-1`; `c-1-2` is left able to certify a store cut that was
  never written. `cutter.py` misses it because with both cuts open the handler answers
  501.
- **Suggested wording:** "GET /api/bills returns a JSON array of 6 bills, each with an
  id, a place, a date, a totalPaise integer, a tipPercent integer and a people integer."

## Worth a look

### W1 - `cut-list-cards` never names the array it has to assign to

- **Where:** spec.md and spec.json, Session 1, cut `cut-list-cards`
- **The line:** "Turn the bills array into one bill-card element per bill, in the order
  of the array, each one a link to that bill's page holding its place in a card-place
  element..."
- **Why it matters:** rule 1 says this block "assigns its card elements to a
  `ReactNode[]` declared above the marker, and the component's `return` renders that
  variable". `cut-bill-shares` says so in its hint - "assign that array of shares to the
  shares variable declared above" - and `cut-store-read-all`, `cut-store-find-one`,
  `cut-money-tip` and `cut-money-split` all name the value they feed. This one does not,
  so a student can write `const cards = bills.map(...)` inside the block, shadow
  nothing, render nothing, and get a red test with no clue why.
- **Suggested wording:** append "...and assign that array of card elements to the cards
  array declared above."

### W2 - Nothing asserts that a card is a link, so navigation is ungraded

- **Where:** spec.md, Screens, `sc-list` elements; testid table
- **The line:** "Each card is a link to `/bills/<id>` and holds a `card-place`, a
  `card-date`, a `card-total` and a `card-people`."
- **Why it matters:** no criterion reads a card's `href` or clicks a card, so a build
  that renders six non-clickable cards passes all 17 criteria while the app cannot be
  navigated. The back link (`Back to saved bills`) and the `bill-saved-people` element
  are in the same position - `bill-saved-people` gets its own paragraph explaining why
  its text spells itself out, and then no criterion ever reads it. The spec accounts for
  the uncovered `loading` states on purpose but is silent about these.
- **Suggested wording:** either extend `c-1-4` with "whose bill-card element links to
  /bills/anand-bhavan", or add a line to the uncovered-states note saying the card link,
  the back link and `bill-saved-people` carry no criterion and why.

### W3 - The stepper controls and back link are found by accessible name but never given a role

- **Where:** spec.md, Screens: "Controls are found by their accessible name: `Fewer
  people` on the minus control, `More people` on the plus control, and `Back to saved
  bills` on the back link."
- **Why it matters:** the test runner drives a real browser (`pipeline/test_runner.py`
  installs Playwright), so a Verifier will almost certainly write
  `getByRole('button', { name: 'Fewer people' })`. A `<div onClick>` with the text `-`
  and a title attribute satisfies "the minus control" and fails that locator. Nothing
  says the controls are `<button>` elements or where the name comes from (visible text
  vs `aria-label`).
- **Suggested wording:** "The minus and plus controls are `button` elements whose
  accessible names are `Fewer people` and `More people` (an `aria-label` when the
  visible text is a symbol), and the back link is an anchor with the accessible name
  `Back to saved bills`."

### W4 - The exact text of a `share-row` is under-specified by one space

- **Where:** spec.md, Screens, `sc-bill`: "each reading the word `Person`, the person's
  position counting from 1, a space, then `formatRupees` of that share"
- **Why it matters:** one space is named (before the amount) and one is not (between
  `Person` and the position), so "Person1 ₹341.00" is a legal reading of the sentence
  even though `c-3-1` quotes "Person 1 ₹341.00". If the Builder renders the label and
  the amount as sibling elements the browser may produce no space at all between them,
  and whether the assertion is exact-equality or whitespace-normalised is not stated
  anywhere.
- **Suggested wording:** "one `share-row` per entry whose text, with runs of whitespace
  collapsed to one space, is `Person`, a space, the position counting from 1, a space,
  then `formatRupees` of that share: `Person 1 ₹341.00`."

### W5 - Session 2 is the fullest session by some distance

- **Where:** spec.md, Session 2
- **Why it matters:** it sits on both caps that matter (6 criteria, 4 cuts) and its
  `teaches` list carries three concepts that each need teaching from scratch - dynamic
  segments for both a page and a route handler, `useParams` plus status branching in a
  client component, and half-up integer percentage rounding. On top of that the session
  ships the whole `BillView`: the stepper, the `What each person owes` heading and the
  `share-row` rendering, none of which any session-2 criterion reads, and two of which
  are visibly dead on screen at the end of the session. Sessions 1 and 3 are lighter.
- **Suggested wording:** no wording change; a Gate 1 decision about whether the inert
  stepper markup can move into session 3's skeleton instead, so session 2 ends with a
  screen where everything visible does something.

### W6 - How `data/bills.json` is located, and whether it is read at all, is untested

- **Where:** spec.md, Data model: "Both read the file on every call"; Session 1 teaches
  "reading a JSON file on the server with node fs"; cut `cut-store-read-all` - "Read the
  bills JSON file from disk"
- **Why it matters:** no criterion can tell `fs.readFileSync(path.join(process.cwd(),
  'data', 'bills.json'))` from `import bills from '../data/bills.json'`, and the second
  one satisfies every criterion while skipping the lesson the session names. The hint
  also does not say the path resolves against the process working directory, which is
  the first thing a student gets wrong when a relative path works in one command and not
  another.
- **Suggested wording:** "Read the bills JSON file from disk with node `fs`, building
  its path from the process working directory, and put every bill in it into the array
  this function returns, keeping the order the file stores them in."
