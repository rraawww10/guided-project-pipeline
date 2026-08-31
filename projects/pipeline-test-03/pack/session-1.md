# Session 1 - Setup, the file, and the parse

**Time:** the plan below runs to 48 minutes against a 40-minute cap. That is an
overrun of eight, disclosed at the bottom with what to trim. Read that section
before you teach this.

**Students start from:** the skeleton, installed and running. `/` already draws
a page: it says **0** lines parsed and **27** lines refused, and every complaint
but one reads `expected 4 fields, found 4`.

**Students end with:** `/` drawing 21 rows above 6 different, numbered
complaints, and `GET /api/ledger` answering the same thing as JSON. c-1-1,
c-1-2, c-1-3 and c-1-4 all green.

## What they learn

1. **A function that answers instead of throwing.** `parseLine` returns a
   discriminated union - `{ ok: true, entry }` or `{ ok: false, diagnostic }` -
   and the caller reads `.ok` to know which one it got. A broken line is a value,
   not an exception, so it can be counted, numbered and drawn.
2. **Rupee text to integer paise, without a float.** Two integers pulled out of
   the text with one regular expression, multiplied and added as integers.
3. **Validating a date by its shape, not by `Date`.** A regular expression that
   says what the ten characters must be. `Date` is the wrong tool here and this
   file proves it.
4. Rule order: a line carries **one** reason, the first rule it breaks.

## Before you start

- Every student has run `npm ci` in `skeleton/` **before the session**, and has
  `npm run dev` up on `http://localhost:3000/`. Do not spend live minutes on the
  install; it is two to four minutes each and it is the first trim if you have
  to.
- Have open: `data/ledger.txt`, `lib/ledger.ts`, and the browser on `/`.
- Have a browser devtools console ready - you will type one expression into it.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Everyone's page is up. It reads 0 parsed and 27 refused, and nearly every complaint says the same thing. Ask the room: there are clearly good lines in that file - why is it refusing all of them? Do not answer yet. |
| 4-10 | Read `data/ledger.txt` together. 30 lines, two comments, one blank, 27 data lines. Write the four rules on the board in order. Then find the six broken lines by eye and say which rule each one breaks. |
| 10-14 | Errors as data. Read `ParseResult`, then `parseLine`, then `parseLedger` off the screen. `parseLine` has no `throw` in it. `parseLedger` asks `.ok` and pushes onto one of two arrays. Point at the two `TODO` lines - that is the whole of today. |
| 14-25 | Live: `cut-amount-paise`. Start in the console with `250.05 * 100`. Then the regular expression, then the two integers, then the sign. Reload `/` - still 0 parsed, and say why that is expected. |
| 25-38 | Live: `cut-parse-line`. Rule 1, rule 2 with the date regex, rule 3, then acquit the line. Reload `/` - 21 and 6. Read the six complaints out loud. |
| 38-46 | Students catch up. Circulate. The symptoms under **Where students get stuck** are the ones you will actually see, in roughly that order. |
| 46-48 | Six lines, six different reasons, and nothing threw. Next session turns those 21 entries into money per account. |

## Cut points in this session

### cut-amount-paise - `lib/ledger.ts:52`

**What students see** (the skeleton, exactly):

```ts
export function amountToPaise(text: string): number | null {
  let paise: number | null = null
  // TODO(cut-amount-paise): Set `paise` to the whole number of paise in `text` when `text` is an optional `-`, one or more digits, a dot, then exactly two digits: multiply the rupee digits by 100, add the paise digits as integers, never through a float, and apply the sign. Leave `paise` at `null` otherwise.
  return paise
}
```

**What they write.** One regular expression that matches the whole string:
optional minus, one or more digits, a literal dot, exactly two digits - with
three capture groups, for the sign, the rupees and the paise. If it matches,
`paise` becomes the rupee group parsed as an integer, times 100, plus the paise
group parsed as an integer, negated when the sign group is a minus. If it does
not match, `paise` is left alone at `null`. Four lines of body.

**Teach it like this.** "The rupees and the paise are already two separate whole
numbers sitting in the text. We are not converting a decimal - we are pulling out
two integers and putting them back together with a multiply and an add. The float
never gets to touch it."

Open with the console. `250.05 * 100` prints `25004.999999999996`. Then point at
the seed file: line 8 is `-250.05`, and c-1-3 pins it at exactly `-25005`.

