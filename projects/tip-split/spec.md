# Tip Split

**Track:** fullstack · **Sessions:** 3 · **Stack:** Next.js 15 (App Router), React 19,
TypeScript, plain CSS modules · **Source material:** none

## Outcome

A shelf of restaurant bills a student can browse, open, and re-split across a
different number of people, running offline from a JSON file on disk. Three sessions,
and something runs at the end of each one.

At the end of session 3 a student has:

- A list screen at `/` showing all 6 seed bills, each card a link carrying the place,
  the date, the bill total and how many people it was split between when it was saved.
- A bill screen at `/bills/<id>` showing that bill's total, its tip percentage, the
  tip in rupees, the total with tip, and one row per person with what that person owes.
- A people stepper on that screen. Moving it from 4 to 3 rewrites every share on
  screen, and moving it back to 4 restores the bill exactly as it was saved. When the
  amount does not divide evenly the leftover paise go to the first people in the list,
  one each, so the shares on screen always add back up to the total with tip to the
  paisa.
- Two route handlers over one JSON file. Nothing is written back to disk.

The payoff is session 3. It is the first time in the track that the number on the
screen is computed from React state rather than read from a server response, and
because it is money a student can see in one click whether the arithmetic is right.

**Two notes for Gate 1, both places where this spec departs from `idea.md`.**

1. **The idea asks for 2 sessions; this spec plans 3.** The work is 11 cut points and
   17 acceptance criteria. Two sessions cannot hold that under the house caps of five
   cuts and six criteria per session, and squeezing it would put the dynamic route,
   the 404 branch, the client fetch, the integer tip, the integer split and the clamped
   stepper all into one 40-minute session. The split below gives each session one
   milestone: session 1 is the list, session 2 is one bill with its tip, session 3 is
   the re-split. Session 3 is the idea's stated payoff and now has a session to itself.
2. **The store is read-only.** The idea's first scope bullet says the JSON file is
   "read and written through route handlers", while the idea's own out-of-scope list
   rules out adding, editing and deleting bills. This spec follows the out-of-scope
   list. There is no write path anywhere in the project.

## Out of scope

- Adding, editing or deleting a bill. The shelf is read-only. There is no POST, PUT,
  PATCH or DELETE handler in the project.
- Accounts, sign-in, anything per-user.
- Itemised bills. A bill is one total, not a list of dishes.
- Currency other than rupees, and any currency conversion.
- A database. `data/bills.json` is the store, and that is deliberate.
- Saving the re-split. The people count lives in React state and returns to the bill's
  stored people count when the page is reloaded. No request is sent when it changes.
- Date formatting. A date is stored as an ISO `YYYY-MM-DD` string and printed
  unchanged. No locale, no month names, no relative dates.
- Thousands separators. `₹1240.00` is printed with a decimal point and nothing else.
- Splitting the tip differently from the bill, tipping a flat rupee amount instead of a
  percentage, or rounding the tip up to a round number.
- A state library and a CSS framework. React state and CSS modules only.

## Data model

One file, `data/bills.json`, holding an array of 6 bills. The type lives in
`lib/types.ts` and is shared by the route handlers and the screens.

```ts
type Bill = {
  id: string          // kebab-case, and the URL segment: "anand-bhavan"
  place: string
  date: string        // ISO calendar date, "2026-03-14"
  totalPaise: number  // the bill before tip, in whole paise
  tipPercent: number  // a whole-number percentage, 1..100
  people: number      // how many people it was split between when it was saved, 1..20
}
```

**Money is whole paise, everywhere.** `totalPaise`, the tip, the total with tip and
every share are integers counting paise. No amount is ever held as a rupee value with
a decimal point. The only place a decimal point exists is inside `formatRupees`, which
builds a string.

**Reading the store.** `lib/store.ts` exports two functions and no others:
`readAllBills(): Bill[]`, which reads and parses `data/bills.json`, and
`findBill(id: string): Bill | null`, which calls `readAllBills` and picks from its
result. Both read the file on every call. Neither writes.

