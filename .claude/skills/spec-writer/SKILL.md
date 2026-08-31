---
name: spec-writer
description: Turn a one-page guided-project idea into a full spec - spec.md for the person at Gate 1 and spec.json for every script downstream. Use for step 2 of the guided project pipeline, including retries after the spec linter rejects.
---

# Spec Writer

Step 2. You turn a one-page idea into a spec with one milestone per session.

You are the only agent that decides what gets built. Everything after you obeys
this file. A line that could mean two things becomes a wrong project.

## Read first

1. `projects/<slug>/idea.md` - the one-page idea. This is the brief.
2. `projects/<slug>/.pipeline/CONTRACT.md` - the exact shape of what you write.
3. `learning/lessons.md` - mistakes already made once. Do not make them again.
4. The source material named in `idea.md`, if any. If `Source material` is
   `none`, work from the idea alone and follow the house format. If it names a
   file, every concept you teach must appear in it - do not invent curriculum.
5. `projects/<slug>/lint.json` - **only on a retry**. If it exists and
   `ok` is false, fix exactly those errors. Do not redesign the project.

## Write two files

`spec.md` is what a person reads at Gate 1. `spec.json` is what the linter,
the builder, the verifier and the cutter parse. They must agree. `CONTRACT.md`
has the full JSON shape and the id patterns - follow them exactly.

### spec.md

Headings, in this order: `## Outcome`, `## Out of scope`, `## Data model`,
`## Endpoints`, `## Screens`, `## Sessions`. Under `## Sessions`, one
`### Session N - Title` per session, each with its goal, what it teaches, its
acceptance criteria written out with their ids, and its cut points with their
ids. A person must be able to read this alone and picture the project.

### spec.json

The machine contract. Every endpoint, every screen, every session, every
criterion, every cut.

## The four things that make a spec pass

**One milestone per session, and it fits 40 minutes.** Two to six acceptance
criteria and at most five cut points per session. If a session needs more, it is
two sessions - say so and raise the session count. The student must have
something that runs at the end of every session, not at the end of session four.

**Every criterion is a thing a script can check.** Name an HTTP method and path,
a status code, or a screen id and what appears on it. Write
`GET /api/todos returns 200 with a JSON array of Todo`, not
`the API works`. Never write: etc, appropriate, as needed, user-friendly,
properly, handle errors, robust, intuitive, various, and so on. The linter
rejects all of them.

**Every cut point is where the learning is.** A cut is the block the student
writes in the session. Cut the state update, the fetch handler, the sort
comparator - the line the concept lives on. Never cut boilerplate, imports,
config, or type declarations. Every cut needs a `hint` that is a real sentence:
the hint is the entire instruction the student sees where the code used to be.
Say what the code must do, never how to write it.

**Cuts and criteria are joined.** Every cut must be referenced by at least one
criterion's `cuts` list, and every criterion that depends on student work must
name its cuts. This join is what lets the cutter prove the skeleton fails the
right tests. A cut no criterion depends on is a hole with no test, and the
linter rejects it.

## The four rules that rejected the last two specs

These are the linter checks added after round 1. Each one has failed a real
spec, so design for them from the start instead of discovering them on retry.

**No two cuts may be graded by exactly the same criteria (`E110`).** Collect the
set of criteria that reference each cut. If two cuts have the *same* set, no
test can tell them apart: a student can leave one empty, do its work inside the
other, and every criterion still passes. On the last project
`cut-fraction-scale` and `cut-recipe-scale-quantity` both appeared in c-4-2,
c-4-3 and c-4-4 and nowhere else, so one of them graded nothing.

The fix is always the same: **give one of the pair a criterion the other does not
gate.** A pure function gets a criterion that exercises it directly; a store
lookup gets its own miss case (a 404); a fetch gets a criterion the render does
not appear in. This is worth doing deliberately as you write, cut by cut - ask
"which criterion fails if *only* this cut is left empty?" If you cannot name
one, the cut is not graded.

The same rule closes the skeleton check's blind spot. It can only prove the
all-cuts-open and no-cuts cases, so a pair that share a signature is exactly
where a half-finished skeleton goes green.

**The session carrying the project setup gets fewer cuts than the others
(`E113`).** Session 1 usually builds the store, the types, the seed data and the
first screen before any cut point is reached. A session with the setup *and* as
many cuts as the others overruns - the last project shipped one at 45 minutes
against the 40 cap. Give session 1 one or two fewer cuts than sessions 2 and 3.

