# Ledger

Two 40-minute sessions. Next.js 15 App Router, React 19, TypeScript. One
hand-written text file ships with the project and is read-only. Nothing is
written to disk at runtime, there is no database, no API key, no clock and no
network call out of the app.

This is round 2. Round 1 was rejected at Gate 1 on two blocking findings, both
about the cut-to-criterion join; the arithmetic, the seed file, the session
split and the reason strings were checked line by line and carried over
unchanged. **What changed since round 1** at the end of this file lists every
edit.

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
rejected, which is exactly the pair that `new Date(...)` gets wrong, so `c-1-1`
and `c-1-2` together fail any implementation that reaches for the built-in
parser.

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
- Any loading indicator, and any failed-fetch branch, on `/`. `sc-ledger` has
  one state, `loaded`. What the page draws between mount and the arrival of the
  `GET /api/ledger` response is deliberately unspecified, and no criterion reads
  it; if the response never arrives, nothing is graded. How many times the page
  calls the endpoint is also unspecified: the endpoint is a pure read of a
  read-only file, so a repeat call changes nothing observable.
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
graded behaviourally - `c-1-1` requires line 20 (`2026-02-30`) to arrive as an
entry, and `c-1-2` requires line 22 (`2026-13-02`) to be rejected with
`date must be YYYY-MM-DD`. `new Date(...)` calls both of those invalid, so it
fails `c-1-1`. Between the static check and those two criteria nothing about
dates is left to a person reading code at Gate 3.

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

`data/ledger.txt` is the block below, byte for byte, with no line numbers and no
annotations of any kind in the file. It is 30 lines. The first byte of the file
is `#`. Line 3 holds no characters at all. Every `|` has exactly one space
before it and one space after it, except on line 13, where the account field is
two spaces between two pipes. No line has trailing spaces. There is one final
newline after line 30 and no blank line after it.

```
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

Line numbers are 1-based over that block, counting the two comment lines and the
blank line, and they are what a `Diagnostic` and an `entry-row-<lineNo>` carry.
The six lines that are broken on purpose, each breaking exactly one rule:

| line | text | rule broken | reason |
|---|---|---|---|
| 9 | `2026-1-06 \| food \| tea \| -30.00` | 2 - one digit in the month | `date must be YYYY-MM-DD` |
| 13 | `2026-01-10 \|  \| printer paper \| -450.00` | 3 - account trims to empty | `account must not be empty` |
| 17 | `2026-01-14 \| food \| coffee` | 1 - three fields | `expected 4 fields, found 3` |
| 22 | `2026-13-02 \| travel \| flight \| -6000.00` | 2 - month 13 | `date must be YYYY-MM-DD` |
| 25 | `2026-01-22 \| utilities \| water bill \| -350.5` | 4 - one decimal place | `amount must be a rupee amount like -250.00` |
| 28 | `2026-01-25 \| rent \| electricity \| 1,200.00` | 4 - thousands separator | `amount must be a rupee amount like -250.00` |

Lines 1 and 2 are comments and line 3 is blank, so all three are skipped and
none of them appears as a diagnostic - which is what makes the skip rule graded
rather than assumed, since line 2 has four fields and would otherwise complain
about its date.

That gives **21 accepted entries** (lines 4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 16,
18, 19, 20, 21, 23, 24, 26, 27, 29 and 30) and **6 diagnostics** (lines 9, 13,
17, 22, 25 and 28). Line 20 is deliberately `2026-02-30`: a real date parser
rejects it, this parser accepts it.

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
statement stays outside the markers, and so that the only call to
`amountToPaise` in the whole project sits **above** `cut-parse-line`'s opening
marker, where the student cannot absorb it:

```ts
export function amountToPaise(text: string): number | null {
  let paise: number | null = null
  // >>> CUT cut-amount-paise
  // <<< CUT cut-amount-paise
  return paise
}

