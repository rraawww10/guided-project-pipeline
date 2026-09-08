"use client"

import { Suspense, useEffect, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

// Types matching API shapes
type Game = { id: string; seed: number }
type Guess = { id: string; gameId: string; code: number[]; black: number | null; white: number | null }

type Hint = { remaining: number; suggestion: number[] | null }

function PageInner() {
  const router = useRouter()
  const search = useSearchParams()
  const [seedInput, setSeedInput] = useState<string>('')
  const [currentGameId, setCurrentGameId] = useState<string | null>(null)
  const [pendingGuess, setPendingGuess] = useState<number[]>([])
  const [guessesState, setGuessesState] = useState<Guess[]>([])
  const [hintState, setHintState] = useState<Hint | null>(null)

  // Initialise from ?game= in URL (mount-only; subsequent URL changes do not reset the current game)
  useEffect(() => {
    const g = search.get('game')
    if (g) {
      setCurrentGameId(g)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function createGame() {
    const seedNum = parseInt(seedInput, 10)
    if (!Number.isFinite(seedNum)) return
    const res = await fetch('/api/games', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seed: seedNum }),
    })
    if (res.ok) {
      const game: Game = await res.json()
      setCurrentGameId(game.id)
      setGuessesState([])
      setPendingGuess([])
      router.push(`/?game=${game.id}`)
    }
  }

  async function loadGame(id: string) {
    const res = await fetch(`/api/games/${id}`)
    if (res.ok) {
      const body = await res.json()
      setGuessesState(body.guesses as Guess[])
    }
    await loadHint(id)
  }

  async function loadHint(id: string) {
    const res = await fetch(`/api/games/${id}/hint`)
    if (res.ok) {
      const body = (await res.json()) as Hint
      // TODO(cut-ui-hint-fetch): Fetch the hint endpoint for the active game and write its { remaining, suggestion } into `hintState` for display
    }
  }

  useEffect(() => {
    if (currentGameId) loadGame(currentGameId)
  }, [currentGameId])

  function pickColor(v: number) {
    setPendingGuess((prev) => (prev.length < 4 ? [...prev, v] : prev))
  }

  async function submitGuess() {
    if (!currentGameId || pendingGuess.length !== 4) return
    const res = await fetch(`/api/games/${currentGameId}/guesses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: pendingGuess }),
    })
    if (res.ok) {
      const saved: Guess = await res.json()
      // TODO(cut-ui-append-guess): Append the just-submitted 4-number code to `guessesState` so a new guess row appears on the board
      // Clear the local pick. The row above is the only thing that puts this
      // guess on the board - re-reading the game here would render it whether
      // or not the block ran, which is what left this task ungraded.
      setPendingGuess([])
      await loadHint(currentGameId)
    }
  }

  async function branchHere(k: number) {
    if (!currentGameId) return
    const res = await fetch(`/api/games/${currentGameId}/branch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ upto: k }),
    })
    if (res.ok) {
      const game: Game = await res.json()
      // TODO(cut-ui-branch-here): After Branch Here is clicked for row k, call the branch endpoint and set `currentGameId` to the returned game's id so the board reloads to k rows
      router.push(`/?game=${game.id}`)
    }
  }

  const rows = useMemo(() => {
    let r: any[] = []
    // TODO(cut-ui-render-scores): Build `rows` from the saved guesses so each row renders the 4 pegs and shows the row's black and white counts in their testids
    return r
  }, [guessesState])

  return (
    <main>
      <h1>Mastermind</h1>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input data-testid="seed-input" placeholder="Seed" value={seedInput} onChange={(e) => setSeedInput(e.target.value)} />
        <button data-testid="new-game" onClick={createGame}>New Game</button>
      </div>

      <div style={{ marginTop: 12 }}>
        <div style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
          {[0, 1, 2, 3, 4, 5].map((v) => (
            <button key={v} data-testid={`picker-color-${v}`} onClick={() => pickColor(v)}>{v}</button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
          {[0, 1, 2, 3].map((i) => (
            <div key={i} data-testid={`slot-${i}`} style={{ width: 24, height: 24, borderRadius: 12, background: typeof pendingGuess[i] === 'number' ? `hsl(${pendingGuess[i]! * 60} 70% 50%)` : '#ddd', textAlign: 'center' }}>
              {typeof pendingGuess[i] === 'number' ? pendingGuess[i] : ''}
            </div>
          ))}
        </div>
        <button data-testid="submit-guess" onClick={submitGuess}>Submit Guess</button>
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>Previous guesses</h3>
        <div>{rows}</div>
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>Hint</h3>
        <div>Remaining: <span data-testid="hint-remaining">{hintState?.remaining ?? ''}</span></div>
        <div>Suggestion: <span data-testid="hint-suggestion">{hintState?.suggestion ? hintState.suggestion.join(',') : 'null'}</span></div>
      </div>
    </main>
  )
}

export default function Page() {
  // Wrap the hook-using inner component to satisfy Next 16's requirement
  return (
    <Suspense fallback={null}>
      <PageInner />
    </Suspense>
  )
}
