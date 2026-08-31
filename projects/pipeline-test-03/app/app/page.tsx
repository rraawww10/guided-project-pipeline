"use client"

import { useEffect, useState } from "react"

import { formatPaise, type Ledger } from "@/lib/ledger"

const EMPTY: Ledger = { entries: [], diagnostics: [] }

/**
 * sc-ledger. A client component that renders from GET /api/ledger. It has one
 * state: what it draws before the response arrives is unspecified.
 */
export default function LedgerPage() {
  const [ledger, setLedger] = useState<Ledger>(EMPTY)

  useEffect(() => {
    let live = true
    fetch("/api/ledger")
      .then((response) => response.json())
      .then((body: Ledger) => {
        if (live) setLedger(body)
      })
      .catch(() => undefined)
    return () => {
      live = false
    }
  }, [])

  const { entries, diagnostics } = ledger

  return (
    <main className="page">
      <h1>Ledger</h1>

      <h2>Accepted</h2>
      <p className="count">
        lines parsed: <span data-testid="entry-count">{entries.length}</span>
      </p>
      <table>
        <thead>
          <tr>
            <th>line</th>
            <th>date</th>
            <th>account</th>
            <th>description</th>
            <th>amount</th>
          </tr>
        </thead>
        <tbody>
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
        </tbody>
      </table>

      <h2>Rejected</h2>
      <p className="count">
        lines refused: <span data-testid="reject-count">{diagnostics.length}</span>
      </p>
      <ul className="plain rejects">
        {diagnostics.map((diagnostic) => (
          <li key={diagnostic.lineNo} data-testid={`reject-row-${diagnostic.lineNo}`}>
            {`line ${diagnostic.lineNo}: ${diagnostic.reason}`}
          </li>
        ))}
      </ul>
    </main>
  )
}
