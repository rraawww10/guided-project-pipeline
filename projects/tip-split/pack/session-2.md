# Session 2 - One bill, tip included

**Time:** 40 minutes. It fits, but there is no slack in it. This session carries
the longest list of new ideas in the project, so keep the 0-4 recap to four
minutes and do not let the 404 discussion run.

**Students start from:** the finished session 1. `/` shows 6 cards and clicking
one goes to `/bills/anand-bhavan`, which sits on `Loading bill` forever.
`GET /api/bills/anand-bhavan` answers 501.

**Students end with:** `/bills/anand-bhavan` showing the place, the date, the
bill, the tip percentage, the tip in rupees and the total with tip, plus the line
`Split 4 ways when saved`. `/bills/not-a-bill` shows `Bill not found` and a link
back. `GET /api/bills/anand-bhavan` answers 200 with the bill;
`GET /api/bills/not-a-bill` answers 404 with an error body.

## What they learn

In this order:

1. A dynamic route segment, `[id]`, used twice: once for a page and once for a
   route handler.
2. Returning a 404 with a JSON body from a route handler - the status and the
   body are two separate decisions.
3. Reading the id off the route in a client component with `useParams`.
4. Branching on the response status in the browser: 200, 404, and neither.
5. Rendering a not-found state.
6. Percentage arithmetic on integers with half-up rounding, so money never
   touches a float.

## Before you start

- `npm run dev` running, `/bills/anand-bhavan` open in the browser showing
  `Loading bill`.
- A second browser tab on `http://localhost:3000/api/bills/anand-bhavan`, showing
  the 501.
- Four files open in tabs, in this order: `lib/store.ts`,
  `app/api/bills/[id]/route.ts`, `app/bills/[id]/page.tsx`, `lib/money.ts`.
- Have `app/bills/[id]/BillView.tsx` open too, but do **not** edit it today.
  Students will ask about the minus and plus buttons in it. See the last stuck
  point below for the answer.
- Students type along with you through the live-coding blocks. The 32-38 block is
  where the ones who fell behind catch up.
- On the board before you start, write: `87550 x 7 = 612850`, and under it
  `612850 + 50 = 612900`, and under that `612900 / 100 = 6129`. You will use it
  at minute 25.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Recap: "the endpoint gave us all six bills; today we ask for one." Show `/bills/anand-bhavan` stuck on `Loading bill` and `/api/bills/anand-bhavan` answering 501. Show the two new `[id]` folders in the tree and say the rule once: **a folder in square brackets means that part of the URL is a value, not a name.** |
| 4-8 | `cut-store-find-one` in `lib/store.ts`. One line. Live-code it. Teach `find` and the `?? null`. |
| 8-16 | `cut-api-bill-get` in `app/api/bills/[id]/route.ts`. Live-code it. Two branches, two statuses. Reload both API tabs: 200 with the bill, 404 with an error. **c-2-1 and c-2-2 green.** |
| 16-25 | `cut-bill-fetch` in `app/bills/[id]/page.tsx`. Live-code it. The bill screen fills in, and `/bills/not-a-bill` shows `Bill not found`. **c-2-3 and c-2-5 green.** Point at `Tip amount ₹0.00` and say "that is the last thing today." |
| 25-32 | `cut-money-tip` in `lib/money.ts`. One line, and the most careful five minutes in the project. Use the board. **c-2-4 and c-2-6 green.** |
| 32-38 | Students catch up. You circulate. The two you will see most are the `params` mistake and the tip that is one paisa low - both are below. |
| 38-40 | Open `/bills/kabab-junction` together and read `₹61.29` off the screen. Say: "the minus and plus buttons under that do nothing, and there are no per-person rows yet. That is the whole of next session." |

## Cut points in this session

### cut-store-find-one - `lib/store.ts`:27

- **What students see:**

  ```ts
  // TODO(cut-store-find-one): Put the bill whose id matches the one asked for into the bill value declared above, leaving it null when the store holds no bill with that id.
  ```

- **What they write:** one line. Search the `bills` array, already read for them
  on the line above, for the bill whose `id` equals the `id` argument, and assign
  it to `bill`. When there is no match, `bill` must be `null`.

- **The finished block, for you:**

  ```ts
  bill = bills.find((candidate) => candidate.id === id) ?? null
  ```

  The function around it, already in their file:

  ```ts
  export function findBill(id: string): Bill | null {
    const bills = readAllBills()
    let bill: Bill | null = null

    // the block goes here

    return bill
  }
  ```

- **Teach it like this:** "`find` walks the array and hands back the first item the
  test says yes to. If nothing matches it hands back `undefined` - and our type
  says `Bill | null`, not `Bill | undefined`. `?? null` says: if the left side is
  `undefined` or `null`, use `null`. One word of type discipline, and every caller
  now has exactly one thing to check for."

  Say the design point too: "`findBill` calls `readAllBills`. It re-reads the file
  every time. That is on purpose - the store is one file and we never cache it, so
  an edit on disk is live immediately."

