import { applyEvent } from "./fsm";
import { parseLine } from "./parse";
import { ApplyResult, LogEntry, State } from "./types";

export interface ScriptResult {
  ok: boolean;
  state: State;
  log: LogEntry[];
  error?: string;
}

export function runScript(script: string, initial: State): ScriptResult {
  let result: ScriptResult = { ok: false, state: initial, log: [...initial.log], error: undefined };
  // >>> CUT cut-run-script
  const lines = script.split(/\r?\n/);
  let state = initial;
  let log = [...initial.log];
  for (const raw of lines) {
    const parsed = parseLine(raw);
    if (!parsed.ok || !parsed.event) {
      result = { ok: false, state, log, error: parsed.error || "parse error" };
      return result;
    }
    // Validate actor names at the runner layer
    if (parsed.event.type === "ack") {
      const known = state.contacts.includes(parsed.event.actor);
      if (!known) {
        result = { ok: false, state, log, error: `unknown actor ${parsed.event.actor}` };
        return result;
      }
    }
    const applied: ApplyResult = applyEvent(state, parsed.event);
    if (!applied.ok) {
      result = { ok: false, state: applied.next, log, error: applied.error || "illegal transition" };
      return result;
    }
    state = applied.next;
    if (applied.added) {
      log = [...log, applied.added];
    } else if (state.log.length > log.length) {
      // fallback: trust state's log
      log = [...state.log];
    }
  }
  result = { ok: true, state, log };
  // <<< CUT cut-run-script
  return result;
}
