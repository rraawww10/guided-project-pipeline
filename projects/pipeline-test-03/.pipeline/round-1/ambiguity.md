# Ambiguity report - pipeline-test-03

**Spec hash read:** `06f8d5c7c353eda66ca4bc825cc307e119a05fa3745c2e971a8eb6928e00816a`
(`.pipeline/breaker-begin.json`)

**Verdict:** 2 blocking, 7 worth a look

The arithmetic in this spec holds. I recomputed every paise value, every account
total, both running-balance tables, the 21/6 split and the six reason strings
against the 30 seed lines, and found no disagreement. Both blocking findings are
about the cut-to-criterion join, not about the data.

## Blocking

### A1 - `cut-amount-paise` can be left empty with every criterion green
- **Where:** spec.md, "Which criterion fails if only one cut is left empty";
  spec.json, session 1 cuts and c-1-3
- **Owner:** nothing
- **The line:** "No two cuts carry the same set of criteria, so no cut can be
  left empty with its work done inside another one."
- **Reading one:** `parseLine` calls `amountToPaise(fields[3])`, exactly as
  `cut-parse-line`'s hint says, so the two cuts are separable and c-1-3 grades
  the integer-paise conversion.
- **Reading two:** `cut-parse-line`'s markers span the whole body between
  `let paise = 0` and the two `return` statements, and nothing outside those
  markers calls `amountToPaise`. A student can validate the amount and compute
  the integer paise inline inside `cut-parse-line`, never call `amountToPaise`,
  and leave `cut-amount-paise` at its shipped `let paise: number | null = null`
  TODO. Every criterion in the project is graded through `GET /api/ledger`,
  `GET /api/accounts` or the DOM - none of them calls `amountToPaise` - so all
  nine go green with session 1's headline cut untouched.
- **Why it matters:** this is the recipe-box round-3 B1 shape, and no downstream
  checker sees it. `spec-linter` E110 only fires when two cuts have *exactly*
  equal criteria sets; here the declared sets differ (`cut-parse-line` carries
  nine criteria, `cut-amount-paise` six), so E110 stays quiet. `cutter.verify`
  states its own blind spot in `skeleton-check.json` - it proves only that a
  criterion fails with *all* its cuts open and passes with none, so a proper
  subset satisfying the criteria is invisible to it. And `partial_state_risks`
  is computed from the same equal-signature grouping E110 uses, so it will not
  list this pair either. It ships as a cut that grades nothing.
- **Suggested wording:** either pre-write the call above the marker, so the
  student cannot route around it - `const amount = fields.length === 4 ?
  amountToPaise(fields[3]) : null` sits between `let paise = 0` and
  `// >>> CUT cut-parse-line`, and the hint then reads `amount` instead of
  calling the function - or add a criterion that grades `amountToPaise` on its
  own through a surface the tests can reach.

### A2 - `account-total` comes from `accountTotals`, but c-2-3 and c-2-4 do not declare `cut-account-totals`
- **Where:** spec.md, Screens, `sc-account`; spec.json, c-2-3 and c-2-4 `cuts`;
  spec.md, "Which criterion fails if only one cut is left empty"
- **Owner:** nothing
- **The line:** "`data-testid=\"account-total\"` - `formatPaise` of that
  account's total from `accountTotals`" against
  `"id": "c-2-3", ... "cuts": ["cut-parse-line", "cut-amount-paise",
  "cut-account-rows", "cut-running-balance"]`
- **Reading one:** the page really does call `accountTotals(entries)` and pick
  the route account out of it. Then c-2-3 cannot pass while `cut-account-totals`
  is empty - the array is empty, the lookup gives `undefined`, and
  `account-total` renders wrong or the page throws. If it throws, c-2-4's
  "`/accounts/salary` responds 200 and renders `account-title` with text
  `salary`" fails too, and c-2-4 declares only `cut-parse-line` and
  `cut-account-rows`.
- **Reading two:** `account-total` is the last value `runningBalance` produced -
  the spec itself says "the last equals the account total from `accountTotals`"
  - or a sum over `accountRows`. Then the declared cut lists are correct and
  `cut-account-totals` really is graded only by c-2-1, c-2-2 and c-2-5.
- **Why it matters:** the two implementations are indistinguishable on the full
  `app/` build, so `test-runner` is green either way, and `skeleton-check` only
  ever sees the fully-open skeleton, where every criterion fails as expected. The
  difference only shows up on a student's partial tree, which nothing in the
  pipeline runs. A student who has filled `cut-account-rows` and
  `cut-running-balance` sees c-2-3 (and possibly c-2-4) red with every cut those
  criteria name already written, and the spec's own "fails alone" table tells
  them the wrong place to look.