`readAllBills` reads the file from disk with node's `fs` module, and builds the path
from the process working directory: `path.join(process.cwd(), 'data', 'bills.json')`.
It does not `import` the JSON, and no other file in the project imports
`data/bills.json` either. Reading the file on the server with `fs` is the lesson
session 1 names, and a bundled import would pass every criterion while skipping it, so
the rule is written here and repeated in the hint for `cut-store-read-all`.

**The 6 seed bills,** in the order they are stored in the file, newest date first. The
endpoint returns them in this order and the list screen renders them in the order the
endpoint returns. These values are fixed, because the acceptance criteria count and
read against them.

| id | place | date | totalPaise | tipPercent | people |
|---|---|---|---|---|---|
| `anand-bhavan` | Anand Bhavan | `2026-03-14` | 124000 | 10 | 4 |
| `kabab-junction` | Kabab Junction | `2026-02-28` | 87550 | 7 | 3 |
| `the-filter-room` | The Filter Room | `2026-02-09` | 45000 | 5 | 2 |
| `paradise-biryani` | Paradise Biryani | `2026-01-26` | 233375 | 12 | 6 |
| `chai-point-mg` | Chai Point MG Road | `2026-01-05` | 19900 | 15 | 2 |
| `kurry-kulture` | Kurry Kulture | `2025-12-19` | 310000 | 8 | 5 |

No seed bill has a `tipPercent` of 0. That matters for the skeleton: a tip of zero is
what an unfilled `cut-money-tip` produces, so no seed bill may make the empty block
look right.

**The three money functions,** all in `lib/money.ts`, all taking and returning whole
paise.

`formatRupees(paise: number): string` **ships written; it is not a cut point.** It
prints `₹`, then `Math.floor(paise / 100)`, then `.`, then `paise % 100` padded to two
digits. So `124000` prints `₹1240.00`, `6129` prints `₹61.29`, and `34100` prints
`₹341.00`. There are no thousands separators and the rupee sign is the single
character `₹`.

`tipPaise(totalPaise: number, tipPercent: number): number` is the tip in whole paise,
rounded half up: `Math.floor((totalPaise * tipPercent + 50) / 100)`. Every value in
that expression is a whole number of paise, so the result is exact. The tip of
`anand-bhavan` is `Math.floor((124000 * 10 + 50) / 100)` = `12400` = `₹124.00`. The
tip of `kabab-junction` is exactly 6128.5 paise before rounding, and rounds up to
`6129` = `₹61.29`. That second one is what `c-2-6` checks. The body is
`cut-money-tip`.

**The total with tip** is `bill.totalPaise + tipPaise(bill.totalPaise, bill.tipPercent)`.
That line ships written in `app/bills/[id]/BillView.tsx`, outside every cut. For the
six seeds it comes to 136400, 93679, 47250, 261380, 22885 and 334800 paise.

`splitPaise(amountPaise: number, people: number): number[]` returns one share per
person, in person order, and the shares add up to `amountPaise` exactly. Each share is
`Math.floor(amountPaise / people)`, and the first `amountPaise % people` people get one
extra paisa each. So 136400 across 3 is `[45467, 45467, 45466]`, and 136400 across 4 is
`[34100, 34100, 34100, 34100]`. The body is `cut-money-split`.

## Endpoints

Both are GET. The store is read on every request; nothing writes to disk.

| id | method | path | request | response | status | built |
|---|---|---|---|---|---|---|
| `ep-bills-list` | GET | `/api/bills` | none | `Bill[]` | 200 | session 1 |
| `ep-bill-get` | GET | `/api/bills/[id]` | none | `Bill` | 200, 404 | session 2 |

`GET /api/bills` takes no parameters and always returns all 6 bills, whole `Bill`
objects, in the stored order. There is no filtering, no search and no summary type;
the list screen reads the fields it shows off the whole object.

`GET /api/bills/[id]` returns the one bill with that id and status 200. When the store
holds no bill with that id it answers 404 with a JSON body holding an `error` field.

Neither endpoint computes the tip or the shares. Both of those are worked out on the
client, which is the point of the project: the number on the screen comes from React
state, not from the server.

## Screens

Both screens are read by tests through their markup, so every element a criterion
counts or reads carries a `data-testid`. These fourteen are the whole list. No
criterion depends on a CSS class name: CSS modules hash class names at build time, and
a hashed name is not something a test can select on.

