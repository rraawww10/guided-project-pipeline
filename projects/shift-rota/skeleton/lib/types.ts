export type Mode = "idle" | "alerting";

export type Event =
  | { type: "alert" }
  | { type: "timeout" }
  | { type: "resolve" }
  | { type: "ack"; actor: string };

export interface LogEntry {
  step: number;
  event: "alert" | "ack" | "timeout" | "resolve";
  actor?: string;
  reason: string;
}

export interface State {
  contacts: string[];
  mode: Mode;
  currentIndex: number | null;
  log: LogEntry[];
}

export interface ApplyResult {
  ok: boolean;
  next: State;
  error?: string;
  added?: LogEntry | null;
}
