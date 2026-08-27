# Session 4 - Scale the servings

**Time:** 40 minutes
**Students start from:** `/recipes/lemon-garlic-pasta` showing 7 ingredients and
4 steps. The stepper is on screen and the number never changes.
**Students end with:** a working stepper. 4 to 6 rewrites every quantity; 6 back
to 4 restores the recipe exactly as written, with no drift.

This is the payoff session. It is the first time in the track that the number on
screen is computed from React state rather than read from a server response, and
a student can see in one click whether the arithmetic is right.

## What they learn

1. Deriving what is on screen from state instead of from the server.
2. Exact fraction arithmetic with a numerator and a denominator - no floating
   point.
3. Reducing a fraction with the greatest common divisor.
4. Clamping a value inside the state setter, not in the UI.
5. Scaling from the **stored** value every time, never from the value on screen.

## Before you start

- Session 3 green.
- `/recipes/lemon-garlic-pasta` open. It is stored as **serves 4**, so every
  criterion this session counts clicks from 4.
- The two rows to watch, on a whiteboard before you write any code:

| Ingredient | stored (serves 4) | at 6 servings | back at 4 |
|---|---|---|---|
| olive oil | `2/1` -> `2 tbsp` | `3/1` -> `3 tbsp` | `2 tbsp` |
| chilli flakes | `1/3` -> `1/3 tsp` | `1/2` -> `1/2 tsp` | `1/3 tsp` |

- The clamps are **1 and 24**. The controls stay clickable at the limits; the
  clamp lives in the setter.

## The plan

| Minutes | What you do |
|---|---|
| 0-5 | Recap and set the trap. Ask: to go from 4 servings to 6, multiply by 1.5. What is `1/3 * 1.5` in floating point? Show `0.5000000000000001` in the console. That is why this project has no decimals in it. |
| 5-13 | `cut-recipe-servings`. The number moves. Quantities do not. Show the clamp at 1 and at 24. |
| 13-26 | `cut-fraction-scale`. Whiteboard first: multiply the numerator by the target, the denominator by the base, then reduce. Then write it. Quantities still do not move - nothing calls it yet. |
| 26-34 | `cut-recipe-scale-quantity`. One line. Everything comes alive. |
| 34-40 | The drift demo: 4 to 6 to 4, read the chilli flakes row out loud each time. Then the 24 clamp. Recap what "derived from state" means. |

## Cut points in this session

### cut-recipe-servings - `app/recipes/[id]/RecipeView.tsx`:19

- **What students see:**
  `// TODO(cut-recipe-servings): Put the requested number into the servings state, holding it at 1 when it would drop below 1 and at 24 when it would climb above 24.`
- **What they write:** one line - `setServings` of the requested number clamped
  between 1 and 24. `Math.min(24, Math.max(1, next))` is the idiom.
- **Teach it like this:** "The two buttons already call this with
  `servings - 1` and `servings + 1`, so they can ask for 0 or for 25. Your job
  is to refuse politely. Notice where the clamp lives: in the setter, not in a
  `disabled` attribute on the button. The buttons stay clickable at the limits -
  clicking minus at 1 just does nothing. One place holds the rule, so it cannot
  disagree with itself."
- **Passes when:** `c-4-1`, `c-4-5` and `c-4-6` go green. The quantities still do
  not move - say so before they report it as a bug.
- **The click counts in the tests are deliberate:** `c-4-5` clicks minus **4**
  times from 4, so the fourth click is the one the clamp answers. `c-4-6` clicks
  plus **21** times, reaching 24 in 20 and asking for 25 on the last one.

### cut-fraction-scale - `lib/fractions.ts`:55

- **What students see:**
  `// TODO(cut-fraction-scale): Multiply the quantity by the target servings over the base servings, then divide the numerator and the denominator by their greatest common divisor.`
- **What they write:** `num = stored.num * servings`, `den = stored.den * serves`,
  divide both by `gcd(num, den)`, return the pair. This block **does** contain
  its own `return` - it is one of the few that does. The `return stored` below it
  is the skeleton's fallback; leave it.
