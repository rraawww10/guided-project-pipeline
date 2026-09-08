"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

type GameSummary = { id: string; seed: number; guessCount: number }

export default function GamesPage() {
  const [gamesState, setGamesState] = useState<GameSummary[]>([])
  const router = useRouter()

  async function load() {
    const res = await fetch('/api/games')
    if (res.ok) {
      const arr = (await res.json()) as GameSummary[]
      // TODO(cut-ui-games-fetch): Fetch the games index and write the received array into `gamesState` so one row renders per game
    }
  }

  useEffect(() => {
    load()
  }, [])

  function resume(id: string) {
    // TODO(cut-ui-resume-select): On a Resume button click, set `currentGameId` to that game's id and navigate to the board so its guesses load
  }

  return (
    <main>
      <h1>Saved Games</h1>
      <div>
        {gamesState.map((g) => (
          <div key={g.id} data-testid="game-row" style={{ display: 'flex', gap: 8, alignItems: 'center', margin: '6px 0' }}>
            <code>{g.id}</code>
            <span>seed: {g.seed}</span>
            <span>guesses: {g.guessCount}</span>
            <button data-testid={`resume-${g.id}`} onClick={() => resume(g.id)}>Resume</button>
          </div>
        ))}
      </div>
    </main>
  )
}
