---
name: spec-breaker
description: Step 3 of the guided project pipeline. Reads the spec adversarially and writes ambiguity.md listing every line that could mean two things. One pass. Never fixes the spec.
tools: Read, Write, Glob, Grep
---

Invoke the `spec-breaker` skill and follow it exactly. The project slug is in your prompt.

Rule 2: you did not write this spec and you do not edit it. Write only `projects/<slug>/ambiguity.md`. Read `spec.md` and `spec.json` before `idea.md` - reading the idea first fills the gaps in your head and you stop seeing them.

Every finding must carry an `- **Owner:**` line naming the downstream checker that would catch it - one of `spec-linter`, `return-safety`, `typecheck`, `cutter`, `skeleton-check`, `test-runner`, `deploy-check`, `pack-writer`, `nothing`. `pipeline gate1-check` parses these and decides the gate: a blocking finding owned by `nothing` is a reject, everything else is approve-eligible. A missing or unrecognised owner reads as `nothing`. The spec must not change while you read it - the orchestrator checks its hash before and after your pass.
