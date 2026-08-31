# Ledger - instructor pack

A hand-written text file becomes a working app. `data/ledger.txt` is thirty
lines of somebody's expenses, six of them wrong on purpose. `/` draws the lines
that parsed as a table, above a panel of the lines that did not, each complaint
carrying the file line number and one exact reason. `/accounts/[name]` folds the
accepted lines into a total per account, lists every account down the side, and
walks one account down the page with a running balance that lands on that total.

The idea being taught is **errors as data**. `parseLine` never throws. It returns
one of two shapes, and the caller decides which pile the answer goes on. The
failure path is graded as hard as the success path.

**Stack:** Next.js 15.5.24 App Router, React 19, TypeScript 5.7 strict.
No database, no writes to disk at runtime, no API key, no clock, no network call
out of the app. The seed file is read on every request and never modified, so the
app answers the same on the tenth run as on the first.

**Shape:** 2 sessions, 5 cut points, 9 acceptance criteria.

---

## Read this before you schedule the sessions

`spec.md` estimates both sessions at 38.5 minutes against a 40-minute cap.
**This pack does not agree.** Timed cut by cut against the real code, the plans
come out at:

| session | spec estimate | this pack | over the cap by |
|---|---|---|---|
| 1 - Setup, the file, and the parse | 38.5 | **48** | 8 |
| 2 - Accounts and running balances | 38.5 | **45** | 5 |

Two things a person at Gate 3 should know about that gap.

**The spec's own relief valves do not work.** Session 1 names
`entry-desc-<lineNo>` and the styling of the complaints panel as its drop
candidate; session 2 names the `txn-date-<lineNo>` and `txn-desc-<lineNo>`
columns. All three are page markup, and **all three ship already written in the
student skeleton.** Nobody types them in either session, so dropping them
recovers nothing. Do not plan on them.

**The trims that do recover minutes are named in each session file**, under
`Timing - the overrun and what to trim`. They are about live teaching time, not
about `app/`: nothing graded is removed by any of them.

This is the fifth consecutive project to land here, and `learning/lessons.md`
already says why - the estimator charges a flat 6 minutes per cut and cannot see
how many rules live inside one. The step 13 dry run is the measurement that
settles it.

---

## What the student is handed

The skeleton is the finished app with five bodies removed. Everything else -
scaffold, types, constants, both API routes, both pages, the 404 boundary, the
seed file, the CSS - ships written.

```text
skeleton/
  app/
    page.tsx                      sc-ledger, the client component  (ships written)
    layout.tsx                    (ships written)
    globals.css                   (ships written)
    api/ledger/route.ts           ep-ledger                        (ships written)
    api/accounts/route.ts         ep-accounts                      (ships written)
    accounts/[name]/page.tsx      sc-account, a server component   (ships written)
    accounts/[name]/not-found.tsx the 404 body                     (ships written)
  lib/
    ledger.ts                     2 TODOs - session 1
    accounts.ts                   3 TODOs - session 2
  data/ledger.txt                 the seed file, read-only         (ships written)
```

**All five cut points are in `lib/`.** No student writes a line of JSX or a line
of routing in this project. That is worth saying out loud on day one, because a
student who goes looking for their work in `app/` will not find it.

## The five cut points

| cut | file (skeleton line) | session | graded by | fails alone on |
|---|---|---|---|---|
| `cut-amount-paise` | `lib/ledger.ts:52` | 1 | c-1-1, c-1-3, c-1-4, c-2-1, c-2-2, c-2-3, c-2-4, c-2-5 | c-1-3 |
| `cut-parse-line` | `lib/ledger.ts:60` | 1 | all nine | c-1-2 |
| `cut-account-totals` | `lib/accounts.ts:17` | 2 | c-2-1, c-2-2, c-2-3, c-2-4, c-2-5 | c-2-1 |
| `cut-account-rows` | `lib/accounts.ts:23` | 2 | c-2-3, c-2-4, c-2-5 | c-2-4 |
| `cut-running-balance` | `lib/accounts.ts:29` | 2 | c-2-3, c-2-5 | c-2-3 |

"Fails alone on" is the criterion that goes red when *only* that cut is left
empty - so it is the one to point a stuck student at.

## The nine criteria

| id | session | what it reads | test |
|---|---|---|---|
| c-1-1 | 1 | `GET /api/ledger` - 21 entries and 6 diagnostics, in line order | `verify/test_api_ledger.py` |
| c-1-2 | 1 | all six reasons, each found by its `lineNo` | `verify/test_api_ledger.py` |
| c-1-3 | 1 | five `paise` values, four with non-zero paise digits | `verify/test_api_ledger.py` |
| c-1-4 | 1 | `/` - counts, 21 rows in order, two amounts, one complaint | `verify/test_ui_ledger.py` |
| c-2-1 | 2 | `GET /api/accounts` - four totals sorted by name | `verify/test_api_accounts.py` |
| c-2-2 | 2 | no `utilities`, no empty account, `rent` at `-3720000` | `verify/test_api_accounts.py` |
| c-2-3 | 2 | `/accounts/rent` - title, total, 3 rows, the running column | `verify/test_ui_account.py` |
| c-2-4 | 2 | 404 for `nope`, `utilities` and `Rent`; 200 for `salary` | `verify/test_ui_account.py` |
| c-2-5 | 2 | `/accounts/salary` running column, the sidebar of four links | `verify/test_ui_account.py` |

