# Integration fixture

`runner-check` is a minimal but real Next.js 15 app used to prove the scripts
against a live build, not a mock. The selftest covers the deterministic core in
a second; this covers the parts that need npm, a browser and a booted server.

```bash
python3 -m pipeline.test_runner fixtures/runner-check --target app       # 3/3 criteria pass
python3 -m pipeline.cutter     cut fixtures/runner-check                 # skeleton + typecheck
python3 -m pipeline.test_runner fixtures/runner-check --target skeleton  # 2 fail, 1 pass
python3 -m pipeline.cutter     verify fixtures/runner-check              # ok, no mismatches
```

It is deliberately shaped to exercise the two things that broke first:

- `app/api/health/route.ts` keeps its `return` **outside** the cut markers, with
  a typed fallback inside. Move the return inside the markers and the cutter
  fails with TS2355 - that is the check working.
- `app/page.tsx` cuts a JSX block, so the `{/* ... */}` comment style is covered.

Not a guided project. It lives outside `projects/` so the watchdog and the
orchestrator never see it.

## The gate machinery, end to end

The selftest covers the gate 1 rule, the spec freeze and the report binding
deterministically. This is the manual pass that puts them on a real project with
a real build - run it against a scratch slug, then delete the project, because a
shipped project stays in the nightly watchdog forever.

```bash
python3 -m pipeline new e2e-health
# copy this fixture's spec.json, spec.md, app/ and verify/ into projects/e2e-health,
# set spec.json slug to e2e-health, and write a real idea.md

python3 -m pipeline lint e2e-health          # clean; also opens the breaker pass
# write ambiguity.md with a BLOCKING finding whose Owner is `nothing`
python3 -m pipeline breaker e2e-health end
python3 -m pipeline gate1-check e2e-health   # exit 1, reject - names the unowned finding
python3 -m pipeline gate e2e-health 1 approve -m x   # refused

# fix the spec, and the bound report goes stale
python3 -m pipeline gate1-check e2e-health   # exit 1, stale - the hashes differ
python3 -m pipeline next e2e-health          # step 3, not the gate
python3 -m pipeline lint e2e-health          # reopens the pass, clears the stale report
# write the report again, this time with every blocking finding owned downstream
python3 -m pipeline breaker e2e-health end
python3 -m pipeline gate e2e-health 1 approve -m "all findings owned downstream"
# -> spec frozen and archived to .pipeline/approved/

python3 -m pipeline spec-status e2e-health   # exit 0, no drift
# edit spec.json, then:
python3 -m pipeline spec-status e2e-health   # exit 1, drift
python3 -m pipeline test e2e-health          # refuses - built against the approved spec
# restore it, then run test -> gate 2 -> cut -> pack -> deploy -> gate 3 -> ship
```

Two things worth injecting on purpose while you are here:

* move a `return` inside a cut's markers in `app/` and run `pipeline cut` - it
  must refuse and name the fix pattern, leaving no skeleton behind;
* pin a dependency version with a live advisory and run `pipeline deploy` - the
  `install advisories` step must fail and Gate 3 must refuse.
