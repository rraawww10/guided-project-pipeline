import { Event } from "./types";

export interface ParseResult {
  ok: boolean;
  event?: Event;
  error?: string;
}

export function parseLine(line: string): ParseResult {
  const trimmed = line.trim();
  let event: Event | undefined = undefined;
  // TODO(cut-parse-line): From one trimmed input line, set `event` to one of: {type: "alert"}, {type: "timeout"}, {type: "resolve"}, or {type: "ack", actor: <name>} when the line matches exactly "ack " + a non-empty name; reject any other shape with an error message that includes the bad line; do not validate the actor against contacts here
  return { ok: true, event };
}