All nine pass on `app/`. All nine fail on the untouched skeleton.

## The seed file

Thirty lines. Lines 1 and 2 are comments, line 3 is empty, so line numbers run
from 4 to 30 over the data and those numbers are what every diagnostic and every
`entry-row-<lineNo>` carries.

```text
# ledger - rupees, one entry per line
# date | account | description | amount

2026-01-01 | salary | january pay | 45000.00
2026-01-02 | rent | january rent | -18000.00
2026-01-03 | food | groceries | -2450.75
2026-01-04 | travel | metro card | -500.00
2026-01-05 | food | canteen | -250.05
2026-1-06 | food | tea | -30.00
2026-01-07 | travel | auto | -120.50
2026-01-08 | rent | maintenance | -1200.00
2026-01-09 | food | dinner | -899.00
2026-01-10 |  | printer paper | -450.00
2026-01-11 | travel | bus | -45.00
2026-01-12 | food | fruit | -310.25
2026-01-13 | salary | freelance invoice | 12000.00
2026-01-14 | food | coffee
2026-01-15 | travel | train ticket | -1650.00
2026-01-16 | food | rice and dal | -1105.50
2026-02-30 | rent | february rent | -18000.00
2026-01-18 | food | snacks | -75.00
2026-13-02 | travel | flight | -6000.00
2026-01-20 | salary | bonus | 5000.00
2026-01-21 | food | milk | -60.00
2026-01-22 | utilities | water bill | -350.5
2026-01-23 | travel | cab | -240.00
2026-01-24 | food | eggs | -95.00
2026-01-25 | rent | electricity | 1,200.00
2026-01-26 | travel | fuel | -2000.00
2026-01-27 | food | lunch | -180.00
```

The six lines broken on purpose, each breaking exactly one rule:

| line | what is wrong | reason string |
|---|---|---|
| 9 | one digit in the month | `date must be YYYY-MM-DD` |
| 13 | the account field trims to empty | `account must not be empty` |
| 17 | three fields, no amount | `expected 4 fields, found 3` |
| 22 | month 13 | `date must be YYYY-MM-DD` |
| 25 | one decimal place | `amount must be a rupee amount like -250.00` |
| 28 | a thousands separator | `amount must be a rupee amount like -250.00` |

That leaves **21 accepted** and **6 rejected**. The four accounts:

| account | lines | total paise | shown as |
|---|---|---|---|
| `food` | 6, 8, 12, 15, 19, 21, 24, 27, 30 | `-542555` | `-5425.55` |
| `rent` | 5, 11, 20 | `-3720000` | `-37200.00` |
| `salary` | 4, 16, 23 | `6200000` | `62000.00` |
| `travel` | 7, 10, 14, 18, 26, 29 | `-455550` | `-4555.50` |

`utilities` is named only by line 25, which is rejected, so it is not an account
at all: `/api/accounts` never mentions it and `/accounts/utilities` is a 404.

## How to run it

Each tree has its own `node_modules`. Install in whichever one you are opening.

```text
cd projects/pipeline-test-03/skeleton     # or .../app for the finished build
npm ci
npm run dev
```

Then `http://localhost:3000/` and `http://localhost:3000/accounts/rent`.
Use `npm run dev`, not `npm run start` - both pages are `force-dynamic` and a
stale production build will not pick up an edit to `lib/`.

To run the graded suite yourself, let the pipeline boot the app:

```text
python3 -m pipeline test pipeline-test-03 --target skeleton
python3 -m pipeline test pipeline-test-03 --target app
```

It builds, starts the server on a free port, sets `BASE_URL`, runs pytest with
Playwright and writes `results.json` / `skeleton-results.json`. Do not start the
server yourself first.

## Two claims in spec.md that are wrong - do not repeat them in class

Both were raised at Gate 1 and both were left in the spec. They land in the
teaching, so they are corrected here.

**1. `new Date("2026-02-30")` is not invalid.** `spec.md` says line 20
(`2026-02-30`) is the fixture that catches a student reaching for the built-in
date parser. It is not. `2026-02-30` is a well-formed ISO date string as far as
the engine is concerned - the day field is only checked for `01`-`31` - so
`new Date("2026-02-30")` is a *valid* Date that silently rolls over to 2 March.

The fixture that actually catches `Date` is **line 9, `2026-1-06`**: the ISO
parser rejects the one-digit month, the legacy fallback parses it happily as
6 January, so a `Date`-based check *accepts* line 9 and goes red on c-1-1 (22
entries, wrong line list) and on c-1-2 (no diagnostic at 9).

Teach line 20 as the **silent rollover** - `Date` does not reject it, it changes
it into a different day, and this parser stores the string it was given.

**2. "never through a float" is not graded.** `spec.md` says a float multiply
fails c-1-3. Only a *truncating* one does.
`Math.round(parseFloat(text) * 100)` returns all five values c-1-3 pins and is
green on every criterion in the project. Teach the integer path because it is
right, and say plainly that here the tests do not catch the difference - the
rounding hides it, and on a longer file it would not.

## Files in this pack

- `session-1.md` - Setup, the file, and the parse
- `session-2.md` - Accounts and running balances
- `troubleshooting.md` - the errors students actually hit, with the fix
