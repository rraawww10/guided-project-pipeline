export const meta = {
  name: 'gp-phase2-code',
  description: 'Guided project CODE phase (steps 7-9): approved plan + tests -> working project, every criterion green and every task proven graded, ready for Gate 2',
  whenToUse: 'After Gate 1 is approved. Stops at Gate 2 - a person reads the pass or fail list instead of testing by hand.',
  phases: [
    { title: 'Guard', detail: 'refuse to start unless Gate 1 was approved' },
    { title: 'Build', detail: 'Builder writes app/, one session milestone at a time' },
    { title: 'Verify', detail: 'Verifier writes verify/ - one test per criterion' },
    { title: 'Test', detail: 'test runner boots the app and runs the suite - script' },
  ],
}

const RETRY_LIMIT = 15
const slug = (args && args.slug) || args
if (!slug || typeof slug !== 'string') throw new Error('pass the project slug, e.g. args: {"slug":"todo-tracker"}')

// Agent definitions in .claude/agents/ and skills in .claude/skills/ are read
// when a session starts. A session older than those files cannot resolve an
// agentType, so fall back to the default agent pointed at the same skill file
// on disk. Once the session has restarted the agent definition wins, and with
// it the tool limits in its frontmatter.
const REPO = '.'  // repo-relative: agents run from the repo root, and this file is checked out on more than one machine
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

// A checker has three outcomes, not two: pass, fail, and DID NOT RUN. Python's
// `_checker` in pipeline/cli.py learned this - "a crash is a failed checker,
// never a verdict" - but these scripts had not. A failed agent returns null, so
// the next `.ok` threw `TypeError: null is not an object` from whatever line
// happened to touch it first: no name for what did not run, and a type error
// where a lost connection belonged. pipeline-test-03 hit it when the API was
// briefly unreachable and the run died on `lint.ok`.
//
// Guard on the line AFTER the assignment, never by wrapping the call. Wrapping
// adds an opening paren to a multi-line call that already ends in `} })`, and a
// miscount there still parses - it just quietly binds the wrong thing.
const mustRun = (label, result) => {
  if (result === null || result === undefined) {
    throw new Error(
      `checker "${label}" did not run - it returned no result. This is a ` +
      `pipeline or transport fault, not a verdict about the project: nothing ` +
      `has been judged and no retry should be burned for it. Fix the cause and ` +
      `resume; the project state on disk is untouched by this failure.`)
  }
  return result
}


const RESULTS = {
  type: 'object',
  required: ['ok', 'counts', 'failing'],
  properties: {
    ok: { type: 'boolean' },
    counts: {
      type: 'object',
      properties: { pass: { type: 'integer' }, fail: { type: 'integer' },
                    skip: { type: 'integer' }, missing: { type: 'integer' } },
    },
    failing: {
      type: 'array',
      items: {
        type: 'object',
        required: ['criterion', 'status', 'check'],
        properties: { criterion: { type: 'string' }, status: { type: 'string' },
                      check: { type: 'string' }, message: { type: 'string' } },
      },
    },
    could_not_run: { type: 'string', description: 'set only if the suite itself failed to boot or collect' },
  },
}

// Rule 3, enforced: the orchestrator locks one subtree per step and a PreToolUse
// hook blocks writes outside it. The Builder cannot reach verify/ even if it tries.
const lock = (tree, label) => agent(
  `Run exactly this from the repo root and nothing else, then return its output:\n\n` +
  `    python3 -m pipeline ${tree === 'off' ? `unlock ${slug}` : `lock ${slug} ${tree}`}\n\n` +
  `Do not edit any file.`,
  { label, phase: 'Guard', effort: 'low',
    schema: { type: 'object', required: ['done'], properties: { done: { type: 'boolean' }, output: { type: 'string' } } } })

const runTests = (n) => agent(
  `Run exactly this from the repo root and nothing else:\n\n` +
  `    python3 -m pipeline test ${slug}\n\n` +
  `It boots the app and runs projects/${slug}/verify/. It takes a few minutes - let it finish.\n` +
  `Then read projects/${slug}/results.json and return: ok, counts, and one entry in "failing" for ` +
  `every criterion whose status is not "pass" (include its status, its check text and the failure ` +
  `message, trimmed to one or two lines). If the suite could not run at all, set could_not_run.\n\n` +
  `Do NOT edit any file. Do NOT fix anything. You are a command runner.`,
  { label: `test-runner:${n}`, phase: 'Test', effort: 'low', schema: RESULTS })

