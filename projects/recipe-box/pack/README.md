# Recipe Box - instructor pack

A recipe library students browse, search, open and re-scale. Four sessions of
40 minutes. Next.js 15 App Router, React 19, TypeScript, plain CSS modules. It
runs offline: the store is one JSON file on disk, read through route handlers.

**Read this first if you are teaching session 3.** Its plan comes to **45
minutes, 5 over the cap**. The fix is in `session-3.md` under "This session does
not fit" and it takes one minute to apply. Nothing else in the pack overruns.

## What students end with

- `/` - all 8 recipes as cards: title, a chip per tag, minutes, servings.
- A search box and a tag chip bar. Both filters live in the query string, so
  `/?q=garlic&tag=baking` is a link that reproduces the filtered list.
- `/recipes/<id>` - the ingredients as quantity, unit and item, and the steps
  numbered in order.
- A servings stepper. Moving it from 4 to 6 rewrites every quantity; moving it
  back to 4 restores the recipe exactly, `1/3 tsp` to `1/2 tsp` to `1/3 tsp`,
  with no drift. That is session 4 and it is the payoff.

## Run it

```bash
cd <the skeleton you hand out>
npm install
npm run dev          # http://localhost:3000
```

`npm run build` before a demo if you want the production numbers. The store is
read on every request, so no restart is needed after editing
`data/recipes.json`.

## The shape of the project

| File | What it holds | Cuts in it |
|---|---|---|
| `lib/types.ts` | `Quantity`, `Ingredient`, `Recipe` | none, ships written |
| `data/recipes.json` | the 8 seed recipes | none, ships written |
| `lib/store.ts` | `readAllRecipes`, `findRecipe` | `cut-store-read-all` (s1), `cut-store-find-one` (s3) |
| `lib/fractions.ts` | `gcd`, `formatQuantity`, `scaleQuantity` | `cut-fraction-scale` (s4) |
| `app/api/recipes/route.ts` | `GET /api/recipes` | `cut-api-recipes-filter` (s2) |
| `app/api/tags/route.ts` | `GET /api/tags` | `cut-api-tags-list` (s2) |
| `app/api/recipes/[id]/route.ts` | `GET /api/recipes/[id]` | `cut-api-recipe-get` (s3) |
| `app/page.tsx` | server component, `<Suspense>` boundary | none, ships written |
| `app/RecipeList.tsx` | the whole list screen | 4 cuts, sessions 1 and 2 |
| `app/recipes/[id]/page.tsx` | fetches one recipe, branches on status | `cut-recipe-fetch` (s3) |
| `app/recipes/[id]/RecipeView.tsx` | the loaded recipe and the stepper | 3 cuts, sessions 3 and 4 |

14 cut points across 4 sessions: 3 / 4 / 4 / 3.

## How the skeleton behaves

Every cut is a block **inside** a function. The `return` always sits outside the
markers, with a typed fallback above it, so **the skeleton compiles from minute
one**. A student never faces a project that will not build.

```ts
export function readAllRecipes(): Recipe[] {
  let recipes: Recipe[] = []                 // ships written
  // TODO(cut-store-read-all): ...
  return recipes                             // ships written
}
```

Two consequences worth knowing before a class asks:

- `GET /api/recipes` **ships fully written** and answers `200` with `[]` until
  `cut-store-read-all` is filled. So on the very first run the list screen says
  `No recipes match`, not `Loading recipes`. That is correct.
- `GET /api/tags` and `GET /api/recipes/[id]` answer `501` while their block is
  open. The screens treat a non-200, non-404 reply as "still loading", so the
  tag bar is simply empty and the recipe page sits on `Loading recipe`.

## Grading

22 acceptance criteria, `c-<session>-<k>`. Every one is a script check against a
running app. The verifier reads the page through eight `data-testid` hooks -
`recipe-card`, `card-tag`, `card-minutes`, `card-serves`, `filter-tag`,
`ingredient-row`, `step`, `servings-count` - and controls by their accessible
name: `Search recipes`, `Fewer servings`, `More servings`,
`Back to all recipes`. **No criterion reads a CSS class name**, because CSS
modules hash them. If a student renames a testid, their tests go red; tell them
the testid is part of the contract, like a function name.

### Two criteria you must never present on their own

`c-3-2` (404 from the endpoint) and `c-3-5` (`Recipe not found` on screen) both
go green with `cut-store-find-one` **still open**, because `findRecipe`'s
fallback `return null` and a genuine miss are indistinguishable from outside.
They also go green with `cut-store-read-all` open. In any per-cut checkpoint,
pair `c-3-2` with `c-3-1` and `c-3-5` with `c-3-3`. Never say "your 404 works,
so your store lookup works" - it does not follow.

Every other criterion needs all of its listed cuts filled. That was checked cut
by cut, not assumed.

## Files in this pack

| File | For |
|---|---|
| `README.md` | this page |
| `session-1.md` | the recipe list |
| `session-2.md` | search and tag filter |
| `session-3.md` | one recipe in full - **reads 45 minutes, see the note** |
| `session-4.md` | scale the servings |
| `troubleshooting.md` | every error a student will actually hit |
