# Ambiguity report - recipe-box

**Verdict:** 4 blocking, 6 worth a look

The spec is unusually tight, and visibly the work of a second round: the testid
table, the fallback-return rule, the `Written for 4` wording, the "`c-2-6`
clicks the filter bar's chip" note, the `/` not `/?` rule and the "no gap where
the unit would be" line each close a hole that `learning/lessons.md` records
from round 1. Everything below is what is left.

Three of the four blocking findings share one root: **the list screen's URL
plumbing is described in prose but no cut owns it.** The prose says what the
finished screen does; the four `RecipeList.tsx` hints between them never say who
writes the effect's dependency array, who preserves the other query parameter,
or whether the search box is controlled. A builder resolves all three silently,
and no criterion catches any of them.

## Blocking

### A1 - Writing one filter to the URL may wipe the other

- **Where:** spec.md + spec.json, Session 2, cuts `cut-list-search-url` and
  `cut-list-tag-toggle`
- **The line:** "Write the text of the search box into the q parameter of the
  page URL, and take q out of the URL when the box is emptied." and "Put the
  clicked tag into the tag parameter of the page URL, and take tag out of the
  URL when the chip that is already active is the one clicked."
- **Reading one:** each control reads the current `useSearchParams()`, sets or
  deletes only its own key, and replaces with the rest of the string intact. A
  tag stays applied while you type.
- **Reading two:** each control builds a fresh query string holding only its own
  key - `router.replace(text ? '/?q=' + text : '/')`. Typing clears the active
  tag; clicking a chip clears the search text. Both hints read perfectly well
  this way, and reading two is the shorter code.
- **Why it matters:** reading two contradicts the Outcome section - "Typing
  narrows the list by title, clicking a chip narrows it by tag, and the two
  narrow together" and "`/?q=garlic&tag=baking` is a link that reproduces the
  filtered list" - and **no criterion catches it.** `c-2-5` starts with no tag
  set, `c-2-6` starts with no q set, and `c-2-3` exercises both keys only
  against the endpoint, never through the UI. A build that ships reading two
  goes green at Gate 2 with the headline feature of session 2 broken.
- **Suggested wording:** add to both hints: "starting from the query string the
  page already has, so the other parameter is left as it is." And add a
  criterion, e.g. `c-2-7`: "sc-list renders 1 recipe-card element and the page
  URL holds both q=garlic and tag=baking after the filter-tag chip reading
  baking is clicked and garlic is typed into the search box."

### A2 - No cut owns the refetch, so session 1 can silently fail session 2

- **Where:** spec.md, Screens / `sc-list`, and Session 1 cut `cut-list-fetch`
- **The line:** "The list screen passes its own query string straight to the
  endpoint: it reads `useSearchParams()`, sends the same string to
  `/api/recipes?...`, and refetches when the string changes." The hint the
  student reads is only "Ask the recipes endpoint for the list, passing the page
  query string straight through, and put the array it answers with into state."
- **Reading one:** the whole `useEffect(..., [deps])` is inside
  `cut-list-fetch`, so a session-1 student writes the dependency array. In
  session 1 the URL never changes, so `[]` is the natural thing to write, and it
  passes `c-1-3`, `c-1-4` and `c-1-5`.
- **Reading two:** the `useEffect` call and its dependency array ship written and
  `cut-list-fetch` is the effect body alone.
- **Why it matters:** under reading one the refetch-on-change behaviour is
  required by `c-2-5` and `c-2-6` but is owned by a **session-1** cut, and no
  session-1 criterion can distinguish `[]` from `[searchParams.toString()]` -
  the first load works either way. A student who fills both session-2 cuts
  perfectly sees both session-2 screen criteria red, and the grader blames
  `cut-list-search-url`. The two readings also put the cut markers in different
  places, so the skeleton generator needs the answer either way.
- **Note the asymmetry:** the spec is explicit that the *other* fetch on this
  screen is owned - "The tag bar's own `GET /api/tags` call ships written in
  `app/RecipeList.tsx`, outside every cut" - which is the lessons file's "every
  fetch needs an owner" applied correctly. The recipes fetch never gets the same
  sentence.
