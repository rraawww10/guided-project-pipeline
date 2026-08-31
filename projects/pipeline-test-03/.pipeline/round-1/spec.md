# Ledger

Two 40-minute sessions. Next.js 15 App Router, React 19, TypeScript. One
hand-written text file ships with the project and is read-only. Nothing is
written to disk at runtime, there is no database, no API key, no clock and no
network call out of the app.

## Outcome

A plain-text expense file becomes three things on screen. `/` reads
`GET /api/ledger` and draws a table of the lines that parsed, above a panel of
the lines that did not, each complaint carrying the file line number and one
exact reason. `/accounts/[name]` folds the accepted entries into a total per
account, lists every account down the side, and walks the chosen account's
entries down the page in file order with a running-balance column whose last
value is that account's total.

The point of the project is that a parser returns **errors as data**. Every line
of `data/ledger.txt` is parsed by `parseLine`, which never throws: it answers
either an `Entry` or a `Diagnostic`, and `parseLedger` partitions thirty lines
into two arrays while keeping the original line number attached to each failure.
Six of the file's lines are wrong on purpose, so the failure path is graded as
hard as the success path - `c-1-2` pins all six line numbers and all six reason
strings, and `c-1-1` pins that the other twenty-one still arrived.

Two things this teaches that the shipped projects do not. First, an input that
can be wrong: every other house project reads JSON that is correct by
construction, so no student has yet written a function whose failure path is a
graded return value rather than an exception. Second, a date validated by its
**shape** and not by `Date` - `2026-02-30` is accepted here and `2026-13-02` is
rejected, which is exactly the pair that `new Date(...)` gets wrong, so `c-1-2`
fails any implementation that reaches for the built-in parser.

## Out of scope

- Writing to the ledger. There is no POST, PUT, PATCH or DELETE, no edit form
  and no upload. `data/ledger.txt` ships in the repository, is read on every
  request, and is never modified - so `app/.gitignore` needs no store entry, the
  suite has no world to reset, and every test may run in any order any number of
  times and get the same answer.
- Recovering from a broken line by guessing what it meant. A line either parses
  whole or is rejected whole, with exactly one reason - the first rule it breaks,
  in the fixed order given under **Data model**.
- Double-entry accounting, currencies other than rupees, and any treatment of
  the date beyond an opaque sortable string. Nothing sorts by date, nothing
  parses a month name, nothing knows how many days February has.
- Categories, budgets, charts, date-range filters and search. There is no filter
  control anywhere in the app.
- Navigation from `/` to an account. `/` is a table and a complaints panel and
  carries no links; an account page is reached by typing its name into the URL,
  and from there the sidebar on `/accounts/[name]` links to every other account.
  This keeps a session-1 screen from depending on anything session 2 builds.
- A failed-fetch branch on `/`. `sc-ledger` declares two states, `loading` and
  `loaded`. If `GET /api/ledger` never answers, the page stays on `loading`
  forever, and nothing grades that.
- An empty complaints panel. The seed file is read-only and ships with six
  broken lines, so the zero-diagnostic case cannot arise in this project and no
  element, and no criterion, is specified for it.
- Account names outside `a-z`. Every account in the seed file is lowercase ascii
  letters only, so `/accounts/<name>` needs no URL encoding.

### A constraint, and what checks it

`code_checks: ["utc-dates"]` is declared. It rejects local-time `Date` accessors
and any reading of the real clock (`new Date()` with no argument, `Date.now()`)
anywhere under `app/` at step 6. That is the whole of what it enforces: it does
**not** by itself forbid `new Date("2026-02-30")`, because the argument form is
legal under the check. The rule that dates are validated by shape is instead
graded behaviourally by `c-1-2`, which requires line 20 (`2026-02-30`) to be
accepted and line 22 (`2026-13-02`) to be rejected. `new Date(...)` calls both
of those invalid, so it fails `c-1-2`. Between the static check and `c-1-2`
nothing about dates is left to a person reading code at Gate 3.

## Data model

The Next.js project root is the pipeline's `app/` directory. Inside it sit
`app/` (the App Router tree), `lib/` (the two library modules) and `data/`.
Every path in this spec is written relative to that project root, so the cuts in
`lib/ledger.ts` are the file `app/lib/ledger.ts` as seen from the repository.

