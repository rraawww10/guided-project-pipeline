# Ambiguity report - recipe-box

**Verdict:** 4 blocking, 4 worth a look

Read `spec.md` and `spec.json` cold first, then `idea.md`, then `learning/lessons.md`.
The spec is unusually tight on the things earlier rounds are likely to have been about:
testid collisions are resolved (`Serves 4` / `Written for 4` / `servings-count`), the
filter-bar chip is distinguished from the card chip in `c-2-5` and `c-2-6`, `c-2-6`
drives both filters through the UI, every fetch has an owning session, no cut swallows a
typed function's only `return`, and two subset-satisfied criteria are named and paired.
What is left is one design contradiction, three grading-integrity holes that no
downstream script can see, and a session-weight problem the caps do not measure.

## Blocking

### A1 - `RecipeList` cannot hold the tag list and still hold "exactly two pieces of state"

- **Where:** spec.md, Screens, `sc-list` ("What holds the screen's state" and the
  paragraph above it); spec.json, `screens[0].state_shape` and `screens[0].elements[1]`
- **The line:** "`app/RecipeList.tsx` holds exactly two pieces of state, both declared
  outside every cut" - followed by `recipes` and `status` only - against "The tag bar's
  own `GET /api/tags` call ships written in `app/RecipeList.tsx`, outside every cut, and
  renders no chips when the reply is not a 200."
- **Reading one:** there is a third state, `tags: string[]` starting at `[]`, written
  outside every cut and filled by that call; the chips render from it, so the bar is
  genuinely empty until `cut-api-tags-list` is filled. The "exactly two" sentence is
  then simply wrong.
- **Reading two:** "exactly two" is binding, so the five chips are not held in state at
  all - the Builder hardcodes the five tag names (or lifts the fetch into
  `app/page.tsx` and passes them as props, which contradicts "in `app/RecipeList.tsx`").
- **Why it matters:** reading two silently voids `cut-api-tags-list` as a grading cut.
  `c-2-5` and `c-2-6` both list it, and both clicks would work with that block still
  open, because hardcoded chips do not care what the endpoint answers. Only `c-2-3`
  would still grade the endpoint, and the spec's own claim that the bar "is therefore
  empty until session 2 fills `cut-api-tags-list`" - the thing that makes session 1's
  skeleton honest - stops being true. Nothing downstream sees this: the tests pass
  either way, and the cutter only compares all-cuts-open with all-cuts-filled.
- **Suggested wording:** "`app/RecipeList.tsx` holds three pieces of state, all declared
  outside every cut: `recipes`, `status`, and `tags: string[]` starting at `[]`. The
  written `GET /api/tags` call is the only thing that sets `tags`, and the filter bar
  renders one `filter-tag` button per entry in `tags`, so the bar is empty until
  `cut-api-tags-list` is filled." Mirror the third state into
  `spec.json screens[0].state_shape`.

### A2 - `cut-api-recipes-list` does not say which of the two variables in scope to send

- **Where:** spec.md, Session 1 cut points, `cut-api-recipes-list`; spec.json,
  `sessions[0].cuts[1].hint`
- **The line:** "Send the recipes the handler has back to the browser as a JSON array
  with status 200."
- **Reading one:** `return NextResponse.json(shown)` - `shown` being the variable rule 2
  declares (`let shown = all`) for `cut-api-recipes-filter` to narrow.
- **Reading two:** `return NextResponse.json(all)` - equally faithful to the hint, since
  rule 2 puts both names in the file and the hint names neither.