| testid | screen | what one element holds |
|---|---|---|
| `bill-card` | sc-list | one per bill; the element is the link to that bill |
| `card-place` | sc-list | that bill's place: `Anand Bhavan` |
| `card-date` | sc-list | that bill's stored date string: `2026-03-14` |
| `card-total` | sc-list | that bill's total before tip: `₹1240.00` |
| `card-people` | sc-list | the word Split, the stored people count, the word ways: `Split 4 ways` |
| `bill-place` | sc-bill | the place: `Anand Bhavan` |
| `bill-date` | sc-bill | the stored date string: `2026-03-14` |
| `bill-total` | sc-bill | the total before tip: `₹1240.00` |
| `bill-tip-percent` | sc-bill | the tip percentage and a percent sign: `10%` |
| `bill-tip-amount` | sc-bill | the tip in rupees: `₹124.00` |
| `bill-grand-total` | sc-bill | the total with tip: `₹1364.00` |
| `bill-saved-people` | sc-bill | `Split 4 ways when saved` |
| `people-count` | sc-bill | the people count the stepper is on, as a bare number: `4` |
| `share-row` | sc-bill | one per person: `Person 1 ₹341.00` |

**How a criterion reads text.** Every criterion in this spec that says an element
*reads* or *displays* a string means: take that element's text content, collapse each
run of whitespace to a single space, strip leading and trailing whitespace, and compare
the result to the quoted string for exact equality. `share-row` is the case that needs
this said out loud - its text is the word `Person`, one space, the person's position
counting from 1, one space, then `formatRupees` of that share, so the first row of a
4-way split of 136400 paise reads exactly `Person 1 ₹341.00` however the Builder nests
the label and the amount.

**How a criterion finds a control.** The minus and plus controls of the stepper are
`button` elements whose accessible names are `Fewer people` and `More people`; their
visible text is `-` and `+`, and the accessible name comes from an `aria-label` on each
button. The back link on `sc-bill` is an anchor to `/` whose visible text, and therefore
whose accessible name, is `Back to saved bills`. A `bill-card` is itself an anchor,
with `href` `/bills/<id>` and the `data-testid` on the anchor.

One cut point renders marked-up elements - `cut-list-cards` - and its hint names the
five testids its block must render and the link each card must be. Every other testid
ships written.

**Why `bill-saved-people` spells itself out.** `people-count` is the only element on
either screen whose whole text is a bare number. `Split 4 ways when saved` holds a 4
but is not one, so a test reading the stepper cannot pick up the stored count by
mistake. The same applies to `card-people` on the list.

### `sc-list` at route `/`

**States:** `loading`, `loaded`. There is no empty state. The store always holds 6
bills, nothing filters the list, and there is no path in the project that produces an
empty array on this screen.

**Elements:** a heading reading `Saved bills`, a loading message reading
`Loading saved bills`, and a grid of bill cards. Each card is an anchor to
`/bills/<id>` carrying the `bill-card` testid and holding a `card-place`, a
`card-date`, a `card-total` and a `card-people`. Nothing on this screen is interactive
except the card links.

**What holds the screen's state.** `app/page.tsx` is a client component holding
exactly two pieces of state, both declared outside every cut:

```ts
const [bills, setBills] = useState<Bill[]>([])
const [status, setStatus] = useState<'loading' | 'loaded'>('loading')
```

`status` starts at `'loading'` and `cut-list-fetch` is the only code in the file that
moves it. In the `loading` state the screen displays `Loading saved bills` and no
grid; that branch ships written, outside every cut. Until `cut-list-fetch` is filled
the screen sits on `Loading saved bills`, which is what a session-1 student sees on
the first run.

**Who owns the fetch.** The `useEffect` call and its empty dependency array `[]` ship
written, and `cut-list-fetch` is the body of that effect. The effect moves `status` to
`'loaded'` only when the reply is a 200, so while `cut-api-bills-list` is still open
the endpoint's 501 leaves the screen on `Loading saved bills` instead of putting a
non-array into `bills`. There is no other fetch on this screen.

