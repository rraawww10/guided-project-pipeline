"use client";

import { useEffect, useMemo, useState } from "react";
import type { Expense } from "../lib/types";
import { computeBalances, settleMinimal, settleNaive } from "../lib/settlement";
import { formatMoney } from "../lib/money";

export default function HomePage() {
  const [items, setItems] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [included, setIncluded] = useState<Set<string>>(new Set());
  const [minimal, setMinimal] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      let loaded: Expense[] = [];
      try {
        // TODO(cut-ui-load-expenses): Fetch "/api/expenses" and write the parsed JSON array into `items`; keep the existing error and loading state handling unchanged
      } catch (e: any) {
        if (!cancelled) setError(e?.message || String(e));
      } finally {
        if (!cancelled) {
          setItems(loaded);
          // Seed included set to all names present in data on first load
          if (included.size === 0) {
            const names = new Set<string>();
            for (const it of loaded) {
              names.add(it.paidBy);
              for (const p of it.participants) names.add(p.person);
            }
            setIncluded(names);
          }
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const peopleSorted = useMemo(() => {
    const names = Array.from(included);
    names.sort();
    return names;
  }, [included]);

  const balances = useMemo(() => {
    let balances: Record<string, number> = {};
    // TODO(cut-ui-set-balances): Derive `balances` from the loaded `items` (and the current included people) using the provided netting function
    return balances;
  }, [items, included]);

  const naiveTransfers = useMemo(() => {
    let transfers = [] as ReturnType<typeof settleNaive>;
    // TODO(cut-ui-set-transfers): Derive `transfers` from the current `balances` using the naive settlement function and make it stable across renders
    return transfers;
  }, [balances]);

  const transfers = useMemo(() => {
    let transfers = naiveTransfers;
    // TODO(cut-ui-use-minimal): When minimal mode is ON, write the refined transfer sequence into `transfers` using the minimal function; when it is OFF, preserve the naive sequence already derived
    return transfers;
  }, [naiveTransfers, minimal, balances]);

  const transfersTotal = useMemo(() => transfers.reduce((s, t) => s + t.amountCents, 0), [transfers]);

  function onToggleInclude(person: string) {
    let next: Set<string> = included;
    // TODO(cut-ui-toggle-include): Toggle the given person's id in the `included` Set while preserving every other selection; the next recompute must use exactly the currently included people
    setIncluded(next);
  }

  // Totals-paid summary
  let totals: Record<string, number> = {};
  // TODO(cut-ui-compute-paid-totals): Accumulate the sum of `amountCents` each payer contributed into `totals` keyed by person id using integer cents already present in `items`

  if (loading) return <div>Loading…</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>FairShare</h1>

      {/* Formatting probe */}
      <div data-testid="money-sample">{formatMoney(-615)}</div>

      {/* Minimal toggle */}
      <label style={{ display: 'block', margin: '8px 0' }}>
        <input
          type="checkbox"
          data-testid="toggle-minimal"
          checked={minimal}
          onChange={() => setMinimal((m) => !m)}
        />
        Minimal transfers
      </label>

      {/* Include/exclude checkboxes */}
      <div style={{ margin: '8px 0' }}>
        {peopleSorted.map((name) => (
          <label key={name} style={{ marginRight: 12 }}>
            <input
              type="checkbox"
              data-testid={`include-${name}`}
              checked={included.has(name)}
              onChange={() => onToggleInclude(name)}
            />
            {name}
          </label>
        ))}
      </div>

      {/* Expenses table */}
      <h2>Expenses</h2>
      <table>
        <thead>
          <tr>
            <th>Description</th>
            <th>Amount</th>
            <th>Paid by</th>
          </tr>
        </thead>
        <tbody>
          {items.map((e) => (
            <tr key={e.id} data-testid="expense-row">
              <td>{e.description}</td>
              <td>{formatMoney(e.amountCents)}</td>
              <td>{e.paidBy}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Totals-paid summary */}
      <h2>Totals paid</h2>
      <ul>
        {Object.keys(totals)
          .sort()
          .map((name) => (
            <li key={name}>{name} {formatMoney(totals[name])}</li>
          ))}
      </ul>

      {/* Balances list */}
      <h2>Balances</h2>
      <ul>
        {Object.keys(balances)
          .sort()
          .map((name) => {
            const val = balances[name] || 0;
            const text = `${name} ${val > 0 ? "+" : ""}${formatMoney(val)}`;
            return (
              <li key={name} data-testid="balance-row">{text}</li>
            );
          })}
      </ul>

      {/* Transfers */}
      <h2>Proposed transfers</h2>
      <div>
        <strong>Total: </strong>
        <span data-testid="transfers-total">{formatMoney(transfersTotal)}</span>
      </div>
      <ul>
        {transfers.map((t, idx) => (
          <li key={idx} data-testid="transfer-row">
            {t.from} pays {t.to} {formatMoney(t.amountCents)}
          </li>
        ))}
      </ul>
    </div>
  );
}