phase('Build')
// The gate check used to be its own agent running `pipeline status`. It is not
// needed: `pipeline lock` carries the phase guard, so the first real command of
// the phase already refuses to proceed unless Gate 1 was approved AND the spec
// still hashes to the one that was approved. One less command-only agent, and
// the check is now fail-closed in the orchestrator rather than in a prompt.
await lock('app', 'lock:app')
await spawn('builder',
  `Build guided project "${slug}".\n\n` +
  `Read projects/${slug}/spec.json, spec.md, ` +
  `ambiguity.md and learning/lessons.md first.\n\n` +
  `Build every session in order into projects/${slug}/app/. Place every cut marker declared in ` +
  `spec.json exactly once, balanced, around the real implementation.`,
  { label: 'builder', phase: 'Build' })

phase('Verify')
await lock('verify', 'lock:verify')
await spawn('verifier',
  `Write the verification suite for guided project "${slug}".\n\n` +
  `Read projects/${slug}/spec.json and read the ` +
  `built code in projects/${slug}/app/ so your selectors match what is really rendered.\n\n` +
  `Write projects/${slug}/verify/ - one test per criterion - and verify/coverage.json covering ` +
  `every criterion id. The app will already be running; read its URL from os.environ["BASE_URL"].`,
  { label: 'verifier', phase: 'Verify' })

phase('Test')
// `pipeline test` clears the lock itself - it has to, since it boots the app.
// That removes the separate `unlock` agent that used to run before every test
// run: one command-only agent per retry iteration, and the one the security
// classifier flagged on both round-1 projects.
let results = await runTests(1)
mustRun('test-runner', results)
let attempt = 0

while (!results.ok && attempt < RETRY_LIMIT) {
  attempt++
  const suiteBroken = !!results.could_not_run || (results.counts && results.counts.missing > 0)

  if (suiteBroken) {
    // the suite itself is wrong, so this one goes back to the Verifier, not the Builder
    await lock('verify', `lock:verify:${attempt}`)
    await spawn('verifier',
      `The verification suite for "${slug}" did not run cleanly.\n\n` +
      (results.could_not_run ? `It could not run: ${results.could_not_run}\n\n` : '') +
      `Criteria reported as missing a test: ` +
      `${results.failing.filter(f => f.status === 'missing').map(f => f.criterion).join(', ') || 'none'}\n\n` +
      `Fix projects/${slug}/verify/ so every criterion in spec.json has ` +
      `exactly one test and an entry in coverage.json, and the suite collects and runs. ` +
      `Do not touch app/.`,
      { label: `verifier:retry-${attempt}`, phase: 'Verify' })
  } else {
    // real failures - the code is wrong, and only the Builder may touch it
    await lock('app', `lock:app:${attempt}`)
    await spawn('builder',
      `Fix guided project "${slug}". ${results.counts.fail} acceptance criteria are failing.\n\n` +
      `Read projects/${slug}/results.json for the full output. ` +
      `Fix exactly these and nothing else:\n` +
      results.failing.map(f => `  ${f.criterion} [${f.status}] ${f.check}\n      ${(f.message || '').slice(0, 200)}`).join('\n') +
      `\n\nRule 3: you cannot edit verify/. A hook will block you. If a test is genuinely wrong, ` +
      `say so in your summary and fix the code anyway. Keep every cut marker balanced and in place.`,
      { label: `builder:retry-${attempt}`, phase: 'Build' })
  }

  results = await runTests(attempt + 1)
  log(`test run ${attempt + 1}: ${results.counts.pass} pass, ${results.counts.fail} fail, ${results.counts.missing} missing`)
}

if (!results.ok) {
  return { slug, gate: 2, ready: false, ticket: true, attempts: attempt,
           reason: `criteria still failing after ${attempt} builder/verifier retries`,
           counts: results.counts, failing: results.failing }
}

// ---- step 8's second checker ----------------------------------------------
// requirements_doc.md rule 3: "The verifier is checked by a script. It must
// cover every requirement, and it must go red when we deliberately break the
// code. Otherwise a useless test looks green."
//
// The break used is the meaningful one: remove exactly one student task and
// leave the rest written. Every task must turn one of its own requirements red.
// A task nothing notices is a task that grades nothing. This is also the
// partial-subset case the skeleton check is blind to - N runs, not 2^N.
//
// It costs one boot and build per task, so it is the slowest step in the phase.
// On a flow-1 project the command steps aside and returns ok.
const mutationOut = await agent(
  `Run exactly this from the repo root and nothing else:\n\n` +
  `    python3 -m pipeline mutation ${slug}\n\n` +
  `For each student task in turn it removes that one task, leaves every other one ` +
  `written, boots the app and runs the suite. It takes several minutes per task - ` +
  `let it finish. Then read projects/${slug}/mutation.json and return it.\n\n` +
  `Do NOT edit any file. You are a command runner.`,
  { label: `mutation:${slug}`, phase: 'Test', effort: 'low',
    schema: {
      type: 'object',
      required: ['ok'],
      properties: {
        ok: { type: 'boolean' },
        checked: { type: 'integer' },
        of_total: { type: 'integer' },
        ungraded_tasks: { type: 'array', items: { type: 'string' } },
        inconclusive_tasks: { type: 'array', items: { type: 'string' } },
        seconds: { type: 'number' },
      },
    } })