**Files:** `app/page.tsx` holds the state, the effect and both list cut points.

### `sc-bill` at route `/bills/[id]`

**States:** `loading`, `loaded`, `not-found`.

**Elements:** a `bill-place` heading and a `bill-date`; a `bill-total`, a
`bill-tip-percent`, a `bill-tip-amount` and a `bill-grand-total`; a
`bill-saved-people`; a people stepper made of a `Fewer people` button, the
`people-count` number and a `More people` button; one `share-row` per person under the
heading `What each person owes`; and a back link to `/`. The `loading` state displays
`Loading bill` and none of that; the `not-found` state displays `Bill not found` and
the back link.

The `What each person owes` heading and the share list render only when `shares` holds
at least one entry. That condition ships written, outside every cut. It means the
screen never shows an empty section: while `cut-bill-shares` or `cut-money-split` is
open, the heading is absent along with the rows.

**What holds the fetch state.** `app/bills/[id]/page.tsx` is a client component
holding two pieces of state, both declared outside every cut:

```ts
const [bill, setBill] = useState<Bill | null>(null)
const [status, setStatus] = useState<'loading' | 'loaded' | 'not-found'>('loading')
```

`status` starts at `'loading'` and `cut-bill-fetch` is the only code that moves it.
`loaded` renders `BillView` with the fetched bill. A reply that is neither 200 nor 404
- the 501 the handler answers while `cut-api-bill-get` is still open - leaves `status`
on `'loading'`. So a skeleton with `cut-bill-fetch` open sits on `Loading bill` at
every route, including `/bills/not-a-bill`, and `c-2-5` cannot pass until that cut is
filled. Both message branches ship written, outside every cut.

**Who owns the fetch.** The id comes from `useParams`, the `useEffect` call and its
dependency array `[id]` ship written, and `cut-bill-fetch` is the body of that effect.
There is no other fetch on this screen.

**What holds the people count.** `app/bills/[id]/BillView.tsx` holds one piece of
state, declared outside every cut:

```ts
const [people, setPeople] = useState<number>(bill.people)
```

It starts at the bill's own stored `people`, so `/bills/anand-bhavan` opens on 4 and
every session-3 criterion counts its clicks from there. `BillView` mounts only in the
`loaded` state, so `bill` is never null when that initial value is read. The minus and
plus controls call `setPeopleClamped(people - 1)` and `setPeopleClamped(people + 1)`,
both written outside every cut; `cut-bill-people` is the body of `setPeopleClamped`.
With that block open the function does nothing and the count never leaves the stored
value. Both stepper controls stay clickable at every count: the clamp to 1 and 20
lives in the state setter, not in a `disabled` attribute.

**Where the shares come from.** `BillView` computes on every render, all outside every
cut except the one line named:

```ts
const grandTotalPaise = bill.totalPaise + tipPaise(bill.totalPaise, bill.tipPercent)
let shares: number[] = []
// cut-bill-shares assigns to shares here
```

The `share-row` elements are rendered from `shares`, one per entry, in order, with the
text described under **How a criterion reads text** above. That rendering ships
written. Because `shares` is rebuilt from the fetched bill and the current `people` on
every render, and never from what is already on screen, moving the stepper from 4 to 3
and back to 4 lands on the stored split exactly.

**What session 2 ships that session 2 is not graded on.** `sc-bill` is built in
session 2, so `BillView.tsx` and its stepper markup exist from session 2. Until session
3 fills `cut-bill-people` the stepper is inert: a session-2 student can click it and
`people-count` stays on the stored count. Until session 3 fills `cut-money-split` and
`cut-bill-shares`, `shares` stays `[]`, and because the heading and the rows are gated
on `shares.length`, neither appears at all. No session-2 criterion reads `people-count`
or a `share-row`. This is a deliberate Gate 1 call and it is argued under **Session 2's
weight** below.

**Files:** `app/bills/[id]/page.tsx` reads the id and owns the fetch;
`app/bills/[id]/BillView.tsx` holds the people state, computes the shares and renders
the loaded bill.

