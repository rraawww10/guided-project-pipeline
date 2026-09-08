import { ApplyResult, Event, LogEntry, State } from "./types";

export function currentContact(state: State): string | null {
  if (state.mode !== "alerting" || state.currentIndex == null) return null;
  return state.contacts[state.currentIndex] ?? null;
}

// Session 1 helper for initial alert
export function initialAlert(state: State): ApplyResult {
  let next: State = { ...state, mode: state.mode, currentIndex: state.currentIndex, log: [...state.log] };
  // >>> CUT cut-logic-initial-alert
  // Move to alerting at the first contact and append a log entry
  const first = state.contacts[0];
  next = {
    ...state,
    mode: "alerting",
    currentIndex: 0,
    log: [
      ...state.log,
      {
        step: state.log.length + 1,
        event: "alert",
        reason: `alert raised; current ${first}`
      } as LogEntry
    ]
  };
  // <<< CUT cut-logic-initial-alert
  return { ok: true, next, added: next.log[next.log.length - 1] };
}

// Escalation helper used by reducer
export function escalateIndex(currentIndex: number, contacts: string[]): number {
  let nextIndex = currentIndex;
  // >>> CUT cut-logic-escalate-index
  if (currentIndex + 1 < contacts.length) {
    nextIndex = currentIndex + 1;
  }
  // <<< CUT cut-logic-escalate-index
  return nextIndex;
}

export function applyEvent(state: State, event: Event): ApplyResult {
  let out: ApplyResult = { ok: false, next: state, error: "illegal transition", added: null };
  // >>> CUT cut-logic-reducer-apply
  const base: State = { ...state };
  const log = [...state.log];

  if (state.mode === "idle") {
    if (event.type === "alert") {
      const res = initialAlert(state);
      out = { ok: true, next: res.next, added: res.added ?? null };
    } else {
      out = { ok: false, next: base, error: `illegal transition from idle via ${event.type}`, added: null };
    }
  } else if (state.mode === "alerting") {
    const idx = state.currentIndex ?? 0;
    const current = state.contacts[idx];

    if (event.type === "ack") {
      if (event.actor === current) {
        const entry: LogEntry = { step: log.length + 1, event: "ack", actor: event.actor, reason: `ack by ${event.actor}` };
        const next: State = { ...base, log: [...log, entry], currentIndex: idx, mode: "alerting" };
        out = { ok: true, next, added: entry };
      } else {
        out = { ok: false, next: base, error: `only ${current} can ack`, added: null };
      }
    } else if (event.type === "timeout") {
      const nextIdx = escalateIndex(idx, state.contacts);
      if (nextIdx === idx) {
        out = { ok: false, next: base, error: "no further escalation", added: null };
      } else {
        const nextContact = state.contacts[nextIdx];
        const entry: LogEntry = { step: log.length + 1, event: "timeout", reason: `timeout -> ${nextContact}` };
        const next: State = { ...base, currentIndex: nextIdx, log: [...log, entry] };
        out = { ok: true, next, added: entry };
      }
    } else if (event.type === "resolve") {
      const entry: LogEntry = { step: log.length + 1, event: "resolve", reason: "resolve" };
      const next: State = { ...base, mode: "idle", currentIndex: null, log: [...log, entry] };
      out = { ok: true, next, added: entry };
    } else if (event.type === "alert") {
      // alert while already alerting is illegal
      out = { ok: false, next: base, error: "illegal transition", added: null };
    }
  }
  // <<< CUT cut-logic-reducer-apply
  return out;
}
