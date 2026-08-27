# Ambiguity report - tip-split

**Verdict:** 1 blocking, 6 worth a look

This is a round-2 spec and it is much tighter than round 1. I re-derived the arithmetic
and it holds: every tip and grand total in both files recomputes (12400/136400,
6129/93679, 2250/47250, 28005/261380, 2985/22885, 24800/334800), `[45467, 45467, 45466]`
sums to 136400, four Fewer clicks reach the lower clamp from 4 and seventeen More clicks
reach the upper one. Counts are inside the caps (4/4/3 cuts, 5/6/6 criteria), every cut
is named by a criterion, every endpoint and screen is built in exactly one session, and
`spec.md` and `spec.json` say the same thing everywhere I checked.

I also redid the subset check by hand, criterion by criterion, opening each listed cut
alone. The claim in **Two criteria that a subset already satisfies** is correct: only
`c-2-2` and `c-2-5` go green with a listed cut open, both are disclosed, and both are
paired. Nothing else leaks. The reverse error is absent too - I found no criterion whose
assertion needs a cut it does not list.

The one blocking finding is a guarantee the spec makes about markup that the DOM cannot
deliver.

## Blocking

### A1 - "however the Builder nests" is not true of element text, and `share-row` is the case it is claimed for

- **Where:** spec.md, Screens, **How a criterion reads text**; spec.json
  `notes.text_assertions`
- **The line:** "its text is the word `Person`, one space, the person's position counting
  from 1, one space, then `formatRupees` of that share, so the first row of a 4-way split
  of 136400 paise reads exactly `Person 1 ₹341.00` **however the Builder nests the label
  and the amount**."
- **Reading one:** the row's text nodes carry the separators, e.g. a single text run
  `Person {n} {formatRupees(share)}` inside the `share-row` element. Text content is
  `Person 1 ₹341.00`, normalisation is a no-op, the assertion passes.
- **Reading two:** the Builder takes the sentence at its word and nests, e.g.
  `<span>Person {n}</span><span>{formatRupees(share)}</span>` with a CSS-module gap doing
  the visual spacing. The row *looks* right in a browser and is exactly what the sentence
  licenses, but the element's text content is `Person 1₹341.00` - there is no whitespace
  text node between the two children, so collapsing runs of whitespace has nothing to
  collapse and cannot insert a separator. The assertion fails.
- **Why it matters:** the rule as written is precisely Playwright's
  `expect(locator).to_have_text("...")` semantics (textContent, whitespace normalised,
  trimmed), which is what `fixtures/runner-check/verify/test_ui_home.py` shows the
  Verifier writing. So the spec has correctly pinned the comparison and then made a
  promise about markup that the comparison does not honour. The Builder ships reading
  two, the Verifier writes the string from the criterion, and `c-3-1`, `c-3-3`, `c-3-4`
  and `c-3-5` - four of session 3's six criteria, the payoff session - come back red at
  Gate 2 over a missing space. The same hole exists for `card-people`
  (`Split 4 ways`), `bill-saved-people` (`Split 4 ways when saved`) and
  `bill-tip-percent` (`10%`), all of which are one element holding a word and a number;
  they are lower risk only because plain JSX interpolation is the obvious way to write
  them, whereas `share-row` is a two-part row that invites two children and is the one
  place the spec says nesting is free.
- **Suggested wording:** replace the clause with "the separating spaces must exist as
  text in the DOM - either the row is one text run, `Person `, the position, a space,
  then `formatRupees` of that share, or a nested label and amount have an explicit space
  text node between them; whitespace normalisation collapses runs of whitespace, it
  cannot create a space no text node holds."

## Worth a look

### W1 - Nothing says how a route handler reads its `id`, or whether that read is inside the cut

- **Where:** spec.md, Sessions, rule 2 and cut `cut-api-bill-get`; spec.json
  `notes.skeleton_rules[1]`
- **The line:** "each declares `let body: unknown = { error: 'not implemented' }` and
  `let status = 501` above its opening marker, its cut block assigns to `body` and to
  `status`, and `return Response.json(body, { status })` is the last statement"
- **Why it matters:** the spec pins every other byte of the handler's shape and is silent
  on the one part of it that changed in Next 15, where the second argument is
  `{ params: Promise<{ id: string }> }` and must be awaited. A handler written with the
  Next 14 shape fails `next build` on the generated route type, which means `npm run
  build` in `pipeline/deploy_check.py` fails and every session-2 and session-3 criterion
  goes red at once, not one test. It is also undecided whether `const { id } = await
  params` sits above the opening marker or inside `cut-api-bill-get` - both compile, but
  the skeleton generator has to pick one, and the cut is materially different in size
  depending on the answer.
- **Suggested wording:** add to rule 2: "`app/api/bills/[id]/route.ts` is
  `export async function GET(request: Request, { params }: { params: Promise<{ id:
  string }> })`, and `const { id } = await params` ships written above the opening
  marker."

### W2 - The lesson session 1 is named for is still the one thing no criterion can see