**The two loading states carry no criterion, on purpose.** `Loading saved bills` and
`Loading bill` are what a skeleton shows while its fetch cut is open, so a criterion
asserting either one would be green on an empty skeleton and would grade nothing. They
are covered indirectly instead: every criterion that reads a card, a bill field or a
share row can only pass once its screen has left `loading`. `not-found` is graded by
`c-2-5`. Every other element in the two testid tables is read by at least one
criterion, and the three non-testid affordances are graded too: the card link by
`c-1-4`, the back link by `c-2-5`, and the two stepper buttons by every session-3
criterion that clicks them.

## Sessions

Session 1 finishes the list screen, session 2 opens one bill and works out its tip,
session 3 is the re-split. One milestone each, and each session ends with something a
student can run.

**Four rules the final code follows, so the generated skeleton behaves.**

1. A cut point is a block inside a function, and the code around it compiles while the
   block is a hint comment. No cut removes a declaration that code outside it uses:
   where a block produces a value the code below it reads, the variable is declared
   above the opening marker and the block assigns to it. `cut-list-cards` assigns its
   card elements to a `ReactNode[]` named `cards` declared above the marker, and the
   component's `return` renders that variable; `cut-bill-shares` assigns to the
   `shares` array declared above its marker.
2. No cut ever contains its function's only `return`. Where a block produces the return
   value, the value is declared above the opening marker with a typed fallback and the
   `return` is the last statement of the function, below the closing marker:
   `return bills` after an initialising `let bills: Bill[] = []` in `readAllBills`,
   `return bill` after `let bill: Bill | null = null` in `findBill`, `return tip` after
   `let tip = 0` in `tipPaise`, and `return shares` after `let shares: number[] = []`
   in `splitPaise`. **The two route handlers follow the same shape:** each declares
   `let body: unknown = { error: 'not implemented' }` and `let status = 501` above its
   opening marker, its cut block assigns to `body` and to `status`, and
   `return Response.json(body, { status })` is the last statement of the function,
   below the closing marker. No `return` sits inside a marker pair anywhere in the
   project, and the finished code has no unreachable statement. 501 belongs to the
   skeleton alone: in the finished project every block is written and the endpoints
   answer only the statuses in the table above.
3. Each fallback fails the criteria it should. `bills = []` in `readAllBills` fails
   `c-1-1` and `c-1-2`; the 501 body fails every endpoint criterion; `tip = 0` makes
   `bill-tip-amount` read `₹0.00` and `bill-grand-total` equal `bill-total`, which
   fails `c-2-4` and `c-2-6` while correctly leaving `c-2-3` green on the stored total;
   `shares = []` renders no `share-row` and no `What each person owes` heading, which
   fails every session-3 criterion that counts a row; and a `setPeopleClamped` that
   does nothing leaves `people-count` on the stored 4, which fails `c-3-2`, `c-3-3`,
   `c-3-4`, `c-3-5` and `c-3-6`.
4. Each cut id appears exactly once in the final code, between its markers.

**How a criterion names its cuts.** One convention, applied to all 17 criteria: a
criterion lists every cut whose block must be filled for its assertion to hold, cuts
from earlier sessions included. Fill all of them and the criterion is green; leave any
of them open and it is not proven. A cut whose block the criterion renders but does not
assert on is not listed - `c-3-6` reads only `people-count`, so it does not list
`cut-money-split`.

**Two criteria that a subset already satisfies.** `c-2-2` and `c-2-5` both assert the
404 path, and `findBill`'s rule-2 fallback is `bill = null` - the same answer a real
miss gives. Fill `cut-api-bill-get` and `cut-bill-fetch` and both go green with
`cut-store-read-all` and `cut-store-find-one` still open, because a store that finds
nothing and a store that correctly finds nothing are indistinguishable from outside.
`Bill | null` admits no other typed fallback, so this is recorded rather than fixed:
session 2 is still graded correctly as a whole, because `c-2-1` and `c-2-3` both need
the real lookup. A per-cut checkpoint must pair `c-2-2` with `c-2-1`, and `c-2-5` with
`c-2-3`, and never present either one as proof on its own. Every other criterion in
this spec has been checked by hand against each of its cuts opened alone, and none is
satisfied while any listed cut is open.