- **Passes when:** nothing on its own, and this is worth knowing: `c-2-2` and
  `c-2-5` will go green later **even if this block is empty**, because a store that
  found nothing and a store that never looked give the same answer. Grade this
  block by `c-2-1` and `c-2-3`, never by the 404 tests.

### cut-api-bill-get - `app/api/bills/[id]/route.ts`:17

- **What students see:**

  ```ts
  // TODO(cut-api-bill-get): Put the bill into the response body and set the status to 200 when the store finds it; when the store finds nothing, put an object holding an error field into the response body and set the status to 404.
  ```

- **What they write:** eight lines. Call `findBill(id)` into a `Bill | null`. If it
  is `null`, set `body` to an object with an `error` field and `status` to 404.
  Otherwise set `body` to the bill and `status` to 200. `findBill` is imported and
  `id` is already unpacked for them on line 11.

- **The finished block, for you:**

  ```ts
  const bill: Bill | null = findBill(id)
  if (bill === null) {
    body = { error: `no bill with the id ${id}` }
    status = 404
  } else {
    body = bill
    status = 200
  }
  ```

  The handler around it, already in their file - do not let anyone retype this
  signature:

  ```ts
  export async function GET(
    request: Request,
    { params }: { params: Promise<{ id: string }> },
  ): Promise<Response> {
    const { id } = await params

    // the return stays outside the markers, so the skeleton still compiles
    let body: unknown = { error: 'not implemented' }
    let status = 501

    // the block goes here

    return Response.json(body, { status })
  }
  ```

- **Teach it like this:** "The folder is called `[id]`, so Next hands us whatever
  is in that slot of the URL. In Next 15 the params arrive as a promise, which is
  why the line above says `await params`. That line is written for you - leave it
  alone." Then the real lesson: "Two things come back from an endpoint: a body and
  a status. They are separate. A 404 is not an empty answer - it is a real answer
  with a real body that says what went wrong. The browser is going to read the
  status number, not the body, to decide what to show."

- **Passes when:** `c-2-1` and `c-2-2` go green. Show both in the browser:
  `/api/bills/anand-bhavan` gives the bill, `/api/bills/not-a-bill` gives the
  error. Open the network tab once, just to show the red 404 next to the request.

### cut-bill-fetch - `app/bills/[id]/page.tsx`:18

- **What students see:**

  ```ts
  // TODO(cut-bill-fetch): Ask the endpoint for the bill named in the route; on a 200 reply put the bill into state and move the status to loaded, and on a 404 reply move the status to not-found.
  ```

- **What they write:** ten lines. Fetch `/api/bills/` plus the `id`. On a 200, read
  the body and put it into `bill` state, then move `status` to `'loaded'`. On a
  404, move `status` to `'not-found'`. Nothing else. The `useEffect` and its `[id]`
  dependency array are already there.

- **The finished block, for you:**

  ```ts
  fetch(`/api/bills/${id}`).then((response) => {
    if (response.status === 200) {
      response.json().then((data: Bill) => {
        setBill(data)
        setStatus('loaded')
      })
    } else if (response.status === 404) {
      setStatus('not-found')
    }
  })
  ```

  The state and the id, already in their file:

  ```ts
  const { id } = useParams<{ id: string }>()
  const [bill, setBill] = useState<Bill | null>(null)
  const [status, setStatus] = useState<'loading' | 'loaded' | 'not-found'>('loading')
  ```

- **Teach it like this:** "`useParams` is how the browser side reads the same `id`
  the handler read on the server side. Same URL, two readers." Then the status
  branch: "Three states, and the fetch decides between them. 200 means we have a
  bill: store it and say loaded. 404 means there is no such bill: say not-found -
  and notice we do not store anything, because there is nothing to store. Anything
  else, we do nothing at all, and the screen stays on `Loading bill`. That is not
  laziness - a 500 from a broken server should not be told to the user as `Bill not
  found`."

  Point at the dependency array: "`[id]` not `[]`. If the id in the URL changes,
  this effect has to run again."

- **Passes when:** `c-2-3` and `c-2-5` go green. `/bills/anand-bhavan` shows
  `Anand Bhavan`, `2026-03-14`, `₹1240.00`, `10%` and `Split 4 ways when saved`.
  `/bills/not-a-bill` shows `Bill not found` and the `Back to saved bills` link.
  `Tip amount` reads `₹0.00` and `Total with tip` equals the bill - that is the
  next block, and saying so now stops six hands going up.

### cut-money-tip - `lib/money.ts`:17

- **What students see:**

  ```ts
  // TODO(cut-money-tip): Work out the tip as the total times the tip percentage divided by a hundred, rounded half up, and put it into the whole-paise tip value declared above, without turning any value into rupees along the way.
  ```

