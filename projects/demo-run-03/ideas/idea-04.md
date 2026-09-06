# Paste-to-DB CSV Importer

**One line:** Paste a small CSV into the browser, preview parsed rows with validation, then upsert contacts into SQLite via Prisma in one transaction.

## Theme
A tiny, deterministic parser and a diff-to-database flow. No external files or network: the CSV is pasted as text, parsed in TypeScript, previewed, and only then committed. Seeds and migrations run clean; tests stay small and reproducible.

## Sessions
1. Setup and preview shell.
   - Prisma schema: Contact(id, name, email UNIQUE, tags TEXT), ImportBatch(id, created_label), ImportRow(id, batch_id, email, name, tags, status ENUM('create','update','error'), message TEXT).
   - Seed a few contacts; render a page with a textarea and a disabled Commit button.
2. CSV parser with header mapping.
   - Parse pasted text into rows handling: quoted commas, CRLF/\n, header case-insensitivity for Name, Email, Tags.
   - Show a preview table with per-row status: valid or error (e.g., missing email, duplicate email within the paste).
3. Diff against existing contacts.
   - For valid rows, compare to DB by email; mark status 'create' or 'update' and show a merged-tags preview rule (distinct, semicolon-joined).
   - Display counts by status and enable Commit when there is at least one create/update.
4. Transactional upsert and import history.
   - POST /api/imports/commit starts a batch, upserts all rows marked create/update in one transaction, writes ImportRow records reflecting outcomes, returns counts.
   - History view lists prior imports with their counts.

## What the student types
- A small, robust-enough CSV tokenizer for the scoped header set and quoted fields.
- A diff algorithm keyed by a unique field (email), including an in-paste duplicate check.
- A single transaction that creates an ImportBatch, upserts contacts, and records ImportRows consistently.

## What this teaches that the shipped projects do not
- Building a simple parser in TS and threading its output through a validated, persisted import flow without uploads or external services.
- Designing idempotent, testable upserts and recording an auditable batch result.

## Out of scope
- File uploads, huge files, custom header mapping UIs, encoding and locale quirks.
- Complex tag normalization beyond a simple de-dup-and-join rule.

## Risks
- Parser edge cases can balloon; the grammar must stay small (headers from a fixed set, quotes, commas, newlines). Keep seeds and fixtures minimal and explicit.