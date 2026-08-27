# Tip Split - instructor pack

A shelf of restaurant bills a student can browse, open, and re-split across a
different number of people. It runs offline from one JSON file on disk. Three
sessions of 40 minutes, and something runs at the end of each one.

**Read this page once before session 1. Then teach from `session-1.md`,
`session-2.md`, `session-3.md`, with `troubleshooting.md` open beside you.**

## Read this first: one honest warning about session 1

Session 1 is the tight one. Its material is about 45 minutes and the plan buys
the 5 minutes back in two named places. Both are things you do **before class**:

1. Run `npm install` in every student's `skeleton/` folder before the session
   starts, or have them run it the night before. In class it costs 5 to 8
   minutes of dead air.
2. You type the `Link` wrapper and the first field of the card, and the students
   type the other three fields. Do not type all 21 lines of card markup yourself.

Sessions 2 and 3 fit 40 minutes as written. Session 2 has no slack either - it
carries the longest list of new ideas in the project - but it has no setup cost.

## What a student has at the end

- A list screen at `/` showing all 6 seed bills. Each card is a link carrying the
  place, the date, the bill total and how many people it was split between.
- A bill screen at `/bills/<id>` showing that bill's total, its tip percentage,
  the tip in rupees, the total with tip, and one row per person.
- A people stepper on that screen. Moving it from 4 to 3 rewrites every share,
  and moving it back to 4 restores the bill exactly as it was saved.
- Two GET route handlers over one JSON file. Nothing is ever written to disk.

The payoff is session 3. It is the first time in the track that the number on
screen is computed from React state rather than read from a server response, and
because it is money, a student can see in one click whether it is right.

## The stack

Next.js 15 (App Router), React 19, TypeScript, plain CSS modules. No database, no
state library, no CSS framework.

## How to run it

The student's project is `skeleton/`. From inside that folder:

```bash
npm install     # once, before the first session
npm run dev     # then open http://localhost:3000
```

The dev server picks up every save. Nothing needs restarting except when
`data/bills.json` is edited by hand and the JSON is left broken.

To run the graded tests yourself, from the repository root:

```bash
python3 -m pipeline.test_runner projects/tip-split --target skeleton --out session-1.json
```

That command does `npm ci`, then `npm run build`, then `npm run start` on a free
port, and writes one entry per criterion. It uses a **production build**, so any
TypeScript error anywhere in the project turns every criterion red at once, not
one of them. Read the build log at `projects/tip-split/.pipeline/server-skeleton.log`
before you believe a wall of red.

## The file map

```
skeleton/
  data/bills.json                    the store: 6 bills, read-only
  lib/types.ts                       type Bill - ships written
  lib/money.ts                       formatRupees ships written; tipPaise and splitPaise are cut
  lib/store.ts                       readAllBills and findBill - both cut
  app/api/bills/route.ts             GET /api/bills - cut
  app/api/bills/[id]/route.ts        GET /api/bills/[id] - cut
  app/page.tsx                       the list screen - two cuts
  app/bills/[id]/page.tsx            the bill screen: id, fetch, three states - one cut
  app/bills/[id]/BillView.tsx        the loaded bill, the stepper, the rows - two cuts
  app/globals.css, *.module.css      all styling ships written
```

## The 6 seed bills

They never change. Every criterion counts and reads against them.

| id | place | date | totalPaise | tipPercent | people |
|---|---|---|---|---|---|
| `anand-bhavan` | Anand Bhavan | `2026-03-14` | 124000 | 10 | 4 |
| `kabab-junction` | Kabab Junction | `2026-02-28` | 87550 | 7 | 3 |
| `the-filter-room` | The Filter Room | `2026-02-09` | 45000 | 5 | 2 |
| `paradise-biryani` | Paradise Biryani | `2026-01-26` | 233375 | 12 | 6 |
| `chai-point-mg` | Chai Point MG Road | `2026-01-05` | 19900 | 15 | 2 |
| `kurry-kulture` | Kurry Kulture | `2025-12-19` | 310000 | 8 | 5 |

Worked answers you will need at the board:

| bill | tip in paise | total with tip |
|---|---|---|
| anand-bhavan | 12400 | 136400 |
| kabab-junction | 6129 | 93679 |
| the-filter-room | 2250 | 47250 |
| paradise-biryani | 28005 | 261380 |
| chai-point-mg | 2985 | 22885 |
| kurry-kulture | 24800 | 334800 |

136400 across 4 is `[34100, 34100, 34100, 34100]`.
136400 across 3 is `[45467, 45467, 45466]`.
136400 across 1 is `[136400]`.

## The one rule that runs through all three sessions

**Money is whole paise, everywhere.** `totalPaise`, the tip, the total with tip
and every share are integers counting paise. The only place a decimal point ever
exists is inside `formatRupees`, which builds a string. Say this in session 1 and
say it again in sessions 2 and 3. Every money bug in this project is a student
who reached for rupees in the middle of a calculation.

`formatRupees` ships written and is not a cut point. It is in `lib/money.ts`:

```ts
/** Ships written: 124000 -> "₹1240.00", 6129 -> "₹61.29", 34100 -> "₹341.00". */
export function formatRupees(paise: number): string {
  const rupees = Math.floor(paise / 100)
  const paisaPart = String(paise % 100).padStart(2, '0')
  return `₹${rupees}.${paisaPart}`
}
```

## The 11 cut points, by session

| session | cut | file | lines to write |
|---|---|---|---|
| 1 | `cut-store-read-all` | `lib/store.ts` | 3 |
| 1 | `cut-api-bills-list` | `app/api/bills/route.ts` | 3 |
| 1 | `cut-list-fetch` | `app/page.tsx` | 8 |
| 1 | `cut-list-cards` | `app/page.tsx` | 21 |
| 2 | `cut-store-find-one` | `lib/store.ts` | 1 |
| 2 | `cut-api-bill-get` | `app/api/bills/[id]/route.ts` | 8 |
| 2 | `cut-bill-fetch` | `app/bills/[id]/page.tsx` | 10 |
| 2 | `cut-money-tip` | `lib/money.ts` | 1 |
| 3 | `cut-money-split` | `lib/money.ts` | 5 |
| 3 | `cut-bill-shares` | `app/bills/[id]/BillView.tsx` | 1 |
| 3 | `cut-bill-people` | `app/bills/[id]/BillView.tsx` | 1 |

Every cut is a block **inside** a function. The variable it fills is declared
above it and the `return` is below it, so the skeleton always compiles. Tell
students this on day one: **never move or delete the `return` line.** Fill the
block, leave everything around it alone.

## One thing to know before you grade a checkpoint

`c-2-2` and `c-2-5` both test the 404 path, and they go green even when
`cut-store-find-one` is still empty - a store that finds nothing and a store that
correctly finds nothing look the same from outside. So never show a student a
green `c-2-2` as proof that `findBill` works. Pair `c-2-2` with `c-2-1`, and
`c-2-5` with `c-2-3`. Every other criterion in the project is honest about its
cuts.

## Two things no test can see, so you have to

1. **`readAllBills` must use `node:fs`.** `import bills from '../../data/bills.json'`
   passes all 17 criteria and skips the entire lesson session 1 is named for.
   Check this by reading the student's code, not by reading a green test.
2. **The `key` on each card.** No criterion can see a key. The console warning is
   the teaching moment - session 1 tells you how to use it.