- **What they write:** one line. Multiply the total in paise by the percentage, add
  half of a hundred, then floor the division by a hundred. Assign it to `tip`.

- **The finished block, for you:**

  ```ts
  tip = Math.floor((totalPaise * tipPercent + 50) / 100)
  ```

  The function around it, already in their file:

  ```ts
  /** The tip in whole paise, rounded half up. */
  export function tipPaise(totalPaise: number, tipPercent: number): number {
    let tip = 0

    // the block goes here

    return tip
  }
  ```

- **Teach it like this:** use the board you prepared. "Kabab Junction is 87550
  paise at 7 percent. 87550 times 7 is 612850. Divide by 100 and the true tip is
  6128.5 paise - half a paisa, and there is no such coin. We have to choose. Half
  up means 6128.5 becomes 6129."

  Then the trick: "Adding 50 before dividing by 100 is the same as adding a half
  before rounding down. 612850 plus 50 is 612900, divided by 100 is exactly 6129,
  and `Math.floor` leaves it alone. If the leftover had been less than half,
  adding 50 would not have pushed it over the line and the floor would still have
  taken it down."

  And the rule of the project, one more time: "Every number in that line is a
  whole number of paise. We never make it into rupees and back. `Math.round(total
  * percent / 100)` looks like the same thing and is not, because the division
  happens first and gives you a float."

  Where the tip goes is already written in `BillView.tsx`, outside every block:

  ```ts
  const grandTotalPaise = bill.totalPaise + tipPaise(bill.totalPaise, bill.tipPercent)
  ```

- **Passes when:** `c-2-4` and `c-2-6` go green. `/bills/anand-bhavan` reads
  `₹124.00` and `₹1364.00`. `/bills/kabab-junction` reads `₹61.29` and `₹936.79`.
  Check kabab-junction on screen with the class - it is the one that catches a
  wrong answer.

## Where students get stuck

- **"Type error on `params`" or "`params` should be awaited"** - they retyped the
  handler signature from memory in the Next 14 shape, `{ params }: { params: { id:
  string } }`. This does not just fail one test: `npm run build` refuses the route
  type and the whole project stops building. Say: "the signature is already
  written. Undo back to it. `params` is a promise in Next 15 and the `await` line
  above your block is doing that for you."

- **Every test is red at once, not just one** - almost always the point above, or a
  stray character. Say: "read the terminal, not the browser. One TypeScript error
  anywhere stops the build, and then nothing passes."

- **"The bill page still says Loading bill"** - `cut-api-bill-get` is not saved, so
  the endpoint answers 501, which is neither 200 nor 404, so the screen never
  leaves loading. Say: "open the API URL directly. If it says `not implemented`,
  the screen is behaving correctly and the handler is the problem."

- **"`/bills/not-a-bill` says Loading bill instead of Bill not found"** - they
  wrote the 200 branch and skipped the `else if` for 404. Say: "nothing is telling
  the screen the bill is missing. The 404 branch is what moves the status."

- **The 404 page is blank or crashes with "cannot read place of null"** - they set
  `status` to `'loaded'` on the 404 path too, so `BillView` gets a null bill. Say:
  "`loaded` means we have a bill. On a 404 we do not. Use `not-found`."

- **"Tip amount says ₹0.00"** - `cut-money-tip` is still open. That is exactly what
  the fallback `let tip = 0` produces, and it is the expected screen between
  minutes 16 and 25.

- **"My tip is one paisa less than yours"** - they wrote `Math.floor(totalPaise *
  tipPercent / 100)`, which truncates. Kabab Junction reads `₹61.28` and the grand
  total `₹936.78`. Say: "you threw the half paisa away instead of rounding it up.
  Where did the 50 go?"

- **"I get ₹61.29 with `Math.round` too, so why the 50?"** - a good student. Say:
  "you are right that it agrees here. `Math.round` on a float is fine until the
  float is not exact, and once a money value has been through a float you cannot
  prove it any more. The integer version cannot be wrong. That is worth one extra
  `+ 50`." Do not spend more than 60 seconds on this.

- **"The minus and plus buttons do nothing"** and **"where are the per-person
  rows?"** - both correct. The stepper markup ships from today, but the block that
  makes it move is next session, and the rows are hidden until there is something
  to show. Say: "you are looking at next session's work, sitting there switched
  off. Do not go and fill it in - the arithmetic in it is the whole of Wednesday."

## Check before moving on

`/bills/kabab-junction` reads `Kabab Junction`, `2026-02-28`, `₹875.50`, `7%`,
`₹61.29`, `₹936.79` and `Split 3 ways when saved`. `/bills/not-a-bill` reads
`Bill not found` with a working `Back to saved bills` link. If the tip on that
page reads `₹61.28`, do not start session 3 - the split in session 3 is built on
the total with tip, and every share will be wrong by a paisa.
