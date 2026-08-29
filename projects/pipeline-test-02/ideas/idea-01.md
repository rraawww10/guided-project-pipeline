# Slab

**One line:** Enter an annual income and see it sliced across tax brackets - what
each slab contributes, the effective rate against the marginal one, and how many
rupees are left before the next slab starts.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

Everyone who has looked at a payslip has wondered whether earning one rupee more
can leave them worse off. The answer is a piecewise function, and it is small
enough to write in a session: fold over an ordered list of brackets, taxing only
the portion of income that falls inside each one. The screen makes the shape
visible - the slab table fills in band by band - and the payoff is the moment a
student sees effective rate and marginal rate diverge on the same income.

## Sessions

1. **Setup, the regime, and the total.** Types, a seed holding two named regimes
   (each an ordered bracket list) and six saved incomes, `GET /api/regimes`, and
   `/` listing every saved income with its tax under the default regime. The work
   is `taxFor(income, brackets)`: the fold that charges each bracket only on the
   slice of income inside it, and stops once income runs out. **Runs:** a list of
   six incomes with a tax figure beside each.
2. **The breakdown and the headroom.** `/regimes/[id]?income=` shows a row per
   slab - the band, the amount taxed in it, the tax it produced - plus
   `effectiveRate` and `marginalRate`, and `headroom(income, brackets)`: rupees
   until the next band begins. A rebate rule applies below a declared threshold
   and creates a genuine cliff, which gets a criterion of its own.
   `POST /api/regimes/[id]/tax` returns the same breakdown as JSON. **Runs:** type
   an income, watch it split across the bands and the two rates disagree.

## What the student types

- `taxFor` - the fold, and the `min(remaining, bandWidth)` slice that is the
  whole idea.
- `marginalRate` and `headroom` - reading the *next* bracket rather than the
  current one, including the top band where there is no next.
- The rebate branch, which is not a rate at all but a cliff, and has to be
  applied after the fold rather than inside it.

## What this teaches that the shipped projects do not

tip-split divides one number by a count; recipe-box multiplies a quantity by a
ratio. Both compute a value from a record in isolation. This is the first
piecewise function in the track: the answer depends on which range the input
lands in, and every interesting case sits exactly on a boundary. It is also the
first project where two correct-looking rates (effective, marginal) describe the
same number and a student has to say which one answers the question.

## Out of scope

- Any claim to be current tax law. The brackets are seed data, clearly labelled
  as illustrative, and the project is arithmetic, not advice.
- Deductions, exemptions, surcharge, cess, capital gains, multiple income heads.
- Editing brackets in the UI, adding regimes, or a second financial year.
- Currency other than rupees, and any conversion.

## Risks

Boundary semantics. Whether a bracket's upper limit is inclusive, and whether
the rebate threshold is `<` or `<=`, must be pinned in the spec or the Builder
and the Verifier will each pick a defensible reading and disagree by one rupee.
Second, straight from `learning/lessons.md`: a fold graded against one income is
satisfied by a hardcoded number, so the criteria need an income exactly on a slab
edge, one a rupee above it, one just under the rebate cliff and one just over.
Third, rounding must happen once at the end, declared explicitly, or per-slab
rounding drifts the total.
