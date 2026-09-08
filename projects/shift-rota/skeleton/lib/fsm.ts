import { ApplyResult, Event, LogEntry, State } from "./types";

export function currentContact(state: State): string | null {
  if (state.mode !== "alerting" || state.currentIndex == null) return null;
  return state.contacts[state.currentIndex] ?? null;
}

// Session 1 helper for initial alert
export function initialAlert(state: State): ApplyResult {
  let next: State = { ...state, mode: state.mode, currentIndex: state.currentIndex, log: [...state.log] };
  // TODO(cut-logic-initial-alert): Build the next State in `next` by setting mode to "alerting", currentIndex to 0, and appending a log entry {step: previous log length + 1, event: "alert", reason: "alert raised; current " + first contact}; preserve existing contacts and earlier log entries
  return { ok: true, next, added: next.log[next.log.length - 1] };
}

// Escalation helper used by reducer
export function escalateIndex(currentIndex: number, contacts: string[]): number {
  let nextIndex = currentIndex;
  // TODO(cut-logic-escalate-index): Compute `nextIndex` as currentIndex + 1 when a later contact exists, otherwise keep the currentIndex unchanged
  return nextIndex;
}

export function applyEvent(state: State, event: Event): ApplyResult {
  let out: ApplyResult = { ok: false, next: state, error: "illegal transition", added: null };
  // TODO(cut-logic-reducer-apply): Fill `out` by applying one event with guards: when State.mode is "idle", only "alert" is allowed and must set mode to "alerting", currentIndex to 0, and append a log entry; when mode is "alerting": an "ack" is allowed only when event.actor equals the current contact and must append a log entry without changing currentIndex; a "timeout" moves to the next contact using escalateIndex unless already at the last, in which case set ok false with a message naming "no further escalation" and leave the index unchanged; a "resolve" sets mode to "idle", clears currentIndex to null, and appends a log entry; for any other combination set ok false with a message that names the illegal transition; always carry forward contacts and the existing log into out.next
  return out;
}
