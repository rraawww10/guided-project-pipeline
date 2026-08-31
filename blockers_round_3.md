# Blockers - pipeline-test-03

First run on the updated pipeline (commit 0f272f2: weighted cut minutes, W114,
watchdog unscheduled, phase-1 command-runner merge).

**Input, deliberately identical to pipeline-test-02** so any difference is
caused by the pipeline changes and not by the stack:
`next, react, typescript`, 2 sessions x 40 minutes.

Reference outcome to beat - pipeline-test-02:
3 Gate 1 rounds, ~3.1 h working time, session 2 measured 50 min against a
40 min cap.

| # | Step | What happened | Pipeline fault? | Resolution |
|---|---|---|---|---|

## Log

### Step 0 - stack input (human)  CLEAN

`pipeline new pipeline-test-03` scaffolded flow 2 (16 steps, 4 gates), and
`pipeline stack` wrote stack.json. `pipeline next` correctly reports step 1.

Cosmetic, not a blocker: `pipeline new` prints a usage example with
`--sessions 3` regardless of what the project needs. It is an example, not a
default, and nothing reads it - noted so it is not re-diagnosed later.

### Step 1 - idea generator (agent)  CLEAN

Run wf_2f09966d-db8. 5 ideas, first attempt, 4.7 minutes, 3 agents, 0 errors.
`pipeline ideas` passed 5/5 with no problems. step_runs ideas=1, retries idea=0.

Better than pipeline-test-02, which needed two idea runs (step_runs ideas=2).
One run is not evidence of a trend; recorded as a data point, not a win.

**The W114 lesson reached the idea stage, one step earlier than it was written
for.** Every agent reads learning/lessons.md, so the new session-timing section
is in front of the Idea Generator, and it wrote the oversized-cut risk into the
`## Risks` section of three of the five ideas unprompted:

- idea-02: "session 2 carries the timeline, the button derivation and the
  endpoint with its two error codes, which is one oversized cut waiting to
  happen - it should be specified as at least three cuts, with the 409 branch
  separate from the append."
- idea-03: "session 2's cut should be split into the search and the wrap so
  neither is oversized."
- idea-04: "which is the oversized-cut shape that has overrun four projects; it
  needs promotion and invalidation cut separately."

idea-04 quotes the four-project count from lessons.md directly. This is the
intended path - the cheapest place to fix an oversized cut is before the spec
exists at all - but it also means W114 may never fire on this run. **If the spec
comes back clean, that is not evidence the rule works.** The rule is still
unproven until something trips it; see basic_needs_v1.md section 9.

### Step 2 - GATE 0  AWAITING THE HUMAN


Picked idea-01 Ledger.

**Near-miss worth recording as a process finding, not a pipeline fault.** The
pick arrived as `pick 1 -m "event log fold, state never stored"`. The number and
the reason named different ideas - that reason describes idea-02 Dispatch;
idea-01 is Ledger, a text-file parser with no event log. Caught by reading the
two against each other before running the command, and confirmed with the human.

Nothing in the pipeline would have caught this. `pipeline pick` validates that
the index exists and copies the file; it has no way to know the note argues for
a different one. Gate 0 is the cheapest gate to get wrong and the most expensive
to discover late - the spec, the tests, the code and the pack all descend from
it, and the only route back is a new project.

Not proposing a checker: the note is free prose and matching it to an idea is a
judgement, which is rule 1 territory (one try and a person reads it). Recording
it because it is the first Gate 0 near-miss across six runs, and if it recurs
the fix is a confirmation prompt on `pick`, not a linter rule.

The gate note records the discrepancy rather than the reason given, so the audit
trail does not carry a rationale for a project that was not chosen.

### Steps 3-6 - PLAN phase, attempt 1  FAILED - two separate causes

Run wf_a7b32f92-f99, 11.7 minutes, 2 agents, both errored.

