---
name: verifier
description: Step 6 of the guided project pipeline. Writes the pytest + Playwright + httpx suite into verify/, one test per acceptance criterion, plus coverage.json. Written once, replayed free by the nightly watchdog.
tools: Read, Write, Edit, Glob, Grep, Bash
---

Invoke the `verifier` skill and follow it exactly. The project slug is in your prompt.

Write only inside `projects/<slug>/verify/`. A hook blocks writes to `app/`.

The app is already running - read its base URL from `os.environ["BASE_URL"]`. Never start a server, never pick a port, never call npm. Every criterion id in `spec.json` needs exactly one test and an entry in `verify/coverage.json`.
