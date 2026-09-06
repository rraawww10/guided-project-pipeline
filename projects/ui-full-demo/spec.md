## Outcome
A single-screen league standings table at "/" renders from seeded match results. It shows one row per team with columns: Team, P, W, D, L, GF, GA, GD, Pts. The Rank column is added in Session 2 once ranking exists. Rows are computed from local JSON in session 1 and, from session 2 on, fetched from GET /api/standings. Ties are deterministic: sort by points desc, then goal difference desc, then goals for desc, then team name asc. Rank numbers are assigned with shared ranks for exact numeric ties (points, GD, GF equal), skipping k−1 ranks for a tie block of size k (e.g. 1,1,1,4).

## Out of scope
- More than one screen or more than one endpoint
- Live schedules, head-to-head or strength-of-schedule rules
- Pagination, filters, search, or importing data
- Auth, database, external services; local JSON only

## Data model
- Match
  - id: string
  - home: string
  - away: string
  - homeGoals: number
  - awayGoals: number
- TeamStat
  - team: string
  - played: number
  - won: number
  - drawn: number
  - lost: number
  - gf: number
  - ga: number
  - gd: number  (gf - ga)
  - points: number  (3 win, 1 draw, 0 loss)
- StandingRow (what the endpoint returns)
  - rank: number
  - team: string
  - played: number
  - won: number
  - drawn: number
  - lost: number
  - gf: number
  - ga: number
  - gd: number
  - points: number

Seed data
- File: data/matches.seed.json (tracked)
- Shape: Match[] as above
- Teams present in seed: Lions, Bears, Hawks, Wolves
- The verifier computes expected totals directly from this file; the spec does not pin numeric totals.

## Endpoints
- ep-standings-list: GET /api/standings
  - Request: none
  - Response: StandingRow[]
  - Status: 200 only

## Screens
- sc-standings
  - route: "/"
  - elements: table[data-testid=standings-table], tr[data-testid=row-<TEAM>], [data-testid=toggle-<TEAM>], [data-testid=panel-<TEAM>], [data-testid=sum-<TEAM>]
  - states: loaded, expanded

## Sessions

### Session 1 - Seed and totals on a table
Goal: Read seeded matches and fold them into per-team totals, then render a basic standings table at "/" from local data, unsorted. No Rank column yet in this session.

Teaches: array reduce, mapping to rows, JSX table rendering

Acceptance criteria
- c-1-1: Screen sc-standings at / renders a table with data-testid "standings-table" and one <tr data-testid="row-<TEAM>"> per team in data/matches.seed.json (4 teams)
  - target: sc-standings
  - cuts: [cut-stats-from-matches, cut-page-rows-render]
- c-1-2: The row for team "Lions" shows P, W, D, L, GF, GA and Pts equal to totals computed from data/matches.seed.json
  - target: sc-standings
  - cuts: [cut-stats-from-matches, cut-page-rows-render]
- c-1-3: Screen sc-standings renders exactly 4 rows with data-testid row-<TEAM> (one per distinct team in data/matches.seed.json)
  - target: sc-standings
  - cuts: [cut-stats-from-matches]

Cut points
- cut-stats-from-matches (app/lib/stats.ts)
  - writes_into: table
  - hint: For every match in the input, ensure both teams have a row in `table`, add goals for and against to their rows, update W/D/L, and add 3/1/0 to points, leaving the updated entries in `table`.
- cut-page-rows-render (app/app/page.tsx)
  - writes_into: rowsEl
  - hint: Build per-team totals from the seed and put one <tr data-testid="row-<TEAM>"> per team into `rowsEl`, with columns Team, P, W, D, L, GF, GA, GD and Pts taken from the computed totals.

### Session 2 - Deterministic ranking and API
Goal: Implement a pure rankTeams(stats) that sorts by points desc, goal difference desc, goals for desc, then team name asc, assigns shared rank numbers to exact numeric ties (skipping k−1 ranks for a tie block of size k), and serve the ranked rows from GET /api/standings; the page reads and renders it.

Teaches: multi-key comparator, tie-block rank assignment, Next.js route handler, client/server data flow

Builds: ep-standings-list

Acceptance criteria
- c-2-1: GET /api/standings returns 200 with a JSON array of StandingRow where each row includes a correct rank per the tie rules and the array is sorted by points desc, goal difference desc, goals for desc, then team name asc
  - target: ep-standings-list
  - cuts: [cut-rank-sort, cut-rank-assign, cut-api-standings]
