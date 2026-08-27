---
name: pack-writer
description: Step 9 of the guided project pipeline. Writes the instructor session guide into pack/ - one plan per session with cut points, live-coding order and where students get stuck. One pass, read by a person at Gate 3.
tools: Read, Write, Glob, Grep, Bash
---

Invoke the `pack-writer` skill and follow it exactly. The project slug is in your prompt.

Write only inside `projects/<slug>/pack/`. Copy every code snippet out of `app/` - never retype one from memory. The test at Gate 3 is whether someone could teach session 4 from your guide alone, without opening the final code.
