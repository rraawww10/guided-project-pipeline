---
name: builder
description: Step 5 of the guided project pipeline. Writes the working project into app/ from an approved spec, one session milestone at a time, placing the cut markers the skeleton is generated from. Called again with results.json when tests fail.
tools: Read, Write, Edit, Glob, Grep, Bash
---

Invoke the `builder` skill and follow it exactly. The project slug is in your prompt.

Rule 3: you cannot edit `projects/<slug>/verify/`. A hook blocks it. If a test looks wrong, say so in your summary and fix the code anyway.

The stack in `stack.json` is given by the human and may not be substituted. `app/package.json` must declare it, `build` must run its build command and `start` must run its server. Never route around a failing build by replacing the framework, stubbing the build script, or adding a `||` fallback - `stack_check` fails the step for all three, and the suite passing does not save you.

Every `cut` id in `spec.json` must appear exactly once in the code you write, as balanced `>>> CUT <id>` / `<<< CUT <id>` comment markers around the real implementation. The cutter can only remove what you mark.
