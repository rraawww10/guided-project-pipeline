# Recipe Box

**Track:** fullstack · **Sessions:** 4 · **Stack:** Next.js 15 (App Router), React 19,
TypeScript, plain CSS modules · **Source material:** none

## Outcome

A recipe library a student can browse, search and re-scale, running offline from a
JSON file on disk. Four sessions, and something runs at the end of each one.

At the end of session 4 a student has:

- A list screen at `/` showing all 8 seed recipes, each card carrying its title, a
  chip per tag, how many minutes it takes and how many it serves.
- A search box and a row of tag chips. Typing narrows the list by title, clicking a
  chip narrows it by tag, and the two narrow together. Both live in the page query
  string, so `/?q=garlic&tag=baking` is a link that reproduces the filtered list.
- A recipe screen at `/recipes/<id>` with the ingredients, each as quantity, unit and
  item, and the steps numbered in order.
- A servings stepper on that screen. Moving it from 4 to 6 rewrites every quantity
  on screen, and moving it back to 4 restores the recipe exactly as written: 1/3 tsp
  becomes 1/2 tsp and then 1/3 tsp again, with no drift.
- Three route handlers over one JSON file. Nothing is written back to disk.

The payoff is session 4. It is the first time in the track that the number on the
screen is computed from React state rather than read from a server response, and a
student can see in one click whether the arithmetic is right.

## Out of scope

- Adding, editing or deleting a recipe. The box is read-only. There is no POST, PUT,
  PATCH or DELETE handler in the project.
- Accounts, sign-in, anything per-user.
- Images. Recipes are text.
- A database. `data/recipes.json` is the store, and that is deliberate.
- Converting units, pluralising unit names, or translating grams to cups. A unit is
  the string that is stored and it is printed unchanged.
- Saving the servings choice. It lives in React state and returns to the recipe's own
  serves count when the page is reloaded.
- A state library and a CSS framework. React state, the URL, and CSS modules only.

One note for Gate 1. The idea's first scope bullet says the JSON file is "read and
written through route handlers", while the idea's own out-of-scope list rules out
adding, editing and deleting recipes. This spec follows the out-of-scope list and
keeps the store read-only. That is the single place the spec narrows the idea, and it
is a decision to confirm now rather than a surprise in session 5.

## Data model

One file, `data/recipes.json`, holding an array of 8 recipes. Types live in
`lib/types.ts` and are shared by the route handlers and the screens.

```ts
type Quantity = { num: number; den: number }   // stored already reduced, den >= 1

type Ingredient = {
  item: string        // "olive oil"
  quantity: Quantity  // 2 tbsp is { num: 2, den: 1 }
  unit: string        // "g", "tbsp", "tsp", "cup", "clove"; "" for a plain count
}

type Recipe = {
  id: string          // kebab-case, and the URL segment: "lemon-garlic-pasta"
  title: string
  tags: string[]      // one or more of the five tags
  minutes: number
  serves: number      // the servings the stored quantities are written for
  ingredients: Ingredient[]
  steps: string[]
}
```

**Reading the store.** `lib/store.ts` exports two functions and no others:
`readAllRecipes(): Recipe[]`, which reads and parses `data/recipes.json`, and
`findRecipe(id: string): Recipe | null`. Both read the file on every call. Neither
writes.

**The five tags,** in the alphabetical order `GET /api/tags` returns them:
`baking`, `one-pot`, `quick`, `spicy`, `vegetarian`.

**The 8 seed recipes.** These ids, titles, tags, minutes and serves are fixed, because
the acceptance criteria count rows against them.

