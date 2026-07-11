# ROUTES.md — ممیزیِ قطعیِ دسترس‌پذیریِ مسیرها (پالایشِ دسترس‌پذیری)

> **منبعِ حقیقت برای «زنده در برابرِ متروک» در سطحِ روت.** ساخته‌شده ۲۰۲۶-۰۷-۱۰ (نشانهٔ `HM`) با اسکنِ dispatchِ `worker.js` + استخراجِ operationId از هر دو فایلِ اکشن + بررسیِ گاردِ داخلِ بلوک/هندلر. هر بلوکِ dispatch در `worker.js` هم یک کامنتِ `// LIVENESS:` هم‌خوان با این جدول دارد.
>
> **دسته‌ها:** `routine-action` = در اکشنِ روتینِ GPT (۲۲ عملیات، بی‌توکن) · `admin-action` = در اکشنِ ادمینِ GPT (۳۰ عملیات، `X-Admin-Token`) · `manual` = در هیچ اکشنی نیست؛ فقط دستی/دیباگ · `alias` = مسیرِ سازگاریِ قدیمی · `cron` = از scheduled صدا زده می‌شود (روت نیست).

## ۱) مسیرهای اکشنِ روتین (GPT بدونِ توکن صدا می‌زند)

| مسیر | operationId | هندلر | احراز |
|---|---|---|---|
| `/` | getWorkerInfo | (inline در fetch) + `buildResearchOrientation` | باز |
| `/unified-search` | unifiedSearch | `handleUnifiedSearch` | باز |
| `/search-text` | searchInsideSelectedText | `handleSearchText` | باز |
| `/read-chunk` | readSelectedTextChunk | `handleReadChunk` | باز |
| `/score-read-evidence` (GET/POST) | scoreReadEvidence / scoreReadEvidenceWithContext | `handleScoreReadEvidence` | باز |
| `/parse-document` | parseDocument | `handleParseDocument` | باز |
| `/search-source` | searchSourceCatalog | `handleSearchSource` | باز |
| `/get-source` | getSourceMetadata | `handleGetSource` | باز |
| `/links` | listSourcePageLinks | `handleLinks` | باز |
| `/hybrid-title-search` | hybridTitleSearchMarxists | `handleHybridTitleSearch` | باز |
| `/hybrid-deep-search` | hybridDeepSearchMarxists | `handleHybridDeepSearch` | باز |
| `/article-search` | articleSearchFullText | `handleArticleSearch` | باز |
| `/cache-status` | getCacheStatus | `cacheStatus` | باز |
| `/cache-integrity` | getCacheIntegrity | `handleCacheIntegrity` | باز |
| `/vectorize-status` | vectorizeStatus | `handleVectorizeStatus` | باز |
| `/memory-bootstrap` | memoryBootstrap | `handleMemoryBootstrap` | باز |
| `/memory-topics` | memoryTopics | `handleMemoryTopics` | باز |
| `/memory-read` | memoryRead | `handleMemoryRead` | باز |
| `/memory-search` | memorySearch | `handleMemorySearch` | باز |
| `/memory-write` (POST) | memoryWrite | `handleMemoryWrite` (append/rewrite/delete با پارامترِ `operation`) | باز (open-write، فلگِ `gpt_memory_open_write`) |
| `/shard-status` | getShardStatus | `shardStatus` | باز |

## ۲) مسیرهای اکشنِ ادمین (GPT با `X-Admin-Token`)

| مسیر | operationId | گارد |
|---|---|---|
| `/set-diagnostics-mode` | setDiagnosticsMode | dispatch |
| `/setup-db` · `/setup-shards` · `/setup-cache` · `/setup-scoring` · `/setup-promotion` · `/setup-memory` · `/setup-vectorize-preflight` · `/reset-vectorize-preflight` | setup* | dispatch (`/setup-memory` با MEMORY_WRITE_TOKEN) |
| `/index-status` | indexStatus | **بدونِ گارد (باز!)** — فقط‌خواندنی |
| `/reindex` | reindexSource | dispatch |
| `/index-url` | indexUrlMarxists | dispatch |
| `/deep-search-source` | deepSearchMarxistsWithJina | داخلِ هندلر |
| `/promotion-audit` | promotionAudit | داخلِ هندلر |
| `/retention-status` | retentionStatus | **بدونِ گارد (باز!)** — فقط‌خواندنی |
| `/doc-fingerprint-compute` · `/doc-merge` · `/doc-unmerge` | docFingerprintCompute / docMerge / docUnmerge | dispatch |
| `/vectorize-candidates` | vectorizeCandidates | **بدونِ گارد (باز!)** — فقط‌خواندنی |
| `/vectorize-schema-audit` | vectorizeSchemaAudit | **بدونِ گارد (باز!)** — فقط‌خواندنی |
| `/vectorize-prepare-one` · `/vectorize-run-jobs` | vectorizePrepareOne / vectorizeRunJobs | dispatch |
| `/vectorize-memory-microtask` · `/vectorize-memory-capacity-maintenance` · `/vectorize-memory-compact-write-window` | vectorizeMemory* | dispatch |
| `/worker-health` | workerHealthReport | dispatch |

