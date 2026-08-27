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
`findRecipe(id: string): Recipe | null`, which calls `readAllRecipes` and picks from
its result. Both read the file on every call. Neither writes.

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
`GET /api/recipes` returns all 8. When both are given, a recipe must satisfy both to
be returned. `GET /api/recipes/[id]` answers 404 with a JSON body holding an `error`
field when the id is not in the store.

`GET /api/tags` takes no parameters and always returns all five tags of the whole
store. It does not narrow with the filter, so every chip in the filter bar stays on
screen and stays clickable no matter which recipes the list is showing.

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

**How a criterion pins the page URL.** Where one query parameter is set, the criterion
quotes the whole URL exactly: `/?q=garlic`, `/?tag=baking`, or `/` when the last
parameter is dropped. Where both are set, the order of the two keys depends on which
control the reader used first, so the criterion names each parameter's value on its
own - `q` set to `garlic` and `tag` set to `baking` - and a test reads them through
`searchParams` rather than comparing the joined string.

**`sc-list`** at route `/`. States: `loading`, `loaded`, `empty`.

Elements: a search box, a tag chip filter bar built from `GET /api/tags`, a grid of
recipe cards, and a card per recipe showing its title, a chip per tag, its minutes and
its serves count. Each card is a link to `/recipes/<id>`.

Only the filter bar's chips are interactive: they are buttons and they carry
`filter-tag`. The chips on a card are text, they carry `card-tag`, and clicking one
follows the card's link like the rest of the card. `c-2-5` and `c-2-6` click the
filter bar's chip.

The tag bar's own `GET /api/tags` call ships written in `app/RecipeList.tsx`, outside
every cut, and renders no chips when the reply is not a 200. The bar is therefore
empty until session 2 fills `cut-api-tags-list`, and the cards session 1 is graded on
are unaffected by it. The search box renders from session 1 too, but nothing is wired
to it until session 2 fills `cut-list-search-url`: a session-1 student can type in it
and the list will not move, and nothing session 1 is graded on depends on it.

**What holds the screen's state.** `app/RecipeList.tsx` holds exactly two pieces of
state, both declared outside every cut:

```ts
const [recipes, setRecipes] = useState<Recipe[]>([])
const [status,  setStatus]  = useState<'loading' | 'loaded'>('loading')
```

`status` starts at `'loading'` and `cut-list-fetch` is the only code in the file that
moves it. The three screen states are what the reader sees, not three values of one
variable: `loading` is `status === 'loading'`, `empty` is `status === 'loaded'` with
`recipes.length === 0`, and `loaded` is `status === 'loaded'` with at least one recipe.
The empty branch tests `recipes.length`, not the number of cards, so a student whose
`cut-list-cards` is still open sees an empty grid rather than the no-match message.
Until `cut-list-fetch` is filled the screen sits on `Loading recipes` and renders no
grid, which is what a session-1 student sees on the first run.

**Who owns the fetch.** `const qs = searchParams.toString()` ships written, the
`useEffect` call and its dependency array `[qs]` ship written, and `cut-list-fetch` is
the body of that effect. The refetch-on-URL-change behaviour that session 2 needs is
therefore already in the file when session 2 starts; the student's block is the call
itself. The effect moves `status` to `'loaded'` only when the reply is a 200, so while
`cut-api-recipes-list` is still open the endpoint's 501 leaves the screen on
`Loading recipes` instead of putting a non-array into `recipes`. `status` never
returns to `'loading'` once a reply has arrived, so a refetch leaves the cards that
are already on screen in place rather than flashing the loading message.

**Who writes the URL.** The search box and the chips write to the URL; the URL drives
the fetch. Nothing else holds the filter. Both write on every change - no debounce, no
submit button, no Enter key to press. Each control builds its next parameters from
`useSearchParams()` as the page already has them and changes only its own key, so
writing `q` leaves an active `tag` in place and clicking a chip leaves the typed `q` in
place. That is what makes `/?q=garlic&tag=baking` reachable by hand and what `c-2-6`
checks.