- **Suggested wording:** in the `sc-list` paragraph: "The `useEffect` that runs
  the recipes fetch ships written, with `[searchParams.toString()]` as its
  dependency array; `cut-list-fetch` is the body of that effect."

### A3 - The initial value of the fetch state is never named

- **Where:** spec.md, Screens, both `sc-list` and `sc-recipe`
- **The line:** "In the `loading` state, before the first reply arrives, the
  screen displays `Loading recipes` and no grid." and "Both branches ship
  written, outside every cut, so a student who has not yet filled
  `cut-list-cards` still sees them."
- **Reading one:** the screen holds `recipes: Recipe[] | null` starting at
  `null`, and `null` means loading. With `cut-list-fetch` still open the
  skeleton sits on "Loading recipes" forever.
- **Reading two:** the screen holds `recipes: Recipe[]` starting at `[]` plus a
  separate `loading` boolean. With `cut-list-fetch` open the skeleton shows "No
  recipes match" straight away, and the student's cut has to set two pieces of
  state, not one - which the hint does not say.
- **Why it matters:** it decides the state shape the student writes into, so it
  decides whether the hint is accurate, and it decides what session 1's first
  run looks like. On `sc-recipe` it decides more: `cut-recipe-fetch` is told to
  "move the page to its not-found state on a 404 reply", and `c-3-5` asserts
  "Recipe not found" with `cut-recipe-fetch` as its only cut. If the builder's
  status variable starts anywhere but `loading`, `c-3-5` goes green against a
  skeleton with that cut still empty - the lessons file's "the fallback must not
  accidentally pass the test", one layer up in React state. The spec's own note
  says a student "who has not yet filled `cut-list-cards`" sees these branches;
  it never says what a student who has not yet filled `cut-list-fetch` or
  `cut-recipe-fetch` sees.