Then build the pattern piece by piece and say what each piece is for:
`^` and `$` because the *whole* field has to match, `(-?)` because the sign is
optional and we want to know about it, `(\d+)` for the rupees, `\.` for a
literal dot, and `(\d{2})` for **exactly** two paise digits - which is the
piece that rejects line 25's `-350.5`. Say that `parseInt` on a capture group
gives an integer, so nothing here is ever a float.

Say plainly what `null` means: not zero, not an error - "I could not read this".
The caller decides what to do about it, and the caller is the next cut.

**Reference solution** - instructor's copy, from `app/lib/ledger.ts`. Build it on
screen; do not project it before they have tried:

```ts
export function amountToPaise(text: string): number | null {
  let paise: number | null = null
  const shape = /^(-?)(\d+)\.(\d{2})$/.exec(text)
  if (shape) {
    const magnitude = parseInt(shape[2], 10) * 100 + parseInt(shape[3], 10)
    paise = shape[1] === "-" ? -magnitude : magnitude
  }
  return paise
}
```

**Passes when:** c-1-3 goes green - and it will not until `cut-parse-line` is
done too, because a rejected line has no `paise` to read. On its own, this cut
changes nothing you can see on the page. Say so before you reload, or the room
will think it failed.

### cut-parse-line - `lib/ledger.ts:60`

**What students see** (the skeleton, exactly - note where the `TODO` sits, and
that both `return`s are below it):

```ts
export function parseLine(line: string, lineNo: number): ParseResult {
  const fields = line.split("|").map((f) => f.trim())
  const amount = fields.length === 4 ? amountToPaise(fields[3]) : null
  let reason: string | null = BAD_FIELDS(fields.length)
  // TODO(cut-parse-line): Set `reason` to `BAD_FIELDS(fields.length)` unless `fields` holds exactly 4 strings; then to `BAD_DATE` unless `fields[0]` is four digits, `-`, a month `01` to `12`, `-` and a day `01` to `31`; then to `NO_ACCOUNT` for an empty `fields[1]`; otherwise to `null`. The amount is judged below the markers, so set no `paise` here.
  if (!reason && amount === null) reason = BAD_AMOUNT
  if (reason) return { ok: false, diagnostic: { lineNo, reason } }
```

**What they write.** Nothing at all unless there are exactly four fields - the
initialiser already carries the right complaint for that case. Inside four
fields: if field 1 does not match the date shape, `reason` is `BAD_DATE`; else if
field 2 is the empty string, `reason` is `NO_ACCOUNT`; else `reason` is `null`.
They set `reason` and nothing else. The amount is judged on the line *below* the
`TODO`, and `fields` was split on the line *above* it.

**Teach it like this.** "`reason` starts guilty. Look at the initialiser - the
line is already accused of having the wrong number of fields. Your job in this
block is to acquit it, or to change the charge."

Then rule order, using line 17 - `2026-01-14 | food | coffee`. It has three
fields *and* a perfectly good date. Its reason must be
`expected 4 fields, found 3`, not a date complaint. That is why the field count
is decided first and why the whole block is inside one `if`.

Then the date pattern, and this is the important minute of the session:
`(0[1-9]|1[0-2])` for the month rather than `\d\d`, and `(0[1-9]|[12]\d|3[01])`
for the day. Two things to say:

- **`\d{2}` for the month is not good enough.** Line 22 is `2026-13-02`. A
  loose pattern accepts it and c-1-2 goes red.
- **`Date` is the wrong tool.** Someone will suggest `new Date(fields[0])`. It
  fails on line 9. `new Date("2026-1-06")` does not complain - it parses it as
  6 January - so a `Date` check *accepts* line 9 and both c-1-1 and c-1-2 go red.
  Line 20 is the other half of the story: `new Date("2026-02-30")` is not
  rejected either, it silently becomes 2 March. We are not checking whether the
  date is real. We are checking that it is written the one way this file writes
  dates, and then we keep the string exactly as given - which is why c-1-1
  requires line 20 to arrive carrying `2026-02-30`.

Finish with the acquittal - `reason = null` on the good path. Reload. 21 and 6.

**Reference solution** - instructor's copy, from `app/lib/ledger.ts`:

