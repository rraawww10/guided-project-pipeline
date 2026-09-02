/**
 * Roll symbols. Shipped written: no cut lives in this file.
 *
 * A roll of 10 is `X`; the second roll of a frame whose first two rolls add to
 * 10 is `/`; a roll of 0 is `-`; anything else is its digit. A frame box holds
 * its symbols joined by one space.
 */
import type { Frame } from "./types"

/** The symbol for the roll at `index` of this frame. */
export function rollSymbol(frame: Frame, index: number): string {
  if (index === 1 && frame[0] + frame[1] === 10) return "/"
  if (frame[index] === 10) return "X"
  if (frame[index] === 0) return "-"
  return String(frame[index])
}

/** Every symbol of this frame, joined by one space. */
export function frameSymbols(frame: Frame): string {
  return frame.map((_roll, index) => rollSymbol(frame, index)).join(" ")
}
