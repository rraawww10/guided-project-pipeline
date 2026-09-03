'use client'

import { useState } from 'react'

import { manualStart } from '@/lib/state'
import { step } from '@/lib/step'
import type { Scenario } from '@/lib/types'

/**
 * The shaft, the readouts, the served lines and the step button.
 *
 * One `SimState` in `useState`, seeded from `manualStart` - spec.md, Screens.
 * The step button's handler is shipped written and is exactly
 * `setState(step(state))`: the learning is inside `step`, not in the click.
 *
 * Rows run highest floor first, floor 8 at the top down to floor 1. Every count
 * and every string a criterion reads is pinned to a `data-testid`, so styling
 * cannot move a test, and only the eight shaft rows carry a testid beginning
 * `floor-`.
 */
export default function Shaft({ scenario }: { scenario: Scenario }) {
  const [state, setState] = useState(() => manualStart(scenario))

  const floors = Array.from({ length: scenario.floors }, (_, index) => scenario.floors - index)

  return (
    <main className="page">
      <h1>{scenario.name}</h1>
      <p className="lede">{scenario.id}</p>

      <ol className="plain shaft">
        {floors.map((floor) => (
          <li className={floor === state.car.floor ? 'here' : undefined} key={floor} data-testid={`floor-${floor}`}>
            {floor}
            <span className="marker">{floor === state.car.floor ? state.car.mode : null}</span>
          </li>
        ))}
      </ol>

      <div className="readouts">
        <span>
          <span className="label">floor</span>
          <span className="value" data-testid="car-floor">{state.car.floor}</span>
        </span>
        <span>
          <span className="label">mode</span>
          <span className="value" data-testid="car-mode">{state.car.mode}</span>
        </span>
        <span>
          <span className="label">tick</span>
          <span className="value" data-testid="tick">{state.tick}</span>
        </span>
        <span>
          <span className="label">served</span>
          <span className="value" data-testid="served-count">{state.served.length}</span>
        </span>
      </div>

      <button type="button" data-testid="step-button" onClick={() => setState(step(state))}>
        step
      </button>

      <h2>served</h2>
      <ul className="plain served">
        {state.served.map((entry) => (
          <li key={entry.floor}>
            {`floor ${entry.floor} served at tick `}
            <span data-testid={`served-${entry.floor}`}>{entry.servedAt}</span>
          </li>
        ))}
      </ul>
    </main>
  )
}
