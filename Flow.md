# Guided project production pipeline

How guided projects are produced today, and what we plan to automate.

---

## The problem

One person does the whole thing by hand.

| Step today | Problem |
|---|---|
| Write a spec and hand it to a coding agent | Nothing checks the spec. Unclear lines get through and the agent guesses |
| Test the finished project by hand | The slowest step. About 40 minutes per project. Does not scale to four tracks |
| Strip the final code by hand to make the student skeleton | The skeleton drifts away from the final code. Students hit walls that are not their fault |
| No session guide | The instructor works out the plan by reading the code |
| Nothing is written down | A mistake fixed in project 3 comes back in project 7 |
| Library versions move on | A project breaks during a live session |

Row two is the one to fix first. A machine can boot the app, open every screen, call every endpoint, and return a pass or fail list.

---

## The twelve steps

```
LEGEND
  [PERSON]  a person decides         |    down    = next step
  [AGENT]   an agent does the work   |    <->     = redo until the check passes
  [SCRIPT]  plain code, no agent     |    . . .   = sent back

  PHASE 1 - THE SPEC                             CHECKED BY

   1  [PERSON]  Write the one-page idea           your call
         |
   2  [AGENT]   Spec Writer               <->     spec linter  [SCRIPT]
         |
   3  [AGENT]   Spec Breaker               ->     one pass, you read it
         |
   4  [PERSON]  Gate 1 - approve the spec  . . .  back to 2 if rejected
         |
  PHASE 2 - THE CODE
         |
   5  [AGENT]   Builder                   <->     test runner  [SCRIPT]
         |
   6  [AGENT]   Verifier                  <->     its own pass or fail
         |
   7  [PERSON]  Gate 2 - read the report   . . .  back to 5 if it failed
         |
  PHASE 3 - THE PACKAGE
         |
   8  [SCRIPT]  Cutter                      ->    skeleton fails the right tests
         |
   9  [AGENT]   Pack Writer                 ->    one pass, you read it
         |
  10  [SCRIPT]  Deploy check                ->    checks itself
         |
  11  [PERSON]  Gate 3 - approve the pack   . . . back to 9 if rejected
         |
  12  [SCRIPT]  Handover, then a nightly watchdog
```

---

## What each step does

| # | Step | Who | What it does |
|---|---|---|---|
| 1 | Write the one-page idea | Person | Theme, scope, number of sessions, tech stack. One page |
| 2 | Spec Writer | Agent | Turns the one page into a full spec, one milestone per session |
| 3 | Spec Breaker | Agent | Reads the spec and flags any line that could mean two things |
| 4 | Gate 1 | Person | Approve the spec. Can each session be taught in 40 minutes. Is every flagged line now clear |
| 5 | Builder | Agent | Writes the working project, one finished milestone at a time |
| 6 | Verifier | Agent | Writes a test script that opens every screen and calls every endpoint, then runs it |
| 7 | Gate 2 | Person | Read the pass or fail list instead of testing by hand |
| 8 | Cutter | Script | Makes the student skeleton by removing the marked blocks from the final code |
| 9 | Pack Writer | Agent | Writes the instructor session guide, including where students usually get stuck |
| 10 | Deploy check | Script | Fresh copy, install, build, temporary preview link |
| 11 | Gate 3 | Person | Approve the pack. Could someone teach session 4 from this guide alone |
| 12 | Handover | Script | Ship it. Every night after that, replay the test script to catch a project that has broken on its own |

---

## Rules

1. Every agent must have something that checks its work. If nothing can check it, the agent gets one try and a person reads the output.
2. The Spec Breaker is a different agent from the Spec Writer, so it is not reviewing its own work.
3. The Builder cannot edit test files. If it could, it would change the test instead of fixing the code.
4. The student skeleton is always generated from the final code, never written by hand. Fixing the final code fixes the skeleton.
5. The orchestrator is plain code. No agent manages another agent.
6. Retries stop at about 15. After that the run stops and raises a ticket with the last error.

---

## Who does what

An agent is used only where judgement is needed. Everything else is plain code.

### Five agents

| Agent | Output | Why an agent |
|---|---|---|
| Spec Writer | A full spec from a one-page idea | Turning a rough idea into structured detail is a writing job |
| Spec Breaker | A list of unclear lines | Spotting that a sentence has two meanings needs reading |
| Builder | The working project | Writing real code |
| Verifier | A test script, written once | Working out how to test a screen needs an understanding of the app |
| Pack Writer | The instructor session guide | Teaching prose needs a writer |

### Six scripts

| Script | What it does | Why not an agent |
|---|---|---|
| Spec linter | Checks the spec format and rules | A rule check must give the same answer every time |
| Test runner | Runs the tests and reports | Pass or fail is not an opinion |
| Cutter | Builds the student skeleton | The same final code must produce the same skeleton every run. An agent would change the shape between runs and students would hit a wall that is not their fault |
| Deploy runner | Install, build, preview link | Mechanical |
| Nightly watchdog | Replays the committed test script | Runs every night on every project. An agent here is a bill that keeps growing |
| Orchestrator | Runs the twelve steps in order | No agent manages another agent |

### Three gates

The only points where a person decides. Each one blocks everything after it.

| Gate | When | What is checked |
|---|---|---|
| Gate 1 | Before any code exists | Session fit, and that no spec line is still unclear |
| Gate 2 | After the project is built and tested | The pass or fail list, every criterion, not a summary |
| Gate 3 | Before handover | Can an instructor teach from the guide. Are the skeleton cut points sensible |

---

## What changes

| | Today | After |
|---|---|---|
| Testing one project | About 40 minutes by hand | About 2 minutes reading a list |
| Student skeleton | Stripped by hand, drifts | Generated, same every run |
| Session guide | Does not exist | Written and reviewed |
| Unclear spec lines | Found at test time | Found at Gate 1, before any code |
| A project that breaks on its own | Found live, in a session | Found overnight |

Two notes on cost. The Builder is about 80 to 90 percent of the total agent cost, because it re-reads the codebase on every retry. All six scripts cost nothing. And because the Verifier writes a script instead of driving the browser itself, a project costs money to verify once, and every run after that is free.

---

## Build order

One track end to end before any multi-track work.

| Order | What | Why |
|---|---|---|
| 1 | Verifier | Biggest win. Works on projects already shipped, so it can be proved before being trusted |
| 2 | Cutter | Second biggest time sink. Stops the skeleton drifting from the final code |
| 3 | Spec Breaker | Moves problem finding from test time to Gate 1 |
| 4 | Pack Writer | Adds the deliverable that does not exist today |
| 5 | Learning loop | So a mistake caught once is not repeated |

---

## Not decided yet

1. Where the spec comes from. Either the reading material is fed in as a source document, or the spec only has to match our house format. The first needs source material per project. The second needs a template. Decide before the Spec Writer is built.

2. Whose API key students use on the AI tracks. Our own testing can be made free by recording the responses once and replaying them, but the instructor teaching live and every student coding along still needs a working key. Options are one institutional key behind a quota, students bring their own, or the project uses a small local model. Each option changes what those projects can be about.