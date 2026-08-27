# Session 3 - One recipe in full

**Time:** 45 minutes as planned below - **5 minutes over the cap.** Read the next
section before you teach this.
**Students start from:** `/` with a working list and both filters. Clicking a
card 404s.
**Students end with:** `/recipes/lemon-garlic-pasta` showing the header, the
ingredients with quantities and units, the steps numbered in order, and
`/recipes/not-a-recipe` showing `Recipe not found` with a way back.

## This session does not fit

Session 3 introduces **three new files** and still carries the **maximum four
cut points**. The other sessions: session 2 adds one small route file for four
cuts, session 4 adds no file at all for three. Timed block by block the plan
below comes to 45 minutes, and the expensive part is not the cuts - it is the
8-minute tour of `RecipeView.tsx`, the largest written component in the project.

**Pick one before the session starts:**

1. **Ship `cut-store-find-one` written** (recommended, one minute of work).
   Open `lib/store.ts` in the skeleton you hand out and replace the TODO on
   line 26 with `recipe = recipes.find((c) => c.id === id) ?? null`. Session 3
   drops to three cuts and the plan lands at 41 minutes. You lose the least by
   cutting this one: it is a one-line lookup, and `c-3-2` and `c-3-5` already
   grade it only weakly (see below). Tell students it is written and why.
2. **Pre-read the file tour.** Send `RecipeView.tsx` out as homework after
   session 2 and open the session at minute 4 with questions instead of a tour.
   Saves 5-6 minutes if they actually read it.
3. **Split it.** Sessions 3a (the endpoint and the fetch) and 3b (the rows).
   Cleanest for learning, but it makes the course five sessions.

Do not solve it by rushing `cut-recipe-fetch`. It is the session's real content.

## What they learn

1. Dynamic route segments - `[id]` for both a page and a route handler.
2. Returning a 404 with a JSON body from a route handler.
3. Reading the route id with `useParams`.
4. Branching on the response status in a client component.
5. Rendering a not-found state that is not a crash.

## Before you start

- Sessions 1 and 2 green.
- Have `/api/recipes/lemon-garlic-pasta` and `/api/recipes/not-a-recipe` ready
  to paste.
- Know these numbers: `lemon-garlic-pasta` has **7 ingredients** and **4 steps**.
  The olive oil row reads `2 tbsp olive oil`. The lemon row reads `1 lemon` -
  with no gap - because its unit is the empty string. 6 of the 7 rows have a
  unit.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Recap. Click a card, get the 404, and name what is missing: a page at that route and an endpoint behind it. |
| 4-12 | Tour the three new files. `app/api/recipes/[id]/route.ts` (small). `app/recipes/[id]/page.tsx` - the three statuses and which branch each renders. `app/recipes/[id]/RecipeView.tsx` - do not read it line by line; point at four things: `rows`, the `ingredientRows` variable, the stepper (inert this session), and `data-testid="step"` already written. |
| 12-16 | `cut-store-find-one`. One line. Or skip if you shipped it written. |
| 16-25 | `cut-api-recipe-get`. The 200 branch and the 404 branch. Test both URLs in the browser. |
| 25-36 | `cut-recipe-fetch`. The longest block of the session. Now the page loads. |
| 36-45 | `cut-recipe-rows`. Rows appear. Demo `/recipes/not-a-recipe`. Recap. |

## Cut points in this session

### cut-store-find-one - `lib/store.ts`:26

- **What students see:**
  `// TODO(cut-store-find-one): Return the recipe whose id matches the one asked for, or null when the store holds no recipe with that id.`
- **What they write:** one line - `.find` over the recipes for a matching `id`,
  with `?? null` so a miss is `null` rather than `undefined`, assigned to the
  `recipe` variable above the TODO.
- **Teach it like this:** "`readAllRecipes` is already called for you on the line
  above. `.find` gives you `Recipe | undefined`, and our return type says
  `Recipe | null`, so `?? null` bridges the two. That distinction is not
  pedantry - `undefined` and `null` serialise differently to JSON."
- **Passes when:** nothing on its own. Say so. `c-3-1` needs
  `cut-api-recipe-get` too.

### cut-api-recipe-get - `app/api/recipes/[id]/route.ts`:19

- **What students see:**
  `// TODO(cut-api-recipe-get): Reply with the recipe as JSON and status 200 when the store finds it, and with status 404 and a JSON body holding an error field when the store finds nothing.`
- **What they write:** call `findRecipe(id)`; if it is `null` return
  `NextResponse.json({ error: ... }, { status: 404 })`; otherwise return
  `NextResponse.json(recipe)`.
- **Teach it like this:** "`const { id } = await params` is already done above -
  in Next 15 params is a promise, and that catches people. Two exits from this
  block, and both are real returns, which is different from every other cut in
  this project. The 501 return below your block is unreachable once you are
  done; leave it there."
- **The 404 must carry a JSON body.** A bare `new Response(null, {status:404})`
  fails `c-3-2`, which reads an `error` field.
