# Round 1

Gate 1: rejected
Note: GATE 1 REJECTED - round 1. Human review at Gate 1, plus two findings the rule requires.

Fix every item below. Keep everything not faulted - this is a revision, not a rewrite.
The parts confirmed good at review are listed at the end: do not regress them.

=== MUST FIX (blocking approval) ===

M1. Remove or make checkable the independence claim in spec.md Session 1:
    "c-1-3 and c-1-4 pin the four streak numbers and pass with an empty week
    array. Neither can be done inside the other."
    This asserts a PARTIAL-skeleton property. The skeleton check proves only two
    states - all of a criterion's cuts open must fail, no cuts must pass - so a
    claim about what happens with one cut filled and another empty is exactly the
    state nothing verifies. It is also load-bearing: it is the justification that
    cut-week-dates and cut-streak-count are independently graded. Either delete
    the sentence, or add a criterion that actually pins the behaviour it claims.
    Do not state an unverified partial-state property as fact.

M2. Define exactly which dates POST /api/habits/[id]/toggle accepts. Say whether
    a date outside the tracked Monday-to-Sunday week is accepted or rejected, and
    with what status. Today only a MISSING date is a 400.

M3. Define the behaviour for an invalid date, including a malformed string
    ("not-a-date", "2026-13-45", "26-08-2026"). Name the status and the body.
    A malformed date currently returns 200 and writes junk into the store.

M4. Make the readStore -> findHabit -> writeStore relationship in cut-api-toggle
    coherent. The hint says "save the file with writeStore(store)" but the habit
    came from findHabit(habitId), whose hint reads from readStore().habits, so
    `store` is not a binding in that route file and the object mutated need not
    be in the store that gets written. Either state in the Data model that
    readStore() re-reads and re-parses on every call and rewrite the hint to
    read the store into `store` and find the habit inside it, or change the
    signature to findHabit(store, habitId) and say so. The Builder cannot edit
    hints, so it will write coherent code that no longer matches the sentence the
    student is given - the recipe-box round-2 failure shape.

M5. (required by the Gate 1 stopping rule - finding A1, owned by `nothing`)
    Out of scope bans "Reading new Date() anywhere in app/ or lib/" while the
    Data model says "No Date object crosses a module boundary", which only makes
    sense if Date may exist inside a module. Under the loose reading the obvious
    implementation is new Date("2026-08-26").getDay(), which is Wednesday in IST
    and Tuesday west of Greenwich - shifting the computed Monday and reddening
    c-1-2 and c-1-5 for students only, because the pipeline runs in one timezone
    and its own suite stays green. Under the literal reading cut-week-dates
    becomes 25+ lines of civil-date arithmetic in a session already at 38.5/40
    minutes. Replace the Out of scope bullet with: "Reading the real clock - no
    zero-argument new Date() and no Date.now(), anywhere in app/ or lib/.
    Constructing a Date from the seed's trackedDay string is allowed." Then add
    to the cut-week-dates hint: "use the UTC accessors (getUTCDay, setUTCDate) or
    plain string arithmetic, so the answer does not change with the machine's
    timezone."

=== SHOULD CLARIFY (before the spec is frozen) ===

S1. State whether an invalid or rejected request must leave data/habits.json
    byte-for-byte untouched, and add a criterion if it must.
S2. `error` is declared as a screen state. Either define what the screen renders
    in it, with a testid, and give it a criterion, or drop it from the declared
    states.
S3. Define the type and value of the { error } body - is it a string, a code, a
    message? c-2-2 only says "a JSON body carrying an error key".
S4. Align "refreshes only that habit's row" with what c-3-5 can actually verify.
    As written it is indistinguishable from a full refetch. Either state the
    observable difference and pin it, or reword the claim.
S5. Say whether a doneDates array may contain duplicates, and what toggleDate
    does if it finds one.
S6. Say whether data/habits.json is git-tracked or ignored, and where
    data/habits.seed.json fits. The tests delete the live file.

S7. (added - Spec Breaker finding A3, blocking, owned test-runner) The reset
    paragraph scopes "delete data/habits.json first" to session 3's tests, but
    every session-3 test leaves the file mutated, so c-1-3, c-1-4 and c-2-1
    assert seed-state numbers that are wrong on the second run of the suite in
    the same working copy. Extend the reset to every test in every session.
    Note: this is what a nightly watchdog run would catch, i.e. after ship.

=== CONFIRMED GOOD AT REVIEW - DO NOT REGRESS ===

Fixed deterministic tracked week; no real clock; strong seed cases (a 5-streak, a
gap-reset 0, an all-empty habit); clear data contract; three sessions; the setup
session carries fewer cuts than the others (2 against 3); good cut/criterion
separation - all eight cuts have distinct grading signatures; strong toggle
testing; the 404 and 400 paths; concrete UI selectors (data-testid, data-habit-id,
data-date, data-done); no network or database dependency; session 2's cut
separation; session 3's add / remove / toggle-twice coverage.

Linter was clean at 0 errors and 0 warnings with session minutes 38.5 / 38.5 /
35.5 against the 40 cap. Keep it that way.
