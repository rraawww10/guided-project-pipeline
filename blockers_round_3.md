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


