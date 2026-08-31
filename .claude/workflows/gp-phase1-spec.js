export const meta = {
  name: 'gp-phase1-spec',
  description: 'Guided project PLAN phase (steps 3-6): idea -> linted, ambiguity-checked spec AND the tests, ready for Gate 1',
  whenToUse: 'After Gate 0 has picked an idea (flow 2), or after a person has written projects/<slug>/idea.md (flow 1). Stops at Gate 1 - a person approves the plan and the tests before any code exists.',
  phases: [
    { title: 'Draft', detail: 'step 3 - Spec Writer turns idea.md into spec.md + spec.json' },
    { title: 'Lint', detail: 'spec linter - script, deterministic' },
    { title: 'Break', detail: 'step 4 - Spec Breaker flags every line that could mean two things' },
    { title: 'Tests', detail: 'step 5 - Test Writer writes the suite BEFORE any code, checked red-first' },
  ],
}

// Workflow scripts have no filesystem or shell access, so a script step is run
// by a thin agent that does nothing but run it. In the Python orchestrator
// (python -m pipeline) these are direct calls. Rule 5 still holds either way:
// the control flow below is plain code, and no agent manages another agent.
const RETRY_LIMIT = 15
const slug = (args && args.slug) || args
if (!slug || typeof slug !== 'string') throw new Error('pass the project slug, e.g. args: {"slug":"todo-tracker"}')

// Agent definitions in .claude/agents/ and skills in .claude/skills/ are read
// when a session starts. A session older than those files cannot resolve an
// agentType, so fall back to the default agent pointed at the same skill file
// on disk. Once the session has restarted the agent definition wins, and with
// it the tool limits in its frontmatter.
const REPO = '/home/nxtwave/AI_projects'
const spawn = async (name, prompt, opts = {}) => {
  const body = `Read ${REPO}/.claude/skills/${name}/SKILL.md and follow it exactly.\n\n${prompt}`
  try {
    return await agent(body, { ...opts, agentType: name })
  } catch (e) {
    if (!/not found/i.test(String((e && e.message) || e))) throw e
    log(`agent type '${name}' is not registered in this session - using the default agent with the same skill file`)
    return await agent(body, opts)
  }
}

// Rule 1: the tests are written by a different agent from the builder, and that
// agent cannot reach the code. The lock is what enforces it - prose in a prompt
// is not enforcement. In this flow verify/ belongs to the spec phase, so the
// lock is available before Gate 1.
const lock = (tree, label) => agent(
  `Run exactly this from the repo root and nothing else, then return its output:\n\n` +
  `    python3 -m pipeline ${tree === 'off' ? `unlock ${slug}` : `lock ${slug} ${tree}`}\n\n` +
  `Do not edit any file.`,
  { label, phase: 'Tests', effort: 'low',
    schema: { type: 'object', required: ['done'], properties: { done: { type: 'boolean' }, output: { type: 'string' } } } })

const LINT = {
  type: 'object',
  required: ['ok', 'error_count', 'errors'],
  properties: {
    ok: { type: 'boolean' },
    error_count: { type: 'integer' },
    errors: {
      type: 'array',
      items: {
        type: 'object',
        required: ['code', 'where', 'message'],
        properties: { code: { type: 'string' }, where: { type: 'string' }, message: { type: 'string' } },
      },
    },
  },
}

const runLint = () => agent(
  `Run exactly this from the repo root and nothing else:\n\n` +
  `    python3 -m pipeline lint ${slug}\n\n` +
  `Then read projects/${slug}/lint.json and return it. Do NOT edit any file. ` +
  `Do NOT fix anything you see. You are a command runner, not a repair agent.`,
  { label: `lint:${slug}`, phase: 'Lint', effort: 'low', schema: LINT })

phase('Draft')
let lint = null
let attempt = 0

while (attempt < RETRY_LIMIT) {
  attempt++
  const retryNote = lint && !lint.ok
    ? `\n\nThis is retry ${attempt} of ${RETRY_LIMIT}. The spec linter rejected the last spec. ` +
      `Read projects/${slug}/lint.json and fix exactly these ${lint.error_count} errors. ` +
      `Do not redesign the project.\n` +
      lint.errors.slice(0, 20).map(e => `  ${e.code} ${e.where}: ${e.message}`).join('\n')
    : ''

  await spawn('spec-writer',
    `Write the spec for guided project "${slug}".\n\n` +
    `Read projects/${slug}/idea.md, ` +
    `projects/${slug}/.pipeline/CONTRACT.md and learning/lessons.md first.\n\n` +
    `If projects/${slug}/.pipeline/round-*/ exists, a previous spec was rejected at Gate 1. ` +
    `Read the highest-numbered round's ambiguity.md and why.md, and its spec.json for what was ` +
    `already decided. Every finding under "## Blocking" must be resolved in this revision, and ` +
    `the findings under "## Worth a look" must each be either resolved or deliberately kept. ` +
    `Keep everything the report did not fault - a revision is not a rewrite.\n\n` +
    `Write projects/${slug}/spec.md and projects/${slug}/spec.json. Nothing else.` + retryNote,
    { label: attempt === 1 ? 'spec-writer' : `spec-writer:retry-${attempt - 1}`,
      phase: 'Draft' })

  lint = await runLint()
  log(`lint attempt ${attempt}: ${lint.ok ? 'clean' : `${lint.error_count} errors`}`)
  if (lint.ok) break
}