- c-2-2: Screen sc-standings renders teams tied on points and goal difference with the higher goals-for team first, and shows consecutive rank numbers for those two rows
  - target: sc-standings
  - cuts: [cut-rank-sort, cut-rank-assign]
- c-2-3: Screen sc-standings reads from /api/standings and renders a Rank column with "1" in the first row and non-decreasing rank numbers down the table
  - target: sc-standings
  - cuts: [cut-page-load-from-api, cut-api-standings]
- c-2-4: Screen sc-standings renders teams tied on points, goal difference and goals for in alphabetical order by team name, and shows the same rank number for both while the next row's Rank skips the following number
  - target: sc-standings
  - cuts: [cut-rank-sort]
- c-2-5: GET /api/standings returns 200 with a JSON array of StandingRow where any tie block of size k>1 shares one rank number across the block and the first following row's rank increases by k (e.g. 1,1,3 or 1,1,1,4)
  - target: ep-standings-list
  - cuts: [cut-rank-assign, cut-api-standings]

Cut points
- cut-rank-sort (app/lib/rank.ts)
  - writes_into: sorted
  - hint: Sort the given per-team stats into `sorted` by points descending, then goal difference descending, then goals for descending, and finally by team name ascending.
- cut-rank-assign (app/lib/rank.ts)
  - writes_into: withRanks
  - hint: Walk the sorted rows and fill `withRanks` so exact numeric ties (points, GD and GF all equal) share the same rank number and the following ranks skip k−1 positions where k is the size of the tie block (e.g. 1,1,1,4); otherwise the rank increases by one per position.
- cut-api-standings (app/app/api/standings/route.ts)
  - writes_into: body
  - hint: Put the ranked standings rows into `body` as JSON and set `status` to 200.
- cut-page-load-from-api (app/app/page.tsx)
  - writes_into: rows
  - hint: Read /api/standings and assign the parsed array into `rows` so the table renders the API result.

### Session 3 - Rationale on demand
Goal: Clicking a team opens a panel listing the matches that contributed its totals with per-match deltas; clicking again closes it. The rationale derives client-side from the same seeded matches (no new endpoint).

Teaches: deriving a per-item detail list from aggregate data, UI toggle state, mapping a derived list to JSX

Acceptance criteria
- c-3-1: On sc-standings, after clicking data-testid "toggle-Lions", "panel-Lions" is displayed and shows one line per match for that team; each line names the opponent and includes a points delta exactly formatted as "+3 pts" (win), "+1 pt" (draw) or "+0 pts" (loss), and a goal-difference delta exactly formatted as "GD +k" (win), "GD 0" (draw) or "GD -k" (loss)
  - target: sc-standings
  - cuts: [cut-build-rationale, cut-render-rationale, cut-toggle-expand]
- c-3-2: The open panel for a team shows a summary with data-testid "sum-<TEAM>" whose points total equals that row's Pts value
  - target: sc-standings
  - cuts: [cut-build-rationale, cut-render-rationale]
- c-3-3: On sc-standings, clicking data-testid "toggle-<TEAM>" twice hides the panel; data-testid "panel-<TEAM>" is not rendered after the second click
  - target: sc-standings
  - cuts: [cut-toggle-expand]
- c-3-4: buildTeamRationale(team, matches) returns one entry per match that team appears in, each entry carrying the match id, opponent name, points delta (3/1/0) and goal-difference delta
  - target: sc-standings
  - cuts: [cut-build-rationale]

Cut points
- cut-build-rationale (app/lib/rationale.ts)
  - writes_into: out
  - hint: From the seeded match list loaded on the client, select only the matches that involve the given team and fill `out` with one entry per match carrying the opponent, a points delta of 3/1/0 from the result, and the goal-difference delta for that match.
- cut-toggle-expand (app/app/page.tsx)
  - writes_into: open
  - hint: Toggle the boolean `open` for the clicked team id so the panel appears on first click and disappears on second click.
- cut-render-rationale (app/app/page.tsx)
  - writes_into: panelEl
  - hint: When a row is open, put a list into `panelEl` (data-testid="panel-<TEAM>") with one item per entry from buildTeamRationale, showing the opponent name plus the points and GD deltas, and include a summary element data-testid="sum-<TEAM>" with the total points from those entries.