| id | title | tags | minutes | serves |
|---|---|---|---|---|
| `lemon-garlic-pasta` | Lemon Garlic Pasta | quick, vegetarian | 20 | 4 |
| `chickpea-curry` | Chickpea Curry | one-pot, spicy, vegetarian | 35 | 4 |
| `banana-bread` | Banana Bread | baking, vegetarian | 60 | 8 |
| `chicken-noodle-soup` | Chicken Noodle Soup | one-pot | 40 | 6 |
| `chilli-prawn-rice` | Chilli Prawn Rice | one-pot, quick, spicy | 25 | 3 |
| `pesto-pasta-salad` | Pesto Pasta Salad | quick, vegetarian | 15 | 6 |
| `beef-stew` | Beef Stew | one-pot | 90 | 6 |
| `garlic-flatbread` | Garlic Flatbread | baking, quick | 40 | 4 |

Two titles contain "garlic" and two recipes are tagged `baking`, and only
`garlic-flatbread` is both. That is what the filter criteria in session 2 count.

**`lemon-garlic-pasta` in full,** because sessions 3 and 4 assert on its rows:

| item | quantity | unit |
|---|---|---|
| spaghetti | 400/1 | g |
| olive oil | 2/1 | tbsp |
| garlic | 4/1 | clove |
| chilli flakes | 1/3 | tsp |
| lemon | 1/1 | *(empty)* |
| flat-leaf parsley | 1/2 | cup |
| salt | 1/2 | tsp |

Its 4 steps, stored in this order, each printed as it is written:

1. `Boil the spaghetti in salted water until it still has a bite.`
2. `Warm the oil in a wide pan with the sliced garlic and the chilli flakes.`
3. `Toss the drained spaghetti through the oil with the lemon juice and the parsley.`
4. `Taste, add the salt, and serve.`

Every other recipe carries 5 to 9 ingredients and 3 to 7 steps, and at least two of
its ingredients have a denominator of 2, 3 or 4, so scaling shows fractions rather
than whole numbers alone.

**Printing a quantity.** `formatQuantity` in `lib/fractions.ts` ships written; it is
not a cut point. It reduces first, then prints:

- `den` is 1 → the numerator alone: `{ num: 600, den: 1 }` → `600`
- `num` is smaller than `den` → a fraction: `{ num: 1, den: 3 }` → `1/3`
- otherwise a mixed number: `{ num: 3, den: 2 }` → `1 1/2`

An ingredient prints as one line of text: the quantity, then the unit when the
ingredient has one, then the item. `2 tbsp olive oil`, `1/3 tsp chilli flakes`, and -
for the one ingredient of `lemon-garlic-pasta` whose unit is the empty string - `1
lemon`, with no gap where the unit would be. 6 of that recipe's 7 rows carry a unit.

**Scaling, and why it does not drift.** A scaled quantity is always computed from the
stored quantity and the recipe's own `serves`, never from the quantity on screen:
`scaleQuantity(stored, recipe.serves, servings)` multiplies by `servings / serves` as
whole numbers and reduces with the greatest common divisor. Halves and thirds stay
exact, and 4 → 6 → 4 lands back on the stored value. `gcd` ships written next to it;
the multiply-and-reduce is `cut-fraction-scale`.

## Endpoints

All three are GET. The store is read on every request; nothing writes to disk.

| id | method | path | request | response | status | built |
|---|---|---|---|---|---|---|
| `ep-recipes-list` | GET | `/api/recipes` | optional `q` and `tag` query parameters | `Recipe[]` | 200 | session 1, filtering added in session 2 |
| `ep-tags-list` | GET | `/api/tags` | none | `string[]` | 200 | session 2 |
| `ep-recipe-get` | GET | `/api/recipes/[id]` | none | `Recipe` | 200, 404 | session 3 |

`GET /api/recipes` returns whole `Recipe` objects, ingredients and steps included.
There is no separate summary type; the list screen reads the fields it shows.

`q` matches a substring of the title, ignoring letter case. `tag` matches one tag
exactly. A parameter that is missing or empty narrows nothing, so bare
`GET /api/recipes` returns all 8. `GET /api/recipes/[id]` answers 404 with a JSON body
holding an `error` field when the id is not in the store.

## Screens

Both screens are read by tests through their markup, so every element a criterion
counts or reads carries a `data-testid`. These eight are the whole list. No criterion
depends on a CSS class name: CSS modules hash class names at build time, and a hashed
name is not something a test can select on.