if (!lint.ok) {
  // Rule 6 - retries stop at about 15, the run stops and raises a ticket.
  return {
    slug, gate: 1, ready: false, ticket: true, attempts: attempt,
    reason: `spec linter still failing after ${attempt} attempts`,
    errors: lint.errors.slice(0, 20),
  }
}

phase('Break')
// Rule 2 - a different agent, so it is not reviewing its own work. One pass.
const ambiguity = await spawn('spec-breaker',
  `Break the spec for guided project "${slug}".\n\n` +
  `Read projects/${slug}/spec.md and ` +
  `spec.json FIRST and on their own, then projects/${slug}/idea.md, then learning/lessons.md.\n\n` +
  `Write projects/${slug}/ambiguity.md. Do not edit the spec.`,
  { label: 'spec-breaker', phase: 'Break',
    schema: {
      type: 'object',
      required: ['blocking', 'worth_a_look', 'summary'],
      properties: {
        blocking: { type: 'integer' },
        worth_a_look: { type: 'integer' },
        summary: { type: 'string' },
        titles: { type: 'array', items: { type: 'string' } },
      },
    } })

// Bind the report to the exact spec it reviewed, then apply the stopping rule.
// `pipeline lint` opened the pass when it went clean, so `end` refuses if the
// spec moved while the Breaker was reading it. gate1-check is the rule itself:
// reject when a blocking finding is owned by 'nothing', approve when every
// finding sits in a column a downstream checker owns. One agent runs both.
const verdict = await agent(
  `Run exactly these two commands from the repo root, in order, and nothing else:\n\n` +
  `    python3 -m pipeline breaker ${slug} end\n` +
  `    python3 -m pipeline gate1-check ${slug}\n\n` +
  `The first binds projects/${slug}/ambiguity.md to the spec it reviewed and fails if the spec ` +
  `changed during the pass. The second applies the Gate 1 stopping rule and writes ` +
  `projects/${slug}/gate1.json.\n\n` +
  `Then read projects/${slug}/gate1.json and return it. If the first command failed, say so in ` +
  `"reasons" and set ok false. Do NOT edit any file. Do NOT fix anything. You are a command runner.`,
  { label: `gate1-rule:${slug}`, phase: 'Break', effort: 'low',
    schema: {
      type: 'object',
      required: ['ok', 'verdict', 'reasons'],
      properties: {
        ok: { type: 'boolean' },
        verdict: { type: 'string' },
        reasons: { type: 'array', items: { type: 'string' } },
        counts: {
          type: 'object',
          properties: { blocking: { type: 'integer' }, worth_a_look: { type: 'integer' },
                        unowned_blocking: { type: 'integer' } },
        },
        findings: { type: 'array', items: {
          type: 'object',
          properties: { id: { type: 'string' }, title: { type: 'string' },
                        blocking: { type: 'boolean' }, owner: { type: 'string' },
                        must_fix_now: { type: 'boolean' } } } },
      },
    } })

log(`gate 1 stopping rule: ${verdict.verdict}` +
    (verdict.counts ? ` (${verdict.counts.blocking} blocking, ` +
     `${verdict.counts.unowned_blocking} of them owned by nothing)` : ''))