- **Suggested wording:** "Each screen holds a `status` of `'loading' | 'loaded'
  | 'empty'` (`'not-found'` on `sc-recipe`) that starts at `'loading'`, and the
  fetch cut is the only code that moves it off `'loading'`. Until that cut is
  filled both screens sit on their loading message."

### A4 - Is the search box controlled by the URL or seeded from it?

- **Where:** spec.md, Screens / `sc-list`
- **The line:** "Both controls write with `router.replace` on every change - no
  debounce, no submit button, no Enter key to press - and the search box takes
  its value from `useSearchParams`, so `/?q=garlic` opens with `garlic` already
  in the box."
- **Reading one:** a controlled input, `value={searchParams.get('q') ?? ''}`.
  Every keystroke fires `router.replace` and the box only shows the character
  once the navigation resolves and the component re-renders.
- **Reading two:** an uncontrolled input, `defaultValue={searchParams.get('q') ??
  ''}`, which satisfies "opens with `garlic` already in the box" identically and
  never waits on the router.
- **Why it matters:** reading one makes a controlled input's displayed value
  depend on an async App Router navigation - the standard way to drop characters
  when typing outruns the transition. `c-2-5` types six characters and then
  asserts the URL reads exactly `/?q=garlic`; under reading one it is the
  strongest flake candidate in the suite, and a flaky graded criterion is a Gate
  2 time sink. The spec has deliberately ruled out both usual escapes (debounce,
  submit button), so the control mode is the only lever left and it should be
  stated rather than inferred.
- **Suggested wording:** "The search box is uncontrolled: its `defaultValue`
  comes from `useSearchParams` so `/?q=garlic` opens with `garlic` in the box,
  and its `onChange` writes to the URL. Its displayed text is never driven back
  from the URL."

## Worth a look

### B1 - The per-criterion `cuts` arrays are inconsistently scoped

- **Where:** spec.json, throughout
- **The problem:** `c-1-4` and `c-1-5` list only `cut-list-cards`, but neither
  can pass without `cut-list-fetch` - no recipes, no cards. `c-1-3` lists both.
  Same gap: `c-2-5` and `c-2-6` need `cut-list-fetch` and `cut-list-cards`, and
  `c-2-6` needs `cut-api-tags-list` as well, because without it the filter bar
  renders no chip to click.
- **Why it matters:** nothing changes in the shipped code, but phase 3 builds
  the instructor guide and any per-cut checkpoint from these arrays. "Fill
  `cut-list-cards` and `c-1-4` goes green" is not true.
- **Suggested fix:** pick one convention - list every cut a criterion depends
  on, including ones from earlier sessions - and apply it to all 22 criteria.

### B2 - `findRecipe`'s fallback makes `c-3-2` green with its own cut still empty

- **Where:** spec.md, Sessions, rule 4; criterion `c-3-2`
- **The line:** "`return null` in `findRecipe`" and `c-3-2` - "GET
  /api/recipes/not-a-recipe returns 404 with a JSON body holding an error field
  - cuts `cut-store-find-one`, `cut-api-recipe-get`"
- **The problem:** fill `cut-api-recipe-get` and leave `cut-store-find-one`
  open, and `findRecipe` returns `null` for every id, so the handler answers 404
  with an error field for `not-a-recipe` and `c-3-2` passes against a store that
  cannot find anything. This is the lessons file's "the fallback must not
  accidentally pass the test", and unlike the other fallbacks it is not fixable
  by choosing a different one - `null` is the only typed fallback `Recipe |
  null` admits.
- **Why it matters:** session 3 as a whole is still graded correctly, because
  `c-3-1` and `c-3-3` both fail. Only a per-cut checkpoint is misled. Worth
  recording so phase 2 does not treat `c-3-2` as proof the store cut works.
- **Suggested fix:** none needed in the code; note it against `c-3-2` so the
  instructor guide pairs it with `c-3-1` rather than presenting it alone.

### B3 - Three of the six declared screen states have no criterion

- **Where:** spec.json, `screens[].states`
- **The problem:** `sc-list` declares `loading` and `empty`, `sc-recipe`
  declares `loading`, and spec.md pins exact copy for all three ("Loading
  recipes", "No recipes match", "Loading recipe"). No criterion in any session
  asserts any of them. Only `not-found` is covered, by `c-3-5`.
- **Why it matters:** `empty` is the state a student reaches by typing nonsense
  into the search box - the first thing they try - and it is the one piece of
  session-2 behaviour nothing verifies.
- **Suggested fix:** one criterion in session 2, e.g. "sc-list displays the
  message No recipes match and renders 0 recipe-card elements after zzz is typed
  into the search box - cuts `cut-list-search-url`, `cut-api-recipes-filter`".
  Note when adding it that a criterion asserting *zero* cards is green on an
  empty skeleton by construction, so it needs to sit alongside `c-1-3`, never
  alone.

### B4 - Session 4 criteria are inconsistent about naming their setup

- **Where:** spec.md + spec.json, Session 4
- **The line:** `c-4-5` - "sc-recipe displays 1 in the servings-count element
  after the minus control is clicked while the servings count is 1"
- **The problem:** it is the only session-4 criterion naming neither a route nor
  a starting count, so the test author invents both (four minus clicks at
  `lemon-garlic-pasta`? three at `chilli-prawn-rice`?). `c-4-2` and `c-4-3` say
  "at 6 servings" without saying that 6 is reached by clicking plus twice.
  `c-4-1`, `c-4-4` and `c-4-6` all spell their setup out.
- **Why it matters:** low - every reading yields the same assertion - but three
  criteria written to a looser standard than their neighbours invite three
  differently-shaped tests.
- **Suggested wording:** `c-4-5` - "sc-recipe displays 1 in the servings-count
  element after the minus control is clicked 4 times at
  /recipes/lemon-garlic-pasta, which is stored as serves 4".

### B5 - The idea contradicts itself on a writable store; the spec already picked

- **Where:** idea.md, Scope bullet 1 vs. idea.md Out of scope bullet 1
- **The problem:** the idea says the JSON file is "read and written through
  route handlers" while its own out-of-scope list rules out "Adding, editing or
  deleting recipes." The spec follows the out-of-scope list, keeps the store
  read-only, and flags the choice itself in a "One note for Gate 1".
- **Verdict:** the spec's reading is the right one - the writable phrasing is
  the only support for a write path anywhere in the idea, and every other
  bullet, constraint and session assumes read-only. Nothing downstream needs to
  change. Listed here only so the gate reader can close it rather than
  re-derive it.

### B6 - Session 1 ships a search box that does nothing, and does not say so

- **Where:** spec.md, Screens / `sc-list`
- **The problem:** the search box is not inside any cut, so it renders from
  session 1, but nothing is wired to it until `cut-list-search-url` in session
  2. A session-1 student types into it and the list does not move. The spec
  calls out exactly this for the tag bar - "The bar is therefore empty until
  session 2 fills `cut-api-tags-list`, and the cards session 1 is graded on are
  unaffected by it" - and says nothing for the search box.
- **Why it matters:** small, but the spec set the precedent, and the phase-3
  instructor guide will want the same sentence.
- **Suggested wording:** one sentence after the tag-bar note: "The search box
  renders from session 1 but is inert until session 2 fills
  `cut-list-search-url`; nothing session 1 is graded on depends on it."

## Checked and clear

Recorded so the next pass does not re-derive them.

**Data.** The seed table supports every count the criteria assert: 2 titles
contain "garlic", 2 recipes are tagged `baking`, `garlic-flatbread` is the only
overlap, and all five tags appear in the eight seeds so `c-2-4` is satisfiable.
`c-2-4`'s alphabetical order matches a default string sort. `c-4-2` and `c-4-3`
are arithmetically right (2 x 6/4 = 3; 1/3 x 6/4 = 1/2), and `c-4-6`'s 21 clicks
from serves 4 does exercise the upper clamp rather than land on it.

**Against `learning/lessons.md`.** Every round-1 spec lesson is answered.
Hashed CSS-module class names: closed by the eight-testid table and the explicit
"No criterion depends on a CSS class name". Ambiguous numbers on the page:
closed by `Written for 4` (so `servings-count` is the only bare servings number)
and by "`c-2-6` clicks the filter bar's chip" plus the `filter-tag` / `card-tag`
split. Every fetch needs an owner: the `GET /api/tags` call is explicitly
written outside every cut, and the tags route ships with rule 4's 501 fallback,
so session 1's skeleton renders an empty bar rather than throwing - the one
remaining unowned fetch is A2.

**Rule 4 does not conflict with the cut-point lesson.** The lesson records that
"return inside the markers fails the cutter's typecheck", which reads at first
like a contradiction of rule 4, since rule 4 keeps the real `return` inside the
markers and adds a fallback below it. It is not one. `pipeline/cutter.py`
typechecks the skeleton with `tsc` and reports TS2355 / TS7030 - the
missing-return errors - and its own hint is rule 4 verbatim: "Keep a typed
fallback return outside the markers, so the skeleton still compiles with the
block replaced by its hint comment." Rule 4's pattern leaves a reachable typed
return in every cut function, so TS2355 cannot fire; the unreachable return left
behind once a block is filled is not a `tsc` error, and no eslint or
`no-unreachable` check runs anywhere in the pipeline. The round-1 failure was
cuts with *no* fallback, which rule 4 fixes. The cutter also enforces rule 3
directly - it raises on a cut id appearing more than once, and on a declared id
missing from the code.

**Skeleton reachability, cut by cut.** All fifteen cuts satisfy rules 1 and 4:
five are void handlers or effect bodies needing no return, two assign to a
declared `ReactNode[]`, `cut-api-recipes-filter` assigns to `let shown = all`,
and the rest have the named fallbacks. Both cuts that render marked-up elements
do name their testids in the hint the student reads, as the spec claims -
`cut-list-cards` names all four of `recipe-card`, `card-tag`, `card-minutes` and
`card-serves`, and `cut-recipe-rows` names `ingredient-row`. Every fallback
fails the criteria it should: 501 fails all seven endpoint criteria, `return []`
in `readAllRecipes` fails `c-1-1`, and `return stored` in `scaleQuantity` fails
`c-4-2`, `c-4-3` and `c-4-4` while correctly leaving session 3's `c-3-3` green
on the stored quantities. The single exception is B2 above.

**Session fit.** 5 / 6 / 5 / 6 criteria and 4 / 4 / 4 / 3 cuts. Session 4 is the
densest concept load but ships `gcd` and `formatQuantity` written, leaving the
student three blocks: multiply-and-reduce, the clamping setter, and the row
quantity replacement. It fits.
