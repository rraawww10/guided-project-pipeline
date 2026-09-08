"use client";

import { runScript } from "../../lib/runScript";
import { currentContact } from "../../lib/fsm";
import { State } from "../../lib/types";
import { useEffect, useState } from "react";

async function fetchState(): Promise<State> {
  const res = await fetch("/api/state", { cache: "no-store" });
  if (!res.ok) throw new Error("failed to load");
  return (await res.json()) as State;
}

export default function ScriptPage() {
  const [initial, setInitial] = useState<State | null>(null);
  const [script, setScript] = useState<string>("");
  const [finalState, setFinalState] = useState<State | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const s = await fetchState();
      setInitial(s);
    })();
  }, []);

  function onRun() {
    if (!initial) return;
    const res = runScript(script, initial);
    if (res.ok) {
      setError(null);
      setFinalState(res.state);
    } else {
      setFinalState(res.state);
      setError(res.error || "error");
    }
  }

  const mode = finalState?.mode ?? initial?.mode ?? "idle";
  const current = finalState ? currentContact(finalState) : initial ? currentContact(initial) : null;
  const logList = finalState?.log ?? initial?.log ?? [];

  return (
    <div>
      <h1>Script Runner</h1>
      <textarea
        data-testid="script-input"
        rows={8}
        cols={50}
        value={script}
        onChange={(e) => setScript(e.target.value)}
      />
      <div>
        <button data-testid="btn-run-script" onClick={onRun}>
          Run Script
        </button>
      </div>

      {error && (
        <div data-testid="script-error" style={{ color: "crimson", marginTop: 12 }}>
          {error}
        </div>
      )}

      <div style={{ marginTop: 12 }}>
        <div data-testid="mode">{mode}</div>
        {mode === "alerting" && current && (
          <div data-testid="current">{current}</div>
        )}
        <div data-testid="log-count">{logList.length}</div>
      </div>

      <h2 style={{ marginTop: 16 }}>Log</h2>
      <ol>
        {logList.map((row, i) => (
          <li key={i} data-testid={`log-row-${i + 1}`}>
            {row.step}. {row.event}
            {row.actor ? ` ${row.actor}` : ""} — {row.reason}
          </li>
        ))}
      </ol>
    </div>
  );
}
