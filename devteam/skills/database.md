# SKILL: Database — schemas and queries that survive production

### Schema design
- Normalize to 3NF; denormalize only with a measured reason (not "just in case").
- Every table: explicit PK (UUID or bigint autoincrement, ONE choice across the
  whole project), timezone-aware `created_at`/`updated_at`.
- Foreign keys with explicit `ON DELETE` (CASCADE/SET NULL/RESTRICT — decide,
  don't leave the default). Uniqueness and CHECK constraints for invariants.
- Indexes: on EVERY FK, on columns used in frequent filters/ordering, and
  composite ones for real queries. No "just in case" indexes (they slow writes).

### Migrations
- Reversible (up/down) and small. One migration = one logical change.
- Backward-compatible when deploying without downtime: add a nullable column
  → backfill → enforce NOT NULL in a later migration. Never rename/drop in the
  same step as the code that still uses the old name.
- Idempotent where possible; never depend on specific production data.

### Queries
- **Kill the N+1**: in lists, load relations with join/selectin, not in a loop.
- Keyset (cursor) pagination for large tables; offset only for small tables.
- Transactions for multi-write operations; the engine's default isolation level
  unless there's a concrete reason. Keep locks short.
- Never build SQL by concatenation (injection) — always parameterized/ORM.
- Measure: run `EXPLAIN` on a query in a hot endpoint if you doubt the plan.

### Data
- Data migrations kept separate from schema migrations.
- Realistic, coherent seeds for demo/test (not "asdf").
- Deletion: soft-delete (`deleted_at`) when you need to audit or recover;
  hard-delete for personal data the user asks to erase (GDPR).
