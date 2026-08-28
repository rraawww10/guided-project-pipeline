/**
 * The win and lose rule.
 *
 * Flags are no part of it: a board with every mine flagged and one cell open is
 * still playing.
 */
import type { Board } from './boards'

export type GameStatus = 'playing' | 'won' | 'lost'

/**
 * `lost` when any revealed index is a mine; otherwise `won` when the number of
 * distinct revealed indices equals the number of cells minus the number of
 * mines; otherwise `playing`.
 */
export function gameStatus(board: Board, revealed: number[]): GameStatus {
  // the fallback stays above the marker and the return below it. `lost` is the
  // one constant that is the wrong answer to every status criterion.
  let status: GameStatus = 'lost'

  // TODO(cut-game-status): Set `status` to `lost` when any index in `revealed` is also in `board.mines`. Otherwise set `status` to `won` when the number of distinct indices in `revealed` equals `board.width * board.height` minus the number of entries in `board.mines`, and to `playing` in every other case. Test the mine case first, so a list that opens the last safe cell and a mine together reads `lost`. Flags are no part of this rule: a board with every mine flagged and 1 cell open is still `playing`.

  return status
}
