# Troubleshooting

Everything below has a cause and a sentence you can say. Ordered by when in the
two sessions you will hit it.

## Getting it running

**`npm ci` fails with `EUSAGE ... lock file` or a missing `package-lock.json`.**
Use `npm install` in that tree instead. `skeleton/` and `app/` each have their
own `package-lock.json` and their own `node_modules`; installing in one does
nothing for the other.

**`npm ci` prints a security advisory for `next`.** Read it and carry on for the
session. It does not stop the build. It is worth noting because a green deploy
check has hidden a CVE line in this pipeline before.

**`Error: listen EADDRINUSE :::3000`.** Something is already on 3000 - very often
a `next` server left behind by an earlier run that was closed with the window
rather than with Ctrl-C. Either kill it, or `npm run dev -- -p 3001` and tell the
room the new port.

**`Module not found: Can't resolve '@/lib/ledger'`.** `@/*` is mapped to the
project root in `tsconfig.json`, so it only resolves when the dev server was
started from the directory holding `package.json`. Someone ran `npm run dev` one
level up, or opened the editor on the repository root and the language server
guessed. Restart the server from `skeleton/`.

**`Cannot find module 'next'`.** No `node_modules` in *this* tree. Install here.

**The page in the browser never changes, no matter what is saved.** Look at the
terminal running `npm run dev`. A TypeScript error stops the rebuild and the
last good bundle keeps being served. The browser is telling you the truth about
five minutes ago.

**Edits to `data/ledger.txt` do nothing.** You are on `npm run start` against a
build made before the edit. Both routes are `force-dynamic`, so `npm run dev`
re-reads the file on every request.

## Session 1 - the parse

**The page reads `0` parsed and `27` refused, every complaint says
`expected 4 fields, found 4`.** This is the correct starting state of the
skeleton, before either cut is filled. Nothing is broken. `reason` is sitting on
its initialiser and nothing has assigned to it.

**Still `0` and `27` after filling `cut-amount-paise` only.** Also correct.
Nothing is visible until `cut-parse-line` stops rejecting the line. Warn the room
before you reload, or half of them will start undoing good work.

**`0` parsed, and `27` complaints that all read `expected 4 fields, found 1`.**
Somebody changed the shipped split. The field split is
`line.split("|").map((f) => f.trim())` on the line above the `TODO` and it is not
theirs to edit; splitting on `" | "` breaks line 13, where the account field is
two spaces.

**22 entries, and line 9 is one of them.** A `Date`-based date check.
`new Date("2026-1-06")` does not fail - it is parsed as 6 January. c-1-1 goes red
on the entry count and c-1-2 goes red because there is no diagnostic on line 9.
The rule is the *shape* of the string, not whether the day exists.

**Line 20 arrives as `2026-03-02` instead of `2026-02-30`.** They converted the
field to a `Date` and formatted it back. `new Date("2026-02-30")` is not
rejected; it rolls silently to 2 March. c-1-1 pins the string as written. Store
the field, do not interpret it.

**Line 22 (`2026-13-02`) is accepted.** The month group is `\d{2}`. Months are
`(0[1-9]|1[0-2])`.

**`entry-amount-8` reads `-250.04`, or a total is off by one paisa.** A
truncating float multiply. `250.05 * 100` is `25004.999999999996` in the console,
and `Math.trunc` takes it to `25004`. Pull two integers out of the text instead.

**Line 25 (`-350.5`) is accepted.** The paise group is `\d+` instead of exactly
`\d{2}`.

**Line 28 (`1,200.00`) is accepted, often with `paise` `20000`.** Either
`parseFloat`, which reads that string as `1`, or a pattern with no `^` and `$`,
which finds `200.00` inside it. Anchor the pattern.

**Every line rejected, including the good ones, after `cut-parse-line` looks
finished.** The good path never assigns `reason = null`. The initialiser is a
fallback the student has to clear, not an accumulator.

**Line 17 complains about its date instead of its field count.** The rules were
checked in the wrong order, or the date check runs outside the `if` that tests
the field count. Line 17 has three fields; that is the first rule it breaks and
the only reason it may carry.

