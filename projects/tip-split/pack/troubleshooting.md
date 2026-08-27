# Troubleshooting - Tip Split

Errors students actually hit in this project, grouped by when you will see them.
Exact messages vary a little between versions, so match on the distinctive words.

## First, three habits that save the session

1. **Read the terminal before the browser.** This project builds with TypeScript.
   One type error anywhere stops the build, and then *every* criterion is red and
   the browser shows a screen that has nothing to do with the mistake.
2. **Check the endpoint directly.** Before debugging a screen, open
   `http://localhost:3000/api/bills` or `/api/bills/anand-bhavan` in a tab. If it
   says `not implemented`, the screen is behaving correctly.
3. **Never move the `return`.** Every cut is a block inside a function. The
   variable is declared above it, the `return` is below it. Fill the middle.

## Setup and the dev server

**`Error: Cannot find module 'next'`, or the dev script does nothing**
`npm install` was never run, or was run in the wrong folder. Run it in the folder
that contains `package.json`.

**`npm ci can only install packages when your package.json and package-lock.json are in sync`**
Someone edited `package.json`. Restore it, or run `npm install` instead of
`npm ci`. Nothing in this project needs a new dependency - the whole project is
Next, React and TypeScript.

**`Port 3000 is in use`, or `EADDRINUSE: address already in use :::3000`**
An old dev server is still running. Next's dev server usually just moves to 3001
and tells you - read the URL it prints rather than typing 3000 from memory. To
kill the old one: `lsof -ti:3000 | xargs kill`.

**`Error: ENOENT: no such file or directory, open '.../data/bills.json'`**
The server was started from the wrong folder, so `process.cwd()` is not the
project root. Stop it, `cd` to the folder holding `package.json`, start it again.
This is the best possible moment to explain what `process.cwd()` means.

**`SyntaxError: Expected double-quoted property name in JSON` / `Unexpected token in JSON`**
`data/bills.json` was edited by hand and left broken - usually a trailing comma
after the last bill, or a single quote. Fix the file. The endpoint reads it fresh
on every request, so no restart is needed once it is valid.

## The whole project stops building

**`TS2355`, "must return a value"**
A `return` was deleted or dragged inside the block. Every one of these functions
must keep its return as the last statement:

```ts
return bills                            // lib/store.ts, readAllBills
return bill                             // lib/store.ts, findBill
return tip                              // lib/money.ts, tipPaise
return shares                           // lib/money.ts, splitPaise
return Response.json(body, { status })  // both route handlers
```

**`Type '{ params: { id: string; }; }' is not assignable ...`, or at runtime
`Route "/api/bills/[id]" used 'params.id'. 'params' should be awaited`**
The handler signature was retyped in the older Next 14 shape. It ships written
and must stay exactly this:

```ts
export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params
```

This is the single most expensive mistake in the project: it fails `npm run
build`, so all 17 criteria go red at once, not one.

**`Module not found: Can't resolve '@/lib/store'`**
The `@/` prefix means the project root, and it is configured in `tsconfig.json`.
Either the import was retyped as a relative path that does not resolve, or the
file was moved. Correct imports, copied from the real files:

```ts
import { readAllBills } from '@/lib/store'          // app/api/bills/route.ts
import { findBill } from '@/lib/store'              // app/api/bills/[id]/route.ts
import { formatRupees } from '@/lib/money'          // app/page.tsx
import { formatRupees, splitPaise, tipPaise } from '@/lib/money'  // BillView.tsx
import type { Bill } from '@/lib/types'
import type { Bill } from './types'                 // inside lib/store.ts
```

**`Module not found: Can't resolve 'fs'`, or "You're importing a component that
needs fs"**
`lib/store.ts` was imported into a client component to skip the fetch. A browser
has no filesystem. The screens get their data from the endpoints, and only the
endpoints touch the store.

**"You're importing a component that needs `useState`. This React hook only works
in a client component."**
The `'use client'` line at the top of `app/page.tsx`, `app/bills/[id]/page.tsx`
or `app/bills/[id]/BillView.tsx` was deleted. Put it back as the first line of
the file.

## Session 1 - the list

**The screen sits on `Loading saved bills` forever**
`status` never left `'loading'`. Either `cut-list-fetch` is empty, or
`cut-api-bills-list` is empty so the endpoint answers 501 and the fetch's
`if (response.status === 200)` never fires. Check `/api/bills` in a tab first.

**The heading shows but the area below it is blank**
Expected between `cut-list-fetch` and `cut-list-cards`. `status` is `'loaded'`,
so the grid renders, and `cards` is still `[]`. Fill `cut-list-cards`.

**`TypeError: bills.map is not a function`**
The 501 error object was put into `bills` state because the status check was
dropped. Restore `if (response.status === 200)`.

**`Warning: Each child in a list should have a unique "key" prop`**
No `key` on the mapped `Link`. No test catches this; the console does. The fix is
`key={bill.id}` on the `Link`.

**The card shows `124000` or `₹124000.00`**
`formatRupees` was not used, or was given something that was not paise.
`formatRupees(bill.totalPaise)` gives `₹1240.00`.

**The card reads `Split4 ways`**
JSX swallowed the spaces. The spaces have to be text outside the braces:

```tsx
Split {bill.people} ways
```

**Cards appear in the wrong order**
Something sorted the array. Nothing in this project sorts anything -
`data/bills.json` is the order, the endpoint keeps it, and `map` keeps it.
`Anand Bhavan` first, `Kurry Kulture` last.

**Everything is green but `lib/store.ts` starts with an `import` of the JSON**
`import bills from '../../data/bills.json'` passes all 17 criteria and skips the
lesson session 1 exists for. No test can catch it - you have to read the code.
Prove the difference by editing `data/bills.json` while the server runs.

