# Session 2 - Accounts and running balances

**Time:** the plan below runs to 45 minutes against a 40-minute cap. That is an
overrun of five, disclosed at the bottom with what to trim.

**Students start from:** `/` drawing 21 rows and 6 complaints - session 1
finished. `lib/accounts.ts` is three functions with an empty array in each and a
`TODO` in the middle. Because of that, `GET /api/accounts` answers `[]` and
**every** account page is a 404, including `/accounts/rent`.

**Students end with:** `/accounts/rent` showing a title, a total, a sidebar of
four linked accounts, and three rows whose running column walks down to the
total at the top; the sidebar links working; `/accounts/nope` still a 404.
c-2-1 through c-2-5 green, and with them the whole project.

## What they learn

1. **Folding a list into a total per key.** One pass over the entries with a
   `Map`, then the keys sorted, then one object per key. The order of the output
   is part of the contract.
2. **A scan.** Like a fold, but it emits the total after *every* row instead of
   only at the end. One carried variable, pushed once per row.
3. **An unknown account is a 404, not an empty page.** `/accounts/[name]` is a
   server component, so it can answer with an HTTP status - and `notFound()`
   throws, which is why the "not found" markup lives in its own file.
4. That a rejected line contributes nothing, anywhere: no total, no row, and no
   entry in the account list.

## Before you start

- Every student's `/` reads 21 and 6. If someone is not there, pair them up -
  nothing today works without both of session 1's cuts.
- Have open: `lib/accounts.ts`, `app/accounts/[name]/page.tsx`, and the browser
  on `/accounts/rent` (a 404 right now).
- Have the account table from `README.md` on the board: `food -5425.55`,
  `rent -37200.00`, `salary 62000.00`, `travel -4555.50`. Students will check
  their own work against it all session.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Recap `/`. Then open `/accounts/rent` - a real 404, not an empty page. Then `/api/accounts` - an empty array. Both from the same cause: `lib/accounts.ts` is three empty functions. Open it. |
| 4-8 | The three folds, on the board, before any code. Totals per account. The rows of one account. The running balance beside those rows. Show the finished page shape and point at which fold feeds which part of it. |
| 8-18 | Live: `cut-account-totals`. Reload `/api/accounts` - four objects, in name order. `/accounts/rent` is still a 404, and ask why before you answer. |
| 18-25 | Live: `cut-account-rows`. Reload `/accounts/rent` - the page appears, and the running column is a row of dashes. |
| 25-34 | Live: `cut-running-balance`. Reload - the column fills in and the last number equals the total at the top. |
| 34-42 | Students catch up. Circulate. Everyone checks `rent` and `salary` against the numbers on the board. |
| 42-45 | Click `salary` in the sidebar, then `food`. Follow the running column down to the total. Then `/accounts/utilities` - still a 404, because line 25 was rejected in session 1 and a rejected line is not an account. |

## Cut points in this session

### cut-account-totals - `lib/accounts.ts:17`

**What students see** (the skeleton, exactly):

```ts
export function accountTotals(entries: Entry[]): AccountTotal[] {
  const totals: AccountTotal[] = []
  // TODO(cut-account-totals): Fill `totals` with one object per distinct `account` in `entries`, its `paise` the sum of that account paise values, sorted by `account` ascending as plain string order. An account named on no accepted entry never appears, and an account whose values cancel to 0 still appears.
  return totals
}
```

**What they write.** One pass over `entries` accumulating a sum per account name
into a `Map`. Then the map's keys, sorted as plain strings, and one object pushed
onto `totals` per key. Sorted output is not decoration - c-2-1 pins the order.

**Teach it like this.** "A fold is: start with nothing, look at each item once,
and end with one answer. Here the 'nothing' is an empty `Map` and the answer is
one number per name. The `Map` is doing the grouping; the sort is doing the
contract."

Two things to make explicit:

- **The `?? 0`.** The first time an account is seen there is no entry in the map
  yet. `summed.get(name)` is `undefined`, not `0`, and `undefined + n` is `NaN`.
  This is the line that bites, and it bites silently - the page renders `NaN.00`
  rather than throwing.
- **What is *not* in `entries`.** `utilities` is on line 25, which was rejected,
  so it never reaches this function. Neither does the empty account name on line
  13. Nothing here filters them out - session 1 already did. That is c-2-2.

Say why `.sort()` with no argument is right here: these are strings, and plain
string order is exactly what the contract asks for. A comparator meant for
numbers on strings gives `NaN` and silently leaves the order alone.

**Reference solution** - instructor's copy, from `app/lib/accounts.ts`:

```ts
export function accountTotals(entries: Entry[]): AccountTotal[] {
  const totals: AccountTotal[] = []
  const summed = new Map<string, number>()
  for (const entry of entries) {
    summed.set(entry.account, (summed.get(entry.account) ?? 0) + entry.paise)
  }
  for (const account of [...summed.keys()].sort()) {
    totals.push({ account, paise: summed.get(account) ?? 0 })
  }
  return totals
}
```

