# Troubleshooting

Errors students actually hit on this project, in the order they hit them. Each
one is a real failure mode of this code, not a generic React problem.

## Getting started

**`npm install` prints a security advisory for `next`**
Read the message, not just the exit code. This project pins `next 15.5.24`,
which is not the version carrying CVE-2025-66478. If you see an advisory naming
a version you did not install, it is about a transitive dependency; if it names
`next` itself, stop and tell whoever maintains the pack.

**`npm run dev` fails with an EADDRINUSE on 3000**
Something else is on the port. `npm run dev -- --port 3001`, and remember the
URL for the rest of the session.

**The page is blank and the terminal shows a TypeScript error**
The skeleton compiles as handed out - every cut keeps its function's `return`
outside the block. So a compile error means something was deleted that was not
part of a TODO. Restore the file from the original skeleton rather than debug it.

## Session 1

**`Module not found: Can't resolve 'fs'`**
`node:fs` was imported into a client component - almost always
`app/RecipeList.tsx`. Only `lib/store.ts` and files under `app/api/` run on the
server and may touch the disk.

**`ENOENT: no such file or directory, open '.../data/recipes.json'`**
A relative path. Use `path.join(process.cwd(), 'data', 'recipes.json')`.
`process.cwd()` is where `npm run dev` was started, which is the project root.

**`/api/recipes` returns `[]` and no error**
That is the shipped behaviour before `cut-store-read-all` is filled. The handler
is written; the store is not. Not a bug.

**`/` says `No recipes match` on the very first run**
Also correct, and it surprises everyone. `GET /api/recipes` ships written and
answers `200` with an empty array, so the screen reaches the "loaded but empty"
state rather than staying on `Loading recipes`.

**The list stays empty after `cut-store-read-all` works**
`cut-list-fetch` is what carries data into the page. Prove the server half in the
`/api/recipes` tab first - it stops the "nothing works" spiral.

**Cards do not appear even though the fetch runs**
They declared a new variable instead of assigning to the `cards` array that
already exists above the TODO. Nothing renders and nothing errors. Look for
`const cards =` where it should be `cards =`.

**`Each child in a list should have a unique "key" prop`**
Two `.map`s here need keys: the card and each tag chip. Use `recipe.id` and the
tag string.

**Tests fail on `20 min` or `Serves 4`**
The strings are pinned by the criteria. Not `20min`, not `20 minutes`, not
`4 servings`.

**Clicking a card 404s**
Expected until session 3.

## Session 2

**`searchParams` is undefined in the route handler**
A route handler receives a `Request`, not props. Use
`new URL(request.url).searchParams`.

**`?q=GARLIC` finds nothing but `?q=garlic` works**
Lowercase both the title and the query before comparing.

**`/api/recipes` with no parameters returns nothing**
An empty parameter must narrow nothing. Test `q === ''` explicitly rather than
relying on `includes('')`.

**The filter works at the endpoint but the page does not narrow**
They assigned to a new local instead of `shown`. The response returns `shown`.

**Typing clears the active tag chip (or clicking a chip clears the typed text)**
The defining bug of session 2. The handler rebuilt the query string from scratch.
Start from `new URLSearchParams(searchParams.toString())` and change one key.
This is what `c-2-6` exists to catch.

**The address bar reads `/?q=` after clearing the search box**
`delete` the key when the value is empty; do not `set` it to `''`.

**Typing feels laggy, or characters appear out of order**
Someone added `value={...}` to the search input. It is uncontrolled on purpose -
`defaultValue` from the URL, and the URL is never pushed back into the box.

**The card count flickers to a wrong number while typing quickly**
The stale-reply guard was dropped from `cut-list-fetch`. Six keystrokes fire six
requests; the block must write to state only while `ignore` is still clear.

**No tag chips ever appear**
`cut-api-tags-list` is still open, so `/api/tags` answers 501 and the `tags`
state stays empty. The chips are not hardcoded anywhere.