- **Why it matters:** reading two passes `c-1-1` and `c-1-2` exactly as reading one does,
  so session 1 closes green. Then in session 2 the student fills
  `cut-api-recipes-filter` correctly, `shown` narrows, the response still carries `all`,
  and `c-2-1`, `c-2-2`, `c-2-4`, `c-2-5` and `c-2-6` all fail - pointing the student at
  the filter code, which is the one part that is right. The hint is the entire text the
  student gets (per CONTRACT.md the skeleton renders it as
  `// TODO(cut-api-recipes-list): ...`), so this ships to every student unless the
  wording names the variable. Step 6 only catches it if the Builder happens to make the
  same choice in the reference code; if the Builder reads rule 2 and writes `shown`, the
  trap ships undetected. This is the round-2 lesson ("a cut hint that names one thing
  implies replacing everything else") recurring in a different cut.
- **Suggested wording:** "Send `shown` back to the browser as a JSON array with status
  200." And, since the spec never says where `readAllRecipes()` is called, add to rule
  2: "the handler's `const all = readAllRecipes()` and `let shown = all` both ship
  written, above `cut-api-recipes-filter`."

### A3 - `c-1-2` is satisfied by a proper subset of its cuts, and the spec says only two criteria are

- **Where:** spec.md, Session 1, `c-1-2`, and the section "Two criteria that a subset
  already satisfies"; spec.json, `sessions[0].criteria[1]`
- **The line:** "GET /api/recipes returns each recipe with an id, a title, a tags array,
  a minutes number and a serves number"
- **Reading one:** the test also asserts the array is the 8 seed recipes, so both cuts
  are required.
- **Reading two:** the test asserts the shape of each element, which is what the
  criterion says. With `cut-api-recipes-list` filled and `cut-store-read-all` still open,
  rule 4's `return []` fallback makes the handler answer 200 with `[]`, and a
  per-element assertion over zero elements is vacuously true. `c-1-2` goes green with
  half its cuts open.
- **Why it matters:** the spec names `c-3-2` and `c-3-5` as "the two criteria that a
  subset already satisfies" and tells the pack author to pair them. A third case that is
  not recorded is worse than one that is, because a per-cut checkpoint will present
  `c-1-2` as proof that the store read works. `lessons.md` records that
  `pipeline/cutter.py` is blind to partial fills, so step 8 cannot catch this and step 6
  will not either - the reference code has every cut filled.
- **Suggested wording:** strengthen `c-1-2` rather than add a criterion (session 1 has
  room at 5 of 6, but a strengthening is cheaper): "GET /api/recipes returns 8 objects,
  and its `lemon-garlic-pasta` entry has id lemon-garlic-pasta, title Lemon Garlic
  Pasta, a tags array of quick and vegetarian, minutes 20 and serves 4." That admits no
  vacuous pass, and the overlap with `c-1-1`'s count is harmless.

### A4 - Session 1 carries the whole project setup plus as many cuts as the sessions that carry none

- **Where:** spec.md, Sessions 1 to 4 (cut counts 4 / 4 / 4 / 3); spec.json, the four
  `cuts` arrays
- **The line:** "Session 1 - The recipe list ... **Cut points.** `cut-store-read-all`,
  `cut-api-recipes-list`, `cut-list-fetch`, `cut-list-cards`"
- **Reading one:** four cuts is within the cap of five, so the session fits.
- **Reading two:** session 1 also carries every file the project stands on -
  `lib/types.ts`, `data/recipes.json` with 8 recipes of 5 to 9 ingredients and 3 to 7
  steps, `lib/store.ts`, `lib/fractions.ts` with `formatQuantity` and `gcd` written,
  `app/page.tsx` with its `<Suspense>` boundary, and `app/RecipeList.tsx` with its
  state, its `qs`, its `useEffect`, its `replaceQuery` helper and its loading and
  no-match branches - and teaches five new concepts on top. Session 4 introduces no
  file and carries three cuts.
- **Why it matters:** `lessons.md` records this exact failure from tip-split: "the
  linter caps cuts and criteria per session but weighs neither setup cost nor teaching
  minutes, so an overrun is not found until the Pack Writer times it at step 9 - after
  the spec, the code, the tests and the skeleton are all built and both gates are
  passed", and the rule it draws is "the session holding the setup should carry fewer
  cuts than the others, not the same number." That rule is violated as written, and the
  only checker that would notice sits two gates downstream.
- **Suggested wording:** ship `cut-api-recipes-list` written and drop session 1 to three
  cuts (`cut-store-read-all`, `cut-list-fetch`, `cut-list-cards`), keeping every count
  inside the caps. The handler then answers 200 with `[]` while `cut-store-read-all` is
  open, which still fails `c-1-1` and - once `c-1-2` is strengthened per A3 - still
  fails `c-1-2`, so nothing is over-graded; the only visible change is that a session-1
  student who has filled `cut-list-fetch` sees `No recipes match` instead of `Loading
  recipes`. Whatever is chosen, say in the Sessions preamble why session 1 carries fewer
  cuts, so a later round does not re-add one.

## Worth a look

### B1 - `cut-recipe-scale-quantity` does not name `scaleQuantity`, so the session's arithmetic cut can be bypassed

- **Where:** spec.md, Session 4 cut points; spec.json, `sessions[3].cuts[2].hint`
- **The line:** "Replace the quantity of the row copy with the stored quantity of that
  ingredient scaled from the recipe's serves count to the servings count on screen."
- **Reading one:** the block calls the written helper -
  `row.quantity = scaleQuantity(ing.quantity, recipe.serves, servings)` - so the
  arithmetic lives behind `cut-fraction-scale`.
- **Reading two:** the block does the multiply-and-reduce inline in `RecipeView` and
  never touches `lib/fractions.ts`. `c-4-2`, `c-4-3` and `c-4-4` then all go green with
  `cut-fraction-scale` still open, because rule 4's `return stored` fallback is never
  reached. A fourth undocumented subset-satisfied criterion set, and the student skips
  the one block session 4 exists to teach.
- **Why it matters:** invisible to step 6 (the reference code calls the helper) and to
  step 8 (all-open still fails, all-filled still passes).
- **Suggested wording:** "Replace the quantity of the row copy by calling
  `scaleQuantity` with that ingredient's stored quantity, the recipe's serves count and
  the servings count on screen." If that reads as too small a block to be worth a cut,
  the alternative is to fold it into `cut-recipe-rows` and let `cut-fraction-scale` be
  session 4's only arithmetic cut - session 4 would then hold 2 cuts, still legal.

### B2 - Nothing grades that a card links to its recipe

- **Where:** spec.md, Screens `sc-list` and Session 1 `cut-list-cards`; criteria
  `c-1-3`, `c-1-4`, `c-1-5`, `c-2-4`, `c-2-5`, `c-2-6`
- **The line:** "Each card is a link to `/recipes/<id>`" - and, in the cut hint, "each
  one a link to that recipe page"
- **Reading one:** the Builder will render a `<Link>`, because the prose and the hint
  both say so.
- **Reading two:** no criterion reads an `href` or navigates from the list, and every
  session-3 and session-4 criterion opens `/recipes/lemon-garlic-pasta` directly. A
  student who renders the card contents without the link passes all 22 criteria and
  ships a list that cannot open a recipe.
- **Why it matters:** it is the app's only navigation and it is ungraded; nothing
  downstream catches it, because the tests are generated from the criteria.
- **Suggested wording:** strengthen `c-1-4` rather than add a criterion (session 1 has
  room, but this fits): "sc-list displays the title Lemon Garlic Pasta inside a
  recipe-card that links to /recipes/lemon-garlic-pasta and whose card-minutes element
  reads 20 min and whose card-serves element reads Serves 4." While editing that line,
  note that the Screens preamble's claim that "every element a criterion counts or reads
  carries a `data-testid`" overstates by one: the title has no testid and is read as text
  inside `recipe-card` by `c-1-4` and `c-2-6`. That is workable for a test author, but
  the sentence should say so rather than promise a hook that does not exist.

### B3 - Three more hints omit the written name the block has to use

- **Where:** spec.md Session 1 `cut-list-cards`, Session 2 `cut-api-recipes-filter`,
  Session 3 `cut-recipe-rows`; the same three hints in spec.json
- **The line:** "Turn the recipes array into one recipe-card element per recipe" /
  "Keep only the recipes whose title contains the q parameter" / "its text reading the
  formatted quantity"
- **Reading one:** the block assigns to the `ReactNode[]` rule 1 declares above the
  marker, reassigns `shown`, and calls the written `formatQuantity`.
- **Reading two:** the student names a fresh variable (nothing renders, no error), or
  filters into a new local (nothing narrows), or prints `num/den` by hand
  (`2/1 tbsp olive oil`).
- **Why it matters:** far milder than A2 - every one of these fails a criterion in the
  same session it is filled, so step 6 and the student's own red test catch them - but
  the spec already names `replaceQuery`, `rows` and `setServingsClamped` in the hints
  that need them, so the omission is inconsistent rather than deliberate.
- **Suggested wording:** name them: "...and assign them to `cards`", "...and assign the
  result to `shown`", "...its text reading `formatQuantity` of that row's quantity, then
  the unit when that ingredient has one, then the item name."

### B4 - The idea's "read and written" store: a decision for the gate, not a defect

- **Where:** spec.md, Out of scope, closing note; idea.md, Scope bullet 1 against
  idea.md, Out of scope bullet 1
- **The line:** "The idea's first scope bullet says the JSON file is 'read and written
  through route handlers', while the idea's own out-of-scope list rules out adding,
  editing and deleting recipes. This spec follows the out-of-scope list and keeps the
  store read-only."
- **Why it flags:** the spec is right that the idea contradicts itself and right to
  choose the narrower reading - there is no writable behaviour the idea asks for that the
  out-of-scope list does not forbid. It is raised here only because the spec asks Gate 1
  to confirm it, so the gate should record the decision rather than leave it as prose in
  a file the Builder also reads. No wording change needed.

## Checked and clean

Worth recording so a later round does not re-litigate: the 4 -> 6 -> 4 arithmetic in
`c-4-2` to `c-4-4` is correct against the stored rows (2/1 -> 3/1, 1/3 -> 1/2 -> 1/3);
`c-4-5`'s four clicks and `c-4-6`'s twenty-one clicks each land exactly one click past
the clamp; the seed table supplies all five tags for `c-2-3` and the 2/2/1 counts
`c-2-1`, `c-2-2` and `c-2-6` need; `c-3-4` correctly omits `cut-recipe-rows`, since the
step elements ship written; every criterion's cut list matches the code path the
convention describes; and no criterion depends on a CSS class name.