Turning those parameters back into a URL is not the student's problem. `RecipeList`
ships one written helper, outside every cut, and both cuts end by calling it:

```ts
function replaceQuery(params: URLSearchParams) {
  const s = params.toString()
  router.replace(s ? `/?${s}` : '/')
}
```

So the URL is replaced with `/`, not `/?`, once the last parameter is dropped, and
`cut-list-search-url` and `cut-list-tag-toggle` are each exactly the decision the
session teaches: which parameters to start from, and which single key to change.

The search box is uncontrolled. Its `defaultValue` comes from `useSearchParams`, so
`/?q=garlic` opens with `garlic` already in the box, and its `onChange` writes to the
URL. Its displayed text is never driven back from the URL, so a keystroke never waits
on a router transition to appear.

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

**What holds the screen's state.** `app/recipes/[id]/page.tsx` holds two pieces of
state, both declared outside every cut:

```ts
const [recipe, setRecipe] = useState<Recipe | null>(null)
const [status, setStatus] = useState<'loading' | 'loaded' | 'not-found'>('loading')
```

`status` starts at `'loading'` and `cut-recipe-fetch` is the only code that moves it.
`loading` displays `Loading recipe`; `not-found` displays `Recipe not found` and the
back link; `loaded` renders `RecipeView` with the fetched recipe. A reply that is
neither 200 nor 404 - the 501 the handler answers while `cut-api-recipe-get` is still
open - leaves `status` on `'loading'`. So a skeleton with `cut-recipe-fetch` open sits
on `Loading recipe` at every route, including `/recipes/not-a-recipe`, and `c-3-5`
cannot pass until that cut is filled. Both message branches ship written, outside
every cut.

**Who owns the fetch.** The id comes from `useParams`, the `useEffect` call and its
dependency array `[id]` ship written, and `cut-recipe-fetch` is the body of that
effect.

**What holds the servings.** `app/recipes/[id]/RecipeView.tsx` holds one piece of
state, declared outside every cut:

```ts
const [servings, setServings] = useState<number>(recipe.serves)
```

It starts at the recipe's own stored `serves`, so `/recipes/lemon-garlic-pasta` opens
on 4 and every session-4 criterion counts its clicks from there. `RecipeView` mounts
only in the `loaded` state, so `recipe` is never null when that initial value is read.
The minus and plus controls call `setServingsClamped(servings - 1)` and
`setServingsClamped(servings + 1)`, both written outside every cut;
`cut-recipe-servings` is the body of `setServingsClamped`. With that block open the
function does nothing and the count never leaves 4.

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

Files: `app/recipes/[id]/page.tsx` is a client component that reads the id with
`useParams` and fetches the recipe; `app/recipes/[id]/RecipeView.tsx` holds the
servings state and renders the loaded recipe. The stepper controls stay clickable at
every count: the clamp to 1 and 24 lives in the state setter, not in a disabled
attribute.

**The two loading states carry no criterion, on purpose.** `Loading recipes` and
`Loading recipe` are what a skeleton shows while its fetch cut is open, so a criterion
asserting either one would be green on an empty skeleton and would grade nothing. They
are covered indirectly instead: every criterion that reads a card, a row or a step can
only pass once its screen has left `loading`. The `empty` state is graded, by the
second half of `c-2-4`, and `not-found` by `c-3-5`.

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

**How a criterion names its cuts.** One convention, applied to all 22 criteria: a
criterion lists every cut that lies on the code path it exercises, cuts from earlier
sessions included. A screen criterion therefore names the store and route-handler cuts
that feed it as well as its own screen cuts. Fill all of them and the criterion is
green; leave any of them open and it is not proven.