## Session 2 - one bill and the tip

**`/bills/<anything>` sits on `Loading bill`**
`cut-api-bill-get` is empty, so the endpoint answers 501, which is neither 200 nor
404, so the screen correctly stays put. This is also why `/bills/not-a-bill`
cannot show `Bill not found` until the handler is written.

**`/bills/not-a-bill` shows `Loading bill` instead of `Bill not found`**
The `else if (response.status === 404)` branch is missing from `cut-bill-fetch`.

**`TypeError: Cannot read properties of null (reading 'place')`**
`status` was set to `'loaded'` on the 404 path, so `BillView` was rendered with
no bill. On a 404 the status must be `'not-found'`.

**`Tip amount` reads `₹0.00` and `Total with tip` equals the bill**
`cut-money-tip` is still open. `let tip = 0` is the fallback, and this is exactly
the expected screen until that block is filled.

**The tip is one paisa low: `₹61.28` instead of `₹61.29`**
The tip truncates instead of rounding half up. `Math.floor(totalPaise *
tipPercent / 100)` throws away the half paisa. The half-up form is:

```ts
tip = Math.floor((totalPaise * tipPercent + 50) / 100)
```

Kabab Junction, 87550 paise at 7 percent, is the bill that shows it: the exact
tip is 6128.5 paise. `c-2-6` exists to catch this.

**The tip has extra decimals, or the grand total does**
Something turned paise into rupees mid-calculation - usually a `/ 100` that was
not floored, or a `toFixed`. Every value in this project is a whole number of
paise until `formatRupees` builds the string.

**"The minus and plus buttons do nothing" / "where are the person rows?"**
Both correct in session 2. The stepper markup ships with `BillView.tsx`, but the
block that makes it move is `cut-bill-people` in session 3, and the rows are
hidden behind `shares.length > 0` until session 3 fills `cut-money-split` and
`cut-bill-shares`.

**`c-2-2` and `c-2-5` are green but `findBill` is empty**
Known and expected. `findBill`'s fallback is `bill = null`, which is exactly what
a real miss returns, so the 404 tests cannot tell the difference. Grade
`cut-store-find-one` with `c-2-1` and `c-2-3`, never with the 404 pair alone.

## Session 3 - the split

**`splitPaise` is written and nothing on screen changed**
Expected. Nothing calls it until `cut-bill-shares` is filled.

**Still no rows and no `What each person owes` heading**
`shares` is still `[]`. The heading and the list are both inside
`{shares.length > 0 && (...)}`, so an empty split renders nothing at all rather
than an empty section.

**Rows read `₹310.00` each**
`bill.totalPaise` was split instead of `grandTotalPaise`. The tip was left out.
124000 across 4 is 31000 paise; 136400 across 4 is 34100.

**Three rows all reading `₹454.67` (they add to `₹1364.01`)**
The leftover test is `index <= leftover`. Two paise were left over and three
people were given one. It must be `index < leftover`.

**Three rows all reading `₹454.66` (they add to `₹1363.98`)**
No leftover handling - everyone got `Math.floor`. Two paise disappeared.

**Rows read `₹454.66` and `₹454.67` in the wrong order, or randomly**
The extra paise must go to the people at the *start* of the list, in order.
`c-3-3` reads the rows in order: `₹454.67`, `₹454.67`, `₹454.66`.

**A share shows more than two decimals**
A float got in. Floor the division first, then hand out the remainder.

**The stepper still does nothing after `cut-bill-people` is filled**
Usually `people = Math.min(...)` instead of `setPeople(Math.min(...))`. Assigning
to a variable does not tell React to render.

**The count goes below 1 or above 20**
The clamp is missing or inverted. The one line is:

```ts
setPeople(Math.min(20, Math.max(1, requested)))
```

**The buttons grey out at 1 and 20**
A `disabled` attribute was added. This fails `c-3-5` and `c-3-6` even though the
screen looks sensible: those tests click one more time than the limit allows and
require the button to still be clickable. The clamp belongs in the setter.

**4 to 3 to 4 does not come back to four rows of `₹341.00`**
The shares were put into state and re-split from what was already on screen. The
split has to be rebuilt from `grandTotalPaise` and the current `people` on every
render, which is why `cut-bill-shares` is a plain line in the component body and
not a `useEffect` and not state.

**"I reloaded and the count went back to 4"**
Correct and deliberate. Nothing is written to disk. The stored `people` on the
bill never changes.

**A row reads `Person 1₹341.00` with no space**
Only happens if the row markup was edited. The row ships written as one text run,
and the space between the position and the amount has to be a real character in
the page - whitespace normalisation in the tests can collapse spaces but cannot
invent one:

```tsx
<li className={styles.shareRow} data-testid="share-row" key={index}>
  Person {index + 1} {formatRupees(share)}
</li>
```

## When you run the graded tests

From the repository root:

```bash
python3 -m pipeline.test_runner projects/tip-split --target skeleton --out session-1.json
```

**Everything is red, including criteria from a session that was working**
The production build failed. Read
`projects/tip-split/.pipeline/server-skeleton.log` - the top of it is the output
of `npm run build`, and the real error is there.

**A test times out waiting for an element**
The screen never left its loading state. Work backwards: does the endpoint answer
200 in a browser? Does the fetch check the status? Did the status get moved?

**What should still be red at the start of each session**

| At the start of | Green | Red |
|---|---|---|
| session 1 | none | all 17 |
| session 2 | `c-1-1` to `c-1-5` | `c-2-*`, `c-3-*` |
| session 3 | `c-1-*`, `c-2-*` | `c-3-1` to `c-3-6` |

If a session-2 or session-3 criterion is green before that session starts, a
student has worked ahead - or has found the `import` shortcut in `lib/store.ts`.