| testid | screen | what one element holds |
|---|---|---|
| `recipe-card` | sc-list | one per recipe in the grid |
| `card-tag` | sc-list | one per tag of that card's recipe, the tag name as its text |
| `card-minutes` | sc-list | the minutes and the word min: `20 min` |
| `card-serves` | sc-list | the word Serves and the count: `Serves 4` |
| `filter-tag` | sc-list | one per tag in the filter bar, the tag name as its text |
| `ingredient-row` | sc-recipe | one per ingredient: quantity, unit and item on one line |
| `step` | sc-recipe | one per step: its position, a full stop, then the step text |
| `servings-count` | sc-recipe | the servings number the stepper is on |

Controls are found by their accessible name: `Search recipes` on the search box,
`Fewer servings` on the minus control, `More servings` on the plus control, and
`Back to all recipes` on the back link. Two cut points render marked-up elements -
`cut-list-cards` and `cut-recipe-rows` - and each names the testids its block must
render in the hint the student reads. Every other testid ships written.

**`sc-list`** at route `/`. States: `loading`, `loaded`, `empty`.

Elements: a search box, a tag chip filter bar built from `GET /api/tags`, a grid of
recipe cards, and a card per recipe showing its title, a chip per tag, its minutes and
its serves count. Each card is a link to `/recipes/<id>`.

Only the filter bar's chips are interactive: they are buttons and they carry
`filter-tag`. The chips on a card are text, they carry `card-tag`, and clicking one
follows the card's link like the rest of the card. `c-2-6` clicks the filter bar's
chip.

The tag bar's own `GET /api/tags` call ships written in `app/RecipeList.tsx`, outside
every cut, and renders no chips when the reply is not a 200. The bar is therefore
empty until session 2 fills `cut-api-tags-list`, and the cards session 1 is graded on
are unaffected by it.

The list screen passes its own query string straight to the endpoint: it reads
`useSearchParams()`, sends the same string to `/api/recipes?...`, and refetches when
the string changes. The search box and the chips write to the URL; the URL drives the
fetch. Nothing else holds the filter. Both controls write with `router.replace` on
every change - no debounce, no submit button, no Enter key to press - and the search
box takes its value from `useSearchParams`, so `/?q=garlic` opens with `garlic`
already in the box. When the last parameter is dropped the URL is replaced with `/`,
not `/?`.

In the `loading` state, before the first reply arrives, the screen displays
`Loading recipes` and no grid. In the `empty` state, when the reply is an empty array
- a search text no title contains, a tag no recipe carries, or the two together - the
grid is replaced by the message `No recipes match`. Both branches ship written,
outside every cut, so a student who has not yet filled `cut-list-cards` still sees
them.

Files: `app/page.tsx` is a server component that renders `app/RecipeList.tsx` inside a
`<Suspense>` boundary, because `RecipeList` is a client component and reads
`useSearchParams`. All four list cut points live in `app/RecipeList.tsx`.

**`sc-recipe`** at route `/recipes/[id]`. States: `loading`, `loaded`, `not-found`.

Elements: a header with the title, a chip per tag, the minutes as `20 min` and the
recipe's stored serves as `Written for 4`; a servings stepper of a minus control, the
`servings-count` number and a plus control; one ingredient row per ingredient; the
steps as a numbered list; and a back link to `/`. The header spells its serves out as
`Written for 4` so that `servings-count` is the only element on the screen whose text
is a bare servings number.

`RecipeView` derives `rows` on every render: one `{...ingredient}` copy per stored
ingredient, in stored order. It renders from `rows`, never from `recipe.ingredients`
directly, and nothing writes back into `recipe.ingredients`. Because `rows` is rebuilt
from the fetched recipe every render, the quantity a row starts from is always the
stored one - which is why 4 to 6 to 4 lands back on the recipe as written.

