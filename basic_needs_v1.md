# Guided Project Automation

# 

## 1. What it is

A pipeline that turns a tech stack into a ready-to-teach course project:
working code, a student starter version, and an instructor guide.

Humans decide. AI drafts. Scripts check.

## 2. Why

Today, one project takes days of manual work. Testing it by hand takes ~40 minutes
and must be repeated after every fix.

Target: 1 project per day. Human time drops to ~2 hours of reviewing, not building.

## 3. Who does what

| Role | Job |
| --- | --- |
| Human | Gives the tech stack. Approves ideas. Approves at 4 gates. |
| AI | Proposes ideas. Writes specs, tests, code, guides. |
| Script | Checks everything the AI produces. |

Two rules that never change:

- **The human gives the stack. The AI does not choose it.**
- **The AI gives the ideas. The human approves them. The AI does not pick.**

## 4. The flow

```
  0  Human gives stack + limits            human
  1  Idea generator (5 options)            AI
  2  GATE 0 — pick one idea                human
 ----------------------------------------------- PLAN
  3  Spec writer                           AI  → spec linter
  4  Ambiguity check                       AI  → read at Gate 1
  5  Test writer                           AI  → red-first check
  6  GATE 1 — approve plan + tests         human
 ----------------------------------------------- CODE
  7  Builder                               AI  → test runner
  8  Verifier (browser tests)              AI  → coverage + mutation
  9  GATE 2 — read pass/fail list          human
 ----------------------------------------------- HANDOVER
 10  Cutter (make student version)         script
 11  Guide writer                          AI  → guide linter
 12  Deploy check                          script
 13  Dry run (timed, by a person)          human
 14  GATE 3 — approve the pack             human
 ----------------------------------------------- LIVE
 15  Nightly check + feedback intake       script
```

## 5. The steps

| # | Step | What it does |
| --- | --- | --- |
| 0 | Stack input | Human states the stack, number of sessions, minutes per session. |
| 1 | Idea generator | AI proposes 5 project ideas that fit that stack. One page each. |
| 2 | **Gate 0** | Human picks one, or asks for 5 more. |
| 3 | Spec writer | Splits the project into sessions. Each session lists what to build, what students will type, and how long it takes. |
| 4 | Ambiguity check | A **different** AI lists sentences with two possible meanings. It only lists. It does not fix. |
| 5 | Test writer | Writes the tests from the spec. A **different** AI from the builder. |
| 6 | **Gate 1** | Human approves the spec, the ambiguity list, and the tests. |
| 7 | Builder | Writes the working code, session by session, until tests pass. |
| 8 | Verifier | Writes a browser test that clicks through every screen, then runs it. |
| 9 | **Gate 2** | Human reads the pass/fail list. ~2 minutes instead of ~40. |
| 10 | Cutter | Removes the marked parts to make the student starter version. No AI. |
| 11 | Guide writer | Writes the instructor guide: what to build, in what order, what to explain. |
| 12 | Deploy check | Fresh install from scratch. Proves it runs on another machine. |
| 13 | Dry run | A person who did not build it teaches one session from the guide, with a timer. |
| 14 | **Gate 3** | Human approves. Checks nothing continues without this. |
| 15 | Live | Nightly re-run of the saved browser test. Instructor feedback goes back to step 3. |

## 6. Rules the build must enforce

These exist because each one is a way the pipeline quietly fails.

1. **Tests are written before the code, by a different AI.** The builder cannot edit them. The tests folder is read-only to it.
2. **Red-first.** Every new test must fail before the code is written. A test that passes early proves nothing.
3. **The verifier is checked by a script.** It must cover every requirement, and it must go red when we deliberately break the code. Otherwise a useless test looks green.
4. **The cutter uses no AI.** The same code must always produce the exact same student version.
5. **The student version must fail exactly the tests students are meant to fix.** No more, no less.
6. **Leak scan.** Solutions must not appear in comments, README, migrations, seed data, or git history.
7. **Builder stops after 15 tries** and files a ticket marked either *code problem* (stays in phase 2) or *spec problem* (goes back to step 3).
8. **Any later edit re-enters at step 7** and re-passes Gates 2 and 3. Never hand-edit the student version.

## 7. Repo layout

```
course/
  ideas/        idea-01.md … idea-05.md
  spec/         S01.yaml … (+ ambiguity notes)
  tests/        read-only to the builder
  e2e/          browser tests, kept forever
  solution/     full working code, with markers
  student/      generated only, never hand-edited
  guide/        S01.md …
  gates/        who approved what, and which commit
  tools/        all check scripts
```

IDs: session `S03`, requirement `S03-AC01`, student task `S03-T01`.

Marker in the solution code:

```
# >>> STUDENT S03-T01 START
#     goal: <one line>
   ...answer code...
# <<< STUDENT S03-T01 END
```

## 8. What we build first

One session. Not the whole pipeline. Humans pass work between steps by hand.

**Order: scripts first, AI second.** The scripts are what make the AI trustworthy.

| Week | Build |
| --- | --- |
| 1 | All check scripts: spec linter, red-first check, marker check, cutter, cut validator, leak scan |
| 2 | Idea generator, spec writer, test writer, builder — run by hand |
| 3 | Verifier + coverage check + mutation check |
| 4 | Guide writer, deploy check, then the timed dry run |

## 9. Done when

1. The cutter run twice gives an identical file, byte for byte.
2. The red-first check catches a fake test (`assert True`).
3. The mutation check catches a fake browser test (one that only checks the page loads).
4. The leak scan catches an answer left in git history.
5. The dry run finishes one session inside its time limit, using only the student version and the guide.

Four of these five feed the pipeline something deliberately broken and require it to notice.
A pipeline that has never caught anything has not been proven to work.

## 10. Not in scope for v1

- No orchestration engine, no queues, no dashboard
- One session only
- No frontend browser tests yet (API level only)
- No nightly checks yet (nothing is live)