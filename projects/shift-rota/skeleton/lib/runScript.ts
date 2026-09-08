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
  // TODO(cut-run-script): Walk the lines in order; for each, obtain an event from the parser; if the parser yields an error, stop immediately and write that message into `result.error`; otherwise apply the reducer to the current State, append any new log entry the reducer indicates, and continue; after the final successful line, write the final State and full log into `result` with ok true
  return result;
}
