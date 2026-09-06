# ShelfSense: Inventory Reorder Planner

**One line:** Compute a reorder plan from small seed files of products, stock, and suppliers using min/max, lead time, and pack sizes.

## Theme
An aggregation-and-query project that feels real without any external systems. Given a few JSON files, compute which SKUs need restock, how much to order (rounded to pack size), and group by supplier for an export. It’s worthwhile because it teaches precise, testable business rules and comparator logic.

## Sessions
1. App boots and lists products: seed products.json, suppliers.json, and stock.json; GET /api/products returns joined view (read-only); UI renders a simple products table.
2. Reorder math: implement computeReorderPlan(products, stock, policies) that calculates reorderQty = max(0, minMax.max - (onHand - reserved) - inboundWithinLeadTime), then round up to packSize; render a grouped-by-supplier plan.
3. Scenarios and sorting: add a UI control for a demand multiplier and lead-time tweak that recomputes the plan; implement a stable multi-key comparator (supplier, priority, sku) and an export-as-TSV button.

## What the student types
- computeReorderPlan(...): pure function applying min/max, lead time, and pack rounding.
- groupBy<K, V>(items, keyFn): utility to group rows deterministically for the UI.
- makeComparator(keys): stable comparator with explicit tiebreakers for predictable tests.

## What this teaches that the shipped projects do not
- Concrete aggregation with multiple inputs and explicit rounding/packing rules rather than a generic filterable list.
- Designing and testing stable sorting with secondary tiebreaks so criteria can assert full sequences.
- Joining small local datasets server-side and rendering a grouped grid client-side without any external database.

## Out of scope
- Live updates, authentication, supplier integrations, or writing to disk.

## Risks
Seeds must avoid already-sorted-by-default pitfalls (so sorting criteria prove the comparator), and the rounding/lead-time rules must be crisp to keep tests unambiguous.