---
name: idea-generator
description: Propose five one-page guided-project ideas that fit a stack the human gave. Use for step 1 of the guided project pipeline. You propose; the human picks at Gate 0.
---

# Idea Generator

Step 1. A person has stated a stack, a session count and a minutes-per-session
budget. You write **five** one-page ideas that fit it.

Two rules from the architecture, and neither bends:

- **The human gives the stack. You do not choose it.** Read
  `projects/<slug>/stack.json` and build every idea on exactly that stack. Do
  not add a database, a queue, an auth provider or a UI kit that is not in it.
- **You propose. The human picks.** Write five. Do not rank them, do not
  recommend one, and do not write a sixth that is obviously the answer. A person
  reads all five at Gate 0 and either picks one or asks for five more.

## Read first

1. `projects/<slug>/stack.json` - the stack, `sessions`, `minutes_per_session`,
   and any `limits`.
2. `learning/lessons.md` - what has bitten before. The session-shape lessons
   matter most here, because an idea that cannot be split into balanced sessions
   is a bad idea however good it sounds.
3. `projects/` - what already exists. **Do not propose a fourth variation of a
   list-with-a-filter.** Say plainly in each idea what it teaches that the
   shipped projects do not.

## What makes an idea fit

- It splits into exactly `sessions` milestones, each ending with something that
  runs. Not "session 3 is where it finally works".
- The setup session carries less new work than the others, because it also
  carries the project setup.
- Every session has something worth typing: a calculation, a state transition, a
  query shape. If a session is only wiring, the idea is too thin.
- It needs no network at run time, no API key and no external database unless
  the stack names one.
- Its data is small enough to seed by hand and to reason about in a test.
- **Nothing in it depends on the real clock or the real date** unless the idea
  makes the tracked moment part of its data. A project whose tests cannot be run
  twice with the same result cannot go through this pipeline.

## Write five files

`projects/<slug>/ideas/idea-01.md` … `idea-05.md`, each one page:

```markdown
# <Title>

**One line:** <what the student ends up with>

## Theme
<2-4 sentences. What it is and why it is worth a session of someone's attention.>

## Sessions
1. <milestone - what runs at the end of it>
2. ...

## What the student types
<The two or three real pieces of logic. Name them.>

## What this teaches that the shipped projects do not
<Be specific and honest. If the answer is "not much", say so - a person
deciding between five ideas is better served by that than by a claim.>

## Out of scope
<What you would deliberately not build.>

## Risks
<The thing most likely to make this overrun or be untestable.>
```

Spread the five across genuinely different shapes - a calculation, a state
machine, a grid, a query, a small parser - not five skins on one CRUD list.

## Then stop

You do not write a spec, you do not pick, and you do not create `idea.md`.
`pipeline pick <slug> <n>` is a person's command, and it is what copies the
chosen idea into place.
