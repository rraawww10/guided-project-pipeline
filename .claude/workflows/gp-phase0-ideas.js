export const meta = {
  name: 'gp-phase0-ideas',
  description: 'Guided project phase 0 (steps 1-2): a stack the human gave -> five one-page ideas, ready for Gate 0',
  whenToUse: 'After a person has run `pipeline stack <slug> --stack .. --sessions .. --minutes ..` (step 0). Stops at Gate 0 - a person picks one idea, or asks for five more.',
  phases: [
    { title: 'Ideas', detail: 'step 1 - Idea Generator writes five one-page ideas that fit the stack' },
    { title: 'Check', detail: 'five real pages, no placeholders - script' },
  ],
}

// This phase exists because requirements_doc.md puts two things in front of the
// spec that the pipeline did not have: the human states the stack, and the AI
// proposes five ideas for the human to choose from. Two rules govern it and
// neither bends:
//
//   The human gives the stack. The AI does not choose it.
//   The AI gives the ideas. The human approves them. The AI does not pick.
//
// So this workflow reads the stack, writes five ideas, checks them, and stops.
// It never writes idea.md - `pipeline pick <slug> <n>` is a person's command and
// that is what records Gate 0.
const RETRY_LIMIT = 15
const slug = (args && args.slug) || args
if (!slug || typeof slug !== 'string') throw new Error('pass the project slug, e.g. args: {"slug":"habit-tracker"}')

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

const IDEAS = {
  type: 'object',
  required: ['ok', 'count', 'problems'],
  properties: {
    ok: { type: 'boolean' },
    count: { type: 'integer' },
    wanted: { type: 'integer' },
    files: { type: 'array', items: { type: 'string' } },
    problems: { type: 'array', items: { type: 'string' } },
  },
}

// step 0 is a person's, so the only thing to do here is refuse if it is missing.
const stack = await agent(
  `Run exactly this from the repo root and nothing else:\n\n` +
  `    python3 -m pipeline next ${slug}\n\n` +
  `Then read projects/${slug}/stack.json if it exists and return its contents, or ` +
  `set missing true if it does not. Do NOT edit any file. Do NOT create it.`,
  { label: `stack:${slug}`, phase: 'Ideas', effort: 'low',
    schema: {
      type: 'object',
      required: ['missing'],
      properties: {
        missing: { type: 'boolean' },
        stack: { type: 'array', items: { type: 'string' } },
        sessions: { type: 'integer' },
        minutes_per_session: { type: 'integer' },
        limits: { type: 'string' },
      },
    } })

if (stack.missing) {
  return {
    slug, gate: 0, ready: false,
    blocked: 'step 0 has not happened - the human states the stack, and the AI does not choose it',
    fix: `python3 -m pipeline stack ${slug} --stack 'next,react,typescript' --sessions 3 --minutes 40`,
  }
}

const runCheck = () => agent(
  `Run exactly this from the repo root and nothing else:\n\n` +
  `    python3 -m pipeline ideas ${slug}\n\n` +
  `Then read projects/${slug}/ideas.json and return it. Do NOT edit any file. ` +
  `Do NOT fix any idea. You are a command runner, not a repair agent.`,
  { label: `ideas:${slug}`, phase: 'Check', effort: 'low', schema: IDEAS })

phase('Ideas')
let check = null
let attempt = 0

while (attempt < RETRY_LIMIT) {
  attempt++
  const retryNote = check && !check.ok
    ? `\n\nThis is retry ${attempt} of ${RETRY_LIMIT}. The idea check rejected the last set. ` +
      `Fix exactly these and change nothing else:\n` +
      check.problems.slice(0, 20).map(x => `  ${x}`).join('\n')
    : ''

  await spawn('idea-generator',
    `Propose five ideas for guided project "${slug}".\n\n` +
    `The human has already given the stack. Read projects/${slug}/stack.json and build ` +
    `every idea on exactly that stack - ${(stack.stack || []).join(', ')}, ` +
    `${stack.sessions} sessions of ${stack.minutes_per_session} minutes` +
    (stack.limits ? `, limits: ${stack.limits}` : '') + `.\n\n` +
    `Read learning/lessons.md, and look at projects/ to see what already exists so you ` +
    `do not propose another variation of a shipped project.\n\n` +
    `Write projects/${slug}/ideas/idea-01.md through idea-05.md. Do not rank them, do ` +
    `not recommend one, and do not write projects/${slug}/idea.md - a person picks at ` +
    `Gate 0.` + retryNote,
    { label: attempt === 1 ? 'idea-generator' : `idea-generator:retry-${attempt - 1}`,
      phase: 'Ideas' })

  phase('Check')
  check = await runCheck()
  log(`idea check attempt ${attempt}: ${check.ok ? `${check.count} ideas, clean` : check.problems.join('; ')}`)
  if (check.ok) break
}

if (!check.ok) {
  // Rule 6 in Flow.md, rule 7 in requirements_doc.md: retries stop and a ticket
  // is raised rather than looping forever.
  return {
    slug, gate: 0, ready: false, ticket: true, attempts: attempt,
    reason: `the idea set still has problems after ${attempt} attempts`,
    problems: check.problems,
  }
}

return {
  slug,
  gate: 0,
  ready: true,
  attempts: attempt,
  stack: { stack: stack.stack, sessions: stack.sessions,
           minutes_per_session: stack.minutes_per_session, limits: stack.limits },
  ideas: check.files,
  read_next: [`projects/${slug}/ideas/`],
  note: 'Gate 0 is one question: is one of these five worth three sessions of someone\'s ' +
        'attention. Read all five. The AI does not pick, and it did not rank them.',
  pick_with: `python3 -m pipeline pick ${slug} <n> -m "<why this one>"`,
  more_with: 'reject nothing - just run this workflow again for five more',
}
