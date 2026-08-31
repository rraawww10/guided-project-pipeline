# Ambiguity report - pipeline-test-03

**Spec read:** `spec.md` + `spec.json`, round 2, spec hash
`46b5465b4952bcbca15cafd4bfef8fc2a47f724050efd86de63983af1da48aec` (the hash
`pipeline breaker begin` recorded and the one in `lint.json`).

**Verdict:** 2 blocking, 5 worth a look

Round 1's two blockers are genuinely closed and I checked the join by hand
rather than taking the table's word for it. Every criterion fails when any one
of its declared cuts is emptied alone, no proper subset of a criterion's cuts
satisfies it, no two cuts carry the same criterion set, and every cut is graded
by more than one fixture. The arithmetic checks out: 30 lines, 3 skipped, 21
accepted, 6 rejected; all four account totals, both running-balance columns and
all five `paise` values in `c-1-3` recompute exactly. Both findings below are
about the shape of the code the spec prescribes and about claims it makes for
its own fixtures, not about the data.

## Blocking

### B1 - `notFound()` throws, so the page cannot also render `account-missing`

- **Where:** spec.md, Screens, `sc-account`; spec.json `screens[1].elements[1]`; c-2-4
- **Owner:** test-runner
- **The line:** "The page then calls `notFound()`: the route answers **404** and
  renders one element with `data-testid="account-missing"` and text `Account not
  found`, and renders no `account-title`, no `account-total`, no sidebar and no
  rows."
- **Reading one:** the page calls `notFound()` and a `not-found.tsx` boundary
  (at `app/accounts/[name]/not-found.tsx` or the app root) renders the
  `account-missing` element. Status 404, element present, c-2-4 green.
- **Reading two:** the page itself returns the `account-missing` markup for the
  miss case, because `sc-account` is the screen the element is declared under
  and `states` lists `not-found` as one of its states. Status 200, c-2-4 red on
  the status assertion. A third variant - call `notFound()` and write no
  boundary - gives 404 with Next's built-in page and no `account-missing` at
  all, which is c-2-4 red on the element.
- **Why it matters:** in the App Router `notFound()` throws; the component that
  called it renders nothing further, so the element has to live in a separate
  file the spec never names. This is the first project in the pipeline to ask
  for a real HTTP 404 on a page route - recipe-box, tip-split and
  pipeline-test-01 all render a client-side "not found" panel with a 200, and
  pipeline-test-02's `puzzle-missing` is the same shape - so there is no house
  pattern for the Builder to copy. The file that renders it is also outside
  every cut, so whichever way it is built it ships into the skeleton unchanged.
  The cost is bounded: c-2-4 pins the status *and* the element, so a wrong guess
  is a red test at step 6 that the Builder/test-runner loop fixes.
- **Suggested wording:** in `sc-account`, "the page calls `notFound()`; the 404
  body is rendered by `app/accounts/[name]/not-found.tsx`, which renders one
  element with `data-testid="account-missing"` and text `Account not found` and
  nothing else."

### B2 - the `parseLine` fallback makes `reason === null` a dead comparison once the cut is removed

- **Where:** spec.md, "What ships written, and what the student writes", the
  `parseLine` block; `cut-parse-line`
- **Owner:** typecheck
- **The line:** "`let reason: string | null = BAD_FIELDS(fields.length)`" followed,
  below the closing marker, by
  "`if (reason === null && amount === null) reason = BAD_AMOUNT`"
- **Reading one:** the shape is fine, because in `app/` the cut body assigns
  `reason = null` on the accepted path, so at the guard `reason` still has its
  declared type `string | null` and the comparison is live.