**Session 2's weight.** Session 2 sits on both caps - six criteria and four cuts - and
ships `BillView.tsx` including a stepper that does not move until session 3. That is
deliberate. There is one skeleton for the whole project, so markup cannot be held back
per session; only cuts can, and moving the stepper's markup into a session-3 cut would
mean cutting JSX that teaches nothing. What was moved is the share list: its heading
and rows are gated on `shares.length`, so the only thing a session-2 student sees that
does not respond is the stepper, sitting on the bill's stored count. Session 3 opens by
making it move, which is the payoff the idea names. The alternative - a fourth session
holding `ep-bill-get` alone - doubles the departure from `idea.md` for one endpoint,
and is not worth it.

### Session 1 - The saved bills

**Goal.** Serve every saved bill from the JSON store through a route handler and
render one card per bill on the list screen.

**Teaches.** Route handlers in the App Router; reading a JSON file on the server with
node fs; typing a response with a shared TypeScript type; fetching into React state
with useEffect; rendering a list with map and keys; printing an integer paise amount
as rupees.

**Builds.** `ep-bills-list`, `sc-list`.

**Acceptance criteria.**

- `c-1-1` GET /api/bills returns 200 with a JSON array of the 6 seed bills — cuts
  `cut-store-read-all`, `cut-api-bills-list`
- `c-1-2` GET /api/bills returns a JSON array of 6 bills, each with an id, a place, a
  date, a totalPaise integer, a tipPercent integer and a people integer — cuts
  `cut-store-read-all`, `cut-api-bills-list`
- `c-1-3` sc-list renders one bill-card element per bill, 6 of them for the 6 seed
  bills — cuts `cut-store-read-all`, `cut-api-bills-list`, `cut-list-fetch`,
  `cut-list-cards`
- `c-1-4` sc-list renders a bill-card element that is a link to /bills/anand-bhavan,
  whose card-place element reads Anand Bhavan, whose card-date element reads
  2026-03-14, whose card-total element reads ₹1240.00 and whose card-people element
  reads Split 4 ways — cuts `cut-store-read-all`, `cut-api-bills-list`,
  `cut-list-fetch`, `cut-list-cards`
- `c-1-5` sc-list renders the 6 bill-card elements in the order the endpoint returns
  them, the card-place element of the first reading Anand Bhavan and the card-place
  element of the last reading Kurry Kulture — cuts `cut-store-read-all`,
  `cut-api-bills-list`, `cut-list-fetch`, `cut-list-cards`

`c-1-2` pins the count of 6 as well as the fields. A criterion that only checked the
fields of each element returned would be green on the empty array an unfilled
`cut-store-read-all` produces, and would certify a store that was never written.

**Cut points.**

- `cut-store-read-all` in `lib/store.ts` — Read the bills JSON file from disk with
  node's fs module, building its path from the process working directory, and put
  every bill in the file into the bills array declared above, keeping the order the
  file stores them in.
- `cut-api-bills-list` in `app/api/bills/route.ts` — Put every bill the store holds
  into the response body, and set the status to 200.
- `cut-list-fetch` in `app/page.tsx` — Ask the bills endpoint for the list, and when
  the reply is a 200 put the array it answers with into the bills state and move the
  status to loaded.
- `cut-list-cards` in `app/page.tsx` — Turn the bills array into one bill-card element
  per bill, in the order of the array, each one a link to that bill's page holding its
  place in a card-place element, its stored date string in a card-date element, its
  total formatted as rupees in a card-total element, and the word Split, its stored
  people count and the word ways in a card-people element; assign that array of card
  elements to the cards array declared above.

### Session 2 - One bill, tip included

**Goal.** Open one bill at its own route with its total and its tip worked out in
whole paise, and answer 404 for an id the store does not hold.

**Teaches.** Dynamic route segments for pages and route handlers; returning 404 with a
JSON body from a route handler; reading the route id with useParams; branching on the
response status in a client component; rendering a not-found state; percentage
arithmetic on integers with half-up rounding, so money never touches a float.

**Builds.** `ep-bill-get`, `sc-bill`.

**Acceptance criteria.**

