# Session 1 - The recipe list

**Time:** 40 minutes
**Students start from:** the skeleton. It builds and runs. `/` shows the heading,
the tagline, an empty search box, no tag chips, and the message
`No recipes match`.
**Students end with:** `/` showing 8 recipe cards, each with a title, a chip per
tag, its minutes and its servings, and each one a link to its recipe page.

## What they learn

1. What a route handler is, and that `app/api/recipes/route.ts` is already one.
2. Reading a file on the server with `node:fs` - and why that only works on the
   server.
3. Typing a response with a type shared between server and client
   (`lib/types.ts`).
4. Fetching into React state with `useEffect`.
5. Rendering a list with `.map` and why each element needs a `key`.

## Before you start

- The skeleton open in an editor, `npm run dev` already running.
- Two browser tabs: `http://localhost:3000` and
  `http://localhost:3000/api/recipes`.
- `data/recipes.json` open in a tab you can show. Students should see the data
  is real before they write a line.

Session 1 carries the whole project's setup, which is why it has three cut
points and sessions 2 and 3 have four. Do not add a fourth - the reading is the
fourth.

## The plan

| Minutes | What you do |
|---|---|
| 0-6 | Show the finished app for 60 seconds, then close it. Tour the skeleton: `lib/types.ts`, `data/recipes.json`, then `app/api/recipes/route.ts`. Point at `/api/recipes` in the browser answering `[]`. Ask: the handler is written, so why is the list empty? |
| 6-14 | `cut-store-read-all`. Live-code it. Refresh `/api/recipes` - 8 recipes of JSON. Nothing on `/` yet. |
| 14-26 | `cut-list-fetch`. Walk the three states in `RecipeList` first, then write the fetch. `/` still shows no cards, because nothing renders them yet. |
| 26-36 | `cut-list-cards`. The four testids go in as you type. Cards appear. |
| 36-40 | Click a card - it 404s in the Next dev overlay, and that is fine: the recipe page is session 3. Recap the path data took: file to handler to fetch to state to markup. |

## Cut points in this session

### cut-store-read-all - `lib/store.ts`:15

- **What students see:**
  `// TODO(cut-store-read-all): Read the recipes JSON file from disk and return every recipe in it as an array of Recipe objects.`
- **What they write:** three lines. Build the path to `data/recipes.json` from
  `process.cwd()`, read it as UTF-8 text, `JSON.parse` it and assign to the
  `recipes` variable already declared above the TODO.
- **Teach it like this:** "This code runs on the server, so it can touch the
  disk. `process.cwd()` is where you started `npm run dev`, so the path works
  the same on every machine. `JSON.parse` hands you back `any`, so we tell
  TypeScript what it is with `as Recipe[]` - that is a promise we are making,
  not a check."
- **Watch for:** they will try to `return` from inside the block. Point at the
  `return recipes` already below the TODO and say the block's job is to fill the
  variable, not to leave the function. This pattern repeats in every cut of the
  project.
- **Passes when:** `c-1-1` and `c-1-2` go green.

### cut-list-fetch - `app/RecipeList.tsx`:53

- **What students see:**
  `// TODO(cut-list-fetch): Ask the recipes endpoint for the list, passing the page query string straight through, and when the reply is a 200 and the ignore flag the wrapper declares is still clear, put the array it answers with into the recipes state and set the status to loaded.`
- **What they write:** `fetch` to `/api/recipes?` plus the `qs` the component
  already computed; on a `200`, read the JSON and - only if `ignore` is still
  `false` - call `setRecipes` and `setStatus('loaded')`.
- **Teach it like this:** "Everything around this block is already written, and
  that is deliberate. `qs` comes from the URL. The `useEffect` and its `[qs]`
  dependency are written, so the moment the URL changes the browser asks again -
  that is what makes session 2 work. And `let ignore = false` above you with
  `ignore = true` in the cleanup below: typing 'garlic' fires six requests and
  they can come back out of order. Your job is to write to state only if your
  reply is still the current one."
- **Do not skip the `ignore` check.** It is one line and it is the difference
  between a list that flickers to a wrong count and one that does not.
- **Passes when:** nothing new goes green on its own - `c-1-3`, `c-1-4` and
  `c-1-5` need `cut-list-cards` too. Say so, so no one thinks they broke it.

### cut-list-cards - `app/RecipeList.tsx`:76

- **What students see:**
  `` // TODO(cut-list-cards): Turn the recipes array into one recipe-card element per recipe and assign them to `cards`, each element a link to that recipe's page at /recipes/ followed by its id, holding its title, a card-tag element per tag, its minutes in a card-minutes element and its serves count in a card-serves element. ``
- **What they write:** `cards = recipes.map(...)` producing a `<Link>` per
  recipe whose `href` is a template literal of `/recipes/` and `recipe.id`, with
  `data-testid="recipe-card"`; inside it the title, a `.map` over
  `recipe.tags` giving one `data-testid="card-tag"` span each, then
  `{recipe.minutes} min` in a `card-minutes` span and `Serves {recipe.serves}`
  in a `card-serves` span.
- **Teach it like this:** "Assign to `cards`, do not make a new variable - the
  JSX at the bottom of the file renders `cards` and nothing else. Two keys are
  needed here, one on the card and one on each tag, because there are two
  `.map`s. And the exact strings matter: `20 min` and `Serves 4`. The tests read
  them."
- **The card is a link, and that is graded.** `c-1-4` checks the `href`. A card
  that renders the right text but is a `<div>` fails.
- **Passes when:** `c-1-3`, `c-1-4` and `c-1-5` go green.

## Where students get stuck

- **`Module not found: Can't resolve 'fs'`** - they imported `node:fs` into
  `RecipeList.tsx` instead of `lib/store.ts`. `RecipeList` is a client
  component; it runs in the browser and there is no disk there. The rule: only
  files under `app/api/` and `lib/store.ts` touch `fs`.
- **`ENOENT: no such file or directory, open '.../data/recipes.json'`** - they
  used a relative path like `./data/recipes.json`. Relative to what? Use
  `path.join(process.cwd(), 'data', 'recipes.json')`.
- **The list still says `No recipes match` after `cut-store-read-all`** -
  correct. `/api/recipes` has the data now, but `cut-list-fetch` is what brings
  it into the page. Show them `/api/recipes` in the other tab to prove the
  server half works. This is the moment to praise, not debug.
- **Cards render but the tests fail on `20 min`** - they wrote `20min` or
  `20 minutes`. The criterion pins the exact string.
- **`Each child in a list should have a unique "key" prop`** in the console -
  they keyed the card but not the tag spans, or used the array index where the
  id would do.
- **They wrote `const cards = recipes.map(...)`** - a fresh `const` shadows
  nothing and renders nothing; the page stays empty with no error. Point at the
  `let cards: ReactNode[] = []` above the TODO.
- **Clicking a card shows a 404 page** - expected all session. `/recipes/<id>`
  is session 3.

## Check before moving on

`/` shows 8 cards. `/api/recipes` returns 8 recipes. `c-1-1` through `c-1-5` are
green. The search box and the tag chip bar are visible but do nothing yet - say
that out loud, because it is the honest state and session 2 opens with it.