Each `step` element prints its position, a full stop, a space, then the stored step
text, so the first step at `/recipes/lemon-garlic-pasta` reads
`1. Boil the spaghetti in salted water until it still has a bite.` A number drawn by
the list's own CSS marker is not text a test can read, which is why the position is
printed.

In the `loading` state the screen displays `Loading recipe`. The `not-found` state
displays `Recipe not found` and the back link. Both branches ship written, outside
every cut.

Files: `app/recipes/[id]/page.tsx` is a client component that reads the id with
`useParams` and fetches the recipe; `app/recipes/[id]/RecipeView.tsx` holds the
servings state and renders the loaded recipe. The stepper controls stay clickable at
every count: the clamp to 1 and 24 lives in the state setter, not in a disabled
attribute.

## Sessions

Session 1 and 2 finish the list screen, session 3 and 4 finish the recipe screen. One
milestone each, and each session ends with something a student can run.

Four rules the final code follows, so the generated skeleton behaves:

1. A cut point is a block inside a function, and the code around it compiles while the
   block is a hint comment. No cut removes a declaration that code outside it uses:
   where a block produces a value the code below it reads, the variable is declared
   above the opening marker and the block assigns to it. `cut-list-cards` assigns its
   card elements to a `ReactNode[]` declared above the marker, and the component's
   `return` renders that variable.
2. A later session's cut must leave the earlier sessions' criteria passing. The route
   handler holds `let shown = all` before `cut-api-recipes-filter`, and each ingredient
   row is a copy of the stored ingredient before `cut-recipe-scale-quantity` replaces
   the copy's quantity. With those blocks still open, session 1 returns all 8 recipes
   and session 3 shows the stored quantities.
3. Each cut id appears exactly once in the final code, between its markers.
4. A cut that would otherwise remove its function's only `return` keeps a typed
   fallback return outside the markers, as the last statement of the function:
   `return []` in `readAllRecipes`, `return null` in `findRecipe`, `return stored` in
   `scaleQuantity`, and
   `return NextResponse.json({ error: 'not implemented' }, { status: 501 })` in each of
   the three route handlers. The skeleton then typechecks, and only the criteria of the
   session that owns the open block fail. Once a block is filled the fallback below it
   is unreachable and stays in the file, because the cutter replaces only what lies
   between the markers. 501 belongs to the skeleton alone: in the finished project
   every block is written and the endpoints answer only the statuses in the table
   above.

### Session 1 - The recipe list

**Goal.** Serve every recipe from the JSON store through a route handler and render
one card per recipe on the list screen.

**Teaches.** Route handlers in the App Router; reading a JSON file on the server with
node fs; typing a response with a shared TypeScript type; fetching into React state
with useEffect; rendering a list with map and keys.

**Builds.** `ep-recipes-list`, `sc-list`.

**Acceptance criteria.**

- `c-1-1` GET /api/recipes returns 200 with a JSON array of the 8 seed recipes —
  cuts `cut-store-read-all`, `cut-api-recipes-list`
- `c-1-2` GET /api/recipes returns each recipe with an id, a title, a tags array, a
  minutes number and a serves number — cuts `cut-store-read-all`,
  `cut-api-recipes-list`
- `c-1-3` sc-list renders one recipe-card element per recipe, 8 of them for the 8 seed
  recipes — cuts `cut-list-fetch`, `cut-list-cards`
- `c-1-4` sc-list displays the title Lemon Garlic Pasta on a recipe-card whose
  card-minutes element reads 20 min and whose card-serves element reads Serves 4 —
  cut `cut-list-cards`
- `c-1-5` sc-list renders one card-tag element per tag of that recipe on every card,
  2 on the Lemon Garlic Pasta card reading quick and vegetarian — cut `cut-list-cards`

**Cut points.**

- `cut-store-read-all` in `lib/store.ts` — Read the recipes JSON file from disk and
  return every recipe in it as an array of Recipe objects.
- `cut-api-recipes-list` in `app/api/recipes/route.ts` — Send the recipes the handler
  has back to the browser as a JSON array with status 200.
