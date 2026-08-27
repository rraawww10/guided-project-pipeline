# Session 3 - Re-split the bill

**Time:** 40 minutes. This one fits with a little room, which is deliberate - the
arithmetic in the middle of it needs the board and it needs questions.

**Students start from:** the finished session 2. `/bills/anand-bhavan` shows the
bill, the tip and the total with tip. The minus and plus buttons are there and do
nothing. There are no per-person rows and no `What each person owes` heading.

**Students end with:** four rows reading `Person 1 ₹341.00` down to `Person 4
₹341.00`. Clicking minus once gives three rows reading `₹454.67`, `₹454.67` and
`₹454.66`. Clicking plus once puts it back exactly as it was saved. The count
stops at 1 going down and at 20 going up, and both buttons stay clickable.

## What they learn

In this order:

1. Splitting money with integer division and remainder, so not one paisa is lost
   or invented.
2. Handing the leftover paise to the first people in the list, one each.
3. Deriving what is on screen from state, on every render, instead of asking the
   server.
4. Clamping a value inside the state setter, not with a `disabled` attribute.
5. Why recomputing from the stored bill - and never from what is already on
   screen - is what makes 4 to 3 to 4 land back on the saved split exactly.

## Before you start

- `npm run dev` running, `/bills/anand-bhavan` open. Click the minus button twice
  in front of them at minute 1 so they see it do nothing.
- Two files open in tabs, in this order: `lib/money.ts`, then
  `app/bills/[id]/BillView.tsx`.
- On the board before you start, write these three lines and leave them up for the
  whole session:

  ```
  136400 paise across 3 people
  136400 / 3 = 45466 each, remainder 2
  45467 + 45467 + 45466 = 136400
  ```

- Have a calculator open. Students will check you.
- Students type along. The 30-38 block is where the ones who fell behind catch up.

## The plan

| Minutes | What you do |
|---|---|
| 0-5 | Recap the total with tip: 124000 plus 12400 is 136400 paise. Click the dead stepper. Then set the problem with the board: "three people, 136400 paise. Everybody take 45466 and 2 paise are left on the table. Who gets them?" Take answers for one minute. Land on: the first two people, one each, because *somebody* has to and being first is a rule anyone can check. |
| 5-17 | `cut-money-split` in `lib/money.ts`. Live-code it, slowly. This is the block of the session. |
| 17-22 | `cut-bill-shares` in `app/bills/[id]/BillView.tsx`. One line. The rows appear. **c-3-1 green.** |
| 22-30 | `cut-bill-people` in `app/bills/[id]/BillView.tsx`. One line. The stepper starts working. **c-3-2 to c-3-6 green.** Do the 4 to 3 to 4 round trip on the projector and say why it lands exactly. |
| 30-38 | Students catch up. You circulate. Ask each student to click down to 1 and read the single row out to you - it must be `₹1364.00`, the whole bill. |
| 38-40 | Run the whole thing end to end: `/`, click a card, move the stepper, hit back. Say what is deliberately not saved: reload the page and the count returns to 4, because the re-split lives in React state and nothing is ever written to disk. |

## Cut points in this session

### cut-money-split - `lib/money.ts`:28

- **What students see:**

  ```ts
  // TODO(cut-money-split): Fill the shares array declared above with one share per person: give every person the amount divided by the number of people ignoring the remainder, then give one extra paisa each to as many people from the start of the list as there are paise left over.
  ```

- **What they write:** five lines. Work out the base share with integer division -
  the division that ignores the remainder. Work out the leftover with the
  remainder operator. Then build an array with one entry per person, where a
  person's position decides whether they get the base share or the base share plus
  one paisa: the first `leftover` people get the extra one. Assign it to `shares`.

- **The finished block, for you:**

  ```ts
  const each = Math.floor(amountPaise / people)
  const leftover = amountPaise % people
  shares = Array.from({ length: people }, (_unused, index) =>
    index < leftover ? each + 1 : each,
  )
  ```

  The function around it, already in their file:

  ```ts
  /** One share per person, in person order, adding up to amountPaise exactly. */
  export function splitPaise(amountPaise: number, people: number): number[] {
    let shares: number[] = []

    // the block goes here

    return shares
  }
  ```