- **Where:** spec.md, Data model, **Reading the store**; session 1 teaches "reading a JSON
  file on the server with node fs"
- **The line:** "a bundled import would pass every criterion while skipping it, so the
  rule is written here and repeated in the hint for `cut-store-read-all`"
- **Why it matters:** the spec diagnoses this honestly and then answers it with prose. It
  is still true that `import bills from '../../data/bills.json'` satisfies all 17
  criteria, and prose is not a gate - the Builder is an agent that optimises for green
  tests. `cut-store-read-all` is the first cut a student ever fills and the whole reason
  session 1 exists. One criterion would close it: rewrite `data/bills.json` at test time,
  re-request `GET /api/bills`, and assert the new value comes back, which a
  production-built bundle cannot do. Failing that, at least say in the spec that this cut
  is checked by reading the source at Gate 2 rather than by a test, so the Verifier knows
  it is on the hook for it.
- **Suggested wording:** either add to session 1 "`c-1-6` GET /api/bills reflects an edit
  made to data/bills.json after the server started, without a rebuild - cuts
  `cut-store-read-all`, `cut-api-bills-list`", or state in **Reading the store** that no
  criterion covers the fs rule and it is a source review item.

### W3 - "Session 2 sits on both caps" is wrong about one of the two caps

- **Where:** spec.md, **Session 2's weight**; spec.json `notes.session_2_weight`
- **The line:** "Session 2 sits on both caps - six criteria and four cuts"
- **Why it matters:** the cap named at the top of the same document is "five cuts and six
  criteria per session", so session 2 is on the criteria cap and has a cut of headroom.
  The sentence is load-bearing: it is part of the argument Gate 1 is being asked to
  accept for departing from `idea.md`'s two sessions, and it is the reason given for not
  rebalancing. The three-session decision itself survives the correction - 11 cuts and 17
  criteria genuinely cannot fit two sessions of at most 5 and 6 - but a reviewer should
  not have to recheck the arithmetic to see that. Separately, session 2 still carries the
  heaviest `teaches` list (dynamic segments for both a page and a handler, `useParams`,
  status branching, a not-found state, half-up integer rounding) in the same 40 minutes,
  which is the real weight problem the sentence was trying to describe.
- **Suggested wording:** "Session 2 sits on the criteria cap at six, with four of its
  five allowed cuts, and it carries the longest teaches list in the project."

### W4 - Two headings are ungraded and the paragraph that enumerates what is ungraded does not mention them

- **Where:** spec.md, Screens, **The two loading states carry no criterion, on purpose**
- **The line:** "Every other element in the two testid tables is read by at least one
  criterion, and the three non-testid affordances are graded too"
- **Why it matters:** the sentence reads as an exhaustive audit, and it is exhaustive
  about testids and affordances, but `sc-list`'s `Saved bills` heading and `sc-bill`'s
  `What each person owes` heading are elements the spec requires and no criterion ever
  reads. Both ship written so no cut is left ungraded by it, and the second one is
  covered indirectly because it is gated on the same `shares.length` that `share-row`
  counts prove - but a reader auditing coverage at Gate 1 has to work that out
  independently, and a Builder could drop either heading and stay green.
- **Suggested wording:** append "The two headings, `Saved bills` and `What each person
  owes`, carry no criterion either: both ship written, and the second appears exactly
  when a `share-row` does, so counting rows already proves its condition."

### W5 - Session 1 teaches keys, and no hint or criterion ever mentions one

- **Where:** spec.md, Session 1 **Teaches**: "rendering a list with map and keys"; cut
  `cut-list-cards`
- **Why it matters:** `cut-list-cards` is the block where a key would be written and its
  hint never says so, while every other item in session 1's teaches list lands in a cut
  hint or a criterion. A student fills the block, the tests go green, and the console
  fills with the key warning - which is the exact moment the concept is teachable and the
  session guide has nothing to hang it on. No criterion can see a key, so this is a hint
  and pack question, not a grading one.
- **Suggested wording:** append to the `cut-list-cards` hint "...giving each card element
  the bill's id as its key."

### W6 - "A grid of bill cards" and "plain CSS modules" are named and nothing else about styling is decided

- **Where:** spec.md header stack line and Screens, `sc-list` **Elements**: "a grid of
  bill cards"
- **Why it matters:** the spec deliberately keeps criteria off class names, which is
  right, but the result is that no line of CSS is required anywhere and a Builder can
  ship zero `.module.css` files and satisfy all 17 criteria with unstyled text. The stack
  line and the idea's "plain CSS modules, so the styling is not the lesson" then describe
  something that does not exist, and "a grid" is a word with no owner. Cheap to settle in
  one sentence, and it stops the Builder from either skipping styling entirely or
  inventing a design system nobody asked for.
- **Suggested wording:** add to `sc-list`'s Elements: "The cards sit in a CSS grid
  declared in a CSS module alongside the page; no criterion reads a class name, and
  styling beyond a readable grid and legible rows is out of scope."