**Two criteria that a subset already satisfies.** `c-3-2` and `c-3-5` both assert the
404 path, and `findRecipe`'s rule-4 fallback is `return null` - the same answer a real
miss gives. Fill `cut-api-recipe-get` and `cut-recipe-fetch` and both go green with
`cut-store-find-one` still open, because a store that finds nothing and a store that
correctly finds nothing are indistinguishable from outside. `Recipe | null` admits no
other typed fallback, so this is recorded rather than fixed: session 3 is still graded
correctly as a whole, because `c-3-1` and `c-3-3` both need the real lookup. A per-cut
checkpoint must pair `c-3-2` with `c-3-1` and never present it as proof on its own.

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
  recipes — cuts `cut-store-read-all`, `cut-api-recipes-list`, `cut-list-fetch`,
  `cut-list-cards`
- `c-1-4` sc-list displays the title Lemon Garlic Pasta on a recipe-card whose
  card-minutes element reads 20 min and whose card-serves element reads Serves 4 —
  cuts `cut-store-read-all`, `cut-api-recipes-list`, `cut-list-fetch`, `cut-list-cards`
- `c-1-5` sc-list renders one card-tag element per tag of that recipe on every card,
  2 on the Lemon Garlic Pasta card reading quick and vegetarian — cuts
  `cut-store-read-all`, `cut-api-recipes-list`, `cut-list-fetch`, `cut-list-cards`

**Cut points.**

- `cut-store-read-all` in `lib/store.ts` — Read the recipes JSON file from disk and
  return every recipe in it as an array of Recipe objects.
- `cut-api-recipes-list` in `app/api/recipes/route.ts` — Send the recipes the handler
  has back to the browser as a JSON array with status 200.
- `cut-list-fetch` in `app/RecipeList.tsx` — Ask the recipes endpoint for the list,
  passing the page query string straight through, and when the reply is a 200 put the
  array it answers with into the recipes state and set the status to loaded.
- `cut-list-cards` in `app/RecipeList.tsx` — Turn the recipes array into one
  recipe-card element per recipe, each one a link to that recipe page holding its
  title, a card-tag element per tag, its minutes in a card-minutes element and its
  serves count in a card-serves element.

### Session 2 - Search and tag filter

**Goal.** Filter the list by title text and by one tag inside the route handler, and
keep both choices together in the page URL.

**Teaches.** Reading searchParams inside a route handler; case-insensitive substring
matching; deriving a distinct sorted list with Set and flatMap; useSearchParams and
router.replace; building the next query string from the one the page already has, so
one control does not drop the other control's parameter.

**Builds.** `ep-tags-list`. Extends `ep-recipes-list` and `sc-list` from session 1.

**Acceptance criteria.**

- `c-2-1` GET /api/recipes?q=garlic and GET /api/recipes?q=GARLIC each return 200 with
  the same 2 recipes, Lemon Garlic Pasta and Garlic Flatbread — cuts
  `cut-store-read-all`, `cut-api-recipes-list`, `cut-api-recipes-filter`
- `c-2-2` GET /api/recipes?tag=baking returns 200 with the 2 recipes tagged baking,
  Banana Bread and Garlic Flatbread, and GET /api/recipes?q=garlic&tag=baking returns
  200 with 1 recipe, Garlic Flatbread — cuts `cut-store-read-all`,
  `cut-api-recipes-list`, `cut-api-recipes-filter`
- `c-2-3` GET /api/tags returns 200 with the JSON array baking, one-pot, quick, spicy,
  vegetarian in alphabetical order — cuts `cut-store-read-all`, `cut-api-tags-list`
- `c-2-4` sc-list renders 2 recipe-card elements and the page URL reads /?q=garlic
  after garlic is typed into the search box, then displays the message No recipes match
  and renders 0 recipe-card elements after the box is changed to zzz — cuts
  `cut-store-read-all`, `cut-api-recipes-list`, `cut-api-recipes-filter`,
  `cut-list-fetch`, `cut-list-cards`, `cut-list-search-url`
