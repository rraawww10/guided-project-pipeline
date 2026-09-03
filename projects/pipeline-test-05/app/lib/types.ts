/**
 * The data model, shipped written - spec.md, "Data model".
 *
 * The car's mode is a discriminated union rather than three booleans, so a car
 * cannot be moving and idle at once. `direction` on a `TraceRow` is `null` for
 * `doors` and `idle`.
 */
export type Direction = 'up' | 'down'
export type Call = { floor: number; tick: number }
export type Scenario = { id: string; name: string; floors: number; start: number; calls: Call[] }

export type Car =
  | { mode: 'moving'; floor: number; direction: Direction; target: number }
  | { mode: 'doors'; floor: number }
  | { mode: 'idle'; floor: number }

export type Served = { floor: number; calledAt: number; servedAt: number }
export type SimState = { tick: number; car: Car; pending: Call[]; served: Served[] }
export type TraceRow = { tick: number; floor: number; mode: Car['mode']; direction: Direction | null }
export type Trace = { rows: TraceRow[]; served: Served[]; complete: boolean }