**Teaching minutes are estimated, not just counted (`E111` / `W112`).** The
linter costs a session at roughly: 10 minutes of base, then each cut (see the
next rule for what a cut costs), 3 per endpoint or screen built, 1.5 per concept
in `teaches`, plus 6 for the setup session. Over 40 is a warning, over 50 is a
rejection. Keep `teaches` honest - padding it costs minutes.

The estimate is calibrated on four sessions, only two of them actually timed,
and its worst error is about 5 minutes. It is a signal to design against, not a
measurement. Nothing before the step 13 dry run measures teaching time.

**A cut costs what its DECISIONS cost, not what its hint length costs
(`W114`).** On flow 2 a cut is priced at 6 minutes plus 1.7 for every branch its
hint states - a condition (`unless`, `otherwise`, `when`, `if`, `except`) or an
ordering between rules (`then`, `before`, `in that order`) - plus a small
residual for length beyond 55 words, which catches an algorithm that states no
conditions at all. A cut taking more than 45% of a session's cut minutes is
warned.

**This replaced a word-count model that pipeline-test-03 disproved.** Every cut
in that spec came in at 46-53 words, under the old nominal; the linter reported
both sessions at 38.5 against the 40 cap and said nothing; the Pack Writer then
timed session 1 at 48 and session 2 at 45. The excess was one cut,
`cut-parse-line`, which states four ordered fallbacks in 53 words and takes
about 13 live minutes. Three ordered rules compress into 53 words as easily as
one rule does.

So, when a cut prices high:

- **Split it so each half states fewer decisions.** That is the only move that
  makes the session shorter.
- **Do not shorten the hint.** It changes the estimate barely and the teaching
  time not at all, and it makes the hint worse. The word term exists only to
  catch algorithms with no conditional prose; it is not a lever.
- **Do not move a cut into the setup session** to relieve a heavy one. That
  trades `W114` for `E113`.

**Name drop candidates that are actually live minutes.** pipeline-test-03's spec
named markup elements as its trims - but all five cuts were in `lib/` and every
page file shipped written, so no student typed that markup and dropping it
recovered nothing. A named mitigation that costs zero live minutes is worse than
naming none, because it reads as slack that is not there. A drop candidate must
be something a student types during the session.

The estimate is in `lint.json` under `session_minutes`, broken down per cut with
its decision count. Read it rather than counting in your head.

**Hints name something concrete, and never say "return" (`W066` / `W067`).**
Name the symbol, the state value, the path, the status or the count the student
is working towards - `` `scaleQuantity` ``, `the items state`, `200`, `one row
per habit`. And phrase the hint as an assignment, not a return: a cut that holds
a typed function's only `return` leaves a skeleton that does not compile, so the
convention is that the return stays *outside* the markers and the cut assigns
what feeds it. Write "put every todo into `body` and set `status` to 200", not
"return every todo as JSON". `.pipeline/CONTRACT.md` has the pattern.

## Constraints the tests cannot see

Some constraints are load-bearing and invisible to a test suite. "The date
arithmetic must give the same answer in every timezone" is one: the Verifier
cannot change the server's `TZ`, so no criterion can assert it, and on
habit-tracker it went straight into the "nothing catches it" column that Gate 1
rejects on.

If the constraint is about the *shape of the code* rather than its behaviour,
declare a named static check at the top level of `spec.json`:

```json
"code_checks": ["utc-dates"]
```

| Name | What it enforces over `app/` at step 6 |
|---|---|
| `utc-dates` | No local-time `Date` accessors (`getDay`, `setDate`, `toLocaleDateString`, ...) and no reading the real clock (`new Date()` with no arguments, `Date.now()`). Declare it whenever the project does date arithmetic on `YYYY-MM-DD` strings |

The linter rejects a name that does not exist, and a violation fails step 6, so
the Builder fixes it in the normal loop. Do not invent names - the list above is
the whole list. If a constraint you need is not on it, say so plainly in
`spec.md` under the constraint, so the person at Gate 1 knows nothing checks it.

## Rules

- Cut ids are global across the whole spec. Criterion ids are `c-<session>-<k>`,
  numbered from 1 within each session, in order.
- Each endpoint and each screen is built in exactly one session.
- Nothing may be TODO, TBD or a placeholder. If you do not know, decide.
- Do not write code. Do not create `app/`.
- Scope down before you scope up. A project that fits is worth more than a
  project that impresses.

## Then stop

Write `spec.md` and `spec.json`. Return a two-line summary: session count and
criteria count. The orchestrator runs the linter. If it fails you will be called
again with `lint.json`.
