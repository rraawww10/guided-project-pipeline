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
        // >>> CUT cut-ui-load-expenses
        const resp = await fetch("/api/expenses");
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        loaded = await resp.json();
        // <<< CUT cut-ui-load-expenses
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
    // >>> CUT cut-ui-set-balances
    balances = computeBalances(items, included);
    // <<< CUT cut-ui-set-balances
    return balances;
  }, [items, included]);

  const naiveTransfers = useMemo(() => {
    let transfers = [] as ReturnType<typeof settleNaive>;
    // >>> CUT cut-ui-set-transfers
    transfers = settleNaive(balances);
    // <<< CUT cut-ui-set-transfers
    return transfers;
  }, [balances]);

  const transfers = useMemo(() => {
    let transfers = naiveTransfers;
    // >>> CUT cut-ui-use-minimal
    if (minimal) {
      transfers = settleMinimal(balances);
    }
    // <<< CUT cut-ui-use-minimal
    return transfers;
  }, [naiveTransfers, minimal, balances]);

  const transfersTotal = useMemo(() => transfers.reduce((s, t) => s + t.amountCents, 0), [transfers]);

  function onToggleInclude(person: string) {
    let next: Set<string> = included;
    // >>> CUT cut-ui-toggle-include
    next = new Set(included);
    if (next.has(person)) next.delete(person);
    else next.add(person);
    // <<< CUT cut-ui-toggle-include
    setIncluded(next);
  }

  // Totals-paid summary
  let totals: Record<string, number> = {};
  // >>> CUT cut-ui-compute-paid-totals
  // Seed every known person to 0 so names with no paid amount (e.g. Eve) still render
  totals = {} as Record<string, number>;
  for (const name of included) totals[name] = 0;
  for (const e of items) {
    totals[e.paidBy] = (totals[e.paidBy] || 0) + e.amountCents;
  }
  // <<< CUT cut-ui-compute-paid-totals

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