```ts
export function parseLine(line: string, lineNo: number): ParseResult {
  const fields = line.split("|").map((f) => f.trim())
  const amount = fields.length === 4 ? amountToPaise(fields[3]) : null
  let reason: string | null = BAD_FIELDS(fields.length)
  if (fields.length === 4) {
    if (!/^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/.test(fields[0])) {
      reason = BAD_DATE
    } else if (fields[1] === "") {
      reason = NO_ACCOUNT
    } else {
      reason = null
    }
  }
  if (!reason && amount === null) reason = BAD_AMOUNT
  if (reason) return { ok: false, diagnostic: { lineNo, reason } }
  return {
    ok: true,
    entry: {
      lineNo,
      date: fields[0],
      account: fields[1],
      description: fields[2],
      paise: amount ?? 0,
    },
  }
}
```

**Passes when:** c-1-2 goes green on its own - it is the only criterion that
reads just the six reason strings, so it turns green from this cut alone. c-1-1,
c-1-3 and c-1-4 need both of today's cuts.

## The code that ships written, and that you will read on screen

These are the pieces you point at, not the pieces they type.

The types - the discriminated union is `ParseResult`:

```ts
export type Entry = {
  lineNo: number
  date: string
  account: string
  description: string
  paise: number
}

export type Diagnostic = {
  lineNo: number
  reason: string
}

export type ParseResult =
  | { ok: true; entry: Entry }
  | { ok: false; diagnostic: Diagnostic }

export type Ledger = {
  entries: Entry[]
  diagnostics: Diagnostic[]
}
```

The four reason strings. They are constants so that nobody grades wording anyone
invented:

```ts
/** The four reason strings. A rejected line carries exactly one of them. */
export const BAD_FIELDS = (n: number) => `expected 4 fields, found ${n}`
export const BAD_DATE = "date must be YYYY-MM-DD"
export const NO_ACCOUNT = "account must not be empty"
export const BAD_AMOUNT = "amount must be a rupee amount like -250.00"
```

`formatPaise`, the inverse of what they are about to write. Every rupee value on
either screen is this string:

```ts
export function formatPaise(paise: number): string {
  const sign = paise < 0 ? "-" : ""
  const magnitude = Math.abs(paise)
  const rupees = Math.floor(magnitude / 100)
  const remainder = magnitude % 100
  return `${sign}${rupees}.${String(remainder).padStart(2, "0")}`
}
```

`parseLedger` - the partition loop. This is where `.ok` gets asked, and it is
where the skip rule for comments and blank lines lives, which is why there is no
`entry-row-1`:

```ts
/**
 * Skip a line whose trimmed text is empty or whose first non-space character
 * is `#`; parse every other one and push its answer onto the matching array.
 * Line numbers are 1-based over the raw file, counting the skipped lines.
 */