- `c-2-5` sc-list renders 2 recipe-card elements and the page URL reads /?tag=baking
  after the filter-tag chip reading baking is clicked, then renders 8 recipe-card
  elements and the URL reads / after that same filter-tag chip is clicked a second time
  — cuts `cut-store-read-all`, `cut-api-recipes-list`, `cut-api-recipes-filter`,
  `cut-api-tags-list`, `cut-list-fetch`, `cut-list-cards`, `cut-list-tag-toggle`
- `c-2-6` sc-list renders 1 recipe-card element reading Garlic Flatbread and the page
  URL has q set to garlic and tag set to baking, after garlic is typed into the search
  box, the URL reaches /?q=garlic, and the filter-tag chip reading baking is then
  clicked — cuts `cut-store-read-all`, `cut-api-recipes-list`,
  `cut-api-recipes-filter`, `cut-api-tags-list`, `cut-list-fetch`, `cut-list-cards`,
  `cut-list-search-url`, `cut-list-tag-toggle`

`c-2-6` is the criterion that catches a control which rebuilds the query string from
scratch instead of from the string the page already has. It waits for the URL to reach
`/?q=garlic` before the chip is clicked, so the chip's handler is reading a query
string that already holds `q`.

**Cut points.**

- `cut-api-recipes-filter` in `app/api/recipes/route.ts` — Keep only the recipes whose
  title contains the q parameter, ignoring letter case, and whose tags include the tag
  parameter; a parameter that is missing or empty narrows nothing.
- `cut-api-tags-list` in `app/api/tags/route.ts` — Collect the tags of every recipe
  into one list without duplicates, sort it alphabetically and return it as a JSON
  array of strings.
- `cut-list-search-url` in `app/RecipeList.tsx` — Build the next query parameters from
  the ones the page already has, so the tag parameter is left as it is, then set q to
  the text of the search box, or drop q when the box is empty, and hand the result to
  replaceQuery.
- `cut-list-tag-toggle` in `app/RecipeList.tsx` — Build the next query parameters from
  the ones the page already has, so the q parameter is left as it is, then set tag to
  the clicked tag, or drop tag when the chip clicked is the one already active, and hand
  the result to replaceQuery.

### Session 3 - One recipe in full

**Goal.** Open one recipe at its own route with its ingredients and its steps, and
answer 404 for an id the store does not hold.

**Teaches.** Dynamic route segments for pages and route handlers; returning 404 with a
JSON body from a route handler; reading the route id with useParams; branching on the
response status in a client component; rendering a not-found state.

**Builds.** `ep-recipe-get`, `sc-recipe`.

**Acceptance criteria.**

- `c-3-1` GET /api/recipes/lemon-garlic-pasta returns 200 with that recipe, its 7
  ingredients and its 4 steps — cuts `cut-store-read-all`, `cut-store-find-one`,
  `cut-api-recipe-get`
- `c-3-2` GET /api/recipes/not-a-recipe returns 404 with a JSON body holding an error
  field — cuts `cut-store-read-all`, `cut-store-find-one`, `cut-api-recipe-get`.
  Pair this one with `c-3-1`: it goes green with `cut-store-find-one` still open,
  because `findRecipe`'s `return null` fallback and a real miss look the same.
- `c-3-3` sc-recipe renders one ingredient-row element per ingredient, 7 at
  /recipes/lemon-garlic-pasta, the olive oil row reading 2 tbsp olive oil and the lemon
  row reading 1 lemon — cuts `cut-store-read-all`, `cut-store-find-one`,
  `cut-api-recipe-get`, `cut-recipe-fetch`, `cut-recipe-rows`
- `c-3-4` sc-recipe renders 4 step elements in stored order at
  /recipes/lemon-garlic-pasta, the text of the first beginning 1. Boil the spaghetti —
  cuts `cut-store-read-all`, `cut-store-find-one`, `cut-api-recipe-get`,
  `cut-recipe-fetch`
