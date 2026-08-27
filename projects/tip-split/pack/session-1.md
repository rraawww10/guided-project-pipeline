# Session 1 - The saved bills

**Time:** 40 minutes as planned below. The honest total for the material is 45.
The plan buys the 5 minutes back in two places, both named under
**Before you start**. If you skip either one, this session runs to 45.

**Students start from:** a skeleton that builds and runs. `/` shows the heading
`Saved bills` and the message `Loading saved bills`, and sits there forever.
`GET /api/bills` answers 501 with `{"error":"not implemented"}`.

**Students end with:** `/` showing 6 cards, one per saved bill, each card a link
to that bill's page carrying its place, date, total in rupees and people count.
`GET /api/bills` answers 200 with all 6 bills.

## What they learn

In this order:

1. A route handler in the App Router. A file called `route.ts` under `app/api/`,
   exporting a function named for the HTTP method.
2. Reading a JSON file on the server with node's `fs`, and building the path from
   `process.cwd()`.
3. Typing what comes back with a shared type, `Bill` from `lib/types.ts`, so the
   handler and the screen agree.
4. Fetching into React state from inside `useEffect`.
5. Rendering a list with `map`, and why each element needs a `key`.
6. Printing a whole number of paise as rupees with `formatRupees`.

## Before you start

- **`npm install` must already have been run** in every student's `skeleton/`
  folder. This is the first of the two places the 5 minutes comes from. Doing it
  in class costs 5 to 8 minutes and teaches nothing.
- Have `npm run dev` running on your machine, on `http://localhost:3000`.
- Have these four files open in tabs, in this order:
  `lib/store.ts`, `app/api/bills/route.ts`, `app/page.tsx`, `data/bills.json`.
- Have a browser tab on `http://localhost:3000/api/bills` so students can see the
  501 before you fix it.
- **You type the `Link` wrapper and the first card field only.** Students type the
  other three fields while you circulate. This is the second place the 5 minutes
  comes from. Do not type all 21 lines of card markup at the front of the room.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Show the finished app for 30 seconds: the list, one card clicked, the stepper moving. Say "today is the list and the endpoint behind it". Then open the skeleton, run it, show `Loading saved bills` stuck, and show `/api/bills` answering 501. Walk the file map in the tabs you have open, and say the rule: **fill the block between the comments, never touch the `return` below it.** |
| 4-11 | `cut-store-read-all` in `lib/store.ts`. Live-code it. Teach `process.cwd()`, `path.join`, `readFileSync`, `JSON.parse`, and why this is not an `import`. |
| 11-16 | `cut-api-bills-list` in `app/api/bills/route.ts`. Live-code it. Reload `/api/bills` in the browser: 6 bills. **c-1-1 and c-1-2 are green here.** |
| 16-23 | `cut-list-fetch` in `app/page.tsx`. Live-code it. The screen leaves `Loading saved bills` and goes blank - that is correct, and it sets up the next block. |
| 23-31 | `cut-list-cards` in `app/page.tsx`. You type the `Link` wrapper and `card-place`, out loud. Then stop typing and hand it over: "add `card-date`, `card-total` and `card-people` the same way". |
| 31-38 | Students finish the card. You circulate. Watch for the three things under **Where students get stuck**. Around minute 36, pull the room back for 60 seconds on the `key` warning in the console. |
| 38-40 | Everyone has 6 cards. Click one: it 404s or shows `Loading bill`. Say "that page is next session". |

## Cut points in this session

### cut-store-read-all - `lib/store.ts`:14

- **What students see:**

  ```ts
  // TODO(cut-store-read-all): Read the bills JSON file from disk with node's fs module, building its path from the process working directory, and put every bill in the file into the bills array declared above, keeping the order the file stores them in.
  ```

- **What they write:** three lines. Build the path to `data/bills.json` from the
  process working directory. Read that file as a UTF-8 string. Parse the string
  and assign the result to the `bills` array that is already declared above, typed
  as `Bill[]`. `fs` and `path` are already imported at the top of the file.

- **The finished block, for you:**

  ```ts
  const filePath = path.join(process.cwd(), 'data', 'bills.json')
  const contents = fs.readFileSync(filePath, 'utf8')
  bills = JSON.parse(contents) as Bill[]
  ```

  The whole function around it, already in their file:

  ```ts
  export function readAllBills(): Bill[] {
    let bills: Bill[] = []

    // the block goes here

    return bills
  }
  ```