export function parseLedger(text: string): Ledger {
  const entries: Entry[] = []
  const diagnostics: Diagnostic[] = []
  const lines = text.split("\n")
  for (let index = 0; index < lines.length; index += 1) {
    const raw = lines[index]
    const trimmed = raw.trim()
    if (trimmed === "" || trimmed.startsWith("#")) continue
    const result = parseLine(raw, index + 1)
    if (result.ok) entries.push(result.entry)
    else diagnostics.push(result.diagnostic)
  }
  return { entries, diagnostics }
```

The endpoint, so they can see that it does nothing except read the file and hand
back what `parseLedger` returned:

```ts
export async function GET(): Promise<Response> {
  const text = readFileSync(path.join(process.cwd(), "data", "ledger.txt"), "utf8")
  const ledger: Ledger = parseLedger(text)
  return Response.json(ledger)
}
```

And the two loops on `/` that draw it, if anyone asks where the page comes from:

```tsx
          {entries.map((entry) => (
            <tr key={entry.lineNo} data-testid={`entry-row-${entry.lineNo}`}>
              <td>{entry.lineNo}</td>
              <td data-testid={`entry-date-${entry.lineNo}`}>{entry.date}</td>
              <td data-testid={`entry-account-${entry.lineNo}`}>{entry.account}</td>
              <td data-testid={`entry-desc-${entry.lineNo}`}>{entry.description}</td>
              <td className="num" data-testid={`entry-amount-${entry.lineNo}`}>
                {formatPaise(entry.paise)}
              </td>
            </tr>
          ))}
```

```tsx
      <ul className="plain rejects">
        {diagnostics.map((diagnostic) => (
          <li key={diagnostic.lineNo} data-testid={`reject-row-${diagnostic.lineNo}`}>
            {`line ${diagnostic.lineNo}: ${diagnostic.reason}`}
          </li>
        ))}
      </ul>
```

## Where students get stuck

- **"Every line still says `expected 4 fields, found 4`."** - The good path never
  sets `reason` back to `null`. The initialiser is a fallback, not a running
  total of complaints. - "You changed the charge but you never dropped it. What
  happens on a line where all three rules pass?"
- **"I get 22 entries, and line 9 is one of them."** - They used
  `new Date(fields[0])` or `isNaN(Date.parse(...))`. `2026-1-06` parses fine. -
  "`Date` is happy with that string. We are not asking whether the date exists,
  we are asking whether it is written `YYYY-MM-DD`. Count the characters."
- **"Line 22 is being accepted."** - The month group is `\d{2}` or `\d\d`, so
  `13` matches. - "Which months are there? Write the two cases: `0` then `1`-`9`,
  or `1` then `0`-`2`."
- **"`entry-amount-8` reads `-250.04`."** - A float multiply that truncates:
  `250.05 * 100` is `25004.999...`, and `Math.trunc` or `| 0` takes it down to
  `25004`. - "Show me the console. Now: which two whole numbers are in that
  string?"
- **"Line 28 (`1,200.00`) came through as an entry."** - Either `parseFloat`,
  which reads `1,200.00` as `1`, or an unanchored regular expression, which finds
  `200.00` inside it and accepts it with `paise` `20000`. - "Add `^` and `$`. The
  whole field has to match, not some part of it."
- **"Line 25 (`-350.5`) came through as an entry."** - The paise group is
  `\d+` rather than `\d{2}`. - "Exactly two digits. `-350.5` is not a rupee
  amount, it is a typo."
- **"Nothing changed when I saved."** - Look at the terminal, not the browser. A
  TypeScript error stops the rebuild and the page keeps serving the last good
  bundle, so it still reads 0 and 27.
- **"The tests pass but I used `parseFloat`."** - They wrote
  `Math.round(parseFloat(text) * 100)` behind the regex guard. It really does
  pass every criterion in this project. - Say it straight: "Your code is green
  and I am still going to argue with it. Rounding hides the error at these five
  values. It stops hiding it on a bigger file, and the integer version has
  nothing to hide."
- **"TypeScript says a comparison is unintentional."** - They rewrote the shipped
  guard below the `TODO` as `if (reason === null && ...)`. With the block still
  empty, TypeScript can see nothing assigns to `reason`, narrows it to `string`,
  and refuses the comparison to `null` - and the whole app stops building. - "Put
  the line back as it shipped: `if (!reason && amount === null)`. It is written
  that way on purpose."

## Check before moving on

`http://localhost:3000/` shows `21` next to "lines parsed" and `6` next to
"lines refused", and the six complaints read six *different* things - line 9 and
line 22 about the date, 13 about the account, 17 about the field count, 25 and 28
about the amount. If a student is still on 0 and 27, or on 22 entries, session 2
will not start for them: every criterion in session 2 depends on both of today's
cuts.

## Timing - the overrun and what to trim

The plan above is 48 minutes. The spec says 38.5. The eight extra minutes are
real and they are all in one place: `cut-parse-line` carries three rules, a rule
*order*, and the argument against `Date`, and that is thirteen live minutes, not
six.

Trim in this order, and stop as soon as you are inside the cap. None of these
removes anything a criterion grades.

1. **Move `npm ci` and the first `npm run dev` out of the session** - make it
   pre-work with a one-line instruction. Saves 3-4 if you were going to do it
   live. The plan above already assumes this.
2. **Put both regular expressions on a slide, already written.** Explain them
   left to right instead of deriving them character by character. Saves 4.
3. **Push the rule-order argument (line 17) into session 2's recap.** Write
   `reason` as three checks without justifying the order, and pick it up when you
   open session 2 on the complaints panel. Saves 3.
4. **Read `parseLedger` in 60 seconds instead of four minutes** - "it skips
   comments and blanks, calls your function, and sorts the answers into two
   piles" - and move the walk-through of the six broken lines to the 38-46 block,
   where students read them off their own screen. Saves 3.

Trims 1 and 2 alone bring the plan to 40.
