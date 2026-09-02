export const meta = {
  name: 'gp-phase3-pack',
  description: 'Guided project HANDOVER phase (steps 10-14): tested project -> student version, instructor guide, leak scan, guide linter and deploy check, ready for the dry run and Gate 3',
  whenToUse: 'After Gate 2 is approved. Ends by asking for the timed dry run, then Gate 3 - a person decides whether an instructor could teach from the guide.',
  phases: [
    { title: 'Guard', detail: 'refuse to start unless Gate 2 was approved' },
    { title: 'Cut', detail: 'step 10 - cutter generates the student version and proves it fails the right tests' },
    { title: 'Pack', detail: 'step 11 - Guide Writer writes the instructor session guide' },
    { title: 'Deploy', detail: 'step 12 - fresh copy, install, build, preview link - script' },
    { title: 'Handover', detail: 'leak scan and guide linter - scripts' },
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


const CUT = {
  type: 'object',
  required: ['ok', 'stage'],
  properties: {
    ok: { type: 'boolean' },
    stage: { type: 'string', enum: ['markers', 'skeleton-check', 'done'],
             description: 'markers = the cutter itself errored; skeleton-check = it cut fine but the skeleton passes or fails the wrong tests' },
    error: { type: 'string' },
    cut_count: { type: 'integer' },
    mismatches: {
      type: 'array',
      items: {
        type: 'object',
        required: ['criterion', 'expected', 'actual'],
        properties: { criterion: { type: 'string' }, expected: { type: 'string' }, actual: { type: 'string' } },
      },
    },
  },
}

const lock = (tree, label) => agent(
  `Run exactly this from the repo root and nothing else, then return its output:\n\n` +
  `    python3 -m pipeline ${tree === 'off' ? `unlock ${slug}` : `lock ${slug} ${tree}`}\n\nDo not edit any file.`,
  { label, phase: 'Guard', effort: 'low',
    schema: { type: 'object', required: ['done'], properties: { done: { type: 'boolean' }, output: { type: 'string' } } } })

const runCut = (n) => agent(
  `Run exactly this from the repo root and nothing else:\n\n` +
  `    python3 -m pipeline cut ${slug}\n\n` +
  `It generates projects/${slug}/skeleton/ from app/, then runs the test suite against the ` +
  `skeleton to prove it fails exactly the criteria whose cuts were removed. It takes a few ` +
  `minutes - let it finish.\n\n` +
  `Report the result. If the cutter itself errored (unbalanced, missing or undeclared markers) ` +
  `set stage to "markers" and put the error text in "error". If it cut cleanly but ` +
  `projects/${slug}/skeleton-check.json reports mismatches, set stage to "skeleton-check" and ` +
  `list them. Otherwise stage is "done".\n\n` +
  `Do NOT edit any file. You are a command runner.`,
  { label: `cutter:${n}`, phase: 'Cut', effort: 'low', schema: CUT })

phase('Cut')
// No gate2-check agent and no pre-cut unlock agent: `pipeline cut` carries the
// phase guard and clears the lock itself, so it refuses to run unless Gate 2
// was approved and the spec still hashes to the one Gate 1 approved.
let cut = await runCut(1)
mustRun('cutter', cut)
let attempt = 0

// Rule 4: the skeleton is generated, never written by hand. Every fix goes into
// app/ - the marker placement - and the skeleton is regenerated from it.
while (!cut.ok && attempt < RETRY_LIMIT) {
  attempt++
  const brief = cut.stage === 'markers'
    ? `The cutter could not generate the skeleton:\n\n${cut.error}\n\n` +
      `Fix the cut markers in projects/${slug}/app/. Every cut id in spec.json must appear ` +
      `exactly once, balanced, never nested, and what is left after removal must still parse.`
    : `The skeleton was generated but it does not fail the right tests:\n` +
      (cut.mismatches || []).map(m => `  ${m.criterion}: expected the skeleton to ${m.expected}, it ${m.actual}ed`).join('\n') +
      `\n\nA criterion whose cuts were removed must FAIL on the skeleton - if it passes, the cut ` +
      `left a working implementation behind (a hard-coded value, a duplicate code path, a default ` +
      `that happens to satisfy the test). A criterion with no cuts must PASS - if it fails, the ` +
      `cut took away code the student was supposed to be given.\n\n` +
      `Fix the marker placement in projects/${slug}/app/. Never edit skeleton/ - it is regenerated.`

  await lock('app', `lock:app:${attempt}`)
  await spawn('builder',
    `Fix the cut markers for guided project "${slug}".\n\n` +
    `${brief}\n\n` +
    `Change marker placement only. Do not change behaviour - every criterion still passes on ` +
    `app/ and the test suite must stay green. Rule 3: you cannot edit verify/.\n\n` +
    `If the cutter reported that a cut removes its function's only return, the fix is to keep ` +
    `the return OUTSIDE the markers and cut the assignment that feeds it. The fallback must ` +
    `not accidentally satisfy the test.`,
    { label: `builder:markers-${attempt}`, phase: 'Cut' })
  cut = await runCut(attempt + 1)
  log(`cut attempt ${attempt + 1}: ${cut.ok ? `clean, ${cut.cut_count} cuts` : `${cut.stage} failed`}`)
}

if (!cut.ok) {
  return { slug, gate: 3, ready: false, ticket: true, attempts: attempt,
           reason: `the skeleton still does not fail the right tests after ${attempt} retries`,
           stage: cut.stage, error: cut.error, mismatches: cut.mismatches }
}

// Pack Writer and deploy check are independent - the guide reads the code and the
// manifest, the deploy check builds a fresh copy. No reason to serialise them.
phase('Pack')
await lock('pack', 'lock:pack')
const [pack, deploy] = await parallel([
  () => spawn('pack-writer',
    `Write the instructor pack for guided project "${slug}".\n\n` +
    `Read projects/${slug}/spec.json, spec.md, ` +
    `app/, skeleton/.cut-manifest.json, results.json, ambiguity.md and learning/lessons.md.\n\n` +
    `Write projects/${slug}/pack/ - README.md, one session-N.md per session, and ` +
    `troubleshooting.md. Copy every snippet out of app/; never retype one from memory.`,
    { label: 'pack-writer', phase: 'Pack',
      schema: { type: 'object', required: ['files', 'sessions'],
                properties: {
                  files: { type: 'array', items: { type: 'string' } },
                  sessions: { type: 'array', items: {
                    type: 'object', required: ['n', 'minutes'],
                    properties: { n: { type: 'integer' }, minutes: { type: 'integer' },
                                  overruns: { type: 'boolean' } } } },
                  concerns: { type: 'string' } } } }),
  () => agent(
    `Run exactly this from the repo root and nothing else:\n\n` +
    `    python3 -m pipeline deploy ${slug}\n\n` +
    `It makes a fresh copy, installs, builds and opens a temporary preview link. It takes several ` +
    `minutes - let it finish. Then read projects/${slug}/deploy.json and return it.\n\n` +
    `Do NOT edit any file. You are a command runner.`,
    { label: 'deploy-check', phase: 'Deploy', effort: 'low',
      schema: { type: 'object', required: ['ok', 'steps'],
                properties: { ok: { type: 'boolean' }, preview: { type: 'string' },
                              steps: { type: 'array', items: {
                                type: 'object', required: ['step', 'ok'],
                                properties: { step: { type: 'string' }, ok: { type: 'boolean' },
                                              detail: { type: 'string' } } } } } } }),
])
await lock('off', 'unlock:final')

// ---- steps 10 and 11's checkers -------------------------------------------
// requirements_doc.md rule 6: "Solutions must not appear in comments, README,
// migrations, seed data, or git history." And step 11's guide linter, because
// the guide was the one AI output with no script behind it.
phase('Handover')
const handover = await agent(
  `Run exactly this from the repo root and nothing else:\n\n` +
  `    python3 -m pipeline handover-checks ${slug}\n\n` +
  `It runs the leak scan over the generated student version and its git history, ` +
  `then the guide linter over the pack. Then read projects/${slug}/leak-scan.json ` +
  `and projects/${slug}/guide-lint.json and return both.\n\n` +
  `Do NOT edit any file. You are a command runner.`,
  { label: `handover-checks:${slug}`, phase: 'Handover', effort: 'low',
    schema: {
      type: 'object',
      required: ['leak_ok', 'guide_ok'],
      properties: {
        leak_ok: { type: 'boolean' },
        guide_ok: { type: 'boolean' },
        leaks: { type: 'array', items: {
          type: 'object',
          properties: { file: { type: 'string' }, task: { type: 'string' },
                        leaked: { type: 'string' } } } },
        guide_errors: { type: 'array', items: {
          type: 'object',
          properties: { code: { type: 'string' }, where: { type: 'string' },
                        message: { type: 'string' } } } },
      },
    } })
mustRun('handover-checks', handover)

log(`handover: leak scan ${handover.leak_ok ? 'clean' : 'LEAKED'}, ` +
    `guide linter ${handover.guide_ok ? 'clean' : 'FAILED'}`)

const overruns = (pack && pack.sessions || []).filter(s => s.overruns || s.minutes > 40)

return {
  slug, gate: 3,
  ready: !!(pack && deploy && deploy.ok && handover.leak_ok && handover.guide_ok),
  handover: {
    leak_scan: handover.leak_ok ? 'clean' : handover.leaks || 'leaked',
    guide_linter: handover.guide_ok ? 'clean' : handover.guide_errors || 'failed',
  },
  cut_count: cut.cut_count,
  cut_retries: attempt,
  pack: pack ? { files: pack.files, concerns: pack.concerns } : 'pack-writer failed',
  deploy: deploy ? { ok: deploy.ok, preview: deploy.preview,
                     failed_steps: deploy.steps.filter(s => !s.ok).map(s => s.step) }
                 : 'deploy check failed',
  sessions_over_40_minutes: overruns.map(s => `session ${s.n}: ${s.minutes} min`),
  read_next: [`projects/${slug}/pack/`, `projects/${slug}/skeleton-check.json`,
              `projects/${slug}/deploy.json`, `projects/${slug}/leak-scan.json`,
              `projects/${slug}/guide-lint.json`],
  note: 'Gate 3 is one question: could someone teach a session from the guide alone, ' +
        'without opening the final code. Step 13 answers it with evidence rather than ' +
        'opinion: a person who did not build it teaches one session from the guide, ' +
        'with a timer.',
  step_13_dry_run: `python3 -m pipeline dryrun ${slug} --session <n> --minutes <measured> ` +
    `--by "<who taught it - not whoever built it>" [--could-not-teach] -m "<what happened>"`,
  approve_with: `python3 -m pipeline gate ${slug} 3 approve -m "<note>" && python3 -m pipeline ship ${slug}`,
  reject_with: `python3 -m pipeline gate ${slug} 3 reject -m "<what to fix>"`,
}
