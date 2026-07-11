# Case Study: Engineering a Production RAG Backend on $0/month

*How a philosophy-research Custom GPT got real retrieval, real citations, and real memory — on the Cloudflare Workers free plan.*

**Try the retrieval engine yourself: [live demo](https://chunking.aminbm1919.workers.dev/demo)** — a budget-capped, read-only showcase with a lexical / semantic / hybrid switch, running on this exact worker.

---

## The problem

A Custom GPT is a great research interface and a terrible research tool. Out of the box it can't fetch a primary source, can't remember what it read last week, and will happily cite a passage that doesn't exist. I wanted a GPT that does philosophy research the way a careful human does: find the actual text, read the actual passage, quote it with a verifiable trail, and build up project memory over months.

That means a backend: source discovery, full-text caching, chunking, search, scoring, and long-term memory — a complete RAG stack. The catch: the budget was **zero**. Everything had to run on free tiers.

## The budget

| Constraint | Limit | Consequence |
|---|---|---|
| Cloudflare Workers free plan | ~50 external subrequests per request; tight CPU budget | fan-out must be engineered, not parallelized away |
| D1 (SQLite) | 50 queries per request; per-DB size caps | query batching everywhere; storage must shard |
| Cron triggers | max 5 per worker | background jobs multiplexed onto shared schedules |
| ChatGPT Actions | max 30 operations per action | the API surface itself needs an architecture |
| Neon / Qdrant free tiers | ~500 MB per project / 1 GB RAM | vector capacity is a *managed resource*, not an assumption |

Every design decision below is downstream of this table.

## Decision 1 — One worker, two hostnames

ChatGPT caps each Action at 30 operations, and the system needed 52. Two Actions, then — but ChatGPT also refuses two Actions on the same domain, and Cloudflare gives exactly one free `workers.dev` subdomain per worker.

The fix costs nothing: a second worker that is nothing but a **service-binding proxy** — it forwards every request (method, headers, body, path) to the main worker via direct worker-to-worker binding, no public round-trip. The admin Action gets its own hostname; all logic stays in one deployable unit. ~20 lines of code. ([admin-proxy/proxy.js](../admin-proxy/proxy.js))

## Decision 2 — Candidates are not evidence

The core anti-hallucination rule is structural, not prompt-based. The pipeline distinguishes two kinds of results:

- **Candidates** — discovery hits, search snippets, tables of contents. Cheap, plentiful, *never citable*.
- **Evidence** — produced only by actually reading a chunk (`readChunk`), which creates a durable `read_event_id`. Scoring (`scoreReadEvidence`, 1–100) attaches to the read event, and only scored evidence can promote a document into the retained corpus.

Every response tells the GPT what to do next (`preferred_next_operation`), so the model is steered through `discover → parse → search → read → score` instead of being trusted to follow instructions. A quality gate rejects raw PDF bytes and CAPTCHA pages before they can masquerade as "read" text.

## Decision 3 — Storage that fits the meter

A single free D1 database can't hold a growing full-text corpus, so storage is layered:

- **Central D1** — registry, sessions, read events, scores, memory, feature flags. Small rows, hot path.
- **9 shard D1 databases** — document and chunk text, one copy only. The shard is chosen by hashing the cache key and **recorded in the registry** — never recomputed on read, so resharding can't silently orphan documents.
- **R2 object storage** — full-text bodies offloaded out of D1 entirely; D1 keeps metadata, offsets, and a **contentless FTS5 index**. Reads are hash-verified. This cut D1 storage pressure by an order of magnitude and made R2 the natural ingestion inbox for user-uploaded texts.

## Decision 4 — Hybrid retrieval, fused with RRF

Lexical search alone misses paraphrase; dense search alone hallucinates relevance. Inside a resolved text both run:

1. **Lexical** — FTS5 with field-weighted scoring and a graded phrase-in-title tier signal.
2. **Dense** — nearest neighbors over `bge-m3` embeddings.
3. **Fusion** — weighted Reciprocal Rank Fusion (k = 60), cross-branch dedup, curator score used only as a tie-breaker.

The most useful ranking lesson came from a failure. Results for author-centric queries were noisy until IDF analysis showed why: **inside a topic-focused corpus, the author's name is almost a stopword** (IDF of "marx" in a Marx-heavy corpus: 0.35). The lexical branch can't distinguish documents by a term they all contain — so the semantic branch has to carry topical anchoring, and the lexical branch earns its keep on rare terms and phrases. The weights follow that division of labor.

## Decision 5 — Vector storage as a managed resource

Free vector storage exists, but only in small boxes. So the boxes became the architecture:

- **Corpus vectors** → Neon Postgres + pgvector, stored as `halfvec(1024)` (half-precision halves the footprint), spread across **10 free projects sharded by topic**. An LLM classifier routes each query to the right topic project — a router, not a bigger database.
- **Memory vectors** → Qdrant free tier, int8-quantized.
- **Eviction is derived, not guessed.** Each store's cap is computed from its real budget (Neon: bytes per project; Qdrant: RAM/disk). At 90% capacity, the lowest-value documents lose their *vectors only* — the text stays, flagged `evicted` so nothing re-embeds it in a loop.
- **Deletes are guaranteed.** Every removal writes a tombstone first, so crashes and replays converge on the same end state across all three stores.

Embedding runs on a 10-minute cron with a fair budget per run — never on the hot path, so a user request never pays for corpus growth.

## Decision 6 — Deduplicate before you embed

The same classical text arrives from multiple archives in slightly different editions. Embedding duplicates wastes the scarcest resource (vector capacity), so near-dup detection runs *before* vectorization:

- Document-level **SimHash** with the thresholds from Manku et al. (WWW 2007 — Google's production web-crawl dedup paper).
- **Two tiers with different blast radii:** a reversible *skip-embed* tier (Hamming ≤ 3) that just avoids double vectorization, and a destructive *merge* tier that requires exact verification **plus a total-length tolerance guard** before deleting anything.
- Session-wide fuzzy-dup checks run behind a cheap length-based preflight, so the expensive comparison never runs on all pairs.

The asymmetry is deliberate: being wrong in the reversible tier costs a redundant vector; being wrong in the destructive tier costs a text. The guards are proportional to the cost.

## Decision 7 — Discipline is what makes 36k lines maintainable

A single-file, solo-maintained, 36,700-line worker survives only with process:

- **Version markers** — every deploy appends an `END_OF_WORKER_*` marker, ledgered in [CHANGELOG.md](CHANGELOG.md) (~90 deployed increments), so any regression bisects to a named change.
- **Runtime flags** — ~40 feature flags in a D1 `storage_policy` table ([FLAGS.md](FLAGS.md)); risky behavior ships dark and is enabled live.
- **Wire contract** — the GPT-facing response shape is an explicit allowlist ([WIRE_CONTRACT.md](WIRE_CONTRACT.md)); `tools/wire-check.py` flags any new key as DRIFT and any debug-gated key that leaks as LEAK. A debug flag collapses responses from 26.6 KB to 8.8 KB by hiding telemetry the GPT doesn't need.
- **E2E regression** — `tools/e2e-check.py` exercises the live pipeline end to end, including the full memory write→search→read→delete cycle, and cleans up after itself.
- **Route liveness audit** — every route is classified live/legacy/manual ([ROUTES.md](ROUTES.md)); nothing gets deleted without proof it's dead.

## What I'd do differently

- **Start with the wire contract.** Telemetry crept into GPT-facing responses for months before the allowlist existed; retrofitting it was harder than starting with it.
- **Shard-by-hash needs its registry from day one.** Recording the shard at write time (instead of recomputing) was a later fix that should have been the first design.
- **Budget for observability early.** The health dashboard (per-store capacity, activity, failure alerts) arrived late; every debugging session before it was slower than it needed to be.

## The numbers

| | |
|---|---|
| Worker source | ~36,700 lines, single file, ~716 functions in 15 subsystems |
| API surface | 52 OpenAPI operations across 2 GPT Actions |
| Storage | 1 + 9 D1 databases · R2 · Neon pgvector ×10 projects · Qdrant |
| Sources | marxists.org · Gutenberg · Wikisource · JSTOR · CORE · arXiv (+ Exa neural discovery) |
| Background jobs | 4 cron pipelines, lock-aware, budget-fair |
| Deployed increments | ~90 ledgered version markers |
| Monthly infrastructure cost | **$0** |

---

*Source: [worker.js](../worker.js) · full docs in [docs/](.) (Persian) · questions welcome via issues.*
