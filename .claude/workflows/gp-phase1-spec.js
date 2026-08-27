export const meta = {
  name: 'gp-phase1-spec',
  description: 'Guided project phase 1: one-page idea -> linted, ambiguity-checked spec ready for Gate 1',
  whenToUse: 'After a person has written projects/<slug>/idea.md. Stops at Gate 1 - a person approves the spec before any code exists.',
  phases: [
    { title: 'Draft', detail: 'Spec Writer turns idea.md into spec.md + spec.json' },
    { title: 'Lint', detail: 'spec linter - script, deterministic' },
    { title: 'Break', detail: 'Spec Breaker flags every line that could mean two things' },
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

return {
  slug,
  gate: 1,
  ready: true,
  spec_attempts: attempt,
  lint: 'clean',
  ambiguity,
  read_next: [`projects/${slug}/spec.md`, `projects/${slug}/ambiguity.md`],
  approve_with: `python3 -m pipeline gate ${slug} 1 approve -m "<note>"`,
  reject_with: `python3 -m pipeline gate ${slug} 1 reject -m "<what to fix>"`,
}
