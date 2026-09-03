# Till

**One line:** A supermarket receipt where the prices are the easy part - the
offers are rules read from a file, applied in a stated order, each printing the
line it took off the bill.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

Every checkout is a small rules engine, and the bug is never the
multiplication. It is which offer applies, how many times it applies, and which
units it consumes when a basket qualifies for two offers over the same items. A
receipt is an unusually good test output for that: a discount that cannot name
the offer that produced it is a discount no customer would accept, and a total
that a person can add up by hand is a criterion that cannot be argued with.

## Sessions

1. **Setup, the catalogue, and the receipt.** Types, `data/shop.json` with eight
   products priced in whole paise - six by the unit, two by weight in paise per
   kilo - and four seeded baskets, one of which buys 350 g of a weighed
   product. `lineTotal(item, product)` returning integer paise: unit price times
   quantity, or grams times price-per-kilo divided by 1000 rounded half-up.
   `subtotal(lines)`, `GET /api/baskets`, and `/baskets/[id]` rendering one
   receipt line per item with a `data-testid` and the subtotal beneath.
   **Runs:** four baskets price to the paise, weighed lines included.
2. **Offers.** `data/offers.json` with three rules - three-for-two on one
   product, any two from a named set for 9900 paise, and ten percent off one
   product's whole line - and `applyOffers(lines, offers)` returning one
   discount line per application under rules the spec closes: offers are tried
   in file order, each applies as many times as its condition still holds, a
   unit consumed by one offer cannot be counted by another, and a set offer
   always consumes the cheapest qualifying units. `POST /api/baskets/price`
   takes a basket in the body and returns lines, discount lines and the total.
   **Runs:** a basket that qualifies twice shows both discount lines, and the
   total reconciles by hand.

## What the student types

- `lineTotal` - the weighed branch and the half-up rounding, in integer paise
  with no float in the path.
- `applyOffers` - the consume-and-mark loop: how many times a rule fires, which
  units it takes, and why the cheapest ones.
- `total` - the fold that the discount lines must reconcile against, which is
  what turns a wrong consumption count into a visible rupee.

## What this teaches that the shipped projects do not

Less than it looks, on the arithmetic: tip-split already did paise, remainders
and an integer-only rule, and this does not improve on that. What is new is
that the *rules are data*. Nothing shipped reads a configuration file and
executes it; every behaviour so far lives in code and every fixture is only
input. Here the fixture includes the rule set, so a student meets ordering,
precedence and resource consumption between rules - and the first bug where two
correct rules produce a wrong bill because of the order they ran in.

## Out of scope

- Searching for the best combination of offers. File order is the rule, so
  there is no optimisation and no backtracking.
- Coupons typed in by the user, loyalty cards, member-only prices.
- Tax, service charges, rounding the grand total to the nearest rupee.
- Editing a basket, saving one, or writing anything back to `data/`.
- Currencies other than rupees.

## Risks

"Applies as many times as it can" together with consumption is the fiddly part
and it is where 40 minutes goes, so the offer kinds must stay at exactly three
and the ten-percent rule is the named drop candidate - it is the smallest of the
three and a student does type it. Second: an engine graded only by the total is
satisfied by a hardcoded discount, so every application needs a criterion naming
the offer id and its paise amount, and one basket must qualify for two offers
over overlapping items. Third: the weighed fixture has to be a quantity where
naive float maths is visibly wrong, or the integer-paise rule grades nothing at
all.