### Types

```
Entry       = { lineNo: number; date: string; account: string
                description: string; paise: number }
Diagnostic  = { lineNo: number; reason: string }
ParseResult = { ok: true;  entry: Entry }
            | { ok: false; diagnostic: Diagnostic }
Ledger       = { entries: Entry[]; diagnostics: Diagnostic[] }
AccountTotal = { account: string; paise: number }
```

`paise` is always an integer. No rupee value is ever held as a float, at any
point, in any of these types.

### The line grammar

A raw line is skipped entirely - it produces neither an entry nor a diagnostic -
when its trimmed text is empty, or when its first non-space character is `#`.

Every other line is split on `|` and each field is trimmed. A line is accepted
when all four of these hold:

1. the split gives exactly 4 fields;
2. field 1 is four digits, `-`, two digits in the range `01` to `12`, `-`, two
   digits in the range `01` to `31`, and nothing else - ten characters. No
   calendar check: `2026-02-30` passes and `2026-13-02` does not;
3. field 2 is not the empty string;
4. field 4 is an optional `-`, then one or more digits, then `.`, then exactly
   two digits. No `+`, no thousands separator, no currency symbol, no bare
   integer, no single decimal place.

Fields 1 to 4 are the date, the account, the description and the amount. The
description may be any text, including the empty string.

### The four reason strings, and their order

A rejected line carries exactly one `reason`, the first rule it breaks, checked
in the order 1, 2, 3, 4 above. The strings are pinned here and shipped as
constants in `lib/ledger.ts`, so the Verifier grades wording this spec chose and
not wording the Builder invented:

```ts
export const BAD_FIELDS = (n: number) => `expected 4 fields, found ${n}`
export const BAD_DATE   = "date must be YYYY-MM-DD"
export const NO_ACCOUNT = "account must not be empty"
export const BAD_AMOUNT = "amount must be a rupee amount like -250.00"
```

The order matters and is graded: file line 17 has three fields *and* a valid
date, and its reason is `expected 4 fields, found 3`, not a date complaint.

### Amount to paise

`amountToPaise("-250.05")` is `-25005`. The rupee digits are multiplied by 100
as an integer and the two paise digits are added as an integer; the sign is then
applied. `250.05 * 100` in floating point is `25004.999...`, which is why
`c-1-3` pins line 8 at `-25005` and lines 6, 19 and 10 at `-245075`, `-110550`
and `-12050`.

`formatPaise` is the inverse and ships written: sign, then `Math.floor(abs /
100)`, then `.`, then the remainder as two digits. `-542555` reads `-5425.55`
and `4500000` reads `45000.00`. Every amount shown on either screen is this
string, and every criterion that reads an amount on screen quotes it exactly.

### The seed file

`data/ledger.txt` is exactly these 30 lines, in this order. Line numbers are
1-based over the raw file and are what a `Diagnostic` and an `entry-row-<lineNo>`
carry. Six lines are broken on purpose; they are marked here and the markers are
not part of the file.

```
 1  # ledger - rupees, one entry per line
 2  # date | account | description | amount
 3
 4  2026-01-01 | salary | january pay | 45000.00
 5  2026-01-02 | rent | january rent | -18000.00
 6  2026-01-03 | food | groceries | -2450.75
 7  2026-01-04 | travel | metro card | -500.00
 8  2026-01-05 | food | canteen | -250.05
 9  2026-1-06 | food | tea | -30.00                     <- broken: date shape
10  2026-01-07 | travel | auto | -120.50
11  2026-01-08 | rent | maintenance | -1200.00
12  2026-01-09 | food | dinner | -899.00
13  2026-01-10 |  | printer paper | -450.00             <- broken: empty account
14  2026-01-11 | travel | bus | -45.00
15  2026-01-12 | food | fruit | -310.25
16  2026-01-13 | salary | freelance invoice | 12000.00
17  2026-01-14 | food | coffee                          <- broken: 3 fields
18  2026-01-15 | travel | train ticket | -1650.00
19  2026-01-16 | food | rice and dal | -1105.50
20  2026-02-30 | rent | february rent | -18000.00
21  2026-01-18 | food | snacks | -75.00
22  2026-13-02 | travel | flight | -6000.00             <- broken: month 13
23  2026-01-20 | salary | bonus | 5000.00
24  2026-01-21 | food | milk | -60.00
25  2026-01-22 | utilities | water bill | -350.5        <- broken: one decimal
26  2026-01-23 | travel | cab | -240.00
27  2026-01-24 | food | eggs | -95.00
28  2026-01-25 | rent | electricity | 1,200.00          <- broken: comma
29  2026-01-26 | travel | fuel | -2000.00
30  2026-01-27 | food | lunch | -180.00
```