**B1 - environmental, not a pipeline fault.** Both the spec-writer and the lint
command runner failed with `API Error: Can't reach the API server - check your
internet or DNS (ENOTFOUND)`. DNS resolved normally on re-test minutes later, so
the outage was transient. Nothing to fix.

**B2 - REAL PIPELINE DEFECT, exposed by B1. Fixed.** The workflow did not fail
on the network error; it failed on

    TypeError: null is not an object (evaluating 'lint.ok')

A failed agent returns null, and `gp-phase1-spec.js` dereferenced every checker
result on the line after it was assigned. So a lost connection surfaced as a
type error at whatever line happened to touch the null first, naming neither the
checker that did not run nor the reason.

This is the same defect Python already fixed in `pipeline/cli.py::_checker`
(commit ab0b893, "a crash is a failed checker, never a verdict"): *a checker has
three outcomes, not two - pass, fail, and DID NOT RUN*. The orchestrator models
all three. The four workflow scripts modelled two. The lesson had been learned
on one side of the pipeline and never carried to the other.

Systemic, not local - every workflow had it:

| Workflow | Unguarded checker results |
|---|---|
| gp-phase0-ideas | `stack` |
| gp-phase1-spec | `lint`, `ambiguity`, `verdict`, `tests`, `redfirst` |
| gp-phase2-code | `results`, `mutationOut` |
| gp-phase3-pack | `cut`, `handover` |

Fix: a shared `mustRun(label, result)` in all four, throwing a message that
names the checker and says explicitly that nothing was judged and no retry
should be burned. 102 insertions, 0 deletions.

**A near-miss inside the fix, worth more than the fix.** The first attempt
wrapped each call - `mustRun('x', await spawn(...))`. That adds an opening paren
to a multi-line call already ending in `} })`, and the result **still passed
`node --check`** while being short a paren, because the imbalance was absorbed
by the rest of the file. A paren-counting pass over the statement showed net +1
where node reported clean. Reverted to `git checkout` and redone as a guard on
the line *after* the assignment, which changes no existing line.

`node --check` returning 0 is not evidence that a call binds what you meant.
Verified the negative control (a deliberately broken file does exit 1) before
trusting the checker, and confirmed the final diff is additive only.

### Steps 3-6 - PLAN phase, attempt 2  COMPLETED

Run wf_30c328b5-c39, 26.5 min, 7 agents, 0 errors. Spec clean on the FIRST lint
attempt (pipeline-test-02 needed three rounds). 9 criteria, 9 tests, red-first
clean. The merged unlock+redfirst command runner worked; no lock was left held.

**B3 - THE NEW RULE MEASURED NOTHING, AND THE REASON IS THE RULE ITSELF.**

lint.json: 0 errors, 0 warnings. W112 silent, W114 silent, both sessions 38.5
against the 40 cap. Every cut priced at exactly the flat 6.0 minutes, because
every hint came in under the 55-word nominal:

    cut-parse-line 54   cut-amount-paise 51   cut-running-balance 52
    cut-account-totals 46   cut-account-rows 46

Compare the hint-word distribution to every earlier project:

| project | flow | cuts | hint words | over 55 |
|---|---|---|---|---|
| pipeline-test-01 | 2 | 7 | 51 73 76 78 81 84 103 | 6 of 7 |
| pipeline-test-02 | 2 | 5 | 34 63 68 70 110 | 4 of 5 |
| **pipeline-test-03** | 2 | 5 | **46 46 51 52 54** | **0 of 5** |

Max 54 against a threshold of 55. Every previous flow-2 project put most of its
cuts over the line; this one put none, and stopped one word short.

The spec-writer SKILL.md now says "a hint running past about 55 words is a
signal the cut does too much". The writer wrote to the number. **The measure
became a target the moment it was published**, and hint length was only ever a
proxy - a writer can compress the description of a large cut as easily as a
small one.

