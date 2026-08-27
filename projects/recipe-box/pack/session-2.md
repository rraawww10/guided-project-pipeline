# Session 2 - Search and tag filter

**Time:** 40 minutes
**Students start from:** `/` showing 8 cards. The search box accepts typing and
does nothing. The tag chip bar is empty.
**Students end with:** typing in the box narrows the list, clicking a chip
narrows it by tag, the two narrow together, and `/?q=garlic&tag=baking` is a
link that reproduces the filtered list.

## What they learn

1. Reading query parameters inside a route handler with `searchParams`.
2. Case-insensitive substring matching, and treating a missing parameter as
   "narrow nothing".
3. Deriving a distinct sorted list with `flatMap` and `Set`.
4. `useSearchParams` and `router.replace` - the URL as the place state lives.
5. Building the next query string **from the one the page already has**, so one
   control does not wipe the other control's parameter.

## Before you start

- Session 1 finished and green.
- Have these four URLs ready to paste, and use them in this order:
  `/api/recipes?q=garlic`, `/api/recipes?tag=baking`,
  `/api/recipes?q=garlic&tag=baking`, `/api/tags`.
- The seed data has exactly two recipes whose title contains "garlic" (Lemon
  Garlic Pasta, Garlic Flatbread) and exactly two tagged `baking` (Banana Bread,
  Garlic Flatbread). Only Garlic Flatbread is both. Every count in this session
  comes from that.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Recap: the URL drives the fetch already, because `useEffect` depends on `qs`. So if we can get `?q=garlic` into the URL, the list refetches for free. Two halves: the server must filter, the page must write the URL. |
| 4-13 | `cut-api-recipes-filter`. Test it in the browser, not the app: the three `/api/recipes?...` URLs. |
| 13-18 | `cut-api-tags-list`. Refresh `/` - the chips appear, and they do nothing yet. |
| 18-27 | `cut-list-search-url`. Type in the box, watch the address bar and the list move together. |
| 27-34 | `cut-list-tag-toggle`. Click a chip, click it again to clear it. |
| 34-40 | The combined check: type `garlic`, then click `baking`. One card. Then edit the address bar by hand to `/?q=garlic&tag=baking` and reload - same card. That is the point of the session. |

## Cut points in this session

### cut-api-recipes-filter - `app/api/recipes/route.ts`:20

- **What students see:**
  `` // TODO(cut-api-recipes-filter): Keep only the recipes whose title contains the q parameter, ignoring letter case, and whose tags include the tag parameter, and assign the result to `shown`; a parameter that is missing or empty narrows nothing. ``
- **What they write:** read `q` and `tag` off
  `new URL(request.url).searchParams`, defaulting each to `''`, then
  `shown = all.filter(...)` where a recipe passes if `q` is empty **or** its
  lowercased title includes the lowercased `q`, and `tag` is empty **or**
  `recipe.tags.includes(tag)`.
- **Teach it like this:** "`const all` and `let shown = all` are already above
  you, and the `return NextResponse.json(shown)` is already below. So the
  handler already works - it returns everything. Your block narrows `shown`.
  Assign to `shown`; a new variable changes nothing and the response will not
  move."
- **The empty-parameter case is the whole trick.** Ask before they type: what
  should `/api/recipes` with no parameters return? All 8. So an empty `q` must
  match everything, which is why the test is `q === '' || ...` and not
  `title.includes('')`. Both work here; only the first says what it means.
- **Passes when:** `c-2-1` and `c-2-2` go green. `c-1-1` and `c-1-2` must stay
  green - bare `GET /api/recipes` still returns all 8. Check that.

### cut-api-tags-list - `app/api/tags/route.ts`:18

- **What students see:**
  `// TODO(cut-api-tags-list): Collect the tags of every recipe into one list without duplicates, sort it alphabetically and return it as a JSON array of strings.`
- **What they write:** one line and a return.
  `[...new Set(all.flatMap((recipe) => recipe.tags))].sort()`, returned as JSON.
- **Teach it like this:** "`flatMap` because each recipe has an array of tags and
  we want one flat list. `Set` because `vegetarian` appears four times and we
  want it once. Spread it back into an array because `Set` is not JSON. Then
  sort, because the test asks for alphabetical order and because a bar of chips
  that reorders itself between reloads is unusable."
- **This endpoint never narrows with the filter.** Say it explicitly: all five
  tags stay on screen no matter what the list is showing, so a student can
  always click their way back out of a filter.