Lines 1 and 2 are comments and line 3 is blank, so all three are skipped and
none of them appears as a diagnostic - which is what makes the skip rule graded
rather than assumed, since line 2 has four fields and would otherwise complain
about its date.

That gives **21 accepted entries** (lines 4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 16,
18, 19, 20, 21, 23, 24, 26, 27, 29, 30) and **6 diagnostics** (lines 9, 13, 17,
22, 25, 28). Line 20 is deliberately `2026-02-30`: a real date parser rejects
it, this parser accepts it.

The four accounts, their totals in paise, and their entry lines in file order:

| account | lines | total paise | shown as |
|---|---|---|---|
| `food` | 6, 8, 12, 15, 19, 21, 24, 27, 30 | `-542555` | `-5425.55` |
| `rent` | 5, 11, 20 | `-3720000` | `-37200.00` |
| `salary` | 4, 16, 23 | `6200000` | `62000.00` |
| `travel` | 7, 10, 14, 18, 26, 29 | `-455550` | `-4555.50` |

`utilities` is named only by line 25, which is rejected, so it is not an
account: `GET /api/accounts` never mentions it and `/accounts/utilities`
answers 404. That is the case `c-2-2` and `c-2-4` grade.

Running balances, which `c-2-3` and `c-2-5` pin:

| `rent` | paise | running | shown | | `salary` | paise | running | shown |
|---|---|---|---|---|---|---|---|---|
| line 5 | `-1800000` | `-1800000` | `-18000.00` | | line 4 | `4500000` | `4500000` | `45000.00` |
| line 11 | `-120000` | `-1920000` | `-19200.00` | | line 16 | `1200000` | `5700000` | `57000.00` |
| line 20 | `-1800000` | `-3720000` | `-37200.00` | | line 23 | `500000` | `6200000` | `62000.00` |

### What ships written, and what the student writes

`lib/ledger.ts` ships with the type declarations, the four reason constants,
`formatPaise`, and `parseLedger` - the ten-line loop that skips comments and
blanks, calls `parseLine` per line, and pushes each answer onto `entries` or
`diagnostics`. `parseLedger` is deliberately **not** a cut point: the setup
session must carry strictly fewer cut points than session 2, and of the three
candidates the partition loop is the one with the least new idea in it. The two
that carry the lesson - the discriminated union and the integer paise - are cut.

The two functions the student fills in session 1 are shaped so that the return
statement stays outside the markers:

```ts
export function amountToPaise(text: string): number | null {
  let paise: number | null = null
  // >>> CUT cut-amount-paise
  // <<< CUT cut-amount-paise
  return paise
}

export function parseLine(line: string, lineNo: number): ParseResult {
  const fields = line.split("|").map((f) => f.trim())
  let reason: string | null = BAD_FIELDS(fields.length)
  let paise = 0
  // >>> CUT cut-parse-line
  // <<< CUT cut-parse-line
  if (reason !== null) return { ok: false, diagnostic: { lineNo, reason } }
  return { ok: true, entry: { lineNo, date: fields[0], account: fields[1],
                              description: fields[2], paise } }
}
```

The fallbacks fail on purpose: with `cut-parse-line` empty, `reason` stays at
the field-count message, every line is rejected, and `c-1-1` goes red. The three
functions in `lib/accounts.ts` follow the same shape, each with an empty-array
fallback declared above its markers and its `return` below them.

```ts
export function accountTotals(entries: Entry[]): AccountTotal[]   // cut-account-totals
export function accountRows(entries: Entry[], name: string): Entry[]  // cut-account-rows
export function runningBalance(rows: Entry[]): number[]           // cut-running-balance
```

## Endpoints

