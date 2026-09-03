# Lift

**One line:** A lift simulated one tick at a time - a seeded list of hall calls,
a dispatch policy written down as closed rules, and a trace saying where the car
was at every tick and which tick each caller got in.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

A simulation turns time into data. Nothing here reads a clock: tick 0 is the
seed, tick *n* is a fold of one pure `step` over the calls due by then, and the
same scenario gives the same trace forever. What makes it worth a session is
that the policy is arguable and the trace makes the argument visible - a student
who serves the nearest call first can see, in the table, the passenger on floor
7 who never gets picked up.

## Sessions

1. **Setup, the shaft, and one tick.** Types, `data/scenarios.json` with four
   scenarios in an 8-floor building - one call above the car, calls on both
   sides of it, a call arriving at a floor the car is about to pass, and a
   scenario with no calls at all - each call given as `{ floor, tick }`.
   `step(state)` advances exactly one tick: move one floor towards the target,
   or spend the tick with the doors open if the car is already there, or stay
   idle. `GET /api/scenarios`, and `/scenarios/[id]` drawing the shaft with the
   car at tick 0, one `data-testid` per floor, and a step button. **Runs:** press
   step and watch the car climb one floor per tick and serve a single call.
2. **Dispatch and the trace.** `nextTarget(state)` as the closed policy - keep
   going in the current direction while any pending call lies ahead of the car,
   serve calls in passing order, reverse only when nothing is pending ahead, go
   idle when nothing is pending at all - `runUntil(scenario, ticks)` folding
   `step` into a trace with a termination guard, and
   `POST /api/scenarios/simulate` taking a scenario in the body and returning
   the per-tick floor and direction plus the tick each call was served.
   **Runs:** the both-sides scenario runs to completion and the trace names the
   tick every passenger got in.

## What the student types

- `step` - one transition over a discriminated state (`moving`, `doors`, `idle`)
  rather than three booleans that can contradict each other.
- `nextTarget` - the direction rule, and the case that decides whether the
  policy is honest: a call registered at tick *t* for the floor the car reaches
  at tick *t*.
- `runUntil` - the fold, and the guard that makes a simulation loop provably
  finite instead of hopefully finite.

## What this teaches that the shipped projects do not

The first discrete-time simulation in the track, and the first loop whose
termination is part of the specification. habit-tracker's toggle was a single
flip and Tenpin's scoring was a pass over a fixed list; nothing shipped evolves
a state repeatedly under a policy, and nothing shipped has a state machine whose
next input is chosen by the student's own code rather than handed to it. It is
also the first place a discriminated union models a *mode* rather than a
success/failure result.

## Out of scope

- More than one lift, and any coordination between cars.
- Destinations inside the car. Every call is a hall call naming a floor only.
- Capacity, weight, door obstruction, express floors, out-of-service states.
- Animation and real elapsed time. A tick is a tick, never a second, and
  nothing reads the clock.
- Choosing or editing the policy from the UI. The policy is code.

## Risks

Policy sprawl is what kills this. "Serve calls in passing order" has at least
three readings, and unless the spec fixes one as an ordered procedure the
Builder and the Verifier will produce two plausible traces and grade different
ones. Second: a trace invites over-pinning - criteria should name the served
tick per call and the floor at two or three named ticks, not assert the whole
array, or a single extra doors tick fails everything at once. Third:
`nextTarget` is the heavy cut, and the fix is to split it inside session 2
(direction choice separate from the pending-ahead test) rather than move part of
it into session 1, which already carries the project setup.