// ---- step 5: the tests, written from the spec BEFORE any code exists ------
// requirements_doc.md rule 1: "Tests are written before the code, by a different
// AI." Rule 2, red-first: "Every new test must fail before the code is written.
// A test that passes early proves nothing."
//
// DO NOT run this in parallel with the Spec Breaker to save wall clock. It reads
// ambiguity.md, so the Breaker is a data dependency and not merely an ordering.
// That dependency is the point: pipeline-test-02 shipped 11 tests each recording
// in its docstring which reading of an ambiguity it took, which is what let Gate
// 1 approve four findings owned by 'nothing' with its eyes open. Started early,
// the Test Writer picks a reading nobody has flagged yet.
// The three agents in this phase are serial by construction - spec -> ambiguity
// -> tests. The phase gets faster by needing fewer Gate 1 rounds, not by
// overlapping these.
phase('Tests')
await lock('verify', 'lock:verify')
const tests = await spawn('test-writer',
  `Write the test suite for guided project "${slug}".\n\n` +
  `Read projects/${slug}/spec.json, spec.md, ambiguity.md, ` +
  `projects/${slug}/.pipeline/CONTRACT.md and learning/lessons.md.\n\n` +
  `There is NO projects/${slug}/app/ and there must not be one when you finish - a ` +
  `different agent writes the code at step 7 and a hook will block you from it. ` +
  `Write projects/${slug}/verify/ with exactly one test per criterion in spec.json, ` +
  `plus verify/coverage.json covering every criterion id.\n\n` +
  `Use only the selectors the spec pins. If a criterion cannot be tested from the ` +
  `spec alone, say so in your summary rather than guessing - that is a finding for ` +
  `the person at Gate 1.`,
  { label: 'test-writer', phase: 'Tests',
    schema: {
      type: 'object',
      required: ['files', 'criteria_covered'],
      properties: {
        files: { type: 'array', items: { type: 'string' } },
        criteria_covered: { type: 'array', items: { type: 'string' } },
        untestable_from_the_spec: { type: 'array', items: { type: 'string' } },
        notes: { type: 'string' },
      },
    } })
// One command runner for both, the same shape as `breaker end` + `gate1-check`
// above. The unlock has to come first because redfirst writes redfirst.json
// into a tree the lock still covers; two agent spawns to run two ordered shell
// commands bought nothing but the spawn.
const redfirst = await agent(
  `Run exactly these two commands from the repo root, in order, and nothing else:\n\n` +
  `    python3 -m pipeline unlock ${slug}\n` +
  `    python3 -m pipeline redfirst ${slug} --static-only\n\n` +
  `The first releases the write lock on projects/${slug}/verify/. The second ` +
  `checks that no test in projects/${slug}/verify/ is one that cannot go red - ` +
  `no assertion at all, or only trivially true ones. Then read ` +
  `projects/${slug}/redfirst.json and return it. If the unlock failed, say so and ` +
  `set ok false.\n\n` +
  `Do NOT edit any file. Do NOT fix anything. You are a command runner.`,
  { label: `redfirst:${slug}`, phase: 'Tests', effort: 'low',
    schema: {
      type: 'object',
      required: ['ok'],
      properties: {
        ok: { type: 'boolean' },
        vacuous_tests: { type: 'array', items: {
          type: 'object',
          properties: { test: { type: 'string' }, problem: { type: 'string' } } } },
      },
    } })

log(`tests: ${(tests.criteria_covered || []).length} criteria covered, ` +
    `red-first ${redfirst.ok ? 'clean' : `${(redfirst.vacuous_tests || []).length} vacuous`}`)

return {
  slug,
  gate: 1,
  ready: true,
  spec_attempts: attempt,
  lint: 'clean',
  ambiguity,
  tests: {
    files: tests.files,
    criteria_covered: (tests.criteria_covered || []).length,
    untestable_from_the_spec: tests.untestable_from_the_spec || [],
    notes: tests.notes,
  },
  red_first: { ok: redfirst.ok, vacuous_tests: redfirst.vacuous_tests || [] },
  red_first_limit: 'the static half runs here, because with no code on disk a ' +
    'dynamic all-red run would pass for the wrong reason. The dynamic proof is ' +
    'the skeleton check at step 10, which requires every criterion whose task was ' +
    'removed to fail.',
  stopping_rule: 'reject when a blocking finding is owned by "nothing"; approve when every ' +
                 'remaining finding sits in a column a downstream checker owns',
  gate1_rule: { verdict: verdict.verdict, ok: verdict.ok, counts: verdict.counts,
                reasons: verdict.reasons },
  must_fix_now: (verdict.findings || []).filter(f => f.must_fix_now)
    .map(f => `${f.id} ${f.title}`),
  read_next: [`projects/${slug}/spec.md`, `projects/${slug}/ambiguity.md`,
              `projects/${slug}/gate1.json`, `projects/${slug}/verify/`,
              `projects/${slug}/redfirst.json`],
  note: verdict.ok
    ? 'The rule says approve-eligible. Gate 1 now covers the plan AND the tests - read the ' +
      'suite too, because the rule proves nothing escapes to the shipped project, not that ' +
      'the tests are worth passing.'
    : 'The rule says reject. `pipeline gate <slug> 1 approve` will refuse until the findings ' +
      'owned by "nothing" are fixed and the Spec Breaker has re-read the spec.',
  approve_with: `python3 -m pipeline gate ${slug} 1 approve -m "<note>"`,
  reject_with: `python3 -m pipeline gate ${slug} 1 reject -m "<what to fix>" && python3 -m pipeline revise ${slug}`,
}