This does not prove the cuts are wrong-sized. It proves the linter can no longer
tell, because the quantity it reads is now managed. The calibration in
spec_linter.py was fitted on specs written *before* the threshold existed, when
hint length was an unmanaged signal. That assumption no longer holds.

Corroboration from an independent reader: the Spec Breaker raised W7 unprompted -
"both sessions estimate 38.5 against a 40 cap with no headroom, where the two
timed flow-2 sessions ran 45 and 50 against flat estimates of 32.5 and 37." The
linter says fine; the breaker says history predicts about 50.

**Deliberately not changing the rule yet.** There is no measurement to change it
against - the honest test is step 13. If session 2 runs near 50 on a 38.5
estimate, the proxy is broken and the weight needs to move to something the
writer cannot compress. If it runs near 40, the cuts really did get smaller and
the guidance worked. Recording the prediction now so the dry run adjudicates it
instead of hindsight.

**B4 - Gate 1 stopping rule says REJECT.** 2 blocking, both owned by `nothing`;
7 worth a look. Not a pipeline fault - the rule working as designed. Both
blockers are the same class: a cut that no criterion can distinguish from a
version that never implements it. That class is now 7 of the 11 archived
blocking findings, and it remains the one with no script behind it.


### Gate 1 round 1 - REJECTED (human), round 2 running

Rejected per the stopping rule. Round 1 archived to `.pipeline/round-1/`,
gate1 reset. Retries still 0/15 in every phase - a Gate 1 rejection is a round,
not a retry, and the revise path is the designed one.

The brief names both blockers with a concrete fix each, closes W6 as the same
class as A2, and asks for an explicit decide-or-drop on W1-W4. W5 accepted as
written (making parseLedger a student task would trip E113).

**Anti-gaming instruction added to the brief, scoped to this project, not to the
pipeline.** The note tells the writer to size each hint to what its cut honestly
needs and specifically NOT to tune length to sit under the 55-word nominal,
since a hint compressed to duck a threshold destroys the signal without making
the session shorter.

Put in the gate note rather than in spec-writer/SKILL.md on purpose. The SKILL.md
wording is what induced the clustering and it does need a systemic fix, but
changing it mid-run would perturb the one experiment that can still adjudicate
B3. Round 2's hint distribution is now a free read on whether the behaviour was
the wording or the model: if hints spread out past 55 when told not to tune them,
the clustering was the published threshold; if they stay at 46-54, the cuts
really are that size. Either answer is worth more than the fix.

### Steps 3-6 - PLAN phase, round 2  COMPLETED, approve-eligible

Run wf_cfb56387-01a, 31 min, 7 agents, 0 errors. Spec clean on the first lint
attempt again. 2 blocking, 0 owned by `nothing`, 5 worth a look. Both round-1
blockers genuinely closed - the Breaker re-derived the cut-to-criterion join in
both directions and every criterion now fails when any one declared cut is
emptied alone.

**B3 REVISITED - THE GOODHART READING IS NOT SUPPORTED. Correcting it.**

The brief told the writer explicitly to size each hint to what its cut needs and
NOT to tune length to sit under the 55-word nominal. The hints did not move:

| cut | round 1 | round 2 |
|---|---|---|
| cut-parse-line | 54 | 53 |
| cut-running-balance | 52 | 52 |
| cut-amount-paise | 51 | 51 |
| cut-account-totals | 46 | 46 |
| cut-account-rows | 46 | 46 |

One word changed across five cuts, under a direct instruction that would have
moved them if the length were being managed. The simplest reading is the boring
one: Ledger's cuts are genuinely smaller than pipeline-test-02's `lineStatus`
(110 words) or pipeline-test-01's `reveal-from` (103). A parser and three folds
over a 30-line file take about 50 words to state. They are not being compressed
to duck a threshold.

