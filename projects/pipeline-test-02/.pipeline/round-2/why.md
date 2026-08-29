# Round 2

Gate 1: rejected
Note: B1: cut-cell-cycle's marker boundary is unpinned - the spec never says whether setGrid and POST /api/puzzles/<id>/check sit inside or below the cut. Both readings satisfy every stated constraint and are identical in app/, so no downstream checker sees the difference; under reading two a student who fills the hint exactly gets c-2-5 green and c-2-6 permanently red, and session 2's payoff never fires. Fix per the breaker's drafted wording: add to the fallback table preamble that both calls sit BELOW the closing marker. W1 and W5 also owned by nothing but non-blocking; W2/W3 owned by pack-writer, W4 by test-runner - noted, not fixed here.