- **Passes when:** `c-3-1` and `c-3-2` go green.

### cut-recipe-fetch - `app/recipes/[id]/page.tsx`:24

- **What students see:**
  `// TODO(cut-recipe-fetch): Ask the endpoint for the recipe named in the route; on a 200 reply put the recipe into state and set the status to loaded, and on a 404 reply set the status to not-found.`
- **What they write:** `fetch` to `/api/recipes/${id}`; if the status is 404 set
  status `not-found` and stop; if the status is not 200 do nothing at all; on a
  200 read the JSON, `setRecipe`, then `setStatus('loaded')`.
- **Teach it like this:** "Three cases, and the third is the interesting one. 404
  is a real answer - the server is telling you the recipe is not there, so show
  `Recipe not found`. 200 is the happy path. Anything else - a 500, or the 501
  this endpoint gave before you wrote it - we deliberately ignore, so the page
  stays on `Loading recipe`. A broken server should not look the same as a
  missing recipe."
- **Order matters:** `setRecipe` before `setStatus('loaded')`, or the loaded
  branch renders for one frame with `recipe` still null. The written code guards
  against it anyway, but the habit is the lesson.
- **Passes when:** `c-3-4` and `c-3-5` go green. The steps appear now, because
  the step elements ship written - that surprises students, so point out that
  `c-3-4` does not need `cut-recipe-rows`.

### cut-recipe-rows - `app/recipes/[id]/RecipeView.tsx`:38

- **What students see:**
  `` // TODO(cut-recipe-rows): Render one ingredient-row element for every entry in rows, its text reading `formatQuantity` of that row's quantity, then the unit when that ingredient has one, then the item name. ``
- **What they write:** `ingredientRows = rows.map(...)` producing an `<li>` per
  row with `data-testid="ingredient-row"`, whose text is the three parts -
  `formatQuantity(row.quantity)`, `row.unit`, `row.item` - with the empty ones
  dropped and the rest joined by a single space.
- **Teach it like this:** "`formatQuantity` is written for you - it turns
  `{num:1,den:3}` into `1/3`. Call it, do not print `num/den` by hand, or
  `2/1 tbsp olive oil` is what you will get. And one ingredient has no unit: the
  lemon. If you join blindly you get `1  lemon` with two spaces. Build the three
  parts, drop the empty ones, then join."
- **Assign to `ingredientRows`.** A fresh variable renders nothing, silently.
- **Passes when:** `c-3-3` goes green.

## Two criteria that do not prove what they look like

`c-3-2` and `c-3-5` both go green with **`cut-store-find-one` still open** -
`findRecipe`'s fallback `return null` gives a 404 for every id, exactly like a
genuine miss. They also go green with `cut-store-read-all` open.

So in a per-cut checkpoint: pair `c-3-2` with `c-3-1`, and `c-3-5` with `c-3-3`.
If a student's `c-3-2` is green and `c-3-1` is red, the likely cause is that the
store lookup does nothing and **every** id is 404ing - which looks like success
on the not-found test. Open `/recipes/lemon-garlic-pasta`: if it says
`Recipe not found`, that is the bug.

## Where students get stuck

- **`params.id` is undefined in the route handler** - Next 15 makes `params` a
  promise. The `await` is already written; if they retyped the signature they
  may have dropped it.
- **The page sits on `Loading recipe` forever** - either `cut-recipe-fetch` is
  still open, or the endpoint is answering something that is neither 200 nor
  404. Check the network tab for a 501 and go back to `cut-api-recipe-get`.
- **`/recipes/not-a-recipe` also sits on `Loading recipe`** - they handled 200
  but not 404.
- **Every recipe says `Recipe not found`** - `findRecipe` is returning null for
  everything. See the paragraph above.
- **`1  lemon` with a double space, or `1 lemon` failing the test** - the empty
  unit. Filter the empty parts before joining.
- **`2/1 tbsp olive oil`** - they formatted the fraction by hand instead of
  calling `formatQuantity`.
- **Rows appear twice, or in the wrong order** - they mapped
  `recipe.ingredients` instead of `rows`. It looks identical today; it will break
  session 4, because `rows` is where the scaling lands.
- **`Cannot read properties of null (reading 'ingredients')`** - they rendered
  `RecipeView` outside the loaded branch. `RecipeView` mounts only when
  `status === 'loaded'`, which is what makes `recipe.serves` safe as an initial
  state value in session 4.
- **The steps show before they wrote anything** - correct, they ship written.

## Check before moving on

`/recipes/lemon-garlic-pasta` shows 7 ingredient rows and 4 numbered steps, the
olive oil row reads `2 tbsp olive oil`, the lemon row reads `1 lemon`.
`/recipes/not-a-recipe` shows `Recipe not found` and a working back link.
`c-3-1` through `c-3-5` green, sessions 1 and 2 still green. The stepper is on
screen and does nothing - that is session 4.
