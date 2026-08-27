# Ambiguity report - recipe-box

**Verdict:** 0 blocking, 2 worth a look

Nothing in this revision forces a builder to guess at something that changes what
ships. The two items below are decisions the spec leaves open whose worst case is a
flaky test or a timing overrun, not a wrong build.

## The flagged area: `app/api/recipes/route.ts` shipping fully written

Checked deliberately, and it holds. Recording the reasoning because a later revision
could break it silently.

The handler answers `200` with `[]` while `cut-store-read-all` is open, so the risk is
the one `lessons.md` names: a fallback that returns plausible-looking data. Walking
every criterion that touches the recipes list:

- `c-1-1`, `c-1-2` both count 8 and `c-1-2` names one entry's fields, so `[]` fails
  both. `cut-store-read-all` stays graded.
- `c-1-3`, `c-1-4`, `c-1-5` need cards, and `cards` is empty while `cut-list-cards` is
  open. `[]` gives 0 cards either way.
- The empty-200 reply lands the screen on `No recipes match` rather than
  `Loading recipes`. Exactly one criterion asserts that message - the second phase of
  `c-2-4` - and it sits behind a same-criterion assertion of 2 cards at `/?q=garlic`,
  which needs all five of `c-2-4`'s cuts. The `empty` branch also tests
  `recipes.length` rather than card count, so `cut-list-cards` open shows an empty grid
  and not the message. Two independent guards.
- `c-2-1`, `c-2-2`, `c-2-5`, `c-2-6` all assert a narrowed count, which `shown = all`
  (filter cut open) and `[]` (store cut open) both fail.
- On `sc-recipe` the empty store propagates through `findRecipe` to a 404, so
  `c-3-1`, `c-3-3`, `c-3-4` and all six session-4 criteria land on `Recipe not found`
  with no `servings-count`, no `ingredient-row` and no `step` element to read. None can
  pass with `cut-store-read-all` open.

No criterion passes with any of its own listed cuts open, except the two the spec
already records (`c-3-2`, `c-3-5`). One footnote, not a finding: those two also go
green with `cut-store-read-all` open, not just `cut-store-find-one` - a store that
reads nothing and a store that finds nothing are equally indistinguishable from
outside. The conclusion and the prescribed pairing with `c-3-1` / `c-3-3` are unchanged.

The forward chain also holds: `cut-api-recipes-filter` filled in session 2 leaves bare
`GET /api/recipes` returning all 8, so `c-1-1` and `c-1-2` survive; and
`cut-recipe-scale-quantity` filled in session 4 scales by `4/4` on first render at
`/recipes/lemon-garlic-pasta`, so `c-3-3`'s `2 tbsp olive oil` and `1 lemon` survive.

## Worth a look

### W1 - The written list `useEffect` has no stale-reply guard, and the spec forbids a debounce
- **Where:** spec.md, "Who owns the fetch" (sc-list); spec.json, `sc-list.owns`
- **The line:** "`const qs = searchParams.toString()` ships written, the `useEffect`
  call and its dependency array `[qs]` ship written, and `cut-list-fetch` is the body of
  that effect." Together with: "Both write on every change - no debounce, no submit
  button, no Enter key to press."
- **Reading one:** the written effect is bare - one `fetch` per `qs`, no cleanup
  function, last reply to arrive wins.
- **Reading two:** the written effect carries a cleanup that drops a reply whose `qs` is
  no longer current (an `ignore` flag or an `AbortController`).
- **Why it matters:** typing `garlic` fires six requests, one per keystroke, all in
  flight at once. `c-2-4` and `c-2-6` both assert a card count after typing, and the
  prefixes are not neutral: `garli`, `garlic` and several shorter prefixes all match
  `Lemon Garlic Pasta`, so an out-of-order reply leaves a different count on screen than
  the URL implies. Because the effect body is the student's cut, the student cannot add
  the guard - only the written wrapper can hold it, so this is the spec's decision and
  not the builder's. Local route handlers reading one small JSON file will almost
  always resolve in order, which is why this is not blocking: it is a latent flake, and
  the criterion that would expose it is the one the spec worked hardest to make
  deterministic.
- **Suggested wording:** add to "Who owns the fetch": "The written effect returns a
  cleanup that sets an `ignore` flag, and the student's block writes to state only when
  that flag is still clear, so a reply for a superseded query string is discarded."

### W2 - Session 3 is now the timing risk, and nothing before step 9 measures it
- **Where:** spec.md, "Why session 1 carries three cut points and sessions 2 and 3 carry
  four"; spec.json, session 1 `weight_note`
- **The line:** "Session 4 holds three cuts as well, for the opposite reason: it
  introduces no file, no endpoint and no screen."
- **Reading one:** cut count plus setup weight is now balanced across all four sessions.
- **Reading two:** the note reasons about sessions 1 and 4 and leaves session 3
  unexamined. Session 3 introduces three files - `app/api/recipes/[id]/route.ts`,
  `app/recipes/[id]/page.tsx`, and `app/recipes/[id]/RecipeView.tsx`, which is the
  largest written component in the project, carrying the header, the tag chips, the
  stepper with its two controls and `servings-count`, the numbered steps list and the
  `rows` derivation - teaches five new concepts, and still carries the maximum four
  cuts. Session 2 carries four cuts against one small new route file; session 4 carries
  three short blocks and no new file at all.
- **Why it matters:** `lessons.md` records that the session holding the setup should
  carry fewer cuts than the others, and that an overrun is not found until the Pack
  Writer times it at step 9 - after the spec, the code, the tests and the skeleton are
  all built. The spec applied that lesson to session 1 and did not re-apply it to
  session 3, which is the only other session with real setup. This is a risk note, not
  a defect: session 3's blocks are individually short.
- **Suggested wording:** extend the weight note with a sentence naming session 3 as the
  second-heaviest session and the relief if step 9 times it over: "If session 3
  overruns, `cut-store-find-one` is the cut to ship written - it is a one-line lookup,
  and the spec already records that `c-3-2` and `c-3-5` grade it only weakly, so
  session 3 loses the least by keeping `cut-api-recipe-get`, `cut-recipe-fetch` and
  `cut-recipe-rows` as its three cuts." No new criterion is involved, so this stays
  inside the linter's caps.

## Checked and clean

Recorded so a later pass does not re-litigate: criterion-to-cut lists (every criterion
names every cut on its path, and no proper subset passes beyond the two documented);
the fraction arithmetic in every session-4 criterion, including that `1/2 tsp` and
`3/4 tsp` never collide on screen at 6 servings and `1/3 tsp` and `1/2 tsp` never
collide at 4; both clamp criteria's click counts; the five tags all being present in
the seed table so `c-2-3` is satisfiable; the two-titles-with-garlic and
two-baking-recipes arithmetic behind `c-2-1`, `c-2-2` and `c-2-6`; every testid a
criterion reads existing and being unambiguous on its page; `servings-count` being the
only bare servings number on `sc-recipe`; the `filter-tag` versus `card-tag`
disambiguation `lessons.md` demanded; both URL cuts naming what they must preserve;
rule 4's fallbacks against the TS2355 lesson; and the drift from `idea.md`, which is
the single read-only narrowing the spec already surfaces for Gate 1.