mustRun('mutation', mutationOut)

const ungraded = mutationOut.ungraded_tasks || []
const inconclusive = mutationOut.inconclusive_tasks || []

log(`mutation: ${mutationOut.ok ? 'every task is graded'
    : ungraded.length ? `UNGRADED ${ungraded.join(', ')}`
    : inconclusive.length ? `INCONCLUSIVE ${inconclusive.join(', ')}`
    : 'failed without naming a task'}`)

// mutation.ok is false for two unrelated reasons and they need opposite
// actions. This branch used to report every failure as ungraded and print an
// instruction to reject a Gate-1-approved spec - which is the exact wrong
// output pipeline/cli.py::_checker records: "an unguarded crash in `mutation`
// read as 'the spec is wrong' and printed an instruction to reject a
// Gate-1-approved spec that was correct". pipeline-test-03 hit it with
// ungraded_tasks empty and inconclusive_tasks holding one entry.
if (!mutationOut.ok) {
  const common = {
    slug, gate: 2, ready: false, retries_used: attempt, counts: results.counts,
    ungraded_tasks: ungraded, inconclusive_tasks: inconclusive,
    read_next: [`projects/${slug}/mutation.json`, `projects/${slug}/results.json`],
  }
  if (ungraded.length) {
    // The suite cannot see the task at all. The requirement list is wrong.
    return { ...common,
      blocked: 'the mutation check found student tasks that grade nothing',
      reason: 'a task no requirement notices can be left empty with every criterion ' +
              'green. This is a SPEC problem - the requirement list is wrong, not the ' +
              'code - so it re-enters at step 3.',
      fix: `python3 -m pipeline gate ${slug} 1 reject -m "<add a requirement that ` +
           `notices each ungraded task>" && python3 -m pipeline revise ${slug}`,
    }
  }
  if (inconclusive.length) {
    // The mutant proved nothing either way. NOT a verdict about the project,
    // and rejecting the spec over it would be rejecting a spec that may be
    // correct. A cut every criterion declares is the usual cause: its expected
    // set is the whole suite, so nothing is left over to stay green and prove
    // the harness was alive. mutation.py takes that control from the run, so
    // this now means the whole run produced no passing criterion anywhere.
    return { ...common,
      blocked: 'the mutation check could not reach a verdict',
      reason: 'an INCONCLUSIVE task is not an ungraded task. No criterion passed ' +
              'against the mutant AND no other mutant in the run proved the harness ' +
              'alive, so nothing was learned about whether the task is graded. Do ' +
              'NOT reject the spec over this - read the run first.',
      fix: 'read mutation.json and the junit for the named task. If the suite ran ' +
           'and every criterion failed, the harness may be broken for the whole run ' +
           '(a port, a fixture path, an install) - that is a pipeline fault. If the ' +
           'suite did not run, boot the mutant by hand and see why.',
    }
  }
  return { ...common,
    blocked: 'the mutation check failed without naming a task',
    reason: 'mutation.ok is false but neither ungraded_tasks nor inconclusive_tasks ' +
            'holds anything. That is a pipeline fault, not a verdict - no conclusion ' +
            'about the project follows from it.',
    fix: `read projects/${slug}/mutation.json directly`,
  }
}

return {
  slug, gate: 2, ready: true, retries_used: attempt, counts: results.counts,
  mutation: { ok: mutationOut.ok, checked: mutationOut.checked,
              of_total: mutationOut.of_total, seconds: mutationOut.seconds },
  read_next: [`projects/${slug}/results.json`, `projects/${slug}/mutation.json`],
  note: 'Gate 2 is every criterion, not a summary. results.json lists each one by id with its check text. mutation.json proves each student task turns a requirement red when removed.',
  approve_with: `python3 -m pipeline gate ${slug} 2 approve -m "<note>"`,
  reject_with: `python3 -m pipeline gate ${slug} 2 reject -m "<what to fix>"`,
}