**Passes when:** c-2-1 goes green - `GET /api/accounts` gives four objects in
name order with the right paise - and c-2-2 with it.

### cut-account-rows - `lib/accounts.ts:23`

**What students see** (the skeleton, exactly):

```ts
export function accountRows(entries: Entry[], name: string): Entry[] {
  const rows: Entry[] = []
  // TODO(cut-account-rows): Fill `rows` with every object in `entries` whose account equals `name`, keeping them in ascending `lineNo` order, which is the order they sit in the file. Match the names exactly, so `Rent` does not match `rent`, and leave `rows` empty when no entry names that account.
  return rows
}
```

**What they write.** Every entry whose `account` is exactly `name`, pushed onto
`rows`, then sorted by `lineNo` ascending. An exact `===` on the name - no
lowercasing, no trimming, no `includes`. When nothing matches, `rows` stays
empty, and that is the answer, not a failure.

**Teach it like this.** "This one is a filter, and the interesting part is what
it does when it finds nothing. Empty is a real answer. The page is the thing that
decides an empty list means 404."

Now show them the four lines on the page that turn the empty array into an HTTP
status, because this is the part they cannot see from `lib/`:

```tsx
  const { name } = await params
  const text = readFileSync(path.join(process.cwd(), "data", "ledger.txt"), "utf8")
  const { entries } = parseLedger(text)

  const rows = accountRows(entries, name)
  if (rows.length === 0) notFound()

  const totals = accountTotals(entries)
  const total: AccountTotal | undefined = totals.find(
    (candidate) => candidate.account === name,
  )
  const running = runningBalance(rows)
```

`notFound()` **throws**. The component stops right there and renders nothing, so
the "Account not found" markup cannot live in this file - it lives in
`app/accounts/[name]/not-found.tsx`, which ships written:

```tsx
export default function AccountNotFound() {
  return (
    <main className="page">
      <h1>Ledger</h1>
      <p data-testid="account-missing">Account not found</p>
    </main>
  )
```

Say why the match is case-sensitive and mean it: `/accounts/Rent` is a 404 and
c-2-4 pins that. A student who "helpfully" lowercases the name turns a graded
404 into a 200.

**Reference solution** - instructor's copy, from `app/lib/accounts.ts`:

```ts
export function accountRows(entries: Entry[], name: string): Entry[] {
  const rows: Entry[] = []
  for (const entry of entries) {
    if (entry.account === name) rows.push(entry)
  }
  rows.sort((a, b) => a.lineNo - b.lineNo)
  return rows
}
```

The sort is belt and braces: `entries` is already in file order, so `rows` comes
out in `lineNo` order without it. Say that out loud - it is the honest reading -
and keep the sort, because the function's contract should not depend on how its
caller happened to build the list.

**Passes when:** c-2-4 goes green - `/accounts/salary` answers 200 while
`/accounts/nope`, `/accounts/utilities` and `/accounts/Rent` all stay 404.

### cut-running-balance - `lib/accounts.ts:29`

**What students see** (the skeleton, exactly):

```ts
export function runningBalance(rows: Entry[]): number[] {
  const running: number[] = []
  // TODO(cut-running-balance): Fill `running` with one number per object in `rows`, in the same order: each one the sum of that object `paise` and of every earlier object `paise`. The first number is the first object own `paise`, the last equals the account total from `accountTotals`, and an empty `rows` gives an empty `running`.
  return running
}
```

**What they write.** One carried number starting at zero. For each row: add that
row's `paise` to the carried number, then push the carried number. One number
out per row in, in the same order. An empty `rows` gives an empty `running`.

**Teach it like this.** "Same shape as the totals fold, one line different: we
push *inside* the loop instead of after it. A fold gives you the answer at the
end; a scan gives you the answer so far, after every step. That is the whole
difference."

Walk `rent` on the board while you type it: `-18000.00`, then `-19200.00`, then
`-37200.00` - and that last number is the total already showing at the top of the
page. That is the check students can run on themselves for the rest of the
session.

Order matters twice: add before you push, or every row shows the balance from
*before* it; and push inside the loop, or you get one number instead of three.

**Reference solution** - instructor's copy, from `app/lib/accounts.ts`:

```ts
export function runningBalance(rows: Entry[]): number[] {
  const running: number[] = []
  let carried = 0
  for (const row of rows) {
    carried += row.paise
    running.push(carried)
  }
  return running
```

Then show the cell that reads it, so the dash they have been staring at all
session has an explanation:

```tsx
          {rows.map((row, index) => {
            const carried: number | undefined = running[index]
            return (
              <tr key={row.lineNo} data-testid={`account-txn-${row.lineNo}`}>
                <td>{row.lineNo}</td>
                <td data-testid={`txn-date-${row.lineNo}`}>{row.date}</td>
                <td data-testid={`txn-desc-${row.lineNo}`}>{row.description}</td>
                <td className="num" data-testid={`txn-amount-${row.lineNo}`}>
                  {formatPaise(row.paise)}
                </td>
                <td className="num" data-testid={`txn-running-${row.lineNo}`}>
                  {carried === undefined ? "-" : formatPaise(carried)}
                </td>
              </tr>
            )
          })}
```

