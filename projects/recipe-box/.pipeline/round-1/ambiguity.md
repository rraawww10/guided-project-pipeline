# Ambiguity report - recipe-box

**Verdict:** 4 blocking, 5 worth a look

The two spec files agree. Every criterion check, cut hint, goal and teaches string in
`spec.json` appears verbatim in `spec.md`; all 15 cut ids are unique; every cut is
referenced by a criterion in its own session and no criterion reaches into another
session's cuts. `learning/lessons.md` is empty, so no prior lesson applies. Everything
below is in what both files leave unsaid.

## Blocking

### A1 - Six cuts remove the only `return` their function has

- **Where:** spec.md, Sessions, rule 1; cuts `cut-store-read-all`, `cut-store-find-one`,
  `cut-fraction-scale`, `cut-api-recipes-list`, `cut-api-tags-list`, `cut-api-recipe-get`
- **The line:** "A cut point is a block inside a function, and the code around it compiles
  while the block is a hint comment. No cut removes a declaration that code outside it uses."
- **Reading one:** the value-producing statement is the whole cut, so in the skeleton
  `readAllRecipes(): Recipe[]` is a body holding one `// TODO(cut-store-read-all): ...` line.
- **Reading two:** a typed fallback `return` stays below the closing marker, so the function
  still returns something and only that session's criteria fail.
- **Why it matters:** reading one does not compile, and rule 1 promises it does.
  `.pipeline/CONTRACT.md` has the cutter replace everything between the markers with a single
  TODO comment, so `lib/store.ts` ends up with a function annotated `Recipe[]` and no return
  (TS2355), and dropping the annotation instead just moves the break to every caller
  (`Property 'filter' does not exist on type 'void'`). Either way `lib/store.ts` and
  `lib/fractions.ts` fail to typecheck, so the student's whole app stops building - not only
  the part they are meant to write. The Builder must invent this convention with nothing in
  the spec to point at, and the bill arrives at step 8 when the skeleton is cut, after the
  project is otherwise finished.
- **Suggested wording:** add a fourth rule - "A cut that would remove a function's only
  `return` keeps a typed fallback return outside the markers: `return []` in `readAllRecipes`,
  `return null` in `findRecipe`, `return stored` in `scaleQuantity`, and
  `return NextResponse.json({ error: 'not implemented' }, { status: 501 })` in each handler,
  so the skeleton typechecks and only that session's criteria fail."

### A2 - Nobody fetches the tags, and the chip bar's session 1 state is unstated

- **Where:** spec.md, Screens, `sc-list`; Session 1 "Builds. `ep-recipes-list`, `sc-list`";
  Session 2 cut `cut-api-tags-list`
- **The line:** "Elements: a search box, a tag chip filter bar built from `GET /api/tags`, a
  grid of recipe cards, and a card per recipe..."
- **Reading one:** the chip bar and its `fetch('/api/tags')` ship written in
  `app/RecipeList.tsx` from session 1, so a student finishing session 1 has a screen calling
  an endpoint whose cut is still open.
- **Reading two:** the chip bar arrives in session 2 - which the cut model cannot express, as
  the cutter opens and closes blocks in one final codebase and does not add elements per
  session.
- **Why it matters:** session 1 claims to build `sc-list`, and `sc-list`'s elements include a
  bar fed by an endpoint session 2 builds. `cut-list-fetch` covers only the recipes call, so
  no cut and no criterion owns the tags call: nothing tells the Builder where it lives or what
  the bar renders while `/api/tags` is unwritten. Rule 2 requires a later session's cut to
  leave the earlier sessions' criteria passing, and this is the case rule 2 does not cover -
  if the unwritten `/api/tags` throws inside `RecipeList`, session 1's `c-1-3` (8 cards) goes
  red in the very skeleton the student starts from.
- **Suggested wording:** in Screens add - "The tag bar's own `GET /api/tags` call ships
  written in `app/RecipeList.tsx` and renders no chips when the reply is not a 200, so the bar
  is empty until session 2 and session 1's cards are unaffected."

### A3 - Nothing pins what a test reads on a card or an ingredient row