- **Teach it like this:** three moves, and name each one as you type it.

  "`Math.floor(amountPaise / people)` is the share everybody definitely gets.
  45466. Nobody can be given less than that."

  "`amountPaise % people` is what is left on the table. The percent sign here is
  not a percentage - it is the remainder, what division could not hand out. 2."

  "`Array.from({ length: people }, ...)` builds an array with one slot per person
  and fills each slot by asking a question about its position. `index < leftover`
  is the question: are you one of the first two? Then `each + 1`. Otherwise
  `each`."

  Then prove it, out loud, with the board: "45467 plus 45467 plus 45466. 136400.
  Exactly. Not close - exactly. Do this with `Math.round` on each share and you
  get three lots of 45467, which is 136401, and you have invented a paisa out of
  nothing. Somebody has to pay that paisa and it will not be you."

  If a student asks for a `for` loop instead of `Array.from`, say yes. Any loop
  that produces the same array is correct. `Array.from` is worth showing because
  it says "one per person" in one line.

- **Passes when:** nothing on its own - the screen does not change at all, because
  nothing is calling `splitPaise` yet. Say that before you save the file.

### cut-bill-shares - `app/bills/[id]/BillView.tsx`:24

- **What students see:**

  ```ts
  // TODO(cut-bill-shares): Work out what each person owes by splitting the total with tip across the number of people currently held in state, and assign that array of shares to the shares variable declared above.
  ```

- **What they write:** one line. Call `splitPaise` with the total *with tip* and
  the `people` value currently in state, and assign the result to `shares`.
  `splitPaise` is already imported and `grandTotalPaise` is already computed above.

- **The finished block, for you:**

  ```ts
  shares = splitPaise(grandTotalPaise, people)
  ```

  What sits around it, already in their file:

  ```ts
  const [people, setPeople] = useState<number>(bill.people)

  const grandTotalPaise = bill.totalPaise + tipPaise(bill.totalPaise, bill.tipPercent)

  let shares: number[] = []
  ```

  And what renders from it, also already written:

  ```tsx
  {shares.length > 0 && (
    <>
      <h2 className={styles.sharesHeading}>What each person owes</h2>
      <ul className={styles.shares}>
        {shares.map((share, index) => (
          <li className={styles.shareRow} data-testid="share-row" key={index}>
            Person {index + 1} {formatRupees(share)}
          </li>
        ))}
      </ul>
    </>
  )}
  ```

- **Teach it like this:** "Two decisions in one line, and both matter.
  `grandTotalPaise`, not `bill.totalPaise` - we are splitting what the table
  actually pays, tip included. And `people`, the state value, not `bill.people`,
  the stored one. The stored one never changes. The state one is about to."

  Then the big idea of the session: "This line is not inside a `useEffect` and it
  is not in state. It runs on every single render. Every time React redraws this
  component it splits the bill again from scratch, from the bill we fetched and
  the count we are on. Nothing on screen is ever edited - it is thrown away and
  rebuilt. That is why the next block is going to work."

  Two questions you will get here, both worth answering:

  - *"Why `key={index}` when session 1 said use the id?"* Because a share row has
    no identity of its own - Person 3 *is* the third slot. When the list has real
    things in it with real ids, use the id. When the position is the identity,
    the index is honest.
  - *"Why is the heading missing before this line works?"* Because the whole
    section is wrapped in `shares.length > 0`. An empty list is not a section with
    nothing in it - it is no section at all.

- **Passes when:** `c-3-1` goes green. Four rows: `Person 1 ₹341.00`, `Person 2
  ₹341.00`, `Person 3 ₹341.00`, `Person 4 ₹341.00`. 34100 times 4 is 136400 - say
  it out loud.

### cut-bill-people - `app/bills/[id]/BillView.tsx`:15

- **What students see:**

  ```ts
  // TODO(cut-bill-people): Put the requested number of people into the people state, holding it at 1 when it would drop below 1 and at 20 when it would climb above 20.
  ```

- **What they write:** one line. Put the requested number into the `people` state,
  but never below 1 and never above 20.

- **The finished block, for you:**

  ```ts
  setPeople(Math.min(20, Math.max(1, requested)))
  ```

  The function around it, already in their file:

  ```ts
  function setPeopleClamped(requested: number): void {
    // the block goes here
  }
  ```

  And the two buttons that call it, also already written - point at them:

  ```tsx
  <button
    type="button"
    className={styles.stepperButton}
    aria-label="Fewer people"
    onClick={() => setPeopleClamped(people - 1)}
  >
    -
  </button>
  <span className={styles.peopleCount} data-testid="people-count">
    {people}
  </span>
  <button
    type="button"
    className={styles.stepperButton}
    aria-label="More people"
    onClick={() => setPeopleClamped(people + 1)}
  >
    +
  </button>
  ```