- **Teach it like this:** "Scaling a fraction by `servings/serves` is just
  multiplying two fractions: tops times tops, bottoms times bottoms. `1/3` times
  `6/4` is `6/12`. Correct, and unreadable - so we reduce: `gcd(6,12)` is 6, and
  `6/12` becomes `1/2`. `gcd` is already written for you. No decimals appear
  anywhere in this function, and that is the entire reason 4 to 6 to 4 comes back
  exactly."
- **Work `1/3` at 6 servings on the board** before they type: `1*6 = 6`,
  `3*4 = 12`, `gcd = 6`, answer `1/2`. Then have them predict olive oil:
  `2*6 = 12`, `1*4 = 4`, `gcd = 4`, answer `3/1`, which prints as `3`.
- **Passes when:** nothing yet - `cut-recipe-scale-quantity` has to call it.

### cut-recipe-scale-quantity - `app/recipes/[id]/RecipeView.tsx`:31

- **What students see:**
  `` // TODO(cut-recipe-scale-quantity): Replace the quantity of the row copy by calling `scaleQuantity` with that ingredient's stored quantity, the recipe's serves count and the servings count on screen. ``
- **What they write:** one line -
  `row.quantity = scaleQuantity(ingredient.quantity, recipe.serves, servings)`.
- **Teach it like this:** "Read the three arguments carefully, because the first
  one is the whole lesson. It is `ingredient.quantity` - the **stored** value
  from the server - not `row.quantity` and not what is on screen. Every render
  rebuilds `rows` from the fetched recipe and scales from the original. So going
  4, 6, 9, 2, 4 lands back on exactly the recipe as written, because you never
  scale a scaled value."
- **Call `scaleQuantity`.** Doing the multiply inline here would pass the tests
  today and skip the one function this session exists to teach. The hint names
  it; hold them to it.
- **Passes when:** `c-4-2`, `c-4-3` and `c-4-4` go green.

## The demo that ends the course

Open `/recipes/lemon-garlic-pasta`. Read the chilli flakes row: `1/3 tsp`. Click
plus twice: `1/2 tsp`. Click minus twice: `1/3 tsp` again, exactly. Then ask what
would have happened if they had scaled the number already on screen instead of
the stored one - `1/3` to `1/2` to `1/3` only works because the second step went
back to `1/3`, not forward from `1/2`. `c-4-4` is precisely this test.

## Where students get stuck

- **The number moves but the quantities do not** - expected until
  `cut-recipe-scale-quantity` is written. Two of the three cuts have no visible
  effect on their own; warn them at the start of the session or you will spend
  ten minutes on false bug reports.
- **`0.5000000000000001 tsp` on screen** - they converted to a decimal
  somewhere, usually `servings / serves` as a number first. Keep numerator and
  denominator as separate whole numbers the whole way.
- **`6/12 tsp` instead of `1/2 tsp`** - they skipped the reduce.
- **Quantities creep and never come back** - they scaled `row.quantity` (already
  scaled) instead of `ingredient.quantity` (stored). This is the bug the session
  is built to prevent; `c-4-4` catches it and nothing else does.
- **The number goes to 0 or 25** - clamp arguments swapped, or they clamped in
  the button instead of the setter.
- **`NaN` everywhere** - `serves` read off the wrong object, so they divided by
  `undefined`. It is `recipe.serves`, the stored value, not `servings`.
- **Quantities reset when they click** - they mutated `recipe.ingredients` in
  place instead of copying. The `{...ingredient}` copy is already written above
  the cut; if they replaced it, put it back.
- **The stepper works on one recipe but not another** - they hardcoded 4 as the
  base instead of using `recipe.serves`. Banana Bread is stored as serves 8, so
  test on it.

## Check before moving on

There is no session 5. Confirm all 22 criteria are green, then do the 4-6-4
demo one more time and let them try `/recipes/banana-bread`, which is stored as
serves 8, so the arithmetic looks different and still comes back exactly.

If anyone asks how to add a recipe: the box is read-only by design and there is
no POST handler. It is a good extension to attempt afterwards; it is not taught
here.
