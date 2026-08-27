---
name: pack-writer
description: Write the instructor session guide for a finished guided project - one plan per session, with the cut points, the live-coding order, and where students usually get stuck. Use for step 9 of the guided project pipeline. One pass, a person reads it at Gate 3.
---

# Pack Writer

Step 9. You write the instructor session guide.

Today this does not exist and the instructor works out the plan by reading the
code. The test at Gate 3 is one question: could someone teach session 4 from
this guide alone, without opening the final code?

## Read first

1. `projects/<slug>/spec.json` and `spec.md` - sessions, criteria, cut points.
2. `projects/<slug>/app/` - the final code, so every snippet you write is real.
3. `projects/<slug>/skeleton/.cut-manifest.json` - exactly what the student is
   handed and exactly what is missing from it, per file and line.
4. `projects/<slug>/results.json` - the criteria and how they are checked.
5. `projects/<slug>/ambiguity.md` - what was unclear at Gate 1. Those are the
   places students will ask about too.
6. `learning/lessons.md` - where students got stuck on earlier projects.

## Write into `projects/<slug>/pack/`

```
pack/
  README.md              the project in one page, and how to run it
  session-1.md           one file per session
  session-2.md
  ...
  troubleshooting.md     every error a student will actually hit
```

## Each `session-N.md`

```markdown
# Session N - <title>

**Time:** 40 minutes
**Students start from:** <what runs at the start of this session>
**Students end with:** <what runs at the end>

## What they learn
<the concepts, in the order you teach them>

## Before you start
<what must be running, what to have open>

## The plan
| Minutes | What you do |
|---|---|
| 0-5   | <recap and set up the problem> |
| 5-30  | <live coding, cut point by cut point> |
| 30-38 | <students finish, you circulate> |
| 38-40 | <what runs now, and what is next> |

## Cut points in this session
### cut-<id> - <file>:<line>
- **What students see:** the TODO line, quoted exactly from the skeleton
- **What they write:** the shape of the answer, not the answer typed out
- **Teach it like this:** <how to explain the concept, in one or two sentences>
- **Passes when:** criterion c-N-k goes green

## Where students get stuck
- **<the symptom they report>** - <the cause> - <what you say>

## Check before moving on
<the one thing that must run before session N+1>
```

## What makes this guide good

**Minutes must add to 40.** The spec was written to fit. Do not overrun it on
paper - if the plan needs 55 minutes, say so plainly at the top, because that is
a spec problem the person at Gate 3 needs to see.

**Every stuck point is a real one.** Take them from the cut points, the
ambiguity report, and `lessons.md`. The npm error, the wrong import path, the
state that does not update because the array was mutated in place. Not
"students may find state confusing".

**Snippets come from the real code.** Copy them out of `app/`, do not retype
them from memory. A guide that drifts from the code is the problem this pipeline
exists to end.

**Write to be read out loud.** Short sentences, plain words, no jargon the
session has not taught yet. An instructor is reading this with a class waiting.

## Then stop

You get one pass and a person reads it. Return the file list and the per-session
minute totals. If any session's plan does not fit 40 minutes, say which and by
how much - that is the most useful thing you can hand Gate 3.
