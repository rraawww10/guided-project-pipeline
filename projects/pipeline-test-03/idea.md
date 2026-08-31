# Ledger

**One line:** A plain-text expense file that becomes a table of typed entries, a
list of complaints about the lines that were malformed, and a running balance per
account.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

The store is not JSON this time - it is a hand-written text file, the kind a
person actually keeps. Every line has to be parsed, and about a fifth of them are
wrong on purpose. The lesson is that a parser returns *errors as data*, with a
line number and a reason, instead of throwing and losing the other forty lines.
Once the entries are typed, a single fold turns them into balances, and the same
seed file is the evidence for both halves.

## Sessions

1. **Setup, the file, and the parse.** Types, `data/ledger.txt` (about 30 lines,
   6 of them deliberately broken), `parseLine(line, lineNo)` returning either an
   entry or a diagnostic, `parseLedger` collecting both lists, `GET /api/ledger`,
   and `/` showing a table of accepted entries above a panel of rejected lines
   with their line numbers and reasons. **Runs:** a raw text file renders as a
   table plus a list of specific, numbered complaints.
2. **Accounts and running balances.** `balances(entries)` folding entries into a
   per-account total in paise, `GET /api/accounts` returning accounts sorted by
   name with their totals, and `/accounts/[name]` showing that account's entries
   in file order with a running-balance column and a 404 for an account the file
   never mentions. **Runs:** click an account, watch the balance walk down the
   page and land on the total from the list.

## What the student types

- `parseLine` - split on the pipe, count the fields, validate the `YYYY-MM-DD`
  date by shape not by `Date`, and convert `-250.00` to the integer `-25000`
  paise without touching a float. Returns a discriminated union, never throws.
- `parseLedger` - the fold that partitions 30 lines into two arrays while keeping
  the original line numbers attached to the failures.
- `runningBalance` - the scan that emits a total after each entry, which is the
  same accumulator as `balances` viewed one row at a time.

## What this teaches that the shipped projects do not

Every shipped project reads a JSON file that is correct by construction. This is
the first one whose input can be wrong, so it is the first place a student writes
a function whose *failure* path is graded as hard as its success path. tip-split
did paise arithmetic, and that part is not new; what is new is a discriminated
union as a return type, and a diagnostic that has to name the right line number
out of thirty.

## Out of scope

- Editing the ledger, writing entries back, or any POST. The file is read-only.
- Double-entry accounting, currencies other than rupees, dates as anything other
  than an opaque sortable string.
- Categories, budgets, charts, date-range filters. There is no filter UI at all.
- Recovering from a broken line by guessing what it meant. It is rejected.

## Risks

Parser grammar sprawls. The spec has to state the accepted line shape and the
closed list of rejection reasons up front, and pin each reason's exact string,
or the Verifier grades wording the Builder invented. Second risk: session 2 is
thin if it is only a sum - the running-balance column and the file-order rule are
what make it worth 40 minutes, and they must be graded separately from the total.
Third: paise conversion needs a fixture with a `.05` on it, because `* 100` on a
float is right for `250.00` and wrong for `250.05`.