- **Teach it like this:** "Read the two buttons first. Neither one knows about
  limits. Minus asks for one fewer, plus asks for one more, and both of them are
  allowed to ask for something silly. The limit lives in one place: the setter.
  `Math.max(1, requested)` says never below one. `Math.min(20, ...)` says never
  above twenty. One line, and every route into this state is now safe."

  Then the design choice, which is the part they will carry to other projects:
  "We could have disabled the minus button at 1 instead. We did not, on purpose.
  A disabled button leaves the rule spread across the markup, and if a second
  thing ever sets this count it will not know the rule at all. Put the rule where
  the value changes."

  Now do the round trip on the projector and narrate it: "4. Click minus: 3, and
  every row is redrawn - 454.67, 454.67, 454.66. Click plus: 4, and we are back to
  four rows of 341.00, exactly as it was saved. Nothing remembered the old split.
  It was rebuilt from the bill and the number 4."

  Then click minus four times to reach 1 and read the single row: `₹1364.00`, the
  whole bill on one person. "The button is still clickable and clicking it does
  nothing. That is the clamp answering."

- **Passes when:** `c-3-2` through `c-3-6` go green:
  - one minus click shows 3 and three rows (`c-3-2`)
  - those rows read `₹454.67`, `₹454.67`, `₹454.66` (`c-3-3`)
  - minus then plus lands back on 4 and four rows of `₹341.00` (`c-3-4`)
  - four minus clicks reach 1, one row, `₹1364.00` (`c-3-5`)
  - seventeen plus clicks reach 20 and stop (`c-3-6`)

## Where students get stuck

- **"I wrote `splitPaise` and nothing changed on screen"** - correct, and expected
  between minutes 5 and 17. Nothing calls it until `cut-bill-shares`.

- **"Still no rows and no heading"** - `cut-bill-shares` is not saved, so `shares`
  is still the empty array, and the heading and rows are wrapped in
  `shares.length > 0`. Say: "the section is not empty, it is absent. Check the
  line above the return."

- **The rows read `₹310.00` instead of `₹341.00`** - they split `bill.totalPaise`
  instead of `grandTotalPaise`. Say: "you split the bill and left the tip on the
  table. 310.00 times 4 is 1240, not 1364."

- **Three rows all reading `₹454.67`, and the total comes to `₹1364.01`** - the
  leftover test is `index <= leftover` instead of `index < leftover`, so three
  people get the extra paisa and only two were owed it. Say: "count them. Two
  paise were left over and you handed out three."

- **Three rows all reading `₹454.66`, total `₹1363.98`** - no leftover handling at
  all, just `Math.floor` for everyone. Two paise vanished. Say: "add up your own
  rows and compare with the total with tip on the same screen."

- **Shares come out with more decimals, like `₹454.666`** - they divided without
  flooring, or used `toFixed`. Say: "there is no such thing as two thirds of a
  paisa. `Math.floor` first, then hand out the remainder."

- **The stepper still does nothing after filling `cut-bill-people`** - usually
  `people = Math.min(...)` instead of `setPeople(...)`. Say: "assigning to a
  variable does not tell React anything. Only the setter causes a render."

- **The count goes 4, 3, 2, 1, 0, -1** - no clamp, or the clamp is on the wrong
  side. Say: "read your `Math.max` and your `Math.min` out loud with the numbers
  in them. Which one is stopping zero?"

- **The buttons go grey at 1 and at 20** - they added a `disabled` attribute to
  the markup. This fails the tests even though the screen looks sensible, because
  the tests click the button one extra time and expect it to still be clickable.
  Say: "take the `disabled` off. The clamp belongs in the setter, and a button
  that cannot be pressed cannot show you that the clamp works."

- **4 to 3 to 4 does not land back on `₹341.00`** - they put `shares` into state
  and re-split the shares that were already on screen instead of rebuilding from
  the bill. Say: "you split a split. Once you throw away a paisa you cannot get it
  back. Rebuild from `grandTotalPaise` every time - that line runs on every render
  for exactly this reason."

- **"I reloaded and it went back to 4"** - correct and deliberate. The re-split is
  not saved anywhere. Say: "nothing is written to disk in this project. The bill
  is what was saved; the stepper is a question you are asking about it."

- **A row reads `Person 1₹341.00` with no space** - only happens if a student has
  edited the row markup, which ships written. Say: "the space has to be a real
  character in the page. Put the markup back the way it was."

## Check before moving on

The project is done. Before the class leaves, each student should be able to do
this in front of you without touching the keyboard twice:

1. Open `/`, see 6 cards, click `Anand Bhavan`.
2. Read `₹1240.00`, `10%`, `₹124.00`, `₹1364.00`, `Split 4 ways when saved`.
3. Four rows of `₹341.00`.
4. Minus once: three rows, `₹454.67`, `₹454.67`, `₹454.66`. Add them up out loud.
5. Plus once: back to four rows of `₹341.00`.
6. `Back to saved bills` returns to the list.

If step 4 does not add up to 136400, the split is wrong, not the display.
