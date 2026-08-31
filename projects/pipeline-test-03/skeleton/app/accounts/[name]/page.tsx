import { readFileSync } from "node:fs"
import path from "node:path"

import Link from "next/link"
import { notFound } from "next/navigation"

import {
  accountRows,
  accountTotals,
  runningBalance,
  type AccountTotal,
} from "@/lib/accounts"
import { formatPaise, parseLedger } from "@/lib/ledger"

export const dynamic = "force-dynamic"

/**
 * sc-account. A server component: it reads data/ledger.txt through parseLedger
 * and makes no fetch, so an unknown account is a real HTTP 404 rather than an
 * empty page.
 */
export default async function AccountPage({
  params,
}: {
  params: Promise<{ name: string }>
}) {
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

  return (
    <main className="page">
      <h1 data-testid="account-title">{name}</h1>
      <p className="count">
        total:{" "}
        <span data-testid="account-total">
          {total === undefined ? "-" : formatPaise(total.paise)}
        </span>
      </p>

      <h2>Accounts</h2>
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

      <h2>Entries</h2>
      <table>
        <thead>
          <tr>
            <th>line</th>
            <th>date</th>
            <th>description</th>
            <th>amount</th>
            <th>running</th>
          </tr>
        </thead>
        <tbody>
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
        </tbody>
      </table>
    </main>
  )
}