`running[index]` is `undefined` while the function returns an empty array, and
the page draws `-` rather than throwing. That is deliberate: a missing answer
looks missing, and the criterion stays red instead of the page dying.

**Passes when:** c-2-3 goes green on `/accounts/rent`, and c-2-5 on
`/accounts/salary` - a second running column, all positive, so the scan is graded
on two different shapes.

## The code that ships written, and that you will read on screen

The endpoint - one line of work, and it is the fold they just wrote:

```ts
export async function GET(): Promise<Response> {
  const text = readFileSync(path.join(process.cwd(), "data", "ledger.txt"), "utf8")
  const totals: AccountTotal[] = accountTotals(parseLedger(text).entries)
  return Response.json(totals)
}
```

The sidebar, which is the app's only navigation. c-2-5 grades the `href`, so
these are real links and not four spans with the right attributes:

```tsx
      <ul className="plain sidebar">
        {totals.map((row) => (
          <li key={row.account} data-testid={`account-row-${row.account}`}>
            <Link href={`/accounts/${row.account}`} data-testid={`account-link-${row.account}`}>
              {row.account}
            </Link>
            <span data-testid={`account-list-total-${row.account}`}>
              {formatPaise(row.paise)}
            </span>
          </li>
        ))}
      </ul>
```

## Where students get stuck

- **"`/accounts/rent` is still a 404 and my totals are right."** - The 404 is
  decided by `accountRows`, not by `accountTotals`. - Show them
  `if (rows.length === 0) notFound()` on the page and ask what `accountRows`
  currently returns.
- **"The total at the top reads `-`."** - The page looks the total up in
  `accountTotals`, not in the rows it just listed. Either the fold is still empty
  or the account name it stored does not match the route name. - "The dash means
  `accountTotals` has no object with that name. Print what it does have."
- **"Every total reads `NaN.00`."** - `summed.get(account) + entry.paise` with no
  `?? 0`, so the first row of each account adds to `undefined`. - "What does a
  `Map` give you for a key it has never seen?"
- **"`utilities` is in my sidebar"** or **"there is a blank name in the list."** -
  They folded over the wrong array - `diagnostics`, or the raw lines - instead of
  the accepted `entries`. - "Line 25 was rejected in session 1. A rejected line
  has no account. That is exactly what c-2-2 checks."
- **"The accounts come out in the wrong order."** - A numeric comparator on
  strings: `sort((a, b) => a.account - b.account)` is `NaN` every time, so
  nothing moves. - "These are strings. `.sort()` with no argument is the string
  order you want."
- **"Every row in the running column shows the same number."** - Either `carried`
  is being reset inside the loop, or they pushed the account total once per row.
- "Say the column out loud: after row one, after row two, after row three."
- **"The running column is one row short, or off by one row."** - They pushed
  before adding, so the first row shows `0` - or they pushed after the loop, so
  only the last number exists and every other cell is `-`.
- **"`/accounts/Rent` works and it should not."** - A `toLowerCase()` on the
  route name or on the account. - "c-2-4 asks for a 404 on `/accounts/Rent`.
  Exact match. `Rent` is not `rent`."
- **"I edited `data/ledger.txt` and the page did not change."** - They are on
  `npm run start` against a stale build. Both pages are `force-dynamic`, so
  `npm run dev` re-reads the file on every request.
- **"My page throws `params.name` is undefined."** - Only reaches students who
  edit the page. In Next 15 `params` is a `Promise` and the shipped code awaits
  it. - "You do not need to touch this file today. Put it back."

## Check before moving on

`/accounts/rent` reads `-37200.00` at the top, has exactly three rows - 5, 11 and
20 - and its running column ends on `-37200.00`. Click `salary` in the sidebar:
`62000.00` at the top, three rows, and the column ends on `62000.00`.
`/accounts/utilities` is still a 404. That is the whole project.

## Timing - the overrun and what to trim

The plan above is 45 minutes against the 40 cap. The five extra are spread
evenly - three folds, each about eight to ten live minutes once the `?? 0`, the
404 mechanism and the scan-versus-fold distinction are actually explained, plus
four minutes of recap that this session genuinely needs because everything here
stands on session 1.

Trim in this order. Nothing here removes anything a criterion grades.

1. **Cut the 4-8 board work to two minutes.** Draw the three folds as three
   arrows over the finished page and move on. Saves 2.
2. **Do not read the sidebar code.** It ships written and no student touches it;
   just click a link at the end. Saves 2.
3. **Move `notFound()` and `not-found.tsx` to a two-sentence aside**, dropped
   into the 34-42 block for whoever asks. Saves 2.

The first two bring the plan to 41; all three bring it to 39.

Note for whoever schedules this: the drop candidate `spec.md` names for this
session - the `txn-date-<lineNo>` and `txn-desc-<lineNo>` columns - is not
available. Those columns ship written in the skeleton and cost zero live minutes,
so removing them relieves nothing.
