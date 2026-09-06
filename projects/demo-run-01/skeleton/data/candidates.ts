import { Candidate } from "../lib/types"

// Exactly 10 candidates, at least one pair sharing the same years value,
// and at least one carrying the preferred tag "typescript".
//
// NOT in name order, deliberately. Listed alphabetically, this file satisfied
// "name ASC decides" on its own: cut-sort-cmp could be removed entirely, the
// comparator fell back to () => 0, sort() did nothing, and c-3-1..c-3-3 all
// still passed. The seed order has to differ from every order the spec asks
// for, or the ordering criteria grade nothing.
export const CANDIDATES: Candidate[] = [
  { id: "c7", name: "Grace", years: 7, tags: ["typescript", "nextjs"] }, // preferred tag
  { id: "c3", name: "Charlie", years: 8, tags: ["python", "django"] },
  { id: "c10", name: "Judy", years: 6, tags: ["design", "ux"] },
  { id: "c1", name: "Alice", years: 5, tags: ["react", "typescript"] },
  { id: "c9", name: "Ivan", years: 1, tags: ["testing"] },
  { id: "c6", name: "Frank", years: 10, tags: ["java", "spring"] },
  { id: "c4", name: "Diana", years: 5, tags: ["go", "kubernetes"] }, // duplicate years with Alice
  { id: "c8", name: "Heidi", years: 3, tags: ["rust"] }, // duplicate years with Bob
  { id: "c2", name: "Bob", years: 3, tags: ["node", "express"] },
  { id: "c5", name: "Eve", years: 2, tags: ["sql", "data"] }
]