- **Suggested wording:** name the source in one sentence - "`account-total` is
  `formatPaise` of the `paise` on the `accountTotals` object whose `account` is
  the route name; when no such object exists the page has already answered 404" -
  and add `cut-account-totals` to c-2-3's and c-2-4's `cuts`, which keeps every
  cut signature distinct (`cut-account-totals` becomes c-2-1, c-2-2, c-2-3,
  c-2-4, c-2-5).

## Worth a look

### W1 - the `loading` state and `ledger-loading` are graded by no criterion
- **Where:** spec.json, `sc-ledger` `states` and first element; spec.md, Screens
- **Owner:** nothing
- **The line:** "one element with `data-testid` `ledger-loading` and text
  `Loading`, drawn until the `GET /api/ledger` response arrives and never after
  it"
- **Reading one:** the element is required, so the student must render it.
- **Reading two:** no criterion in either session mentions `ledger-loading`, and
  out-of-scope says the failed-fetch branch is not graded, so a skeleton that
  renders nothing while the fetch is outstanding passes all four session-1
  criteria.
- **Why it matters:** this is the recurring class the lessons file counts six
  times, "a rule the spec states that no criterion grades". It does not break the
  build; it means one of the two declared states is decoration.
- **Suggested wording:** either grade it (c-1-4 could assert `ledger-loading` is
  absent once `entry-count` reads `21`, which is cheap and deterministic under
  Playwright) or drop the element and the `loading` state and say the page
  renders nothing until the response arrives.

### W2 - the `href` on `account-link-<name>` is the app's only navigation and nothing grades it
- **Where:** spec.json, `sc-account` elements; spec.md, Screens and Session 2
  "Runs at the end"; c-2-5
- **Owner:** nothing
- **The line:** "an anchor with `data-testid` `account-link-<name>`, text
  `<name>` and `href` `/accounts/<name>` ... This is the navigation: clicking a
  name loads that account's page"
- **Reading one:** the anchor must carry the href, because it is how the whole
  app is navigated - `/` deliberately carries no links.
- **Reading two:** c-2-5 counts four `account-link-<name>` elements and reads
  their names in document order, and nothing anywhere reads an `href` or follows
  a click, so four `<span>`s with the right testids pass.
- **Why it matters:** session 2's "Runs at the end" demo is "click an account,
  watch the balance walk down the page", and a student can be fully green with
  no working click. Small fix now, unfixable after the spec freezes.
- **Suggested wording:** extend c-2-5 with "and `account-link-food` has `href`
  `/accounts/food`", or with a click that lands on `/accounts/food` and renders
  `account-title` with text `food`.

### W3 - "exactly 3 elements with `data-testid` `account-entry-<lineNo>`" has two counts
- **Where:** spec.json, c-2-3; spec.md, Session 2 acceptance criteria
- **Owner:** test-runner
- **The line:** "exactly 3 elements with `data-testid`
  `account-entry-<lineNo>` whose `lineNo` values in document order are 5, 11 and
  20"
