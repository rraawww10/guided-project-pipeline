/**
 * The ledger parser. Errors are data: `parseLine` never throws, it answers
 * either an `Entry` or a `Diagnostic`, and `parseLedger` partitions the file
 * into the two arrays every screen and both endpoints read.
 *
 * Nothing here touches the filesystem, so the client component on `/` can
 * import `formatPaise` from this module.
 */

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

/** The four reason strings. A rejected line carries exactly one of them. */
export const BAD_FIELDS = (n: number) => `expected 4 fields, found ${n}`
export const BAD_DATE = "date must be YYYY-MM-DD"
export const NO_ACCOUNT = "account must not be empty"
export const BAD_AMOUNT = "amount must be a rupee amount like -250.00"

/**
 * The inverse of `amountToPaise`, and the only way a rupee value reaches a
 * screen: sign, whole rupees, `.`, then the remainder as two digits.
 */
export function formatPaise(paise: number): string {
  const sign = paise < 0 ? "-" : ""
  const magnitude = Math.abs(paise)
  const rupees = Math.floor(magnitude / 100)
  const remainder = magnitude % 100
  return `${sign}${rupees}.${String(remainder).padStart(2, "0")}`
}

export function amountToPaise(text: string): number | null {
  let paise: number | null = null
  // TODO(cut-amount-paise): Set `paise` to the whole number of paise in `text` when `text` is an optional `-`, one or more digits, a dot, then exactly two digits: multiply the rupee digits by 100, add the paise digits as integers, never through a float, and apply the sign. Leave `paise` at `null` otherwise.
  return paise
}

export function parseLine(line: string, lineNo: number): ParseResult {
  const fields = line.split("|").map((f) => f.trim())
  const amount = fields.length === 4 ? amountToPaise(fields[3]) : null
  let reason: string | null = BAD_FIELDS(fields.length)
  // TODO(cut-parse-line): Set `reason` to `BAD_FIELDS(fields.length)` unless `fields` holds exactly 4 strings; then to `BAD_DATE` unless `fields[0]` is four digits, `-`, a month `01` to `12`, `-` and a day `01` to `31`; then to `NO_ACCOUNT` for an empty `fields[1]`; otherwise to `null`. The amount is judged below the markers, so set no `paise` here.
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
}