**But this test is weaker than it looks, and the confound is mine.** The same
brief also said "this is a revision, not a rewrite - keep everything the report
did not fault", and the hints were not faulted. So "the writer left them alone
because they are honest" and "the writer left them alone because I told it to"
are not separable from this run. Recorded as inconclusive-leaning-against, not
as refuted. Do not treat one word of movement as evidence either way.

What has not changed is the thing both readings agree on: the estimate is 38.5
against a 40 cap on a model that was 12.5 and 13 minutes low on the only two
flow-2 sessions ever timed. The Spec Breaker reached that independently for the
second round running, and priced the available mitigations at about a minute
each against a 13-minute error bar. **Step 13 is still the only thing that can
settle this.** The prediction on record: if session 2 runs near 50 on a 38.5
estimate, the flat-plus-surcharge model is wrong in a way hint length cannot fix.


### Gate 1 - APPROVED round 2 (human), on the rule's own verdict, no --override

Committed before the code phase per the working conventions:
  d52d219  workflows: a checker that did not run is not a verdict
  076a6fa  pipeline-test-03: the Gate 1 approved spec, round 2

Spec frozen at 46b5465b4952. Two blockers ship, both in a downstream checker's
column, and one of them carries a caveat that is itself a finding:

**B2's owner can fail open.** `typecheck` is the second-line check, and a
fail-open owner passes when it cannot run - which is the one way a blocking
finding in an *owned* column still reaches the skeleton. The Gate 1 note
requires step 10 to read `typecheck_fail_open` in skeleton-check.json and
require it false. "Owned by a checker" is not the same claim as "checked", and
the Gate 1 stopping rule cannot tell the two apart. Worth considering as a
future rule: a blocking finding whose only owner is a fail-open check is closer
to `nothing` than the rule currently treats it.

### Steps 7-9 - CODE phase  BLOCKED at the mutation check

Run wf_d8c8ff9a-34a, 32.7 min, 6 agents, 0 errors. The build itself was clean:
9 pass / 0 fail / 0 skip / 0 missing, pytest rc 0, builder first pass, code
retries 0 at the time of the build. B1 did not materialise - the Builder got
notFound right, so c-2-4 is green.

Mutation: 4 of 5 cuts proven graded with clean red sets. `cut-parse-line` came
back INCONCLUSIVE, which sets mutation ok=false and stops the phase.

**B5 - WORKFLOW REPORTS THE WRONG DIAGNOSIS AND PRESCRIBES THE WRONG FIX.**

The phase-2 workflow returned:

    blocked: "the mutation check found student tasks that grade nothing"
    ungraded_tasks: []
    reason:  "a task no requirement notices can be left empty with every
              criterion green. This is a SPEC problem"
    fix:     "pipeline gate 1 reject ... && pipeline revise"

Every clause is wrong for what actually happened. `ungraded_tasks` is empty;
the real cause is `inconclusive_tasks: ['cut-parse-line']`. The task is not
unnoticed - it is declared by all nine criteria, and removing it turns all nine
red. It cannot be left empty with anything green.

Cause: gp-phase2-code.js branches on `!mutationOut.ok` and reports every failure
as ungraded. Its result schema does not even declare `inconclusive_tasks`, so
the distinction cannot survive the agent boundary. mutation.py gets this right -
it separates the two lists and words the `why` accurately - and the workflow
flattens them.

This is the failure recorded verbatim in pipeline/cli.py::_checker: "an
unguarded crash in `mutation` read as 'the spec is wrong' and printed an
instruction to reject a Gate-1-approved spec that was correct." Same wrong
output, reached down a different path. The Python side was hardened; the
workflow was not. Second instance this run of a lesson learned on one side of
the pipeline and not carried to the other - see B2.

**B6 - THE INCONCLUSIVE VERDICT IS CORRECT, AND MY FIRST INSTINCT WAS WRONG.**

The junit for the mutant shows tests=9 failures=9 errors=0, so the suite plainly
ran, while `ran = any(status == 'pass')` in mutation.py called it "never ran".
That looked like a bug. It is not.