- `c-2-1` GET /api/bills/anand-bhavan returns 200 with that bill, its totalPaise
  reading 124000, its tipPercent reading 10 and its people reading 4 — cuts
  `cut-store-read-all`, `cut-store-find-one`, `cut-api-bill-get`
- `c-2-2` GET /api/bills/not-a-bill returns 404 with a JSON body holding an error
  field — cuts `cut-store-read-all`, `cut-store-find-one`, `cut-api-bill-get`. Pair
  this one with `c-2-1`: it goes green with `cut-store-find-one` still open, because
  `findBill`'s null fallback and a real miss look the same.
- `c-2-3` sc-bill displays Anand Bhavan in its bill-place element, 2026-03-14 in its
  bill-date element, ₹1240.00 in its bill-total element, 10% in its bill-tip-percent
  element and Split 4 ways when saved in its bill-saved-people element at the route
  /bills/anand-bhavan — cuts `cut-store-read-all`, `cut-store-find-one`,
  `cut-api-bill-get`, `cut-bill-fetch`
- `c-2-4` sc-bill displays ₹124.00 in its bill-tip-amount element and ₹1364.00 in its
  bill-grand-total element at the route /bills/anand-bhavan, which is stored as 124000
  paise with a tip of 10 percent — cuts `cut-store-read-all`, `cut-store-find-one`,
  `cut-api-bill-get`, `cut-bill-fetch`, `cut-money-tip`
- `c-2-5` sc-bill displays the message Bill not found and a link whose accessible name
  is Back to saved bills and whose href is / at the route /bills/not-a-bill — cuts
  `cut-store-read-all`, `cut-store-find-one`, `cut-api-bill-get`, `cut-bill-fetch`.
  Pair this one with `c-2-3`, for the same reason as `c-2-2`.
- `c-2-6` sc-bill displays ₹61.29 in its bill-tip-amount element and ₹936.79 in its
  bill-grand-total element at the route /bills/kabab-junction, which is stored as
  87550 paise with a tip of 7 percent, where the exact tip is 6128.5 paise and rounds
  up — cuts `cut-store-read-all`, `cut-store-find-one`, `cut-api-bill-get`,
  `cut-bill-fetch`, `cut-money-tip`

`c-2-6` is the criterion that catches a tip that truncates instead of rounding half
up. 87550 paise at 7 percent is 6128.5 paise exactly; truncating gives `₹61.28` and a
grand total of `₹936.78`, both of which the criterion rejects.

**Cut points.**

- `cut-store-find-one` in `lib/store.ts` — Put the bill whose id matches the one asked
  for into the bill value declared above, leaving it null when the store holds no bill
  with that id.
- `cut-api-bill-get` in `app/api/bills/[id]/route.ts` — Put the bill into the response
  body and set the status to 200 when the store finds it; when the store finds nothing,
  put an object holding an error field into the response body and set the status to
  404.
- `cut-bill-fetch` in `app/bills/[id]/page.tsx` — Ask the endpoint for the bill named
  in the route; on a 200 reply put the bill into state and move the status to loaded,
  and on a 404 reply move the status to not-found.
- `cut-money-tip` in `lib/money.ts` — Work out the tip as the total times the tip
  percentage divided by a hundred, rounded half up, and put it into the whole-paise
  tip value declared above, without turning any value into rupees along the way.

### Session 3 - Re-split the bill

**Goal.** Compute what each person owes from the people count held in React state, so
the shares on screen always add back up to the total with tip.

**Teaches.** Deriving what is on screen from state instead of from the server; integer
division and remainder as a way to split money without losing a paisa; handing the
leftover paise to the first people in the list; clamping a value inside a state setter;
recomputing from the stored bill on every render rather than from what is on screen, so
a value survives a round trip.

**Builds.** No new endpoint and no new screen. Extends `sc-bill`: the share rows start
appearing and the stepper starts working.

Every session-3 criterion opens at `/bills/anand-bhavan`, which is stored as
124000 paise, a tip of 10 percent and a split 4 ways. Its total with tip is 136400
paise, and every criterion reaches its people count by clicking the stepper from 4.

**Acceptance criteria.**