- `c-3-5` sc-recipe displays the message Recipe not found at the route
  /recipes/not-a-recipe — cuts `cut-store-read-all`, `cut-store-find-one`,
  `cut-api-recipe-get`, `cut-recipe-fetch`. Pair this one with `c-3-3` for the same
  reason as `c-3-2`.

**Cut points.**

- `cut-store-find-one` in `lib/store.ts` — Return the recipe whose id matches the one
  asked for, or null when the store holds no recipe with that id.
- `cut-api-recipe-get` in `app/api/recipes/[id]/route.ts` — Reply with the recipe as
  JSON and status 200 when the store finds it, and with status 404 and a JSON body
  holding an error field when the store finds nothing.
- `cut-recipe-fetch` in `app/recipes/[id]/page.tsx` — Ask the endpoint for the recipe
  named in the route; on a 200 reply put the recipe into state and set the status to
  loaded, and on a 404 reply set the status to not-found.
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

Every session-4 criterion opens at `/recipes/lemon-garlic-pasta`, which is stored as
serves 4, and reaches its servings count by clicking the stepper from that 4.

**Acceptance criteria.**

- `c-4-1` sc-recipe displays 6 in the servings-count element after the plus control is
  clicked 2 times at /recipes/lemon-garlic-pasta, which is stored as serves 4 —
  cuts `cut-store-read-all`, `cut-store-find-one`, `cut-api-recipe-get`,
  `cut-recipe-fetch`, `cut-recipe-servings`
- `c-4-2` sc-recipe displays an ingredient-row reading 3 tbsp olive oil after the plus
  control is clicked 2 times at /recipes/lemon-garlic-pasta, taking the count from its
  stored 4 to 6, where the stored quantity is 2 tbsp — cuts `cut-store-read-all`,
  `cut-store-find-one`, `cut-api-recipe-get`, `cut-recipe-fetch`, `cut-recipe-rows`,
  `cut-recipe-servings`, `cut-fraction-scale`, `cut-recipe-scale-quantity`
- `c-4-3` sc-recipe displays an ingredient-row reading 1/2 tsp chilli flakes after the
  plus control is clicked 2 times at /recipes/lemon-garlic-pasta, taking the count from
  its stored 4 to 6, where the stored quantity is 1/3 tsp — cuts `cut-store-read-all`,
  `cut-store-find-one`, `cut-api-recipe-get`, `cut-recipe-fetch`, `cut-recipe-rows`,
  `cut-recipe-servings`, `cut-fraction-scale`, `cut-recipe-scale-quantity`
- `c-4-4` sc-recipe displays an ingredient-row reading 1/2 tsp chilli flakes after the
  plus control is clicked 2 times at /recipes/lemon-garlic-pasta, then one reading
  1/3 tsp chilli flakes again after the minus control is clicked 2 times — cuts
  `cut-store-read-all`, `cut-store-find-one`, `cut-api-recipe-get`, `cut-recipe-fetch`,
  `cut-recipe-rows`, `cut-recipe-servings`, `cut-fraction-scale`,
  `cut-recipe-scale-quantity`
- `c-4-5` sc-recipe displays 1 in the servings-count element after the minus control is
  clicked 4 times at /recipes/lemon-garlic-pasta, which is stored as serves 4 — cuts
  `cut-store-read-all`, `cut-store-find-one`, `cut-api-recipe-get`, `cut-recipe-fetch`,
  `cut-recipe-servings`
- `c-4-6` sc-recipe displays 24 in the servings-count element after the plus control is
  clicked 21 times at /recipes/lemon-garlic-pasta, which is stored as serves 4 — cuts
  `cut-store-read-all`, `cut-store-find-one`, `cut-api-recipe-get`, `cut-recipe-fetch`,
  `cut-recipe-servings`

`c-4-5` walks 4 → 3 → 2 → 1 and then asks for 0, so the fourth click is the one the
lower clamp answers. `c-4-6` walks 4 up to 24 in 20 clicks and then asks for 25, so the
twenty-first click is the one the upper clamp answers.

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