`cut-parse-line` is declared by **all nine** criteria. With its expected set
equal to the whole suite, that mutant run has no criterion outside the set left
to prove the harness was alive. All-red is therefore genuinely ambiguous between
"removing it correctly turned everything red" and "the harness broke". The
module comment says why the guard exists: a target whose log path could not be
created once reported every criterion missing, counted them all red, and passed
every task vacuously. Loosening `ran` would reintroduce exactly that false
green, which the module calls its worst outcome.

Recorded because I nearly shipped the loosening before checking `graded_by`.

**B7 - A PROMOTABLE LINTER RULE, FOUND BY RUNNING THE PIPELINE.**

The shape is detectable at step 2 from spec.json alone, with no code: *a cut
declared by every criterion in the project can never be isolated by the mutation
check.* Corpus:

| project | cut | fires |
|---|---|---|
| pipeline-test-03 | cut-parse-line 9/9 | yes - blocked this run |
| recipe-box (shipped) | cut-store-read-all 22/22 | yes |
| tip-split (shipped) | cut-store-read-all 17/17 | yes |
| habit-tracker, test-01, test-02 | - | clean, all rounds |

It fires on the project it would have saved and on two shipped projects with the
same unverifiable cut, and stays quiet on the three whose mutation runs were
conclusive. recipe-box and tip-split shipped before mutation.py worked at all
(commit 325743d, "it had never run, and it failed green"), which is why nobody
saw it then.

Unlike the two candidates rejected earlier, this one fires on the round that
actually contains the defect. Firing at step 2 would have saved the whole code
phase - 33 minutes plus a revise cycle - and it costs one pass over spec.json.

**A second, complementary fix is available and NOT yet made:** mutation.py could
take its harness-alive control from the run rather than the mutant. If any other
mutant in the same run produced a passing criterion, the harness is proven live,
and an all-red mutant is then genuine rather than ambiguous. In this run the
other four mutants all produced passes minutes either side of cut-parse-line, so
the harness was demonstrably healthy. Not implemented: it changes the semantics
of the one checker whose false green is its worst outcome, and that is a human
decision, not a mid-run edit.


### Mutation fix applied and re-run  GREEN

`_apply_run_control` added to mutation.py: the harness-alive control is taken
from the run, not the mutant. Two independent conditions, both required, because
a false green is this checker's worst outcome:

  1. some OTHER mutant in the run produced a passing criterion - the harness is
     proven live by a run that is not this one;
  2. this mutant produced real per-test outcomes, at least one pass or fail, not
     the all-`missing` shape the original guard was written for.

Neither alone suffices. Condition 2 alone would trust a run whose harness was
broken for every mutant; condition 1 alone would trust a mutant that never
reported a per-test outcome. 8 selftest checks cover it, including the two
historical failure shapes and the case where reclassifying must still yield
NOT GRADED rather than a green. Selftest 340 -> 348.

Result: mutation ok=true, 5 of 5 checked, 0 ungraded, 0 inconclusive,
`stayed_green` empty for every cut. cut-parse-line reports 9 red of 9 with the
run-level reasoning stated in its `why`.

**B8 - EVERY MUTATION RUN LEAKS ITS SERVERS. Found because it broke the re-run.**

The first re-run crashed:

    PermissionError: [WinError 32] The process cannot access the file because
    it is being used by another process: .pipeline/mutants/cut-account-rows

12 orphaned node processes were still alive from the previous run - 6 `npm run
start` parents and 6 `next` children, one pair for the app and one per mutant.
test_runner.py's teardown calls `server.terminate()` on the Popen it holds,
which is npm; npm's `next` child survives, keeps a handle on the mutant
directory, and Windows then refuses the rmtree.

Two things hid it until now:

- `shutil.rmtree(mdir, ignore_errors=True)` swallowed the failure on the first
  run, so the leak left five undeleted mutant trees and said nothing. The crash
  only came on the *next* run, in `mutate_one`, one layer away from the cause.
- On POSIX an orphan holding an open file does not block unlink, so the same
  leak would show as drifting processes rather than a hard failure. The process
  leak is cross-platform; only the crash is Windows-specific.

Confirmed reproducible: this green run leaked 10 more. Killed by hand both
times, filtered on the project path so nothing else was touched.

NOT FIXED - it is a change to test_runner.py's process handling, which is core
and outside what was asked. The fix is to kill the tree rather than the parent:
`taskkill /F /T /PID` on Windows, `os.killpg` with `start_new_session=True` on
POSIX. Until then, every mutation run leaves ~2 processes per mutant behind and
the run after it fails on Windows unless they are cleared.

Cost of the two masked defects: code retries 2/15 burned on pipeline faults,
neither of which was about the project. `_checker` labelled both correctly -
"this is a pipeline fault, not the spec's; no conclusion can be drawn" - which
is the Python hardening doing its job.

### B8 FIXED and verified empirically

`stop_server()` in test_runner.py now kills the tree rather than the handle:
`taskkill /F /T /PID` on Windows, `os.killpg` on POSIX with the server spawned
under `start_new_session=True` so it has a group to signal. Both paths fall back
to the old `terminate()` if the tree kill is unavailable, so this is never worse
than what it replaced.

Verified by measurement, not assertion: `pipeline test pipeline-test-03` boots a
server on exactly the path that used to leak. node processes before 0, after 0,
where the same path previously left 2 behind. Tests still 9 pass / 0 fail.

5 selftest checks added, including one that spawns a real sleeping process and
asserts it is dead after teardown. Selftest 348 -> 353.

### Gate 2 - APPROVED

9 pass / 0 fail / 0 skip / 0 missing, pytest rc 0, builder first pass.
Mutation 5 of 5, 0 ungraded, 0 inconclusive, stayed_green empty everywhere.
Gate 1's B1 did not materialise - the Builder handled notFound() correctly and
c-2-4 is green on both the status and the element.

**Rule 3 is weaker in flow 2 than pipeline-test-02's Gate 2 could claim.**
verify/ is NOT byte-identical to the Gate 1 commit: the Verifier added an
explicit timeout to helpers.py's text_of() at step 8, which it owns and holds
the lock for. Nine lines, no assertion weakened, no expected value changed, and
strictly better for step 10 where missing elements are the norm.

The point is not this diff, which is fine. It is that "the suite that graded the
code is the one approved before any code existed" is a claim flow 2 cannot make
by construction, because step 8 lets the Verifier edit verify/ after Gate 1.
pipeline-test-02's Gate 2 note asserted byte-identity and happened to be right;
nothing checked it. What a gate can actually verify is that every change is the
Verifier's and weakens nothing - which here meant reading a nine-line diff.
Worth a checker: diff verify/ against the Gate 1 commit and require every hunk
to be non-weakening, or at least surface the diff at Gate 2 instead of leaving
it to whoever thinks to run git diff.

**B9 - a gate note is free prose and nothing protects it.** Passing the note
through a shell let backticks fire as command substitution and silently delete a
clause from the permanent record; the gate recorded 'approved' with a mangled
sentence and reported success. Caught by reading the stored note back, not by
anything in the pipeline. Repaired by re-recording through argv with no shell
involved. My own mistake rather than a pipeline defect, but the pipeline has no
defence: gate notes are read later by the spec-writer on a revision and by
whoever writes lessons, and a note can be corrupted without any signal.

### Steps 10-14 - HANDOVER phase  COMPLETED, all checks green

Run wf_ca6aae72-d25, 14.5 min, 6 agents, 0 errors. Cut ran first pass, 5 cuts,
0 retries. Leak scan clean, 0 leaks. Guide lint 0 errors and 2 warnings, both
the intended G032 overrun disclosures. Deploy ok, 0 advisories, preview served.