- **Reading one:** exact match on `^account-entry-\d+$` - three row wrappers.
- **Reading two:** a prefix locator, which is what the shipped suites use
  (`page.locator('[data-testid^="cell-"]')` in pipeline-test-02's helpers).
  `account-entry-` is a prefix of `account-entry-date-5`,
  `account-entry-desc-5`, `account-entry-amount-5` and
  `account-entry-running-5`, so the same criterion counts 15.
- **Why it matters:** the Verifier picks one and the count is pinned wrong; it
  surfaces as a red c-2-3 at step 6. Note that `entry-row-<lineNo>` on `/` does
  not have this problem - `entry-row-` is not a prefix of any child testid -
  which is why only the account page needs the fix.
- **Suggested wording:** rename the row wrapper to `account-row-entry-<lineNo>`,
  or say in the criterion that the three are matched exactly and not by prefix.

### W4 - the exact bytes of `data/ledger.txt` are not pinned
- **Where:** spec.md, "The seed file"
- **Owner:** test-runner
- **The line:** "Six lines are broken on purpose; they are marked here and the
  markers are not part of the file."
- **Reading one:** only the `<- broken: ...` markers are excluded; the
  two-column line-number gutter (` 1 `, `10 `, ...) that begins every line of the
  block is also presentation, and the file starts at `# ledger - rupees`.
- **Reading two:** the sentence excludes the markers and says nothing about the
  gutter, so a literal transcription writes ` 4  2026-01-01 | salary | ...` and
  every line then has a leading `4` glued to nothing - or, worse, line 3 gets
  written as `3` rather than blank, which is no longer skipped.
- **Why it matters:** a shifted or non-blank line 3 renumbers everything and
  every one of the nine criteria goes red at once, which the Builder/test-runner
  loop resolves - but only after a full red round.
- **Suggested wording:** "the leading two-column line numbers and the
  `<- broken:` markers are presentation only; the file's first byte is `#` and
  line 3 is empty."

### W5 - the idea makes `parseLedger` a student task; the spec ships it written
- **Where:** idea.md, "What the student types"; spec.md, "What ships written,
  and what the student writes"
- **Owner:** spec-linter
- **The line:** idea.md - "`parseLedger` - the fold that partitions 30 lines into
  two arrays while keeping the original line numbers attached to the failures."
- **Reading one:** the spec dropped one of the three things the idea promised the
  student would type.
- **Reading two:** the spec states the reason - the setup session must carry
  strictly fewer cuts than session 2, and the partition loop is the candidate
  with the least new idea in it.
- **Why it matters:** the drift is real but the spec is right and says so:
  making `parseLedger` a third session-1 cut gives session 1 three cuts against
  session 2's three, which is `spec-linter` E113 and a hard error. Recording it
  so the Gate 1 reader sees the trade rather than the omission.
- **Suggested wording:** none needed; leave as written unless the reader wants
  the idea amended to match.

### W6 - c-1-2, c-2-2 and c-2-4 omit `cut-amount-paise` although none can pass while it is empty
- **Where:** spec.json, c-1-2, c-2-2 and c-2-4 `cuts`; spec.md, "Which criterion
  fails if only one cut is left empty"
- **Owner:** nothing
- **The line:** "`cut-amount-paise` ... fails alone on c-1-3 - `null` for every
  amount, so every line is rejected with `BAD_AMOUNT`"
- **Reading one:** the `cuts` list names the cuts a criterion is *about*, so
  c-1-2 is "about" the reason strings and lists only `cut-parse-line`.
- **Reading two:** the `cuts` list names every cut a criterion cannot pass
  without, which is how `cutter.expected_skeleton_results` and the student-facing
  table read it. By the spec's own sentence above, an empty `cut-amount-paise`
  rejects all 27 data lines, so c-1-2's six-diagnostic list, c-2-2's rent total
  and c-2-4's 200 on `/accounts/salary` all fail.
- **Why it matters:** same class as A2 and the same reason nothing catches it -
  the full build is green and the fully-open skeleton fails everything. It
  matters less than A2 because `cut-amount-paise` sits in session 1, so a student
  reaching session 2 has already filled it.
- **Suggested wording:** pick one meaning for `cuts` and apply it everywhere;
  if it is "cannot pass without", add `cut-amount-paise` to c-1-2, c-2-2 and
  c-2-4 and re-check E110 (the signatures stay distinct).

### W7 - both sessions estimate 38.5 minutes against a 40 cap, with no headroom
- **Where:** spec.md, Sessions 1 and 2; spec.json, `sessions`
- **Owner:** pack-writer
- **The line:** "Two 40-minute sessions."
- **Reading one:** the linter's model agrees - session 1 is 10 base + 2 cuts + 2
  builds + 3 concepts + 6 setup = 38.5, session 2 is 10 + 3 cuts + 2 builds + 3
  concepts = 38.5, both under `SESSION_MINUTES_CAP` and neither hint over the
  55-word nominal, so no W112 and no W114.
- **Reading two:** the two flow-2 sessions that have actually been timed came in
  at 45 and 50 against flat estimates of 32.5 and 37. Session 1 here teaches a
  discriminated union, integer paise arithmetic and shape-not-`Date` validation,
  and also carries the Next.js scaffold, the types, four constants,
  `formatPaise`, `parseLedger`, a 30-line seed file and a fetching client
  component with two panels.
- **Why it matters:** nothing before step 9 measures this, and by step 9 the only
  real fix invalidates the spec, the code, the tests and the skeleton. Flagging
  it at step 2 is the whole point of the lesson; the estimate is information, not
  a check.
- **Suggested wording:** none - the shape is legal and the split between sessions
  is the right one. Ask the Pack Writer to time session 1 first at step 9, and
  name a drop candidate inside session 1 now (the complaints panel's styling and
  the `entry-desc` column are the obvious ones) rather than at the dry run.
