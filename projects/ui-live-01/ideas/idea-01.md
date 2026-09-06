# Mini-Markdown Previewer

**One line:** A small Next.js app that parses and renders a safe subset of Markdown with a live preview and file-backed save.

## Theme
A tiny text-to-HTML pipeline is a great place to practice writing a small parser and a renderer in TypeScript. The project stays local: notes are seeded on disk, edited in the browser, parsed server-side for safety, and rendered as React elements without any external service.

## Sessions
1. Skeleton and seed: Next + TS scaffold, seed 2–3 `.md` notes in `app/data/notes/`, build an API to list/load a note, and a page that shows raw text in a textarea and a read-only preview pane. End: pick a note and see raw text round-tripped from the API.
2. Parsing and rendering: implement a tiny Markdown subset (headings `#`, `##`, paragraphs, `*italic*`, `**bold**`, and inline code `` `code` ``). Build `parseBlocks` and `parseInlines` to output a small AST, and a pure React renderer for that AST. End: editing text updates a correctly rendered preview.
3. Save and safety: add a server route to persist the edited text back to a JSON file (no DB), validate input, and sanitize to the known subset when rendering. Add a minimal note switcher. End: edits survive a reload and render safely.

## What the student types
- `parseBlocks(source: string): BlockNode[]` – line-oriented block parser (headings, paragraphs).
- `parseInlines(text: string): InlineNode[]` – inline emphasis/bold/code tokenizer with proper nesting rules for the small subset.
- `renderAst(nodes: BlockNode[] | InlineNode[]): ReactNode` – deterministic mapping from AST to React elements.

## What this teaches that the shipped projects do not
- A hand-rolled string parser and AST to React render loop; existing projects lean on lists, filters, and API wiring (recipe-box, ui-full-demo) or numeric calculations (tip-split) rather than text parsing and rendering.
- Safety and subset thinking: accepting user text while constraining output to a known-safe subset.

## Out of scope
- Full Markdown (lists, links, images, tables, HTML passthrough).
- Drag-and-drop note ordering, user auth, or cloud storage.
- Any external parser or UI kit.

## Risks
- Parser edge cases can balloon: keep the subset tight and the rules explicit so session 2 stays within 40 minutes.