**Clicking a tag opens a recipe instead of filtering**
They clicked a chip on a card (`card-tag`, plain text inside the card's link),
not a chip in the filter bar (`filter-tag`, a real button).

## Session 3

**`params.id` is undefined**
In Next 15 `params` is a promise. `const { id } = await params` is already
written; it gets lost when students retype the function signature.

**The recipe page sits on `Loading recipe` forever**
Either `cut-recipe-fetch` is open, or the endpoint returned something that is
neither 200 nor 404 - check the network tab for the 501 and finish
`cut-api-recipe-get`. A non-200, non-404 reply deliberately leaves the status on
loading, so a broken server does not look like a missing recipe.

**`/recipes/not-a-recipe` also sits on `Loading recipe`**
The 404 branch is missing from the fetch block.

**Every recipe shows `Recipe not found`**
`findRecipe` is returning `null` for everything - usually `cut-store-find-one`
still open, or a comparison against the wrong field. Note this state makes
`c-3-2` and `c-3-5` **pass**, so never read those two as proof the lookup works.
Check `/recipes/lemon-garlic-pasta` instead.

**The 404 test fails even though the page says not found**
The 404 response needs a JSON body with an `error` field. A bare
`new Response(null, { status: 404 })` fails `c-3-2`.

**`1  lemon` with two spaces, or the lemon row failing its test**
One ingredient has `unit: ''`. Build the three parts, drop the empty ones, then
join with a single space.

**`2/1 tbsp olive oil`**
The fraction was printed by hand. Call `formatQuantity`.

**`Cannot read properties of null (reading 'ingredients')`**
`RecipeView` was rendered outside the `loaded` branch. It must mount only when
`status === 'loaded'` - that is what makes `useState(recipe.serves)` safe in
session 4.

**Steps appear before anything was written**
Correct. The step elements ship written, which is why `c-3-4` does not list
`cut-recipe-rows`.

**Ingredient rows render from the wrong array**
Map `rows`, not `recipe.ingredients`. Identical output today; breaks session 4,
because `rows` is where the scaled quantity lands.

## Session 4

**The servings number changes but no quantity moves**
Expected until `cut-recipe-scale-quantity` is written. Two of session 4's three
cuts have no visible effect alone.

**`0.5000000000000001 tsp`**
A decimal got in. Keep the numerator and the denominator as separate whole
numbers from start to finish; never compute `servings / serves` as a number.

**`6/12 tsp` instead of `1/2 tsp`**
The reduce step was skipped. Divide both parts by `gcd(num, den)`.

**Quantities drift upward and never return to the original**
They scaled `row.quantity`, which is already scaled, instead of
`ingredient.quantity`, which is the stored value. This is the bug the session
exists to prevent, and `c-4-4` is the only test that catches it.

**`NaN` in every row**
The base servings came from the wrong place. It is `recipe.serves` - the value
the recipe was written for - not the `servings` on screen.

**The count reaches 0 or 25**
The clamp arguments are the wrong way round, or the clamp was put in the button's
handler instead of inside `setServingsClamped`.

**Quantities reset to stored values on every click**
`recipe.ingredients` was mutated in place. The `{...ingredient}` copy above the
cut must stay.

**It works on Lemon Garlic Pasta but not Banana Bread**
4 was hardcoded as the base. Banana Bread is stored as serves 8. Use
`recipe.serves`.

## Grading questions students ask

**"My test is red but the page looks right."**
Read the criterion, not the screen. The tests find elements by `data-testid` and
controls by accessible name. If a testid was renamed, the test cannot see the
element. The eight testids are part of the contract: `recipe-card`, `card-tag`,
`card-minutes`, `card-serves`, `filter-tag`, `ingredient-row`, `step`,
`servings-count`.

**"Can I style it differently?"**
Yes, freely. No criterion reads a CSS class name - CSS modules hash them, so a
test could not rely on one even if it wanted to.

**"Why is there no add-recipe button?"**
The box is read-only by design; there is no POST, PUT, PATCH or DELETE handler
anywhere in the project. Adding one is a good exercise afterwards and is not
taught here.

**"Why does the tag bar show all five tags even when one recipe is showing?"**
`GET /api/tags` returns every tag in the store and never narrows with the
filter, so students can always click their way back out of a filter.