**TypeScript: "This comparison appears to be unintentional because the types
have no overlap" on `reason === null`.** They rewrote the shipped guard below the
`TODO`. With the block empty, nothing assigns to `reason` after its initialiser,
so TypeScript narrows it to `string` and the whole app stops compiling - not one
red test, no build at all. The shipped line is `if (!reason && amount === null)
reason = BAD_AMOUNT` and it is written that way for exactly this reason. Put it
back.

**Everything is green but they used `parseFloat`.**
`Math.round(parseFloat(text) * 100)` passes every criterion in this project.
Nothing here catches it. Argue the point on its merits - say that the rounding is
hiding an error rather than not making one - and do not claim the tests caught
it, because they did not.

## Session 2 - accounts

**`/accounts/rent` 404s even though `/api/accounts` is right.** The 404 comes
from `accountRows`, not from `accountTotals`. The page calls `notFound()` when
`rows.length === 0`.

**404 on every account, and `accountRows` looks finished.** The name comparison
is not exact - `includes`, a `toLowerCase()` on one side only, or a compare
against `entry.description`.

**`/accounts/Rent` returns 200.** Someone lowercased the route name. c-2-4 pins
`/accounts/Rent` as a 404.

**The 404 page is Next's default and has no `account-missing` element.** The
`not-found.tsx` file was moved, renamed or deleted. It ships written at
`app/accounts/[name]/not-found.tsx` and it must sit beside the page that calls
`notFound()`.

**`account-total` reads `-`.** The page reads it out of `accountTotals`, and
`accountTotals` has no object for that route name - the fold is empty, or it
stored a different string as the key.

**Totals read `NaN.00`.** `summed.get(account) + entry.paise` without the
`?? 0`. `Map.get` on an unseen key is `undefined`, and `undefined + 5` is `NaN`.

**`utilities`, or an empty name, appears in the account list.** They folded over
something other than the accepted `entries`. A rejected line contributes no
account and no paise - that is c-2-2.

**The account list is not in name order.** `sort((a, b) => a.account - b.account)`
on strings is `NaN` for every pair and leaves the order untouched. Plain `.sort()`
on the keys is the string order the contract asks for.

**Every `txn-running` cell reads `-`.** `runningBalance` returned fewer numbers
than there are rows - usually an empty array, so the cut is still open, or the
push is outside the loop.

**The running column repeats one number.** Either `carried` is being declared
inside the loop, so it restarts every row, or the account total is being pushed
once per row.

**The running column is right but shifted by one row.** The push happens before
the add, so the first row shows `0`.

**The last running number does not equal the total at the top.** Two different
sources disagree: the total comes from `accountTotals`, the column from
`runningBalance` over `accountRows`. On a correct build they must match, and
`rent` on the board (`-37200.00`) is the fastest check.

**`params.name` is undefined.** Only students who edited the page hit this. In
Next 15 `params` is a `Promise` and the shipped code does
`const { name } = await params`. They do not need to touch this file.

## Running the graded suite

Let the pipeline boot the app; do not start a server first.

```text
python3 -m pipeline test pipeline-test-03 --target skeleton
python3 -m pipeline test pipeline-test-03 --target app
```

It runs `npm ci`, `npm run build`, `npm run start` on a free port, sets
`BASE_URL`, and runs pytest with Playwright. Results land in
`skeleton-results.json` and `results.json`, one entry per criterion with the
assertion message.

**`KeyError: 'BASE_URL'`.** The suite was run by hand with plain `pytest`.
Nothing in `verify/` starts a server or picks a port; it expects the app to be
running already and the URL in the environment.

**Playwright cannot find a browser.** The project venv needs
`playwright install chromium`. The runner does this on first use; a venv copied
between machines will not have it.

**`PermissionError` on Windows during a rerun.** Orphaned `next` servers from an
earlier run holding the build directory. `npm run start` spawns `next` as a
child, and killing npm has left the child alive before. Kill the stray `node`
processes and rerun.

**A criterion reports a Playwright timeout rather than a value mismatch.** The
element is not on the page at all, which on the skeleton is the normal shape for
a cut that is still open. The suite waits 20 seconds by choice, so a missing
element fails on that budget rather than on Playwright's longer default.
