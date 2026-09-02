# Index

**One line:** A search box over twenty seeded notes that answers from an
inverted index the student builds, with multi-word queries intersected, one
exclusion operator, and results ranked by a stated rule.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

Every student's first search is `notes.filter(n => n.text.includes(q))`. This
project builds the other thing: tokenise once, keep a map from token to the
notes that hold it, and then answer a query by intersecting posting lists
without ever looking at a note's body again. It is the first time the student
builds a data structure whose whole reason to exist is that a later question
becomes cheap, and the stats page in session 1 makes that structure something
you can actually look at.

## Sessions

1. **Setup, the notes, and the index.** Types, `data/notes.json` with twenty
   short notes (a title and two or three sentences each), containing one token
   that appears in exactly one note and one that appears in all twenty,
   `tokenize(text)` - lowercase, split on non-letters, drop tokens under two
   characters, no stemming - `buildIndex(notes)` producing token to note-ids with
   a per-note occurrence count, `GET /api/search?q=<one token>`, and `/` showing
   the note list, a search box bound to the query string, and a line reporting
   how many distinct tokens the index holds. **Runs:** a one-word search returns
   the right notes and the index size is a number you can check by hand.
2. **Multi-term queries and ranking.** `search(index, query)`: every token must
   match, a leading `-` excludes, an unknown token yields nothing rather than
   everything, an empty query yields every note. Results ordered by the summed
   occurrences of the query's positive terms, ties broken by title A to Z, and
   the screen shows a rank number and the match count per row. **Runs:** a
   two-word query narrows the list, `-word` drops a note out of it, and two
   equally-scoring notes appear in a stated, stable order.

## What the student types

- `tokenize` - the split and the two discard rules, which is where the
  difference between `Deadline.` and `deadline` stops being invisible.
- `buildIndex` - accumulating into a map of arrays, deduping a note within one
  token while still counting how many times it occurred.
- `search` - reducing the posting lists down to an intersection, subtracting the
  excluded ones, and the two degenerate cases (empty query, unknown token) that
  differ from each other.
- The ranking comparator, including the alphabetical tie-break.

## What this teaches that the shipped projects do not

recipe-box searched, and it searched by scanning eight recipes with `includes`
on every keystroke - the filter, not the index. This is the first data structure
in the track that the student *constructs*, the first set intersection, and the
first ordering with a stated tie-break. Be plain about the overlap: the screen
looks like a filtered list, and the difference is entirely in what the query
touches.

## Out of scope

- Stemming, a stopword list beyond the length rule, fuzzy or prefix matching.
- Phrase queries, proximity, `OR`, parentheses. Exclusion is the only operator
  and the grammar is closed.
- Adding, editing or reindexing notes; incremental index updates; pagination.
- Highlighting the matched term inside a note body.

## Risks

Intersection and union are indistinguishable unless the seed contains a query
whose union is four notes and whose intersection is one - that fixture is the
project. Second: ranking graded on one query can be satisfied by a comparator
that ignores the tie-break, so a criterion must pin the full ordered id list for
a query with a genuine tie. Third: query languages sprawl, and ledger's lesson
applies here - the accepted query shape and the exact behaviour of every
degenerate case belong in the spec before the Builder invents them.
