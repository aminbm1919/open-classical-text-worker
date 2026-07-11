# Phase 2 Design — External-content FTS5 for the document cache + relevance-only selection

Designed 2026-06-13 via a multi-agent pass (5 source-mappers → draft → 2 adversarial reviewers). Anchors verified against `worker.js`. The adversarial pass caught two real bugs in the first draft (an index-corrupting rowid-bind and a duplicate-`let` syntax error); both are fixed below and flagged ⚠️FIXED.

## Thesis
Add ONE external-content FTS5 table per shard — `cached_text_chunks_fts(content='cached_text_chunks', content_rowid='id', detail=full)` — created in `setupOneTextShard`. Keep it in sync via FTS5 special-command idioms at the 3 live mutation sites. Then rewrite `searchDocumentTextCache`'s N+1 `LIKE`/`chunk_index` loop into a per-shard `bm25` MATCH (≤9 parallel queries) producing the **byte-identical** `resolvedChunks` shape; the registry is consulted *after* ranking, only for metadata + realm filtering. Selection is `bm25`-only — retention/scored never bias it.

This is the **first external-content FTS table in the codebase**. The two existing tables (`text_chunks_fts` L1911, `local_text_chunks_fts` L3117) are standalone/contentless and stay as-is. The one hard divergence: **delete uses the `'delete'` special command, not `DELETE FROM ..._fts WHERE rowid=?`.**

---