- **This is the cut that makes the chips exist at all.** The chips render from
  the `tags` state, and nothing else sets it. Nothing is hardcoded, so with this
  block open the bar is genuinely empty.
- **Passes when:** `c-2-3` goes green.

### cut-list-search-url - `app/RecipeList.tsx`:67

- **What students see:**
  `// TODO(cut-list-search-url): Build the next query parameters from the ones the page already has, so the tag parameter is left as it is, then set q to the text of the search box, or drop q when the box is empty, and hand the result to replaceQuery.`
- **What they write:** `new URLSearchParams(searchParams.toString())`, then
  `next.delete('q')` when the text is empty else `next.set('q', text)`, then
  `replaceQuery(next)`.
- **Teach it like this:** "Start from what the URL already has. If you build a
  fresh string like `/?q=` plus the text, you have just deleted the tag the user
  clicked - and it will look like it works, because you will test it without a
  tag active. Copy, change one key, hand it over."
- **Why `delete` and not `set('q', '')`:** an empty `q` in the URL leaves
  `/?q=` in the address bar, and `c-2-5` asserts the URL reads exactly `/` once
  the last parameter is gone. `replaceQuery` is already written and handles the
  `/` versus `/?` decision - they only decide which keys exist.
- **The box is uncontrolled on purpose.** Its `defaultValue` comes from the URL,
  and its text is never driven back from the URL. If a student "fixes" this by
  adding `value={...}`, every keystroke will wait on a router transition and the
  box will feel broken. Mention it before they try.
- **Passes when:** `c-2-4` goes green.

### cut-list-tag-toggle - `app/RecipeList.tsx`:71

- **What students see:**
  `// TODO(cut-list-tag-toggle): Build the next query parameters from the ones the page already has, so the q parameter is left as it is, then set tag to the clicked tag, or drop tag when the chip clicked is the one already active, and hand the result to replaceQuery.`
- **What they write:** the same copy-then-change shape, but the decision is a
  toggle: if `next.get('tag')` already equals the clicked tag, `delete` it,
  otherwise `set` it.
- **Teach it like this:** "Same shape as the search box - copy the parameters,
  change one key. The new idea is the toggle: clicking the active chip is how
  you turn the filter off, so the same click means two things depending on what
  is already in the URL."
- **Passes when:** `c-2-5` and `c-2-6` go green.

## The combined check, and why it exists

`c-2-6` is the criterion that catches a control which rebuilds the query string
from scratch. It types `garlic`, **waits for the URL to actually reach
`/?q=garlic`**, then clicks the `baking` chip and asserts one card reading
`Garlic Flatbread` with both `q` and `tag` set. A student whose chip handler
starts from an empty `URLSearchParams` passes every other criterion in the
session and fails this one. Do the demo by hand at minute 34 so they see it.

Note the two kinds of chip: the **filter bar** chips are buttons and carry
`filter-tag`; the chips on a card are text and carry `card-tag`. Clicking a card
chip follows the card's link, it does not filter. If a student reports "clicking
a tag opens a recipe", they clicked the wrong chip.

## Where students get stuck

- **`searchParams` is empty in the route handler** - they reached for a
  `searchParams` prop. A route handler gets a `Request`; read
  `new URL(request.url).searchParams`.
- **`?q=GARLIC` returns nothing** - they lowercased one side only. Both sides.
- **The tag disappears when they type** - the classic. Their search handler
  built a fresh query string. This is `c-2-6` failing and it is the lesson of
  the session.
- **The URL shows `/?q=` after clearing the box** - they used `set` with an
  empty string instead of `delete`.
- **Typing feels laggy or characters arrive out of order** - they added
  `value={}` to the search input, making it controlled. Take it back out.
- **The chips never appear** - `cut-api-tags-list` is still open, or
  `/api/tags` is answering 501. Check the network tab.
- **All five chips look active** - they compared against the wrong thing;
  `aria-pressed` is already written against `activeTag` from the URL, so this
  usually means they wrote `tag` into the URL as a list rather than one value.
- **Filtering works but the count is briefly wrong while typing fast** - the
  stale-reply guard. Check they kept the `ignore` check from session 1.

## Check before moving on

Type `garlic`, click `baking`, see one card. Paste
`/?q=garlic&tag=baking` into a fresh tab and get the same one card. `c-2-1`
through `c-2-6` green, and `c-1-1` through `c-1-5` still green.