export function parseLine(line: string, lineNo: number): ParseResult {
  const fields = line.split("|").map((f) => f.trim())
  const amount = fields.length === 4 ? amountToPaise(fields[3]) : null
  let reason: string | null = BAD_FIELDS(fields.length)
  // >>> CUT cut-parse-line
  // <<< CUT cut-parse-line
  if (reason === null && amount === null) reason = BAD_AMOUNT
  if (reason !== null) return { ok: false, diagnostic: { lineNo, reason } }
  return { ok: true, entry: { lineNo, date: fields[0], account: fields[1],
                              description: fields[2], paise: amount ?? 0 } }
}
```

Three consequences of that placement, and they are the round-1 blocker A1 fix:

- every `paise` value in the project comes from `amountToPaise`, on a line no
  student edits, so `cut-amount-paise` cannot be left empty with its work done
  inside `cut-parse-line`. With it empty, `amount` is `null` for every line, rule
  4 rejects all 27 data lines, and `c-1-1`, `c-1-3` and `c-1-4` go red;
- `cut-parse-line` owns rules 1, 2 and 3 and sets `reason` only. Rule 4 is
  applied below the closing marker, which is why the hint says to set no
  `paise`;
- `c-1-2` reads only the six reason strings, and all six are still correct when
  `cut-amount-paise` is empty (lines 9, 13, 17 and 22 fail an earlier rule;
  lines 25 and 28 are `BAD_AMOUNT` either way). So `c-1-2` grades
  `cut-parse-line` and not `cut-amount-paise`, which is what keeps the two cuts
  independently gradable.

The fallbacks fail on purpose: with `cut-parse-line` empty, `reason` stays at
the field-count message, every line is rejected, and `c-1-1` goes red. The
three functions in `lib/accounts.ts` follow the same shape, each with an
empty-array fallback declared above its markers and its `return` below them.

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

Every element a criterion reads is pinned to a `data-testid`, so styling is free
and the same selector reads in the skeleton. **Every `data-testid` a criterion
names is matched exactly, never as a prefix**, and no `data-testid` in this spec
is a prefix of another one - which is why the account page's row wrapper is
`account-txn-<lineNo>` and its cells are `txn-*-<lineNo>`.

### `sc-ledger` - route `/`, state `loaded`

A client component that renders from `GET /api/ledger`. It has one state: what
it draws before the response arrives is not specified and no criterion reads it,
so there is no loading element and no error element.

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

No `entry-row-1`, `entry-row-2` or `entry-row-3` is ever rendered, because lines
1 to 3 are skipped before parsing. `c-1-4` grades that: it pins the count at 21
and lists the 21 `lineNo` values in document order, and none of 1, 2 or 3 is in
the list.

### `sc-account` - route `/accounts/[name]`, states `loaded` and `not-found`

A server component. It reads `data/ledger.txt` through `parseLedger` directly
and makes no fetch, which is why it has no `loading` state and why an unknown
account can be a real HTTP 404 rather than an empty page.

The route account is missing exactly when `accountRows(entries, name)` is empty.
The page then calls `notFound()`: the route answers **404** and renders one
element with `data-testid="account-missing"` and text `Account not found`, and
renders no `account-title`, no `account-total`, no sidebar and no rows. The match
is exact and case-sensitive, so `/accounts/Rent` is a 404 while `/accounts/rent`
is a 200.

Otherwise it renders:

- `data-testid="account-title"` - the route account name;
- `data-testid="account-total"` - `formatPaise` of the `paise` on the
  `accountTotals(entries)` object whose `account` equals the route name. This is
  the contract, and it is the round-1 blocker A2 fix: the total on this page
  comes from `accountTotals` and not from the last `runningBalance` value, which
  is why `c-2-3` and `c-2-4` both declare `cut-account-totals`. When
  `accountTotals` holds no object for that name - which on a finished build
  cannot happen, because a name with rows always has a total - the element
  renders the single character `-`, a value no `formatPaise` output can equal,
  so the criteria stay red instead of the page throwing;
- the sidebar: one `data-testid="account-row-<name>"` per object
  `accountTotals` gives, in that order, each holding an anchor
  `data-testid="account-link-<name>"` with text `<name>` and `href` of
  `/accounts/<name>`, plus `data-testid="account-list-total-<name>"` with
  `formatPaise` of that object's `paise`. This is the navigation: clicking a
  name loads that account's page, and `c-2-5` grades the `href` on
  `account-link-food` so the click is not decoration;
- one `data-testid="account-txn-<lineNo>"` per entry `accountRows` gives, in
  ascending `lineNo` order, each holding `txn-date-<lineNo>`,
  `txn-desc-<lineNo>`, `txn-amount-<lineNo>` (`formatPaise` of that entry's
  `paise`) and `txn-running-<lineNo>` (`formatPaise` of the `runningBalance`
  number at the same position). When `runningBalance` gives no number at that
  position - which happens only while `cut-running-balance` is empty - the cell
  renders the single character `-`, so `c-2-3` and `c-2-5` go red and the page
  still renders.

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

**Estimated at 38.5 minutes against the 40 cap, and that estimate has been wrong
by up to 13 minutes on flow-2 sessions.** If this session runs long, the drop
candidate inside it is the `entry-desc-<lineNo>` column together with the styling
of the complaints panel: no criterion reads `entry-desc-<lineNo>`, so dropping
the column from the live build costs nothing that is graded. Do not move a cut
into or out of this session to relieve it.

**Acceptance criteria.**

- **c-1-1** - `GET /api/ledger` returns 200 with `entries` holding 21 objects
  whose `lineNo` values in array order are 4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 16,
  18, 19, 20, 21, 23, 24, 26, 27, 29 and 30, with `diagnostics` holding 6 objects
  whose `lineNo` values in array order are 9, 13, 17, 22, 25 and 28, with
  `entries[0]` equal to `lineNo` 4, date `2026-01-01`, account `salary`,
  description `january pay` and `paise` `4500000`, with `entries[20]` equal to
  `lineNo` 30, date `2026-01-27`, account `food`, description `lunch` and `paise`
  `-18000`, and with the entry whose `lineNo` is 20 carrying date `2026-02-30`.
  Cuts: `cut-parse-line`, `cut-amount-paise`. This is where both counts, both
  orderings and the shape-not-`Date` acceptance of line 20 are graded.
- **c-1-2** - `GET /api/ledger` returns a diagnostic whose `lineNo` is 9 and
  whose `reason` is `date must be YYYY-MM-DD`, a diagnostic whose `lineNo` is 13
  and whose `reason` is `account must not be empty`, a diagnostic whose `lineNo`
  is 17 and whose `reason` is `expected 4 fields, found 3`, a diagnostic whose
  `lineNo` is 22 and whose `reason` is `date must be YYYY-MM-DD`, a diagnostic
  whose `lineNo` is 25 and whose `reason` is
  `amount must be a rupee amount like -250.00`, and a diagnostic whose `lineNo`
  is 28 and whose `reason` is `amount must be a rupee amount like -250.00`.
  Cuts: `cut-parse-line`. Each diagnostic is found by its `lineNo`, not by its
  position in the array, which is what makes this criterion pass while
  `cut-amount-paise` is empty and fail the moment `cut-parse-line` is - it is the
  criterion that tells the two session-1 cuts apart. It also grades the rule
  order: line 17 complains about its field count and not about its date.
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
  renders `entry-account-4` with text `salary`, `entry-amount-4` with text
  `45000.00` and `entry-amount-8` with text `-250.05`, renders `reject-count`
  with text `6`, and renders `reject-row-17` with text
  `line 17: expected 4 fields, found 3`.
  Cuts: `cut-parse-line`, `cut-amount-paise`.

**Cut points.**

- **`cut-amount-paise`** in `lib/ledger.ts`, inside `amountToPaise`. The markers
  sit between `let paise: number | null = null` and `return paise`, so the return
  is below the closing marker. It is the project's only conversion from rupee
  text to paise, and the only call to it is on a shipped line above
  `cut-parse-line`'s opening marker. Hint: *Set `paise` to the whole number of
  paise in `text` when `text` is an optional `-`, one or more digits, a dot, then
  exactly two digits: multiply the rupee digits by 100, add the paise digits as
  integers, never through a float, and apply the sign. Leave `paise` at `null`
  otherwise.*
- **`cut-parse-line`** in `lib/ledger.ts`, inside `parseLine`. The markers sit
  between `let reason: string | null = BAD_FIELDS(fields.length)` and
  `if (reason === null && amount === null) reason = BAD_AMOUNT`, so the split,
  the `amountToPaise` call, rule 4 and the two `return` statements are all
  outside them. The student sets `reason` and nothing else. Graded on its own by
  `c-1-2`. Hint: *Set `reason` to `BAD_FIELDS(fields.length)` unless `fields`
  holds exactly 4 strings; then to `BAD_DATE` unless `fields[0]` is four digits,
  `-`, a month `01` to `12`, `-` and a day `01` to `31`; then to `NO_ACCOUNT` for
  an empty `fields[1]`; otherwise to `null`. The amount is judged below the
  markers, so set no `paise` here.*

### Session 2 - Accounts and running balances

**Goal.** Fold the accepted entries into one total per account, and walk a single
account down the page with a running balance that lands on that total.

**Teaches.** Folding a list of entries into a total per key; a scan that emits a
total after every row; an unknown account as a 404 rather than an empty page.

**Builds.** `ep-accounts`, `sc-account`.

**Runs at the end.** Click an account in the sidebar, watch the balance walk down
the page and land on the total shown beside that account's name in the list.

**Estimated at 38.5 minutes against the 40 cap.** If this session runs long, the
drop candidate inside it is the `txn-date-<lineNo>` and `txn-desc-<lineNo>`
columns: no criterion reads either, and the sidebar and the running column are
what the session is for.

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
  Cuts: `cut-parse-line`, `cut-amount-paise`, `cut-account-totals`. This is the
  criterion that proves a rejected line contributes nothing - to the totals or to
  the account list.
- **c-2-3** - `/accounts/rent` responds 200 and renders `account-title` with text
  `rent`, `account-total` with text `-37200.00`, exactly 3
  `account-txn-<lineNo>` elements whose `lineNo` values in document order are
  5, 11 and 20, and `txn-running-5`, `txn-running-11` and `txn-running-20` with
  texts `-18000.00`, `-19200.00` and `-37200.00`.
  Cuts: `cut-parse-line`, `cut-amount-paise`, `cut-account-totals`,
  `cut-account-rows`, `cut-running-balance`. The three row wrappers are counted
  by an exact match on `account-txn-<lineNo>`; `account-txn-` is a prefix of no
  other `data-testid` on the page, and the four cells inside each row start with
  `txn-`.
- **c-2-4** - `/accounts/nope` responds 404 and renders `account-missing` with
  text `Account not found`, `/accounts/utilities` responds 404, `/accounts/Rent`
  responds 404, and `/accounts/salary` responds 200 and renders `account-title`
  with text `salary` and `account-total` with text `62000.00`.
  Cuts: `cut-parse-line`, `cut-amount-paise`, `cut-account-totals`,
  `cut-account-rows`. The miss case belongs to `cut-account-rows` alone - it is
  the only criterion that fails when the rows are empty and the running column is
  not read - and the `account-total` on `/accounts/salary` is what makes this
  criterion depend on `cut-account-totals` as well. It reaches the scan not at
  all, which is what separates `cut-account-rows` from `cut-running-balance`.
- **c-2-5** - `/accounts/salary` renders `txn-running-4`, `txn-running-16` and
  `txn-running-23` with texts `45000.00`, `57000.00` and `62000.00`, renders
  exactly 4 `account-link-<name>` elements whose names in document order are
  `food`, `rent`, `salary` and `travel`, renders `account-link-food` with `href`
  `/accounts/food`, and renders `account-list-total-food` with text `-5425.55`.
  Cuts: `cut-parse-line`, `cut-amount-paise`, `cut-account-totals`,
  `cut-account-rows`, `cut-running-balance`. A second running-balance fixture, on
  an all-positive account, so the scan is graded on two different shapes; and the
  `href` is graded here so the app's only navigation is not four spans with the
  right testids.

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

A criterion's `cuts` list means **every cut it cannot pass without** - that is the
one reading, applied everywhere in `spec.json`. Both directions of the join hold:
each criterion lists every cut it needs, and each cut below is graded by every
criterion that lists it.

| cut | graded by | fails alone on |
|---|---|---|
| `cut-parse-line` | c-1-1, c-1-2, c-1-3, c-1-4, c-2-1, c-2-2, c-2-3, c-2-4, c-2-5 | c-1-2 - every `reason` stays the field-count message, so line 9 reads `expected 4 fields, found 4` |
| `cut-amount-paise` | c-1-1, c-1-3, c-1-4, c-2-1, c-2-2, c-2-3, c-2-4, c-2-5 | c-1-3 - `amount` is `null` on every line, rule 4 rejects all 27, and no entry exists to carry a `paise` |
| `cut-account-totals` | c-2-1, c-2-2, c-2-3, c-2-4, c-2-5 | c-2-1 - the array is empty |
| `cut-account-rows` | c-2-3, c-2-4, c-2-5 | c-2-4 - every account page 404s, including `/accounts/salary` |
| `cut-running-balance` | c-2-3, c-2-5 | c-2-3 - every `txn-running-<lineNo>` cell reads `-` |

No two cuts carry the same set of criteria, so no cut can be left empty with its
work done inside another one. The pair that needs the argument is the session-1
pair: `c-1-2` grades `cut-parse-line` and not `cut-amount-paise`, and
`cut-amount-paise` is unreachable from inside `cut-parse-line` because the only
call to `amountToPaise` sits above that cut's opening marker.

### What changed since round 1

Round 1 was rejected with two blocking findings and seven worth a look. The data
was checked and kept; these are the edits.

- **A1** - the `amountToPaise` call moved above `cut-parse-line`'s opening
  marker, rule 4 moved below its closing marker, and every entry's `paise` now
  comes from `amount`. `cut-parse-line` sets `reason` only. `c-1-2` was rewritten
  to find each diagnostic by `lineNo` rather than by array position, so it passes
  with `cut-amount-paise` empty and fails with `cut-parse-line` empty; the counts
  and orderings it used to carry moved into `c-1-1`.
- **A2** - `account-total` is pinned to `accountTotals`, and
  `cut-account-totals` was added to `c-2-3` and `c-2-4`. `c-2-4` now reads
  `account-total` on `/accounts/salary`, so the dependency it declares is real;
  the same assertion was removed from `c-2-5`, which keeps its sidebar and
  running-balance work.
- **W6** - `cuts` now means "cannot pass without" everywhere, so
  `cut-amount-paise` was added to `c-1-2`'s siblings `c-2-2` and `c-2-4` (and
  `c-1-2` itself does not list it, by A1).
- **W1** - resolved by removal: `ledger-loading` and the `loading` state are
  gone, and **Out of scope** now says what `/` draws before the response arrives
  is unspecified and ungraded. Nothing on this screen is a stated rule that no
  criterion grades.
- **W2** - `c-2-5` grades `href` `/accounts/food` on `account-link-food`.
- **W3** - the account page's row wrapper is now `account-txn-<lineNo>` and its
  cells are `txn-date`, `txn-desc`, `txn-amount` and `txn-running`, so no
  `data-testid` is a prefix of another; **Screens** states that criteria match
  testids exactly and never by prefix.
- **W4** - the seed file is printed with no line-number gutter and no inline
  markers, the broken lines moved to a table beside it, and the first byte, the
  empty line 3, the spacing around `|` and the final newline are pinned.
- **W5** - kept as round 1 wrote it: `parseLedger` ships written, because making
  it a third session-1 cut is `E113`. The idea file still lists it as a student
  task; the spec is the one that governs.
- **W7** - both sessions still estimate 38.5 minutes. No hint was shortened to
  duck a threshold - `cut-parse-line` got shorter because rule 4 left it, which
  is a real reduction in the work. Each session now names its own drop candidate
  above, and session 1 should be timed first at step 9.
