# Recipe Box

**Track:** fullstack
**Sessions:** 4
**Stack:** Next.js 15 (App Router), React 19, TypeScript
**Source material:** none

## Theme                  

A place to keep the recipes you actually cook. Students build a small library
they can browse, search by tag, open, and re-scale for a different number of
people. The scaling step is the payoff: it is the first time in the track that
the number on the screen is computed from state rather than read from the
server, and students can see straight away whether they got it right.

## Scope

- A JSON file on disk as the store, read and written through route handlers.
- List every recipe: title, tag chips, how long it takes, how many it serves.
- Open one recipe: its ingredients with quantities and units, and its steps.
- Search recipes by title, and narrow by tag. Both at once.
- Change how many people a recipe serves and see every ingredient quantity
  scale with it. Nothing is saved - it is a view of the same recipe.
- Seed data ships with the project: eight recipes across five tags, so the list
  and the filters have something real in them from session one.

## Out of scope

- Adding, editing or deleting recipes. The box is read-only. Students who ask
  can add it afterwards; it is not taught.
- Accounts, sign-in, anything per-user.
- Images. Recipes are text.
- A database. The JSON file is the store, and that is deliberate.

## Constraints

- Runs offline. No external API, no network call the student has to configure.
- No state library. React state and the URL only - the search and tag filter
  live in the query string so a filtered list can be shared as a link.
- Ingredient quantities must handle thirds and halves without drifting - a
  recipe scaled from 4 to 6 and back to 4 must read exactly as it started.
- No CSS framework. Plain CSS modules, so the styling is not the lesson.