- **Teach it like this:** "This code runs on the server, so it can open a file.
  `process.cwd()` is the folder the server was started from - the project root -
  and `path.join` glues the pieces on in a way that works on every operating
  system. `readFileSync` hands us a string, `JSON.parse` turns it into objects,
  and `as Bill[]` tells TypeScript what those objects are."

  Then the part that matters most: "You could write `import bills from
  '../../data/bills.json'` and the screen would look identical. Do not. An import
  is baked in when the app is built. Reading the file means that if I edit
  `bills.json` while the server is running, the next request sees the change."
  Prove it: change `Anand Bhavan` to `Anand Bhavan Annexe` in `data/bills.json`,
  reload `/api/bills`, change it back.

- **Passes when:** nothing on its own. It is half of `c-1-1` and `c-1-2`, which go
  green with the next cut.

### cut-api-bills-list - `app/api/bills/route.ts`:12

- **What students see:**

  ```ts
  // TODO(cut-api-bills-list): Put every bill the store holds into the response body, and set the status to 200.
  ```

- **What they write:** three lines. Call `readAllBills()` into a `Bill[]`, assign
  it to `body`, and set `status` to 200. `readAllBills` is already imported.

- **The finished block, for you:**

  ```ts
  const bills: Bill[] = readAllBills()
  body = bills
  status = 200
  ```

  The shape around it, already in their file:

  ```ts
  export async function GET(): Promise<Response> {
    // the return stays outside the markers, so the skeleton still compiles
    let body: unknown = { error: 'not implemented' }
    let status = 501

    // the block goes here

    return Response.json(body, { status })
  }
  ```

- **Teach it like this:** "A file called `route.ts` under `app/api/bills` becomes
  the URL `/api/bills`. The function you export is named after the HTTP method,
  so `GET` answers a GET. `Response.json` turns our array into a JSON body and
  sets the content type. We do not build the response ourselves - we set two
  variables and the line below sends them." Point at the 501 fallback: "that is
  what has been answering you all morning."

- **Passes when:** `c-1-1` and `c-1-2` go green. Show it in the browser at
  `/api/bills`: an array of 6 objects, `anand-bhavan` first.

### cut-list-fetch - `app/page.tsx`:17

- **What students see:**

  ```ts
  // TODO(cut-list-fetch): Ask the bills endpoint for the list, and when the reply is a 200 put the array it answers with into the bills state and move the status to loaded.
  ```

- **What they write:** a `fetch` of `/api/bills`. When, and only when, the reply's
  status is 200, read the JSON body and put it into `bills` state and move
  `status` to `'loaded'`. The `useEffect` and its empty `[]` are already there.

- **The finished block, for you:**

  ```ts
  fetch('/api/bills').then((response) => {
    if (response.status === 200) {
      response.json().then((data: Bill[]) => {
        setBills(data)
        setStatus('loaded')
      })
    }
  })
  ```

  The state it writes into, already in their file:

  ```ts
  const [bills, setBills] = useState<Bill[]>([])
  const [status, setStatus] = useState<'loading' | 'loaded'>('loading')
  ```

- **Teach it like this:** "The component renders first and asks the server after.
  `useEffect` with an empty `[]` means run this once, after the first render. The
  fetch comes back later, `setBills` puts the answer into state, and setting state
  is what makes React render again - this time with data." Then the status check:
  "Why `if (response.status === 200)`? Because before you wrote the handler, this
  endpoint answered 501 with an object, not an array. If we had put that into
  `bills` the screen would have crashed on `bills.map`. Check the status before
  you trust the body."

- **Passes when:** nothing yet, and the screen goes **blank below the heading**.
  Say this out loud before they panic: "`status` is now `loaded`, so we render the
  grid instead of the loading message, and the grid is empty because `cards` is
  still an empty array. Next block fills it."

### cut-list-cards - `app/page.tsx`:31

- **What students see:**

  ```ts
  // TODO(cut-list-cards): Turn the bills array into one bill-card element per bill, in the order of the array, each one a link to that bill's page holding its place in a card-place element, its stored date string in a card-date element, its total formatted as rupees in a card-total element, and the word Split, its stored people count and the word ways in a card-people element; assign that array of card elements to the cards array declared above.
  ```

- **What they write:** `bills.map(...)` producing one `Link` per bill, assigned to
  the `cards` array declared above. Each `Link` has `href` `/bills/` plus the
  bill's id, `data-testid="bill-card"`, and four `div`s inside it carrying
  `card-place`, `card-date`, `card-total` and `card-people`. The total goes
  through `formatRupees`. The people line reads the word `Split`, then the count,
  then the word `ways`. `Link`, `formatRupees` and `styles` are already imported.

- **The finished block, for you:**

  ```tsx
  cards = bills.map((bill) => (
    <Link
      key={bill.id}
      href={`/bills/${bill.id}`}
      className={styles.card}
      data-testid="bill-card"
    >
      <div className={styles.cardPlace} data-testid="card-place">
        {bill.place}
      </div>
      <div className={styles.cardDate} data-testid="card-date">
        {bill.date}
      </div>
      <div className={styles.cardTotal} data-testid="card-total">
        {formatRupees(bill.totalPaise)}
      </div>
      <div className={styles.cardPeople} data-testid="card-people">
        Split {bill.people} ways
      </div>
    </Link>
  ))
  ```

- **Teach it like this:** type the `Link` opening tag and the `card-place` div,
  saying: "`map` turns a list of six bills into a list of six pieces of markup.
  The card *is* the link - we are not putting a link inside a card, we are making
  the whole card clickable. `data-testid` is how the tests find this element;
  class names get scrambled by CSS modules, so tests cannot use them."

  Then hand it over: "three more fields, same pattern. The total is not
  `bill.totalPaise` - that is 124000. Wrap it in `formatRupees`."

  At minute 36, pull the room together for the `key`: open the console, show
  `Warning: Each child in a list should have a unique "key" prop`. "React needs a
  stable name for each row so it can tell them apart when the list changes. The
  bill's id is already unique - use it. No test checks this. The console does."

- **Passes when:** `c-1-3`, `c-1-4` and `c-1-5` go green - 6 cards, in file order,
  and the first one reads `Anand Bhavan`, `2026-03-14`, `₹1240.00`, `Split 4 ways`
  and links to `/bills/anand-bhavan`.

## Where students get stuck

- **"It still says Loading saved bills"** - `cut-api-bills-list` is not saved, so
  the endpoint is still answering 501 and the fetch's `if` never fires. Say: "open
  `/api/bills` in a browser tab. If you see `not implemented`, the problem is in
  the handler, not the screen."

- **"`bills.map is not a function`"** - they dropped the status check and put the
  501 error object into state. Say: "you fetched the error body. Put the
  `if (response.status === 200)` back."

- **"`Module not found: Can't resolve 'fs'`" or "You're importing a component that
  needs fs"** - they imported `lib/store` into `app/page.tsx` to skip the fetch.
  Say: "`page.tsx` starts with `'use client'` - it runs in the browser, and a
  browser has no filesystem. The only way the screen gets data is by asking the
  endpoint."