- `c-3-1` sc-bill renders one share-row element per person, 4 at the route
  /bills/anand-bhavan, whose texts are Person 1 ₹341.00, Person 2 ₹341.00, Person 3
  ₹341.00 and Person 4 ₹341.00 in that order — cuts `cut-store-read-all`,
  `cut-store-find-one`, `cut-api-bill-get`, `cut-bill-fetch`, `cut-money-tip`,
  `cut-money-split`, `cut-bill-shares`
- `c-3-2` sc-bill displays 3 in its people-count element and renders 3 share-row
  elements after the Fewer people button is clicked 1 time at the route
  /bills/anand-bhavan, which is stored as a split 4 ways — cuts `cut-store-read-all`,
  `cut-store-find-one`, `cut-api-bill-get`, `cut-bill-fetch`, `cut-money-split`,
  `cut-bill-shares`, `cut-bill-people`
- `c-3-3` sc-bill renders share-row elements reading Person 1 ₹454.67, Person 2
  ₹454.67 and Person 3 ₹454.66 after the Fewer people button is clicked 1 time at the
  route /bills/anand-bhavan, where 136400 paise across 3 people leaves 2 paise over —
  cuts `cut-store-read-all`, `cut-store-find-one`, `cut-api-bill-get`,
  `cut-bill-fetch`, `cut-money-tip`, `cut-money-split`, `cut-bill-shares`,
  `cut-bill-people`
- `c-3-4` sc-bill displays 3 in its people-count element after the Fewer people button
  is clicked 1 time at the route /bills/anand-bhavan, and then displays 4 in its
  people-count element and renders 4 share-row elements whose texts are Person 1
  ₹341.00, Person 2 ₹341.00, Person 3 ₹341.00 and Person 4 ₹341.00 after the More
  people button is clicked 1 time — cuts `cut-store-read-all`, `cut-store-find-one`,
  `cut-api-bill-get`, `cut-bill-fetch`, `cut-money-tip`, `cut-money-split`,
  `cut-bill-shares`, `cut-bill-people`
- `c-3-5` sc-bill displays 1 in its people-count element and renders 1 share-row
  element reading Person 1 ₹1364.00 after the Fewer people button is clicked 4 times
  at the route /bills/anand-bhavan, which is stored as a split 4 ways — cuts
  `cut-store-read-all`, `cut-store-find-one`, `cut-api-bill-get`, `cut-bill-fetch`,
  `cut-money-tip`, `cut-money-split`, `cut-bill-shares`, `cut-bill-people`
- `c-3-6` sc-bill displays 20 in its people-count element after the More people button
  is clicked 17 times at the route /bills/anand-bhavan, which is stored as a split 4
  ways — cuts `cut-store-read-all`, `cut-store-find-one`, `cut-api-bill-get`,
  `cut-bill-fetch`, `cut-bill-people`

`c-3-4` is the round-trip criterion, and it asserts the trip out as well as the trip
back: 4 to 3 has to show on `people-count` before the return to 4 counts for anything.
Without that first assertion a stepper that never moves would satisfy it, because a
bill that stays on 4 renders exactly the four ₹341.00 rows the end state expects.

`c-3-5` walks 4 → 3 → 2 → 1 and then asks for 0, so the fourth click is the one the
lower clamp answers, and the single share is the whole total with tip. `c-3-6` walks 4
up to 20 in 16 clicks and then asks for 21, so the seventeenth click is the one the
upper clamp answers. `c-3-3` is the criterion that catches a split that drops or
invents a paisa: 45467 + 45467 + 45466 is 136400, while three equal shares of ₹454.66
or ₹454.67 are not.

**Cut points.**

- `cut-money-split` in `lib/money.ts` — Fill the shares array declared above with one
  share per person: give every person the amount divided by the number of people
  ignoring the remainder, then give one extra paisa each to as many people from the
  start of the list as there are paise left over.
- `cut-bill-shares` in `app/bills/[id]/BillView.tsx` — Work out what each person owes
  by splitting the total with tip across the number of people currently held in state,
  and assign that array of shares to the shares variable declared above.
- `cut-bill-people` in `app/bills/[id]/BillView.tsx` — Put the requested number of
  people into the people state, holding it at 1 when it would drop below 1 and at 20
  when it would climb above 20.
