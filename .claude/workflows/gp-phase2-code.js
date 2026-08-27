export const meta = {
  name: 'gp-phase2-code',
  description: 'Guided project phase 2: approved spec -> working project + test suite, every criterion green, ready for Gate 2',
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

phase('Guard')
const gate = await agent(
  `Run \`python3 -m pipeline status ${slug}\` from the repo root and return whether gate1 shows ` +
  `as approved. Do not edit anything.`,
  { label: 'gate1-check', phase: 'Guard', effort: 'low',
    schema: { type: 'object', required: ['gate1_approved'],
              properties: { gate1_approved: { type: 'boolean' }, detail: { type: 'string' } } } })

if (!gate.gate1_approved) {
  return { slug, gate: 2, ready: false, blocked: 'Gate 1 has not been approved - no code may be written yet',
           fix: `python3 -m pipeline gate ${slug} 1 approve -m "<note>"` }
}

phase('Build')
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
await lock('off', 'unlock')
let results = await runTests(1)
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

  await lock('off', `unlock:${attempt}`)
  results = await runTests(attempt + 1)
  log(`test run ${attempt + 1}: ${results.counts.pass} pass, ${results.counts.fail} fail, ${results.counts.missing} missing`)
}

if (!results.ok) {
  return { slug, gate: 2, ready: false, ticket: true, attempts: attempt,
           reason: `criteria still failing after ${attempt} builder/verifier retries`,
           counts: results.counts, failing: results.failing }
}

return {
  slug, gate: 2, ready: true, retries_used: attempt, counts: results.counts,
  read_next: [`projects/${slug}/results.json`],
  note: 'Gate 2 is every criterion, not a summary. results.json lists each one by id with its check text.',
  approve_with: `python3 -m pipeline gate ${slug} 2 approve -m "<note>"`,
  reject_with: `python3 -m pipeline gate ${slug} 2 reject -m "<what to fix>"`,
}