- `cut-list-fetch` in `app/RecipeList.tsx` — Ask the recipes endpoint for the list,
  passing the page query string straight through, and put the array it answers with
  into state.
- `cut-list-cards` in `app/RecipeList.tsx` — Turn the recipes array into one
  recipe-card element per recipe, each one a link to that recipe page holding its
  title, a card-tag element per tag, its minutes in a card-minutes element and its
  serves count in a card-serves element.

### Session 2 - Search and tag filter

**Goal.** Filter the list by title text and by one tag inside the route handler, and
keep both choices in the page URL.

**Teaches.** Reading searchParams inside a route handler; case-insensitive substring
matching; deriving a distinct sorted list with Set and flatMap; useSearchParams and
router.replace; keeping screen state in the URL so a filtered list is a link.

**Builds.** `ep-tags-list`. Extends `ep-recipes-list` and `sc-list` from session 1.

**Acceptance criteria.**

- `c-2-1` GET /api/recipes?q=garlic returns 200 with the 2 recipes whose title
  contains garlic in any letter case — cut `cut-api-recipes-filter`
- `c-2-2` GET /api/recipes?tag=baking returns 200 with the 2 recipes tagged baking —
  cut `cut-api-recipes-filter`
- `c-2-3` GET /api/recipes?q=garlic&tag=baking returns 200 with 1 recipe, Garlic
  Flatbread — cut `cut-api-recipes-filter`
- `c-2-4` GET /api/tags returns 200 with the JSON array baking, one-pot, quick, spicy,
  vegetarian in alphabetical order — cut `cut-api-tags-list`
- `c-2-5` sc-list renders 2 recipe-card elements and the page URL reads /?q=garlic
  after garlic is typed into the search box — cuts `cut-list-search-url`,
  `cut-api-recipes-filter`
- `c-2-6` sc-list renders 2 recipe-card elements and the page URL reads /?tag=baking
  after the filter-tag chip reading baking is clicked, then renders 8 and the URL reads
  / after that same filter-tag chip is clicked a second time — cuts
  `cut-list-tag-toggle`, `cut-api-recipes-filter`

**Cut points.**

- `cut-api-recipes-filter` in `app/api/recipes/route.ts` — Keep only the recipes whose
  title contains the q parameter, ignoring letter case, and whose tags include the tag
  parameter; a parameter that is missing or empty narrows nothing.
- `cut-api-tags-list` in `app/api/tags/route.ts` — Collect the tags of every recipe
  into one list without duplicates, sort it alphabetically and return it as a JSON
  array of strings.
- `cut-list-search-url` in `app/RecipeList.tsx` — Write the text of the search box into
  the q parameter of the page URL, and take q out of the URL when the box is emptied.
- `cut-list-tag-toggle` in `app/RecipeList.tsx` — Put the clicked tag into the tag
  parameter of the page URL, and take tag out of the URL when the chip that is already
  active is the one clicked.

### Session 3 - One recipe in full

**Goal.** Open one recipe at its own route with its ingredients and its steps, and
answer 404 for an id the store does not hold.

**Teaches.** Dynamic route segments for pages and route handlers; returning 404 with a
JSON body from a route handler; reading the route id with useParams; branching on the
response status in a client component; rendering a not-found state.

**Builds.** `ep-recipe-get`, `sc-recipe`.

**Acceptance criteria.**

- `c-3-1` GET /api/recipes/lemon-garlic-pasta returns 200 with that recipe, its 7
  ingredients and its 4 steps — cuts `cut-store-find-one`, `cut-api-recipe-get`
- `c-3-2` GET /api/recipes/not-a-recipe returns 404 with a JSON body holding an error
  field — cuts `cut-store-find-one`, `cut-api-recipe-get`
- `c-3-3` sc-recipe renders one ingredient-row element per ingredient, 7 at
  /recipes/lemon-garlic-pasta, the olive oil row reading 2 tbsp olive oil and the lemon
  row reading 1 lemon — cuts `cut-recipe-fetch`, `cut-recipe-rows`
