import { Event } from "./types";

export interface ParseResult {
  ok: boolean;
  event?: Event;
  error?: string;
}

export function parseLine(line: string): ParseResult {
  const trimmed = line.trim();
  let event: Event | undefined = undefined;
  // >>> CUT cut-parse-line
  if (trimmed === "") {
    return { ok: false, error: "empty line" };
  }
  if (trimmed === "alert") {
    event = { type: "alert" };
  } else if (trimmed === "timeout") {
    event = { type: "timeout" };
  } else if (trimmed === "resolve") {
    event = { type: "resolve" };
  } else if (trimmed.startsWith("ack ")) {
    const actor = trimmed.slice(4).trim();
    if (actor.length === 0) {
      return { ok: false, error: `bad line: ${line}` };
    }
    event = { type: "ack", actor };
  } else {
    return { ok: false, error: `bad line: ${line}` };
  }
  // <<< CUT cut-parse-line
  return { ok: true, event };
}