| id | method | path | status | response |
|---|---|---|---|---|
| `ep-ledger` | GET | `/api/ledger` | 200 | `Ledger` - `entries` in ascending `lineNo`, `diagnostics` in ascending `lineNo` |
| `ep-accounts` | GET | `/api/accounts` | 200 | `AccountTotal[]`, sorted by `account` ascending |

Neither endpoint takes a request body or a query parameter, and neither has a
non-200 answer: both read a file that ships with the project, so there is no
input that could be rejected. `/api/accounts` is served by
`accountTotals(parseLedger(file).entries)`.

## Screens

### `sc-ledger` - route `/`, states `loading` and `loaded`

A client component. It sends one `GET /api/ledger` on mount, no second one, and
no other request. While the response is outstanding it renders one element with
`data-testid="ledger-loading"` and text `Loading`, which is gone once the
response arrives.

Loaded, it renders:

- `data-testid="entry-count"` - the number of accepted entries as a decimal
  string, `21` for the shipped file;
- one `data-testid="entry-row-<lineNo>"` per accepted entry, in ascending
  `lineNo` order, each containing `entry-date-<lineNo>` (the date string
  unchanged), `entry-account-<lineNo>`, `entry-desc-<lineNo>` and
  `entry-amount-<lineNo>` (`formatPaise` of that entry's `paise`);
- `data-testid="reject-count"` - the number of diagnostics as a decimal string,
  `6` for the shipped file;
- one `data-testid="reject-row-<lineNo>"` per diagnostic, in ascending `lineNo`
  order, whose text is exactly `line <lineNo>: <reason>` - so line 17 reads
  `line 17: expected 4 fields, found 3`.

Every element a criterion reads is pinned to a `data-testid`, so styling is free
and the same selector reads in the skeleton.

### `sc-account` - route `/accounts/[name]`, states `loaded` and `not-found`

A server component. It reads `data/ledger.txt` through `parseLedger` directly
and makes no fetch, which is why it has no `loading` state and why an unknown
account can be a real HTTP 404 rather than an empty page.

When `accountRows(entries, name)` is empty, the page calls `notFound()`: the
route answers **404** and renders one element with
`data-testid="account-missing"` and text `Account not found`, and renders no
`account-title` and no `account-total`. The match is exact and case-sensitive,
so `/accounts/Rent` is a 404 while `/accounts/rent` is a 200.

Otherwise it renders:

- `data-testid="account-title"` - the route account name;
- `data-testid="account-total"` - `formatPaise` of that account's total from
  `accountTotals`;
- the sidebar: one `data-testid="account-row-<name>"` per object
  `accountTotals` gives, in that order, each holding an anchor
  `data-testid="account-link-<name>"` with text `<name>` and `href` of
  `/accounts/<name>`, plus `data-testid="account-list-total-<name>"` with
  `formatPaise` of that object's `paise`. This is the navigation: clicking a
  name loads that account's page;
- one `data-testid="account-entry-<lineNo>"` per entry `accountRows` gives, in
  ascending `lineNo` order, each holding `account-entry-date-<lineNo>`,
  `account-entry-desc-<lineNo>`, `account-entry-amount-<lineNo>` and
  `account-entry-running-<lineNo>` - the last being `formatPaise` of the
  `runningBalance` number at the same position.

## Sessions

### Session 1 - Setup, the file, and the parse

**Goal.** Turn a 30-line hand-written ledger file into 21 typed entries and 6
numbered diagnostics, and draw both on one page.

**Teaches.** A discriminated union as a return type instead of a thrown error;
rupee text to integer paise without a float; validating a date by its shape
rather than by `Date`.

**Builds.** `ep-ledger`, `sc-ledger`. This session also carries the project
setup: the Next.js scaffold, the types, the four reason constants,
`formatPaise`, `parseLedger` and `data/ledger.txt`. It therefore carries two cut
points against session 2's three.

**Runs at the end.** A raw text file renders as a table of 21 rows above a list
of 6 specific, numbered complaints.

**Acceptance criteria.**

- **c-1-1** - `GET /api/ledger` returns 200 with `entries` holding 21 objects and
  `diagnostics` holding 6 objects, with `entries[0]` equal to `lineNo` 4, date
  `2026-01-01`, account `salary`, description `january pay` and `paise`
  `4500000`, and `entries[20]` equal to `lineNo` 30, date `2026-01-27`, account
  `food`, description `lunch` and `paise` `-18000`.
  Cuts: `cut-parse-line`, `cut-amount-paise`.
- **c-1-2** - `GET /api/ledger` returns `diagnostics` whose `lineNo` values in
  order are 9, 13, 17, 22, 25 and 28, whose `reason` values in the same order are
  `date must be YYYY-MM-DD`, `account must not be empty`,
  `expected 4 fields, found 3`, `date must be YYYY-MM-DD`,
  `amount must be a rupee amount like -250.00` and
  `amount must be a rupee amount like -250.00`, and returns an entry whose
  `lineNo` is 20 and whose date is `2026-02-30`.
  Cuts: `cut-parse-line`. This is the criterion that grades the rule order (line
  17 complains about fields, not about its date), the skip rule (lines 1 to 3
  produce nothing), and shape-not-`Date` (20 in, 22 out).
- **c-1-3** - `GET /api/ledger` returns the entry with `lineNo` 8 with `paise`
  `-25005`, the entry with `lineNo` 6 with `paise` `-245075`, the entry with
  `lineNo` 19 with `paise` `-110550`, the entry with `lineNo` 10 with `paise`
  `-12050` and the entry with `lineNo` 16 with `paise` `1200000`.
  Cuts: `cut-parse-line`, `cut-amount-paise`. Five different values, four of them
  with non-zero paise digits, so a hardcoded constant cannot pass it and a float
  multiply fails on line 8.
- **c-1-4** - `/` renders `entry-count` with text `21`, renders 21
  `entry-row-<lineNo>` elements whose `lineNo` values in document order are 4, 5,
  6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20, 21, 23, 24, 26, 27, 29 and 30,
  renders `entry-account-4` with text `salary` and `entry-amount-4` with text
  `45000.00`, renders `reject-count` with text `6`, and renders `reject-row-17`
  with text `line 17: expected 4 fields, found 3`.
  Cuts: `cut-parse-line`, `cut-amount-paise`.

**Cut points.**

- **`cut-amount-paise`** in `lib/ledger.ts`, inside `amountToPaise`. The
  student sets `paise`; the `return paise` is below the closing marker. Graded on
  its own by `c-1-3`, which no other single cut can satisfy. Hint: *Set `paise`
  to the whole number of paise in `text` when `text` is an optional `-`, one or
  more digits, a dot, then exactly two digits: multiply the rupee digits by 100,
  add the paise digits as integers, never through a float, and apply the sign.
  Leave `paise` at `null` otherwise.*
- **`cut-parse-line`** in `lib/ledger.ts`, inside `parseLine`. The split and the
  two `return` statements are outside the markers; the student sets `reason` and
  `paise`. Graded on its own by `c-1-2`, which reads the reason strings and their
  order and touches no other cut. Hint: *Set `reason` to
  `BAD_FIELDS(fields.length)` unless `fields` has exactly 4 entries; then to
  `BAD_DATE` unless `fields[0]` is four digits, `-`, a month 01 to 12, `-` and a
  day 01 to 31; then to `NO_ACCOUNT` for an empty `fields[1]`; then to
  `BAD_AMOUNT` when `amountToPaise(fields[3])` gives `null`. Otherwise set
  `paise` from it and `reason` to `null`.*

### Session 2 - Accounts and running balances

**Goal.** Fold the accepted entries into one total per account, and walk a single
account down the page with a running balance that lands on that total.

**Teaches.** Folding a list of entries into a total per key; a scan that emits a
total after every row; an unknown account as a 404 rather than an empty page.

**Builds.** `ep-accounts`, `sc-account`.

**Runs at the end.** Click an account in the sidebar, watch the balance walk down
the page and land on the total shown beside that account's name in the list.

**Acceptance criteria.**

- **c-2-1** - `GET /api/accounts` returns 200 with a JSON array of 4 objects
  whose `account` values in order are `food`, `rent`, `salary` and `travel`, and
  whose `paise` values in the same order are `-542555`, `-3720000`, `6200000`
  and `-455550`.
  Cuts: `cut-parse-line`, `cut-amount-paise`, `cut-account-totals`.
- **c-2-2** - `GET /api/accounts` returns no object whose `account` is
  `utilities`, no object whose `account` is the empty string, and a `rent` object
  whose `paise` is `-3720000`, which is the sum of lines 5, 11 and 20 with the
  rejected line 28 left out.
  Cuts: `cut-parse-line`, `cut-account-totals`. This is the criterion that proves
  a rejected line contributes nothing - to the totals or to the account list.
- **c-2-3** - `/accounts/rent` responds 200 and renders `account-title` with text
  `rent`, `account-total` with text `-37200.00`, exactly 3
  `account-entry-<lineNo>` elements whose `lineNo` values in document order are
  5, 11 and 20, and `account-entry-running-5`, `account-entry-running-11` and
  `account-entry-running-20` with texts `-18000.00`, `-19200.00` and
  `-37200.00`.
  Cuts: `cut-parse-line`, `cut-amount-paise`, `cut-account-rows`,
  `cut-running-balance`.
- **c-2-4** - `/accounts/nope` responds 404 and renders `account-missing` with
  text `Account not found`, `/accounts/utilities` responds 404, `/accounts/Rent`
  responds 404, and `/accounts/salary` responds 200 and renders `account-title`
  with text `salary`.
  Cuts: `cut-parse-line`, `cut-account-rows`. The miss case belongs to
  `cut-account-rows` alone and reaches neither the fold nor the scan.
- **c-2-5** - `/accounts/salary` renders `account-entry-running-4`,
  `account-entry-running-16` and `account-entry-running-23` with texts
  `45000.00`, `57000.00` and `62000.00`, renders `account-total` with text
  `62000.00`, renders exactly 4 `account-link-<name>` elements whose names in
  document order are `food`, `rent`, `salary` and `travel`, and renders
  `account-list-total-food` with text `-5425.55`.
  Cuts: `cut-parse-line`, `cut-amount-paise`, `cut-account-rows`,
  `cut-running-balance`, `cut-account-totals`. A second running-balance fixture,
  on an all-positive account, so the scan is graded on two different shapes and
  the sidebar is graded on the same page.

**Cut points.**

- **`cut-account-totals`** in `lib/accounts.ts`, inside `accountTotals`. Hint:
  *Fill `totals` with one object per distinct `account` in `entries`, its `paise`
  the sum of that account paise values, sorted by `account` ascending as plain
  string order. An account named on no accepted entry never appears, and an
  account whose values cancel to 0 still appears.*
- **`cut-account-rows`** in `lib/accounts.ts`, inside `accountRows`. Hint: *Fill
  `rows` with every object in `entries` whose account equals `name`, keeping them
  in ascending `lineNo` order, which is the order they sit in the file. Match the
  names exactly, so `Rent` does not match `rent`, and leave `rows` empty when no
  entry names that account.*
- **`cut-running-balance`** in `lib/accounts.ts`, inside `runningBalance`. Hint:
  *Fill `running` with one number per object in `rows`, in the same order: each
  one the sum of that object `paise` and of every earlier object `paise`. The
  first number is the first object own `paise`, the last equals the account total
  from `accountTotals`, and an empty `rows` gives an empty `running`.*

### Which criterion fails if only one cut is left empty

Written out so the grading join is checkable by reading, not only by the linter.

| cut | graded by | fails alone on |
|---|---|---|
| `cut-parse-line` | c-1-1, c-1-2, c-1-3, c-1-4, c-2-1, c-2-2, c-2-3, c-2-4, c-2-5 | c-1-2 - `reason` stays at the field-count message for all 27 data lines |
| `cut-amount-paise` | c-1-1, c-1-3, c-1-4, c-2-1, c-2-3, c-2-5 | c-1-3 - `null` for every amount, so every line is rejected with `BAD_AMOUNT` |
| `cut-account-totals` | c-2-1, c-2-2, c-2-5 | c-2-1 - the array is empty |
| `cut-account-rows` | c-2-3, c-2-4, c-2-5 | c-2-4 - every account page 404s, including `/accounts/salary` |
| `cut-running-balance` | c-2-3, c-2-5 | c-2-3 - no `account-entry-running-<lineNo>` element is rendered |

No two cuts carry the same set of criteria, so no cut can be left empty with its
work done inside another one.