**B2 IS GENUINELY CLOSED, not merely owned.** skeleton-check.json reports
typecheck_fail_open FALSE, 9 checked, 0 mismatches, 0 partial-state risks. The
fail-open owner actually ran, so the TS2367 dead comparison did not reach the
student skeleton. This was the one Gate 1 finding whose owner could have passed
by failing to run, and checking the flag was the only way to know.

**B3 ADJUDICATED: THE HINT-LENGTH PROXY DOES NOT MEASURE TEACHING TIME.**

The Pack Writer, timing the sessions independently from the guide it wrote:

    session 1: 48 minutes against the 40 cap  (spec estimate 38.5)
    session 2: 45 minutes against the 40 cap  (spec estimate 38.5)

and it located session 1's excess exactly: cut-parse-line "carries three rules,
a rule ORDER, and the argument against Date - about 13 live minutes, not the
flat 6 the linter charges."

cut-parse-line's hint is **53 words**, under the 55-word nominal, so the
weighted model charged it the flat 6.0 and W114 and W112 both stayed silent.
A 53-word hint describes 13 minutes of live teaching. That is the proxy failing
on its own terms, and it is the answer to the question left open at Gate 1:
the hints were not being gamed - they were honest, and honest hint length still
does not predict teaching load.

What drives the time is the number of *rules* a cut states and whether their
ORDER matters, not how many words state them. Three rules plus an ordering
constraint compress to 53 words as easily as one rule does.

Note this was reached without any dry run: the estimate came from the Pack
Writer reading its own session plan. The step 13 measurement still has to
confirm it, and the Pack Writer was slightly conservative last time -
pipeline-test-02 it estimated at 48 and Priya measured 50.

Fifth consecutive project to land here. The model in spec_linter.py is now
known-wrong rather than merely uncalibrated, and the weight has to move to a
quantity that tracks rules rather than prose length. NOT changing it before the
dry run measures it - the same discipline that stopped the earlier premature fix.

**W5 CONFIRMED, and it matters more than it looked.** The spec's named drop
candidates do not exist as live minutes: session 1 names entry-desc markup and
session 2 names txn-date/txn-desc, but all five cuts are in lib/ and every page
file ships written in the skeleton, so no student types that markup and dropping
it recovers nothing. A spec can name mitigations that are not mitigations and
no checker notices. The Pack Writer found replacement trims that do recover
minutes and bring session 1 to 40 and session 2 to 39-41, none of which removes
anything a criterion grades.

**Two spec claims corrected rather than repeated by the Pack Writer:**
- W1: new Date("2026-02-30") is NOT invalid, it rolls silently to 2 March. The
  fixture that actually catches a Date-based parser is line 9, 2026-1-06, which
  Date accepts as 6 January. The guide teaches both cases correctly.
- W2: "never through a float" is ungraded - Math.round(parseFloat(text) * 100)
  returns all five values c-1-3 pins. The guide says so and tells the instructor
  to argue the integer path on merit rather than claim the tests caught it.

An agent correcting the approved spec's own reasoning, in the artifact a person
teaches from, is the pipeline working.

**B8 HAD A SECOND SITE, AND I MISSED IT.** Phase 3 left 2 node processes alive.
deploy_check.py starts its own preview server with its own Popen and its own
`server.terminate()` - the identical defect, in the pipeline's other server
site. My earlier "verified fixed" was true only of the path I changed.

Fixed the same way and verified the same way: deploy re-run, 0 node processes
after, where it left 2 before. Swept every `subprocess.Popen` in pipeline/ to
confirm there is no third site - there is not.

The lesson is the one this run keeps repeating: fixing the instance is not
fixing the class. mustRun had to go into four workflows, not one; stop_server
had to go into two checkers, not one. Grep for the pattern after every fix.

