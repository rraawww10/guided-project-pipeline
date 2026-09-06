# Ambiguity report - ui-full-demo

**Verdict:** 2 blocking, 3 worth a look

## Blocking
### A1 - GD column present in Session 1 or not
- **Where:** spec.md, Session 1, criterion c-1-2 and cut-page-rows-render hint; spec.json mirrors both
- **Owner:** nothing
- **The line:** "The row for team \"Lions\" shows P, W, D, L, GF, GA and Pts equal to totals computed from data/matches.seed.json"
- **Reading one:** Session 1 does not require a GD column (it is omitted here intentionally), so rendering P, W, D, L, GF, GA, Pts is sufficient.
- **Reading two:** Session 1 must include a GD column, because the cut hint for cut-page-rows-render says to render "Team, P, W, D, L, GF, GA, GD and Pts".
- **Why it matters:** The builder must choose the table’s column set for Session 1; picking the wrong one changes the shipped UI while tests may not assert GD at all. This is a gap between acceptance and hint with no downstream check to force alignment.
- **Suggested wording:** Either add GD to c-1-2 ("... GF, GA, GD and Pts ...") or remove GD from the cut hint; make the Session 1 column set explicit in one place.

### A2 - Rationale list ordering is unspecified
- **Where:** spec.md, Session 3, criteria c-3-1 and c-3-4
- **Owner:** test-runner
- **The line:** "buildTeamRationale(team, matches) returns one entry per match that team appears in, each entry carrying the match id, opponent name, points delta (3/1/0) and goal-difference delta"
- **Reading one:** The entries may appear in any order (e.g., input file order or as computed), and the UI may render them in that order.
- **Reading two:** The entries must be sorted in a specific, stable order (e.g., by match id, by date, or by home/away/chronological order) for display consistency.
- **Why it matters:** The builder has to pick an order; tests that assume an order will fail if the other is built, and if tests don’t assert order, two students can ship different UIs.
- **Suggested wording:** State the required order explicitly (e.g., "Order entries by match id ascending" or "preserve the order of matches in the seed file").

## Worth a look
### W1 - One panel open vs multiple panels open
- **Where:** spec.md, Session 3, criterion c-3-3
- **Owner:** nothing
- **The line:** "clicking data-testid \"toggle-<TEAM>\" twice hides the panel; data-testid \"panel-<TEAM>\" is not rendered after the second click"
- **Reading one:** Panels are independent; multiple teams’ panels can be open at once, each toggled separately.
- **Reading two:** The UI is an accordion; opening one team closes any other open panel.
- **Why it matters:** Both are reasonable; the choice changes shipped behaviour and layout, and no criterion states exclusivity.
- **Suggested wording:** Add whether multiple panels may be open simultaneously ("Panels are independent; multiple may be open" or "At most one panel may be open at a time").

### W2 - Rank column criterion is weakly specified
- **Where:** spec.md, Session 2, criterion c-2-3
- **Owner:** test-runner
- **The line:** "renders a Rank column with \"1\" in the first row and non-decreasing rank numbers down the table"
- **Reading one:** Any non-decreasing sequence (allowing repeats or 1..n) satisfies this, independently of the tie rules, as long as it never decreases.
- **Reading two:** The UI must display the exact rank values from the API, including shared ranks and skips per the tie-block rules.
- **Why it matters:** A builder could compute 1..n locally and still meet this sentence; only stricter assertions will guarantee duplicates and skips appear. Other criteria cover tie behaviour in parts, but c-2-3 alone admits two builds.
- **Suggested wording:** "Display the rank value from /api/standings for each row (first row is 1) so ranks repeat for ties and skip after tie blocks."

### W3 - Unsorted order in Session 1 is unspecified
- **Where:** spec.md, Session 1, Goal paragraph and overall table rendering
- **Owner:** test-runner
- **The line:** "render a basic standings table at \"/\" from local data, unsorted"
- **Reading one:** Preserve the input seed’s team discovery order (e.g., first-seen order) when rendering rows.
- **Reading two:** Any consistent order is acceptable (e.g., alphabetical by team), since “unsorted” only means “no ranking yet”.
- **Why it matters:** The shipped UI’s row order may differ between reasonable implementations; tests that assert a specific order would fail one reading.
- **Suggested wording:** State the intended Session 1 order explicitly (e.g., "render rows in alphabetical order by team" or "preserve first-seen order from the seed").