- **Reading two:** in the *skeleton* the cut body is gone, so nothing assigns to
  `reason` between the initialiser and the guard. TypeScript's flow analysis
  narrows it to `string`, and `string === null` is the TS2367 shape ("this
  comparison appears to be unintentional because the types have no overlap").
  If tsc reports it, the generated skeleton does not compile and the student's
  whole app stops building - the TS2355 failure mode from `learning/lessons.md`
  arriving through a comparison instead of a return.
- **Why it matters:** the defect exists only in the artifact no one writes by
  hand, which is exactly where the previous instances of this class hid. It is
  owned: step 8 runs tsc over the generated skeleton and this is what that check
  is for. Note the check is the demoted second line - if `node_modules` is
  missing it records `fail_open` rather than failing - so read the flag, not
  just `ok`. The static return-safety scan will not see this one; both `return`s
  are outside the markers, which is correct.
- **Suggested wording:** keep the fallback and write the two shipped guards
  without a null comparison - "`if (!reason && amount === null) reason =
  BAD_AMOUNT`" and "`if (reason) return { ok: false, diagnostic: { lineNo,
  reason } }`" - or declare the fallback as
  "`let reason: string | null = BAD_FIELDS(fields.length) as string | null`".

## Worth a look

### W1 - `new Date("2026-02-30")` is not invalid, so line 20 discriminates nothing

- **Where:** spec.md, Outcome, and "A constraint, and what checks it"
- **Owner:** pack-writer
- **The line:** "`2026-02-30` is accepted here and `2026-13-02` is rejected,
  which is exactly the pair that `new Date(...)` gets wrong" / "`new Date(...)`
  calls both of those invalid, so it fails `c-1-1`."
- **Reading one:** as written - a `Date`-based parser rejects line 20, so
  `c-1-1` fails it and line 20 is the fixture that enforces shape-not-`Date`.
- **Reading two:** what V8 actually does - `2026-02-30` conforms to the ISO
  date-time format (the day field is only checked for 01-31), so
  `new Date("2026-02-30")` is a *valid* Date that rolls over to 2 March 2026. A
  `!isNaN(new Date(f))` check therefore **accepts** line 20, which is what
  `c-1-1` wants, and rejects `2026-13-02`, which is what `c-1-2` wants. Neither
  of the two named lines fails a `Date`-based implementation.
- **Why it matters:** the conclusion still holds, but through a different line.
  Line 9, `2026-1-06`, is the one that saves it: the ISO parser rejects the
  one-digit month, V8's legacy fallback parses it happily as 6 January, so a
  `Date`-based parser accepts line 9 and goes red on both `c-1-1` (22 entries,
  wrong `lineNo` list) and `c-1-2` (no diagnostic at 9). So the guarantee rests
  on a single fixture, not on the pair the spec names, and anyone later trimming
  the seed file would read lines 9 and 20 as interchangeable. The false half
  also lands in the session guide, where the teaching point is stated as
  "`Date` calls `2026-02-30` invalid" - a person reads that at Gate 3.
- **Suggested wording:** "Line 9 (`2026-1-06`) is the fixture that fails a
  `Date`-based parser: `new Date` parses it as 6 January. Line 20
  (`2026-02-30`) is the fixture for silent rollover - `new Date` does not reject
  it, it turns it into 2 March - and this parser stores the string it was given."

### W2 - "a float multiply fails on line 8" is only true for a truncating one

- **Where:** spec.md, "Amount to paise"; c-1-3
- **Owner:** nothing
- **The line:** "`250.05 * 100` in floating point is `25004.999...`, which is why
  `c-1-3` pins line 8 at `-25005`" and c-1-3's "a float multiply fails on line 8"
- **Reading one:** any implementation that goes through a float fails `c-1-3`,
  so "never through a float" is graded.
- **Reading two:** only a *truncating* float implementation fails.
  `Math.round(parseFloat(text) * 100)` returns exactly -25005, -245075, -110550,
  -12050 and 1200000 for the five values `c-1-3` pins, so it is green on every
  criterion in the spec. The shape rule does bite a naive float path -
  `parseFloat("1,200.00")` is 1 and `parseFloat("-350.5")` is -350.5, so lines
  28 and 25 would be accepted and `c-1-1`/`c-1-2` would go red - but a regex
  guard plus `Math.round` passes everything.
- **Why it matters:** "rupee text to integer paise without a float" is one of
  session 1's three teaching points and the headline of `cut-amount-paise`, and
  no criterion, and no `code_checks` entry, can tell the two apart. The registry
  is fixed (`utc-dates` only), so no named static check owns it either. The cut
  is not ungraded - the null/reject shape, the sign and the exact-two-digit rule
  all bite - but this particular rule ships on trust.
- **Suggested wording:** either drop the claim ("`c-1-3` pins five values,
  four with non-zero paise digits, so a hardcoded constant cannot pass; a
  truncating float multiply also fails on line 8, a rounding one does not") or
  add a fixture a rounding float still gets wrong.

### W3 - c-2-4's dependency on `cut-account-totals` rests on an unobservable choice

- **Where:** spec.md, Screens, `sc-account`, the `account-total` bullet; c-2-4
- **Owner:** nothing
- **The line:** "`data-testid="account-total"` - `formatPaise` of the `paise` on
  the `accountTotals(entries)` object whose `account` equals the route name.
  This is the contract, and it is the round-1 blocker A2 fix"
- **Reading one:** `account-total` is read off `accountTotals`, as pinned. With
  `cut-account-totals` empty the cell renders `-`, `c-2-4` goes red on
  `/accounts/salary`, and the declared dependency is real.
- **Reading two:** a Builder sums `accountRows(entries, name)` instead, or takes
  the last `runningBalance` value. On a finished build every criterion is
  identical - the account total *is* the sum of that account's rows - so nothing
  in the pipeline can see the difference, and `c-2-4` would then be green with
  `cut-account-totals` still empty.
- **Why it matters:** step 8's skeleton check only exercises the fully-open
  skeleton, where `cut-account-rows` is empty too and `/accounts/salary` 404s
  either way, so the partial state that would expose the wrong source is never
  run (the known blind spot in `learning/lessons.md`). A1's independence argument
  is enforced by code placement, which is checkable; A2's is enforced by a
  sentence. Worth closing cheaply because the sidebar is unambiguous.
- **Suggested wording:** add to c-2-4 "and renders `account-list-total-salary`
  with text `62000.00`" - the sidebar total can only come from `accountTotals`,
  so the declared dependency becomes something a test can see.

### W4 - five specified elements that no criterion reads, and two whose text is never stated

- **Where:** spec.md, Screens, both screens; spec.json `screens[*].elements`
- **Owner:** nothing
- **The line:** "each holding `txn-date-<lineNo>`, `txn-desc-<lineNo>`,
  `txn-amount-<lineNo>` (`formatPaise` of that entry's `paise`) and
  `txn-running-<lineNo>`"
- **Reading one:** the account page carries a money column per row, as the
  screen says, and it is worth building correctly.
- **Reading two:** `txn-amount-<lineNo>` can hold anything at all. No criterion
  reads it, and the same is true of `entry-date-<lineNo>` on `/` and of the
  `account-row-<name>` wrapper (c-2-5 counts `account-link-<name>`, not the
  wrapper). Separately, `txn-date-<lineNo>` and `txn-desc-<lineNo>` are declared
  to exist but their *contents* are never stated, while the matching cells on
  `/` are - "`entry-date-<lineNo>` carries the entry date string unchanged,
  `entry-account-<lineNo>` the account, `entry-desc-<lineNo>` the description".
- **Why it matters:** this is the class that recurs most often in the corpus - a
  rule the spec states that no criterion grades. It costs nothing at grading
  time, because the page markup is not inside any cut and so is shipped to the
  student rather than written by them; the whole exposure is that `app/` can
  drift from its own screen contract with everything green. One assertion on
  `txn-amount-5` (`-18000.00`) inside c-2-3 would close the substantive half.
- **Suggested wording:** add "and `txn-amount-5` with text `-18000.00`" to
  c-2-3, and one sentence: "`txn-date-<lineNo>` carries that entry's date string
  unchanged and `txn-desc-<lineNo>` its description."

### W5 - the named drop candidates are about a minute each, against a 13-minute error bar

- **Where:** spec.md, Session 1 and Session 2, the estimate paragraphs
- **Owner:** pack-writer
- **The line:** "**Estimated at 38.5 minutes against the 40 cap, and that
  estimate has been wrong by up to 13 minutes on flow-2 sessions.** If this
  session runs long, the drop candidate inside it is the `entry-desc-<lineNo>`
  column together with the styling of the complaints panel"
- **Reading one:** the session has a declared relief valve, so an overrun is
  handled.
- **Reading two:** the valve is one table column. `lint.json` charges every one
  of the five cuts a flat 6.0 minutes (no hint exceeds the 55-word nominal, so
  `W114` is silent and `largest_cut_share` is 0.50 and 0.33), and that flat
  model was 12.5 and 13 minutes low on the only two measured flow-2 sessions.
  Dropping `<td>{entry.description}</td>` recovers perhaps a minute. Session 1
  also carries the entire scaffold plus three new concepts, and session 2 is
  three cuts with no setup, yet both land on the same 38.5.
- **Why it matters:** by the time the Pack Writer times this at step 9 the spec,
  the code, the tests and the skeleton exist and the only real fix invalidates
  the build - the pack can then only disclose the overrun, which is what
  pipeline-test-02 did. Worth deciding now which whole *criterion* comes out if
  session 1 runs long, rather than which column. Secondary: the drop advice sits
  oddly against the screens contract, which requires `entry-desc-<lineNo>` on
  every row - "dropping the column from the live build" reads as licence to omit
  it from `app/` unless the sentence says it is about live teaching time only.
- **Suggested wording:** name the criterion to drop, not the column - e.g. "if
  session 1 runs long, `c-1-4` is demoted to `entry-count` and `reject-count`
  and the row table is finished in session 2's first five minutes" - and mark
  the column advice as applying to the live walkthrough, not to `app/`.