- `c-3-4` sc-recipe renders 4 step elements in stored order at
  /recipes/lemon-garlic-pasta, the text of the first beginning 1. Boil the spaghetti —
  cut `cut-recipe-fetch`
- `c-3-5` sc-recipe displays the message Recipe not found at the route
  /recipes/not-a-recipe — cut `cut-recipe-fetch`

**Cut points.**

- `cut-store-find-one` in `lib/store.ts` — Return the recipe whose id matches the one
  asked for, or null when the store holds no recipe with that id.
- `cut-api-recipe-get` in `app/api/recipes/[id]/route.ts` — Reply with the recipe as
  JSON and status 200 when the store finds it, and with status 404 and a JSON body
  holding an error field when the store finds nothing.
- `cut-recipe-fetch` in `app/recipes/[id]/page.tsx` — Ask the endpoint for the recipe
  named in the route, put it into state on a 200 reply, and move the page to its
  not-found state on a 404 reply.
- `cut-recipe-rows` in `app/recipes/[id]/RecipeView.tsx` — Render one ingredient-row
  element for every entry in rows, its text reading the formatted quantity, then the
  unit when that ingredient has one, then the item name.

### Session 4 - Scale the servings

**Goal.** Compute every ingredient quantity from the servings number held in React
state, so raising the count and lowering it again returns the recipe to the quantities
it was written with.

**Teaches.** Deriving what is on screen from state instead of from the server; exact
fraction arithmetic with a numerator and a denominator; reducing a fraction with the
greatest common divisor; clamping a value inside a state setter; scaling from the
stored value every time rather than from the value on screen.

**Builds.** No new endpoint and no new screen. Extends `sc-recipe`: the stepper starts
working and the ingredient rows start computing.

**Acceptance criteria.**

- `c-4-1` sc-recipe displays 6 in the servings-count element after the plus control is
  clicked twice at /recipes/lemon-garlic-pasta, which is stored as serves 4 —
  cut `cut-recipe-servings`
- `c-4-2` sc-recipe displays an ingredient-row reading 3 tbsp olive oil at 6 servings,
  where the stored quantity is 2 tbsp at serves 4 — cuts `cut-recipe-servings`,
  `cut-fraction-scale`, `cut-recipe-scale-quantity`
- `c-4-3` sc-recipe displays an ingredient-row reading 1/2 tsp chilli flakes at 6
  servings, where the stored quantity is 1/3 tsp at serves 4 — cuts
  `cut-recipe-servings`, `cut-fraction-scale`, `cut-recipe-scale-quantity`
- `c-4-4` sc-recipe displays an ingredient-row reading 1/2 tsp chilli flakes after the
  servings count is raised from 4 to 6, then one reading 1/3 tsp chilli flakes again
  after it is lowered back to 4 — cuts `cut-recipe-servings`, `cut-fraction-scale`,
  `cut-recipe-scale-quantity`
- `c-4-5` sc-recipe displays 1 in the servings-count element after the minus control is
  clicked while the servings count is 1 — cut `cut-recipe-servings`
- `c-4-6` sc-recipe displays 24 in the servings-count element after the plus control is
  clicked 21 times at /recipes/lemon-garlic-pasta, which is stored as serves 4 —
  cut `cut-recipe-servings`

**Cut points.**

- `cut-fraction-scale` in `lib/fractions.ts` — Multiply the quantity by the target
  servings over the base servings, then divide the numerator and the denominator by
  their greatest common divisor.
- `cut-recipe-servings` in `app/recipes/[id]/RecipeView.tsx` — Put the requested number
  into the servings state, holding it at 1 when it would drop below 1 and at 24 when it
  would climb above 24.
- `cut-recipe-scale-quantity` in `app/recipes/[id]/RecipeView.tsx` — Replace the
  quantity of the row copy with the stored quantity of that ingredient scaled from the
  recipe's serves count to the servings count on screen.
