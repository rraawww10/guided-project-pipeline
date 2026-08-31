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
  // >>> CUT cut-amount-paise
  const shape = /^(-?)(\d+)\.(\d{2})$/.exec(text)
  if (shape) {
    const magnitude = parseInt(shape[2], 10) * 100 + parseInt(shape[3], 10)
    paise = shape[1] === "-" ? -magnitude : magnitude
  }
  // <<< CUT cut-amount-paise
  return paise
}

export function parseLine(line: string, lineNo: number): ParseResult {
  const fields = line.split("|").map((f) => f.trim())
  const amount = fields.length === 4 ? amountToPaise(fields[3]) : null
  let reason: string | null = BAD_FIELDS(fields.length)
  // >>> CUT cut-parse-line
  if (fields.length === 4) {
    if (!/^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/.test(fields[0])) {
      reason = BAD_DATE
    } else if (fields[1] === "") {
      reason = NO_ACCOUNT
    } else {
      reason = null
    }
  }
  // <<< CUT cut-parse-line
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
