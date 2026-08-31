# Column

**One line:** A reader that lays a passage out itself - greedy word wrap at a
chosen character width, then pagination at a chosen number of lines, with both
knobs live in the URL.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

The browser already wraps text, which is exactly why doing it by hand is a good
exercise: the output is an array of strings a test can assert character for
character, and the student can see their own algorithm's line breaks in a
monospace column. Session 2 then stacks a second layout pass on top of the first,
and the two parameters interact - narrowing the column produces more lines, which
produces more pages - so the interesting bugs live in the combination rather than
in either function alone.

## Sessions

1. **Setup, the passages, and the wrap.** Types, `data/passages.json` with 3
   short passages (one containing a 30-character unbreakable word, one with a
   double space, one with two paragraphs), `wrapParagraph(text, width)` returning
   lines, `wrapPassage` joining paragraphs with a single blank line, `GET
   /api/passages`, and `/read/[id]?width=N` rendering one `<li>` per line.
   **Runs:** change `width` in the URL and the column reflows.
2. **Pages and navigation.** `paginate(lines, perPage)` grouping lines into
   pages under one stated rule - a page never *begins* with a blank separator
   line, which is what makes it more than a chunk function. `?page=N` renders one
   page with prev/next links, page 0 and page 99 are answered by a stated clamp,
   and `GET /api/passages/[id]/pages?width=&perPage=` returns the page count and
   the requested page's lines with 400 on a non-positive width. **Runs:** page
   through a passage, then narrow the width and watch the page count grow.

## What the student types

- `wrapParagraph` - the greedy accumulator, the "does the next word still fit
  including the space" test, and the hard-split branch for a word longer than the
  whole column.
- `paginate` - the chunking plus the blank-line rule, which means a page can end
  up one line short of `perPage`.
- The two query parameters parsed, defaulted and validated in one place, so the
  screen and the endpoint cannot disagree about what `width=0` means.

## What this teaches that the shipped projects do not

Nothing shipped produces layout as data. Every other project renders values it
was given; here the student's function decides where the text breaks, so the
assertion is on exact strings rather than on counts or on a number in a cell. It
is also the first project built to be graded on the *combination* of two inputs -
the lessons file says two filters each with their own criterion still need one
that drives both, and this idea is that lesson turned into a project.

## Out of scope

- Rich text, markdown, italics, headings. Plain paragraphs separated by a blank
  line, and nothing else.
- Hyphenation dictionaries, justification, proportional-font measurement. Width
  is counted in characters, and the column is monospace.
- Editing or uploading passages, scroll position, bookmarks, themes.
- Letting CSS do any of the wrapping. `white-space: pre` and the student's own
  line array.

## Risks

Whitespace is where this fails silently: the spec must state whether a wrapped
line can end in a space, what a double space does, and how the blank separator
line is represented, or the Builder and the Verifier assert different strings.
Second risk: HTML collapses whitespace, so criteria that read the DOM need either
a `data-testid` per line plus a stated normalisation, or they should read the
endpoint and leave the screen to a count. Third: session 1 is a single function
and could come in light, so the paragraph joining and the hard-split case need to
be separate cuts rather than one.