- **Where:** spec.md, Session 1, `c-1-3`, `c-1-4`, `c-1-5`; Session 3, `c-3-3`, `c-3-4`;
  Session 4, `c-4-1`
- **The line:** "`c-1-4` sc-list displays the title, the minutes and the serves count on every
  card"
- **Reading one:** the card prints labelled text - `20 min`, `Serves 4` - and a test matches
  those strings.
- **Reading two:** the card prints bare numbers inside styled spans, and a test needs a
  `data-testid` or a role to find them.
- **Why it matters:** the spec picks CSS modules, so every class name is hashed at build time
  and there is no stable selector unless the spec names one, and the numbers do not
  disambiguate themselves: `4` is the serves count on three of the eight cards, `40` is the
  minutes on two, and on the recipe screen the header's serves count and the stepper both read
  `4` at load. So the Verifier cannot write `c-1-4`, `c-1-5` or `c-3-3` from the criterion
  alone - it has to read the Builder's markup - and then the student, who rewrites exactly
  that markup from `cut-list-cards` ("showing its title, a chip per tag, its minutes and its
  serves count"), fails a test whose hook the hint never mentions. `c-3-4` has the same shape:
  "numbered from 1" is satisfied by an `<ol>` whose numbers are CSS markers, not text any
  assertion can read. The spec already pins exact text where it matters - `No recipes match`,
  `Recipe not found`, `1 lemon`, `1/3 tsp chilli flakes` - it just stops before the card.
- **Suggested wording:** in Screens add - "Every element a criterion counts or reads carries a
  `data-testid`: `recipe-card`, `card-tag`, `card-minutes`, `card-serves`, `filter-tag`,
  `ingredient-row`, `step`, `servings-count`, and each cut hint names the testid its block must
  render."

### A4 - "the baking chip" names three elements on the page

- **Where:** spec.md, Session 2, `c-2-6`
- **The line:** "`c-2-6` sc-list renders 2 cards and the page URL reads /?tag=baking after the
  baking chip is clicked, then renders 8 cards and the URL reads / after the same chip is
  clicked a second time"
- **Reading one:** only the filter bar's chips are clickable; the chips on a card are labels,
  and the test clicks the bar.
- **Reading two:** every chip filters, card chips included - a common design the spec never
  rules out - so clicking Banana Bread's `baking` chip does the same thing as the bar's.
- **Why it matters:** on the unfiltered list three elements read `baking` - the filter chip,
  Banana Bread's card chip and Garlic Flatbread's card chip - so the test for `c-2-6` cannot
  resolve "the baking chip", and a strict locator makes that a hard error rather than a first
  match. The two readings also ship different components: reading two puts a button inside the
  card's `<Link>`, which changes the markup `cut-list-cards` produces and needs a click that
  does not navigate.
- **Suggested wording:** in Screens add - "Only the filter bar's chips are interactive; the
  chips on a card are text. `c-2-6` clicks the filter bar's chip."

## Worth a look

### B1 - The `empty` and `loading` states have no criterion and no owner

- **Where:** spec.json, screens `sc-list` `"states": ["loading", "loaded", "empty"]`; spec.md,
  Screens, `sc-list`
- **The line:** "In the `empty` state, when a search matches no title, the grid is replaced by
  the message `No recipes match`."
- **Reading one:** the message lives inside `cut-list-cards`, whose hint says only "Turn the
  recipes array into one card per recipe" - so the student ships a blank grid and nothing
  catches it.
- **Reading two:** the message ships written above the cut and the cut only maps.
- **Why it matters:** neither state is asserted anywhere in the 21 criteria, so both readings
  pass Gate 2. The same gap covers the `loading` state on both screens - no text, no criterion
  - and the upper clamp of 24 in `cut-recipe-servings`, which `c-4-5` only tests at the bottom
  end. "when a search matches no title" also undersells the state: a tag can empty the list too.
- **Suggested wording:** either add `c-2-7` ("sc-list displays `No recipes match` at /?q=zzz")
  or say in Screens that the empty and loading branches ship written outside every cut.

### B2 - One of the 7 ingredient rows has no unit

- **Where:** spec.md, Session 3, `c-3-3`
- **The line:** "`c-3-3` sc-recipe renders one row per ingredient, 7 rows at
  /recipes/lemon-garlic-pasta, each row showing the quantity, the unit and the item"
- **Reading one:** all 7 rows carry a unit element, empty for lemon.
- **Reading two:** the lemon row has no unit element at all, per "an empty unit printing
  nothing".
- **Why it matters:** the data model settles the printed text (`1 lemon`), so the Builder is
  safe, but a test written from `c-3-3` alone asserts a unit on all 7 rows and one of them is
  `""`. Under a testid convention (A3) that difference becomes a real pass or fail.
- **Suggested wording:** "...each row showing the quantity, the item, and the unit when the
  ingredient has one - 6 of the 7 rows at /recipes/lemon-garlic-pasta do."

### B3 - `cut-recipe-rows` hints at a "rows array" the spec never defines

- **Where:** spec.md, Session 3, cut `cut-recipe-rows`
- **The line:** "Render one row for every entry in the rows array, showing the formatted
  quantity, then the unit, then the item name."
- **Reading one:** `rows` is `recipe.ingredients` itself, and session 4's
  `cut-recipe-scale-quantity` then has to build a copy somewhere the spec has not said.
- **Reading two:** `rows` is a derived array of `{...ingredient}` copies built above the cut,
  which is what rule 2 implies.
- **Why it matters:** `rows` appears in a student-facing hint and nowhere in the data model or
  Screens, so a session 3 student is told to map an array nobody introduced. Reading one also
  makes `cut-recipe-scale-quantity` ("Replace the quantity of the row") mutate the fetched
  recipe: 4 to 6 stores 3 tbsp, and back to 4 then scales 3 by 4/4 and keeps 3 instead of
  restoring 2. `c-4-4` catches it, which is exactly the guess that costs a rebuild.
- **Suggested wording:** in Screens under `sc-recipe` - "`RecipeView` derives `rows`, one
  `{...ingredient}` copy per ingredient, and renders from `rows`, never from
  `recipe.ingredients` directly."

### B4 - How the URL gets written when a filter changes

- **Where:** spec.md, Session 2, `c-2-5`, `c-2-6`; cuts `cut-list-search-url`,
  `cut-list-tag-toggle`
- **The line:** "`c-2-5` sc-list renders 2 cards and the page URL reads /?q=garlic after
  garlic is typed into the search box"
- **Reading one:** every keystroke calls `router.replace`, so the URL and the fetch move with
  the typing and the box's value is read back from `useSearchParams` ("Nothing else holds the
  filter").
- **Reading two:** the write is debounced, or waits for Enter or blur, and the box holds its
  own state between writes.
- **Why it matters:** the two ship different components and different tests - a debounce needs
  the assertion to wait, and a submit means filling the box alone never changes the URL, so
  `c-2-5` fails. Reading two also leaves `/?q=garlic` opening with a filtered list and an empty
  search box, which undercuts "a link that reproduces the filtered list". The same pair leaves
  the cleared shape unsaid: `c-2-6` wants the URL to read `/`, and building it with
  `URLSearchParams` yields `/?` unless the spec says to drop the bare `?`.
- **Suggested wording:** "Both controls write with `router.replace` on every change and are
  not debounced; the search box takes its value from `useSearchParams`; and when no parameter
  is left the URL is replaced with `/`, not `/?`."

### B5 - The idea has the store written, the spec has it read-only

- **Where:** idea.md, Scope, first bullet; spec.md, Out of scope
- **The line (idea.md):** "A JSON file on disk as the store, read and written through route
  handlers."
- **Reading one:** a slip in the idea - its own out-of-scope list says "Adding, editing or
  deleting recipes. The box is read-only", and the spec followed that.
- **Reading two:** the idea meant a write path and the spec dropped it.
- **Why it matters:** the spec goes further than the idea's out-of-scope list, banning POST,
  PUT, PATCH and DELETE outright and stating "Nothing is written back to disk". That is almost
  certainly the right call, but it is the one place the spec narrows the idea, and Gate 1 is
  where a person confirms it rather than session 5.
- **Suggested wording:** none for the spec - just a nod at Gate 1 that the idea's "and
  written" was a slip.