- **"`ENOENT: no such file or directory ... data/bills.json`"** - they started
  `npm run dev` from the wrong folder, so `process.cwd()` is not the project root.
  Say: "stop the server, `cd` into the folder that has `package.json`, start it
  again." This is the moment `process.cwd()` becomes real - use it.

- **The card shows `₹124000.00` or `124000`** - `formatRupees` missing, or fed the
  wrong thing. Say: "everything in the file is paise. `formatRupees` is the only
  thing in this project that knows about the decimal point."

- **The card reads `Split4 ways` or `Split 4ways`** - JSX ate the spaces because
  they wrote `Split{bill.people}ways`. Say: "the spaces have to be real text.
  Write `Split {bill.people} ways` with spaces outside the braces."

- **The whole app stops building, red screen, `TS2355`** - they deleted or moved
  `return bills`, `return cards` or the `Response.json` line. Say: "the return
  lives outside the block. Put it back exactly where it was and only fill the
  space between the comments."

- **Everything is green but the store starts with `import bills from ...`** - a
  fast student who found the shortcut. This is the one thing no test catches. Say:
  "your tests pass and you skipped the lesson. Show me `/api/bills` picking up an
  edit I make to the file right now." Then edit the file.

## Check before moving on

`http://localhost:3000/` shows 6 cards, the first reading `Anand Bhavan`,
`2026-03-14`, `₹1240.00`, `Split 4 ways`, and the last reading `Kurry Kulture`.
Clicking a card changes the URL to `/bills/anand-bhavan`. It is fine that the
page it lands on shows only `Loading bill` - that is session 2's first minute.