## Part 1 — Schema
External-content fts5; `cached_text_chunks.id` is `INTEGER PRIMARY KEY AUTOINCREMENT` (L3150) = true rowid alias. Index only `chunk_text`; recover metadata by JOIN-back on `c.id = fts.rowid` (as existing MATCH queries already do, L2082/L3891). Stores only the inverted index — no second copy of `chunk_text`. Default unicode61 tokenizer (no `tokenize=`) so `buildFtsQuery` phrase/AND/OR strings match identically across all three FTS tables.

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS cached_text_chunks_fts USING fts5(
  chunk_text, content='cached_text_chunks', content_rowid='id', detail=full
)
```

Insertion point: `setupOneTextShard(db)` between the `idx_cached_text_chunks_key` index (ends L3168) and the `ensurePhaseTwoOneShardSchema` call (L3170). This is the single create-everything path reached from both `setupShards` (L3031) and `setupCacheLayer` (L1076), and where the sibling `local_text_chunks_fts` is already created. The FTS table lives on `shard.db`, NEVER `env.DB`.

---

## Part 2 — Write-path sync
Exactly 4 statements mutate `cached_text_chunks` (grep-verified). 3 live, 1 no-op.

Shared helper — note the **integer** rowid bind (⚠️FIXED: not `String()`):
```js
async function ftsDeleteCachedChunksByDocument(db, documentId) {
  const rows = await db.prepare(
    `SELECT id, chunk_text FROM cached_text_chunks WHERE document_id = ?`
  ).bind(documentId).all().catch(() => ({ results: [] }));
  for (const r of rows.results || []) {
    await db.prepare(
      `INSERT INTO cached_text_chunks_fts(cached_text_chunks_fts, rowid, chunk_text) VALUES ('delete', ?, ?)`
    ).bind(r.id, r.chunk_text).run().catch(() => null);   // ⚠️FIXED: raw integer r.id, NOT String(r.id)
  }
  return (rows.results || []).length;
}
```
**Why the fix matters:** the standalone deletes elsewhere use `WHERE rowid = String(old.id)` (safe — SQLite coerces in a WHERE comparison). But the external-content `'delete'` command passes rowid as a *positional value* into FTS5; a string there can mismatch the stored integer rowid and silently corrupt/orphan the index. Bind the raw integer. (Both adversarial reviewers flagged this independently as the #1 corruption risk.)

| # | Line | Function | Base op | FTS op |
|---|------|----------|---------|--------|
| 1 | 25105 | `writeDocumentCache` | DELETE by `document_id` | `ftsDeleteCachedChunksByDocument(shard.db, old.id)` **before** base delete |
| 2 | 25130 | `writeDocumentCache` | INSERT per chunk | capture `ins.meta.last_row_id` → `INSERT INTO cached_text_chunks_fts(rowid, chunk_text) VALUES (?, ?)` (raw `cid`) |
| 3 | 25308 | `pruneExpiredCaches` | DELETE by `document_id` | `ftsDeleteCachedChunksByDocument` **before** base delete (folds in the existing count SELECT → net-zero extra query) |
| 4 | 3376 | `ensurePhaseTwoOneShardSchema` | UPDATE `source_family` only | **none** — `chunk_text`/rowid unchanged, FTS indexes only `chunk_text` |

Ordering inside `writeDocumentCache`: FTS `'delete'` (L25105 area) runs before the base DELETE — the only window where the exact indexed `chunk_text` is still retrievable. New inserts (L25128+) get fresh AUTOINCREMENT ids → no rowid collision, no orphan postings. All FTS ops are best-effort (`.catch(() => null)`) so they never break the base write.

---

## Part 3 — Search rewrite (relevance-only)
Replace the per-doc loop (L19064–19085). Keep L18999–19062 except: **remove** the registry `ORDER BY retention_score DESC … LIMIT 200` (L19050) — that is the exact selection-bias the user prohibited.

1. **Per-shard MATCH (≤9, parallel-safe):** `buildFtsQuery(query)` → for each shard, `SELECT c.* , bm25(cached_text_chunks_fts) AS rank FROM cached_text_chunks_fts JOIN cached_text_chunks c ON c.id = cached_text_chunks_fts.rowid WHERE cached_text_chunks_fts MATCH ? ORDER BY rank LIMIT ?`. No `cache_key`/retention predicate → pure relevance. `Promise.all` over ≤9 independent shard bindings (safe; well under the 50-subrequest cap). Empty `buildFtsQuery` → all shards return `[]` (mirrors old empty-`firstLike`).
2. **Merge + global bm25 order**, then derive `candidateKeys` from **only the chunks you will keep** (walk merged in bm25 order until `maxResolvedChunks` chunks OR a key cap). ⚠️FIXED: cap `candidateKeys` to a small constant (≤~100) and/or chunk the registry `IN (...)` across ≤3 queries — the draft's unbounded `IN` would throw past D1's bound-parameter limit.
3. **ONE central registry query:** the **verbatim** realm filters from L19026/L19029–19049 (`cache_status='ready'`, `source IN`, `text_state IN`, `value_score >=`, the scored-cache clause) **plus** `cache_key IN (candidateKeys)`. No `ORDER BY retention`. Build `regByKey` map.
4. **Assemble `allResolvedChunks` by reusing the existing builder** — ⚠️FIXED: group merged rows by `cache_key` and call `buildDocumentCacheResolvedChunks(regRow, chunkRowsForKey)` **once per key** (reproduces the original one-`unit`-shared-by-reference semantics, L18983, cleanly — no per-chunk unit patch-up). Keep `regByKey` row `SELECT *` so `shard_name` (read from the registry row, L18966/18991) is present. Drop chunks whose key failed the realm filter.
5. **Reuse the existing counter `let`s** (L19059–19062: `scannedChunks`/`scannedDocuments`/`lexicalChunkRowsFound`/`lexicalChunkQueryErrors`) — ⚠️FIXED: do NOT re-`let` them in the new block (duplicate `let` in the same scope = syntax error).
6. **`allowedOwnerKeys`** regenerated from the surviving (realm-passed, matched) keys.

Downstream (L19087+: `searchResolvedTextChunksHybrid` at L19097, scored top-up L19131, vector `allowed_owner_keys`) is unchanged — it consumes the two rebuilt arrays.

Shape contract preserved by delegating to `buildDocumentCacheResolvedChunks` (L18953): `unit` (26 fields incl. `document_cache_key`/`cache_key`/`parent_document_key`/`evidence_unit_key`/`shard_name`/metadata), `chunk` (`cache_chunk_id` from `id`, `chunk_index`/`chunk_start`/`chunk_end`, `text` from `chunk_text`), top-level `content_match_scope: "document_chunk"`. Retention/scored ride on `unit.*` as **metadata only**; `minValueScore` + scored-cache clause remain **opt-in** filters.

**✅ DECIDED — option (b) (2026-06-13):** keep a SEPARATE broader allowed-owner set for the vector branch (one extra registry query over realm-eligible docs) so vector recall is preserved; the lexical/assembled `allowedOwnerKeys` tightening applies only to the lexical candidate set. Wire in Step 3.

(Original analysis:) the new `allowedOwnerKeys` is derived from matched keys only, vs. the old "all ≤200 registry rows". This **tightens** the vector branch's allowed-owner universe: a doc that is realm-eligible but whose chunks didn't *lexically* match is now excluded from vector scope too → could regress semantic recall (the whole point of the vector branch is finding docs that did NOT lexically match). Options: (a) accept the tightening (cleaner, but loses cross-lexical vector recall); (b) keep a separate broader allowed-owner set for the vector branch (one extra registry query). Recommend (b) to preserve vector recall, or a flag.

---

## Part 4 — Backfill (one-time admin route)
Existing cached docs (and everything that took the `already_cached` fast path L25046) aren't indexed → backfill required; lazy-on-write covers everything after. Canonical full-populate for external-content = the `'rebuild'` command (idempotent, self-correcting, one statement per shard):
```sql
INSERT INTO cached_text_chunks_fts(cached_text_chunks_fts) VALUES('rebuild')
```
Add admin route `/setup-fts` (mirror `/setup-cache` L451 boilerplate + `isAdminRequest` L1719) → `setupCacheFts(env, opts)` fans out over `getTextShardBindings` (L2853): ensure-table-exists, optional `dry_run`, `'rebuild'` per shard, then verify `base_chunks == fts_rows` per shard. Resumable fallback for very large shards (avoid per-request CPU ceiling): page `SELECT id, chunk_text FROM cached_text_chunks WHERE id NOT IN (SELECT rowid FROM cached_text_chunks_fts) ORDER BY id LIMIT ?` + rowid-insert, return `{scanned, inserted, next_cursor, done}` (mirrors the bounded-backfill convention at L3229). The `NOT IN` predicate makes re-runs idempotent. Prefer `'rebuild'` first.

This is the first use of these FTS5 special commands in the repo (no in-repo precedent) — test on ONE shard before fan-out.

---

## Part 5 — Rollout (3 separable, reversible deploys; each = deploy + two-criteria test + end-of-worker marker)
1. **Schema + backfill** (additive, zero behavior change): Part 1 DDL + Part 4 route. Reverts via `DROP TABLE cached_text_chunks_fts` per shard. Marker `_PHASE2_FTS_SCHEMA_V1`. Test: `/setup-fts?dry_run=1` → `base_chunks == fts_rows`; a manual `MATCH` returns rows; existing search unchanged (still old loop).
2. **Write-path sync** (lazy-on-write keeps index live): Part 2 helper + 3 patches. ⚠️FIXED: gate Site #2's FTS insert behind a **mandatory** storage-policy flag `enable_cache_fts_write` **default OFF** (ship dark; D1 is non-transactional, so a toggle that reverts without redeploy is required insurance). Marker `_PHASE2_FTS_WRITESYNC_V1`. Test: force-rewrite a doc → its words appear in FTS; prune/rewrite → words disappear (no orphan); `cached_text_chunks_count` unchanged for untouched docs.
3. **Search rewrite** (only behavior-visible change): Part 3, behind a `cache_search_mode: "fts" | "legacy"` flag **default legacy** until verified (single flag flip reverts). Marker `_PHASE2_FTS_SEARCH_V1`. Test: a multi-term query the old `firstLike` missed now returns bm25-ranked chunks; ≤9 shard queries instead of ≤200; realm filters still exclude the same docs; `resolvedChunks` shape intact (no downstream skips).

Strict order: table-exists → live-index → read-from-index. Each independently revertible.

---

## Part 6 — Risks / operational requirements
- **Index-drift from non-transactional D1:** best-effort FTS ops can drift if one half fails. Orphan postings are hidden from results by the JOIN-back, BUT they **skew global bm25** until reconciled. ⚠️Make periodic `/setup-fts?rebuild` + `base_chunks==fts_rows` parity a **required** operational check, not optional.
- **Prune site (L25308) is the highest-drift omission** — explicitly wired; folding the FTS delete into the existing count round-trip makes it hard to drop in future edits.
- **`already_cached` fast path (L25046)** bypasses chunk writes → why the Part 4 backfill is mandatory and lazy-on-write alone is insufficient.
- **Teardown invariant (latent):** any future path that drops/recreates `cached_text_chunks` must `DROP TABLE cached_text_chunks_fts` first (drop FTS child before content parent), else the external-content table breaks.
- **Term richness:** MATCH uses up to 12 terms (`buildFtsQuery`/`uniqueFtsTerms`) vs the hybrid ranker's 6-term `terms` array — an intended richness increase; flag in Step-3 test.

## Key anchors (worker.js)
Schema insert pt: after L3168 before L3170 · sibling FTS L3117 · base table L3148–3163 · write sites L25105/L25130/L25308 · no-op UPDATE L3376 · search loop L19064–19085 · registry SQL+filters L19024–19052 · `buildDocumentCacheResolvedChunks` L18953 · `buildFtsQuery`/`quoteFtsValue` L2542/L2567 · hybrid consumer L19097 · bm25 MATCH precedent L2081/L3890 · `/setup-cache` route L451 · `isAdminRequest` L1719 · `getTextShardBindings` L2853.

---

## Testing performed (2026-06-13) + limitations

All 3 steps DEPLOYED (`wrangler deploy --keep-vars`) and given the two-criteria test (change applied + no regression):
- **Step 1** (`fab32edd`): `/setup-fts` → `parity_all=true`, `base_chunks == fts_rows` on all 9 shards; live `MATCH 'commodity'` (11 hits) + bm25 + JOIN-back confirmed; root + read-chunk unregressed.
- **Step 2** (`9e5fbef7`): enabled `enable_cache_fts_write`, force-rewrote a doc → shard parity stayed `base == fts` (proves the integer-rowid `'delete'` left no orphan + insert worked); MATCH on rewritten content; base write unaffected.
- **Step 3** (`224de050`): legacy default unchanged (same 3 results); FTS mode `commodity`→3, `surplus value labour`→4; **recall win shown**: `zzznotword value commodity` (first term absent) → FTS found the doc (legacy `firstLike` would return 0); flag flip legacy↔fts works.

**Limitations (NOT yet exhaustively tested — honest list):**
- **Tiny corpus** — only a handful of cached docs across shards; not load/scale tested. The `IN()` KEY_CAP (100) and the broad-owner cap (500) are never hit at this size.
- **Vector branch / E2(b) unexercised** — vectors were wiped, so the vector branch returns nothing; the broader allowed-owner set is code-correct but its effect on vector recall is untested until vectorization is re-enabled (which also needs C4/C5 first).
- **Prune FTS delete (Site #3) not directly triggered** — needs cache expiry; it uses the SAME `ftsDeleteCachedChunksByDocument` helper that Site #1 (rewrite delete) validated via the parity check, so high confidence but not directly exercised.
- **Drift reconciliation is operational** — periodic `/setup-fts?rebuild` + parity check should be run as the corpus grows (D1 is non-transactional).
