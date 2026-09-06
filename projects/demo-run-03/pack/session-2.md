# Session 2 - Reorder suggestions

Time: 40 minutes
Students start from: Session 1 done. "/suggestions" renders an empty table. /api/reorder-suggestions returns 501.
Students end with: /api/reorder-suggestions returns Suggestion[] with qty_to_order = max(0, reorder_point - on_hand); "/suggestions" renders only rows with qty_to_order > 0 and shows the number in each row.

What they learn
- Shape a computed REST view
- Array mapping
- Client fetch
- Conditional rendering/filter

Before you start
- Server running from Session 1.
- Open these files:
  - app/app/api/reorder-suggestions/route.ts
  - app/app/suggestions/page.tsx
- In a browser: http://localhost:3000/suggestions

The plan
| Minutes | What you do |
|---|---|
| 0-5 | Recap and set the goal: compute qty_to_order on the server, filter to only positives on the page. |
| 5-30 | Live code, in this order: 1) API compute: cut-ep-suggestions-calc in app/app/api/reorder-suggestions/route.ts. 2) UI fetch: cut-ui-suggestions-fetch in app/app/suggestions/page.tsx. 3) UI filter: cut-ui-suggestions-filter in the same file to keep only qty_to_order > 0. Refresh and verify rows and numbers. |
| 30-38 | Students finish and you circulate. Check data-testid="suggestion-row" count matches positives and each row shows a cell with data-testid="qty-to-order". |
| 38-40 | Bridge to next: we’ll select rows and commit them as a purchase order. |

Cut points in this session
### cut-ep-suggestions-calc - app/api/reorder-suggestions/route.ts:6
- What students see: // TODO(cut-ep-suggestions-calc): Build `body` as an array of { sku_id, name, on_hand, reorder_point, qty_to_order } where qty_to_order is max(0, reorder_point - on_hand), and set `status` to 200
- What they write: Read all SKUs; map each to a Suggestion with qty_to_order = Math.max(0, reorder_point - on_hand); write the array to `body` and set `status` 200.
- Teach it like this: Compute at the API layer so the UI stays simple. Shape the exact view model the screen needs.
- Passes when: criterion c-2-1 goes green

### cut-ui-suggestions-fetch - app/suggestions/page.tsx:15
- What students see: // TODO(cut-ui-suggestions-fetch): Fetch GET /api/reorder-suggestions and write the parsed array into `suggestions`
- What they write: In useEffect, fetch '/api/reorder-suggestions', parse to Suggestion[], setSuggestions(arr).
- Teach it like this: Same pattern as Session 1. Keep the active flag pattern to avoid setting state after unmount.
- Passes when: criteria c-2-2 and c-2-3 go green

### cut-ui-suggestions-filter - app/suggestions/page.tsx:26
- What students see: // TODO(cut-ui-suggestions-filter): Write into `visible` only the suggestions whose qty_to_order is greater than 0
- What they write: When suggestions change, setVisible(suggestions.filter(s => s.qty_to_order > 0)).
- Teach it like this: Derived state from source state. The filter belongs in an effect keyed on suggestions.
- Passes when: criterion c-2-2 goes green

Where students get stuck
- "Everything shows, including zeros" - They forgot the filter or used ">=". Point them to the visible-only filter.
- "Rows render but qty_to_order cell is empty" - They didn’t include qty_to_order in the mapped shape or typoed the property name. Match the exact key.
- "404 on /api/reorder-suggestions" - Wrong path in fetch. It is '/api/reorder-suggestions'.
- "State update after unmount" warning - They removed the active flag. Keep the cleanup return in useEffect.

Check before moving on
- GET /api/reorder-suggestions returns 200 with correctly computed qty_to_order; the Suggestions page renders one data-testid="suggestion-row" per positive suggestion and shows a data-testid="qty-to-order" cell for each.
