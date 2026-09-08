# Session 2 - Exact and colour-only scoring

Time: 40 minutes
Students start from: Session 1 working: can create a game, submit one guess, see one row
Students end with: black/white pegs computed correctly and rendered per row

What they learn
- Pure functions and tests in your head: implement scoreGuess(secret, guess)
- Avoiding double counting when computing white pegs
- Enriching a POST response with computed fields and rendering them

Before you start
- Keep / open with a game loaded and at least one guess
- Open these files:
  - app/lib/scoring.ts (scoreGuess)
  - app/app/api/games/[id]/guesses/route.ts (compute score on submit)
  - app/app/page.tsx (render scores in rows)

The plan
| Minutes | What you do |
|---|---|
| 0-6 | Recap Mastermind scoring with a 4-slot example. Blacks: exact positions; Whites: colour matches minus blacks. |
| 6-14 | Live-code cut-score-count-black in lib/scoring.ts. Unit-think: for i in 0..3, compare secret[i] to guess[i]. |
| 14-22 | Live-code cut-score-count-white. Count per-colour frequencies, sum min(secret_c, guess_c), then subtract black once. Show a repeated-colour case to justify. |
| 22-27 | Live-code cut-ep-score-on-submit: derive secret from seed and call scoreGuess; include black/white when saving/returning the guess. Post a correct and a permuted guess; read JSON. |
| 27-33 | Live-code cut-ui-render-scores: build rows that show g.black and g.white in score-black and score-white. Verify on the page. |
| 33-38 | Students try two more guesses to see whites change; you circulate. |
| 38-40 | What runs now and what Session 3 will add (hint + remaining). |

Cut points in this session

### cut-score-count-black - lib/scoring.ts:27
- What students see: `// TODO(cut-score-count-black): Count exact matches into \`black\` by comparing secret and guess at the same index for all 4 slots`
- What they write: loop i = 0..3 and increment black when secret[i] === guess[i].
- Teach it like this: Blacks are position-sensitive; this is a straight pass over 4 elements.
- Passes when: c-2-2 and c-2-4 go green.

### cut-score-count-white - lib/scoring.ts:32
- What students see: `// TODO(cut-score-count-white): Count colour-only matches into \`white\` without double counting: for each colour 0..5, add the minimum of its frequency in secret and in guess, then subtract \`black\``
- What they write: build two length-6 histograms, sum min counts across colours into total, then set white = total - black.
- Teach it like this: Whites are colour matches ignoring position but must not double count; subtract black once at the end.
- Passes when: c-2-3 and c-2-4 go green.

### cut-ep-score-on-submit - app/api/games/[id]/guesses/route.ts:30
- What students see: `// TODO(cut-ep-score-on-submit): After loading the Game's secret from its seed, compute the guess's black/white using the scoring function, assign the result to \`score\`, and include those numbers when saving and in the response`
- What they write: deriveSecret(game.seed), call scoreGuess(secret, code), assign into the provided score object; persist black/white with the guess and return them.
- Teach it like this: Compute first, then write once; the shape is pure logic then persistence, keeping the return outside the block.
- Passes when: c-2-2, c-2-3 and c-2-4 go green.

### cut-ui-render-scores - app/page.tsx:112
- What students see: `// TODO(cut-ui-render-scores): Build \`rows\` from the saved guesses so each row renders the 4 pegs and shows the row's black and white counts in their testids`
- What they write: map guessesState to divs with guess-row-<n>, render code pegs and include <span data-testid="score-black">{g.black}</span> and <span data-testid="score-white">{g.white}</span>.
- Teach it like this: Render from saved guesses, not the pending pick. These spans are the test hooks; keep them as plain text.
- Passes when: c-2-5 goes green.

Where students get stuck
- "I subtracted black per colour and whites are low" - Subtract once at the end from the total min-frequency across colours.
- "Everything is black=0 white=0" - You never computed or saved score; ensure cut-ep-score-on-submit assigns score and the save uses those numbers.
- "Scores show as empty strings" - You returned nulls; in S2 they must be numbers. Compute score and include both values in the response.
- "UI shows NaN or [object Object]" - You rendered the whole score object; render g.black and g.white separately as text.

Check before moving on
- POSTing a guess equal to the secret returns black=4 white=0; a permuted-all-colours guess returns black=0 white=4. On the page, each row shows matching black and white counts.