## ۳) مسیرهای manual (در هیچ اکشنی نیستند — فقط دستی/دیباگِ ما)

**با گاردِ ادمین (سالم):** `/set-storage-policy`، `/drain-document-index`، `/exa-search`، `/setup-fts`، `/setup-phase2-schema`، `/vacuum-shards`، `/vectorize-transition-owner`، `/vectorize-mark-owner-deleted`، `/vectorize-run-deletes`، `/vectorize-query-probe`، `/ingest-from-r2`، `/embed-compare`، `/neon-status`، `/neon-migrate-corpus`، `/neon-corpus-selftest`، `/neon-corpus-drain`، `/neon-corpus-search`، `/neon-corpus-auto-enqueue`، `/scored-cache-neon-eviction`، `/neon-corpus-delete-owner`، `/neon-corpus-delete-flush`، `/qdrant-memory-delete-flush`، `/qdrant-memory-quantize`، `/fts-repair`، `/qdrant-keepalive`، `/classify-doc`، و گروهِ `/qdrant-memory-status|upsert|search|backfill` (گاردِ بلوکِ دربرگیرنده).

**⚠ بدونِ هیچ گاردی (یافتهٔ امنیتیِ این ممیزی — هر کاربرِ اینترنت می‌تواند صدا بزند):**

| مسیر | نوع | ریسک |
|---|---|---|
| `/prune-cache` | **نویسنده** — هرسِ دستیِ کش | اجرای هرسِ خارج از برنامه |
| `/r2-text-backfill` | **نویسنده** — بک‌فیلِ R2 از D1 | نوشتنِ R2 + مصرفِ منابع |
| `/r2-text-null-sweep` | **نویسنده/مخرب** — NULLکردنِ بدنهٔ چانک‌ها در D1 (پشتِ چکِ R2) | مخرب‌ترینِ فهرست؛ هرچند verify-R2-first |
| `/enrich-cache-titles` | **نویسنده** — بازنویسیِ عنوان‌ها در رجیستری | نوشتنِ D1 |
| `/reconcile-shard-registry` | **نویسنده** — اصلاحِ رجیستریِ شارد | نوشتنِ D1 |
| `/index-status` · `/retention-status` · `/memory-versions` · `/r2-latency-probe` · `/r2-embed-loader-check` · `/vectorize-schema-audit` · `/vectorize-candidates` | فقط‌خواندنی | افشای متادیتا/آمارِ درونی |

**توصیهٔ رفع (تصمیمِ کاربر):** پنج روتِ نویسندهٔ بالا گاردِ `isAdminRequest` بگیرند (تغییرِ یک‌خطی در هر بلوک؛ کرون‌ها مستقیم تابع را صدا می‌زنند و آسیب نمی‌بینند). فقط‌خواندنی‌ها کم‌خطرند ولی برای CORSِ باز (بدهیِ 🟠 موجود) بهتر است هم‌زمان بسته شوند.

## ۴) aliasهای قدیمی (زنده ولی فقط سازگاری)

| alias | مقصد |
|---|---|
| `/read` | `/read-chunk` (source پیش‌فرض marxists) |
| `/search` | `/search-text` (source پیش‌فرض marxists) |
| `/readSelectedTextChunk` | `/read-chunk` |
| `/score-evidence` · `/score-read` | `/score-read-evidence` |
| `/meta-search` | `/unified-search` (متاسرچِ legacy جذبِ unified شد) |

## ۵) کرون‌ها (روت نیستند — `scheduled` → `runScheduledByCron`)

| cron | وظیفه | تابع |
|---|---|---|
| `0 0 L */3 *` | بازایندکسِ فصلیِ کاتالوگِ marxists | `reindexMarxists(env,'core')` |
| `*/10 * * * *` | microtaskِ بردارِ حافظه + درینِ ایندکسِ معوّق + بردارِ پیکرهٔ Neon؛ piggyback: evictionِ scored در ساعاتِ UTC ۴/۱۲/۲۰ | `runScheduledGptMemoryVectorMicrotaskOnly` (+`runScoredCacheCapacityEviction`) |
| `17 */8 * * *` | ظرفیتِ بردارِ حافظه (Qdrant) | `runScheduledGptMemoryCapacityOnly` |
| `33 2 * * *` | هرسِ روزانهٔ کش + sweepِ ادغامِ خودکارِ اسناد | `runScheduledCachePruneOnly` |
| `0 6 */3 * *` | keep-aliveِ سه‌روزهٔ Qdrant | `runScheduledQdrantKeepAlive` |

## ۶) پاسخِ 404
مسیرِ ناشناخته فقط فهرستِ مسیرهای روتین را برمی‌گرداند؛ فهرستِ کامل (شاملِ ادمین) فقط در dev-mode (نشانهٔ `HI`).
