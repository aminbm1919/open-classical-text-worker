# طراحیِ مرحلهٔ Neon (پیکرهٔ سند) — سندِ تحویل برای چتِ بعدی

> **این سند برای ازسرگیریِ سرد است.** چتِ قبلی حافظهٔ Qdrantِ **حافظهٔ GPT** را کامل پیاده کرد (نشانه‌های V→Z). این سند مرحلهٔ بعدی را طراحی می‌کند: **بردارهای پیکرهٔ سند → Neon (pgvector، ۱۰ پروژهٔ موضوع‌محور)**. خط‌شماره‌ها «در زمانِ این نشست» است و ممکن است جابه‌جا شود — همیشه با **نامِ تابع** grep کن.

> ⚠️ **به‌روزرسانیِ ۲۰۲۶-۰۶-۱۵:** خط‌شماره‌های این سند سیستماتیک کهنه‌اند (۲۰ تا ~۴۰۰ خط جابه‌جا) و چند ادعای کدی غلط دارد (مثلِ «INSERT OR REPLACE» که در کد نیست، و کامنتِ soft-fail در L14758 نه L9620). نقشهٔ آمادگیِ کامل + لنگرهای واقعی + DDLِ اصلاح‌شده در `NEON_CORPUS_SCHEMA.sql` و `NEON_PHASE1_SETUP.md`. همیشه grep کن.

---

## مرحلهٔ ۰ب) مقدمهٔ AI — تخصیصِ کارها (قطعی‌شده ۲۰۲۶-۰۶-۱۵)

> پیش از ساختِ نئون، دو کارِ AI **به‌عنوان مقدمه** به NVIDIA برون‌سپاری می‌شوند تا ظرفیت/CPUِ Cloudflare آزاد بماند. جزئیاتِ پرامپت و مدل‌ها در `TOPIC_CLASSIFIER.md`. تأییدِ هم‌فضاییِ امبدینگ منتظرِ تستِ `/embed-compare` است (نیازمندِ سکرتِ `NVIDIA_API_KEY`).

**چهار کارِ AI و محلِ اجرا:**
1. **امبدینگ** — `bge-m3` (۱۰۲۴، cosine). مدلِ مشترکِ **هم‌فضا** روی هر دو ارائه‌دهنده: CF `@cf/baai/bge-m3` و NVIDIA `baai/bge-m3` (عینِ یک checkpoint، CLS pooling، instruction-free، ۱۰۰+ زبان). **برون‌سپاری به NVIDIA** (پیکره/بک‌فیل؛ بی‌نیاز به سرعت). زیرِ cosine اختلاط امن است (فقط جهتِ بردار مهم است، نه طول)؛ بیمه: L2-normalizeِ سمتِ کلاینت، chunk ≤۸۱۹۲ توکن، `truncate=END`، بدونِ `input_type`.
2. **تعیینِ مسیرِ نوشتن** (موضوعِ سندِ مادر — یک‌بار، دائمی) — **NVIDIA `meta/llama-3.3-70b-instruct`** + `guided_json` (escalate به `meta/llama-3.1-405b-instruct` برای `confidence=low`). بی‌نیاز به سرعت، اولویت با دقت.
3. **تعیینِ مسیرِ کوئریِ سرچ** (کدام پروژه‌ها) — **Cloudflare `@cf/meta/llama-3.1-8b-instruct`** + همان پرامپتِ کامل. مسیرِ داغ → هم‌مکان/سریع/کش‌شونده. سیاست: ۱ / اغلب ۲ / استثنائاً تا ۵، **هرگز نامربوط**؛ و طبقِ قاعدهٔ یونیفایدسرچ **همیشه + مموریِ Qdrant** (غیرموضوعی) + لغویِ FTS.
4. **تلفیق** — `RRF` (k=۶۰): **الگوریتم، نه AI**؛ از قبل در کد هست، فقط به N پروژه + مموری + لغوی گسترش می‌یابد. (ریرنکِ cross-encoder اختیاری/آینده روی CF.)

**نوشتن تک‌مقصد، خواندن چندمقصد.** موضوعِ هر سند یک‌بار محاسبه و روی `document_cache_registry` (ستونِ `topic`) کش می‌شود؛ بدونِ ذخیرهٔ دوگانه.

**فلگ‌های backend (همه پیش‌فرض خاموش/CF):** `embedding_backend = cf|nvidia` · `classifier_backend = cf|nvidia` · سکرتِ `NVIDIA_API_KEY`. fallbackِ خودکار به CF هنگامِ خطا/۴۲۹/۴۰۳ (تیرِ رایگانِ NVIDIA «فقط ارزیابی» است + endpointِ بیرونی).

**نکتهٔ بازِ کوچک (پس از تست قطعی شود):** ارائه‌دهندهٔ امبدینگِ *کوئری* — NVIDIA (هم‌خوانِ تضمینی، یک hopِ خارجی روی مسیرِ داغ) یا CF (سریع‌تر، اختلاطِ امن‌زیرِ-cosine). تستِ `/embed-compare` (کسینوسِ هم‌متن ≥۰٫۹۹۹) تصمیم می‌گیرد.

---

## ۰) وضعیتِ فعلی (آنچه از قبل انجام شده)

- **حافظهٔ GPT کاملاً روی Qdrant است** (یک کلاستر، collection `oct_memory`، ۱۰۲۴/Cosine):
  - `fa032ba` آداپتورِ Qdrant (fetch) · `9efcca7` dual-write + خواندن · `b6a6213` backfill + آینهٔ حذف · `2b11f81` سینکِ بادوامِ pending + دامنهٔ تخلیه.
  - فلگ‌های زنده در `storage_policy`: `enable_qdrant_memory=true`، `qdrant_memory_write=true`، `memory_vector_backend=qdrant`. سکرت‌ها: `QDRANT_URL`، `QDRANT_API_KEY`.
  - تک‌مدل: **bge-m3، ۱۰۲۴ بُعد، Cosine** (bge-large بازنشسته — نشانه T). همه‌جا همین.
- **نشانهٔ نسخهٔ بعدی: از `AA` شروع کن** (آخرین `_Z_QDRANT_MEMORY_PENDING_SYNC_AND_EVICTION_SCOPE`). الگوی کامنتِ انتهای `worker.js` و دستورِ دیپلوی در `CLAUDE.md`.
- **منبعِ واحد:** `worker.js` (~۲۶هزار خط، بدونِ build/package.json). دیپلوی: `wrangler deploy --keep-vars`. تست: endpointهای زنده + `wrangler d1 execute classical_text_index --remote`.
- **امنیت:** کاربر کلیدهای Qdrant/admin/memory-write را در چت داد و قرار است rotate کند؛ اگر rotate شد، سکرت‌ها را دوباره `wrangler secret put` کن.

---

## ۱) هدف و معماری

**هدف:** بردارهای پیکره (چانک‌های سندِ امتیازخورده/`scored_cache`) در **Neon/pgvector** ذخیره شوند (نه CF Vectorize)، موضوع‌محور روی ۱۰ پروژه؛ و شاخهٔ برداریِ جست‌وجوی سند از Neon بخواند و با FTSِ لغوی از طریقِ **RRFِ موجود** تلفیق شود.

**چرا Neon برای پیکره (و Qdrant برای حافظه):** پیکره بزرگ است → Neon ۵GBِ رایگان (۰٫۵GB × ۱۰ پروژه) می‌دهد؛ حافظه کوچک است → یک کلاسترِ Qdrant. این دو **افزونه نیستند**، دادهٔ متفاوت دارند.

**تصمیم‌های قطعی‌شده (در چت قبل):**
- تک‌مدل **bge-m3 (۱۰۲۴، Cosine)** — schemaهای Neon هم `vector(1024)` + HNSW `vector_cosine_ops`اند.
- روتینگِ موضوعی با **centroid** (بازاستفاده از بردارِ پرسش؛ بدونِ کلاسیفایرِ جدا). ۵ موضوع × ۲ پروژه: ۰۰/۰۱ علومِ طبیعی+مهندسی+ریاضی+AI · ۰۲/۰۳ فلسفه/منطق/زبان‌شناسی · ۰۴/۰۵ تاریخ · ۰۶/۰۷ سیاست/روابطِ بین‌الملل/ژئوپلیتیک · ۰۸/۰۹ علومِ جسم‌وذهن‌وجامعه.
- «اولی پر شد، دومی فعال» (fill-first-then-overflow per topic).
- `target_shards` صریح؛ بدونِ fan-outِ خودکار به همه.
- **ریرنک** با `@cf/baai/bge-reranker-base` (CF Workers AI) — در ورکر، روی نامزدهای ادغام‌شده. (اختیاری، فاز بعد.)
- merge/dedup و read/evidence در ورکر.

---

## ۲) تنشِ کلیدی: گامِ build (تصمیمِ اول)

ورکر **تک‌فایلِ بی‌build** است. برخلافِ Qdrant (که با `fetch` خالص حل شد)، Neon از Worker نیاز به **درایورِ Postgres** دارد:
- **توصیه‌شده:** درایورِ سرورلسِ Neon `@neondatabase/serverless` (HTTP، نه Hyperdrive). تابعِ `neon(connStr)` کوئریِ تک‌شات HTTP می‌زند — بدونِ pooling/Hyperdrive، بدونِ سقفِ ۱۰‌تاییِ Hyperdrive. روی پلنِ رایگانِ Worker هم کار می‌کند.
- **هزینه:** افزودنِ `package.json` + `npm i @neondatabase/serverless` + اجازه‌دادن به wrangler برای bundle. این تنها تغییرِ مدلِ دیپلوی است (از این پس `npm install` لازم است). wrangler خودکار bundle می‌کند.
- **جایگزینِ بدونِ build (شکننده):** صداکردنِ مستقیمِ endpointِ HTTP SQLِ Neon با `fetch` — توصیه نمی‌شود (پروتکل غیرمستند/شکننده).
- **Hyperdrive لازم نیست** و برای این بار (کم‌ترافیک، کوئریِ یکتا، ۱۰ دیتابیس) ارزشِ افزوده ندارد (سقفِ ۱۰/۲۵ config را هم پر می‌کند). جزئیات در گفت‌وگوی چت قبل.
- **پیش‌نیازِ کاربر:** ۱۰ connection-string (هر پروژه) را به‌صورتِ secret بدهد: `NEON_00 … NEON_09` (یا الگویی که انتخاب می‌کنی). در چت نفرست؛ خودش `wrangler secret put` کند.

> اگر گامِ build نامطلوب بود، می‌توان کلِ پیکره را هم روی Qdrant گذاشت (یک collection + فیلترِ payloadِ موضوع) و Neon را کنار گذاشت — ولی کاربر صریحاً Neon را برای ذخیرهٔ بزرگ‌ترِ پیکره می‌خواهد. اول این تصمیم را با کاربر قطعی کن.

---

## ۳) schemaی Neon (کاربر در هر ۱۰ پروژه ساخته)

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS vector_segments (
  vector_id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL, owner_key TEXT NOT NULL,
  source_ref TEXT, document_cache_key TEXT, global_chunk_id BIGINT, cache_chunk_id BIGINT,
  memory_segment_id TEXT, vector_segment_key TEXT NOT NULL, content_hash TEXT NOT NULL,
  source TEXT, title TEXT, url TEXT,
  segment_start INTEGER, segment_end INTEGER, read_start INTEGER, read_limit INTEGER DEFAULT 12000,
  embedding_model TEXT NOT NULL, embedding_dim INTEGER NOT NULL, vector_index_key TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active', metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  embedding VECTOR(1024) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ... idx_vector_segments_owner ON vector_segments(owner_type, owner_key);
CREATE INDEX ... idx_vector_segments_document ON vector_segments(document_cache_key);
CREATE INDEX ... idx_vector_segments_status ON vector_segments(status);
CREATE INDEX ... idx_vector_segments_embedding_hnsw ON vector_segments USING hnsw (embedding vector_cosine_ops);
```
- **id:** `vector_id TEXT PRIMARY KEY` — برخلافِ Qdrant (که UUID لازم داشت)، اینجا می‌توان مستقیماً از `vector_segment_key` (یا `vector_id`ِ موجود) استفاده کرد. idempotency با `ON CONFLICT (vector_id) DO UPDATE`.
- **کوئریِ جست‌وجو:** `ORDER BY embedding <=> $1::vector LIMIT k` و `1 - (embedding <=> $1::vector) AS similarity` (کسینوس). بردار به‌صورتِ literalِ `'[v1,v2,...]'::vector` پاس شود (متن، نه آرایهٔ pg).
- موضوع را در `metadata` JSONB یا یک ستونِ `topic` نگه دار (برای فیلتر/تشخیص؛ ولی چون هر پروژه = یک موضوع، ستون اختیاری است).

---

## ۴) نقاطِ ادغامِ سورس (دقیق — موازیِ کارِ Qdrant)

### نوشتن (dual-write به Neon)
- **`handleVectorizeRunJobs`** (~L8285؛ grep `async function handleVectorizeRunJobs`). در **مسیرِ موفقِ** بعد از upsertِ CF، یک بلوکِ موازی برای `document_cache` اضافه کن (الگو: همان بلوکِ `gpt_memory`ی که `qdrantUpsertMemoryVector` را صدا می‌زند، ~بعد از UPDATEِ `gpt_memory_segments`، جایی که `embedding`، `vectorId`، `segment` در دسترس‌اند). شرط: `segment.owner_type === "document_cache"` **و** فلگِ `neon_corpus_write`. روتینگ: موضوع را از centroid (یا metadata) تعیین کن → پروژهٔ مقصد (fill-first) → upsert به Neon. **بهترین کار: همان الگوی Qdrant را تعمیم بده** (dual-write خوش‌بینانه + ستونِ `neon_sync_status` + flush). 
- **دامنه:** بردارسازیِ `document_cache` با گاردِ `U` (نشانه `_U_DOC_CACHE_VECTORIZATION_SCOPE_GUARD`) فقط برای `scored_cache` مجاز است — `handleVectorizePrepareOne` (~L10061) قبل از ساختِ سگمنت چک می‌کند `desired.active_cache_role === "scored_cache"`. پس فقط مالکانِ امتیازخورده اصلاً بردار می‌شوند → فقط همان‌ها به Neon می‌روند. خوب است.
- **خاموش بودنِ مسیرِ بردارِ سند:** بردارسازیِ سند الان عملاً خاموش است (`dry_run` پیش‌فرض + بدونِ pending jobsِ سند). پس برای پُرکردنِ Neon یا باید **backfill** بزنی (مثلِ `handleQdrantMemoryBackfill`) یا چند سندِ امتیازخورده را prepare+run کنی.

### خواندن (شاخهٔ برداریِ سند از Neon)
- زنجیرهٔ زنده: **`searchDocumentTextCache`** (~L19649) → **`searchResolvedTextChunksHybrid`** (~L19519) → لغوی `searchResolvedTextChunks` (~L19060، **دست‌نخورده بماند**) + شاخهٔ برداری `runHybridVectorBranchesForResolvedScope` (~L19300) → ادغام `dedupeAndMergeHybridCandidates` (**RRF k=60، `HYBRID_DEFAULT_RRF_WEIGHTS`** — از قبل موجود).
- **شاخهٔ برداری الان:** `runHybridVectorBranchesForResolvedScope` روی `runHybridVectorBranchForIndex(env, query, indexKey, ...)` حلقه می‌زند (`m3_cache`, `bge_large_scored_en`) و از **CF Vectorize** می‌خواند. `bge_large` بازنشسته (خالی). **fusion در حالتِ `diagnostic_light` است** (`production_fusion_enabled:false`, `final_ranking_policy:"lexical_primary_with_vector_merge"` در report، ~L19571).
- **کارِ Neon (خواندن):** در `runHybridVectorBranchForIndex` (یا `...ForResolvedScope`) یک **انتخابِ backend** بگذار — اگر `corpus_vector_backend=neon`، به‌جای CF، Neon را برای موضوع(های) مرتبط کوئری کن و نتیجه را در **همان شکلِ candidate** برگردان تا dedup/RRF بی‌تغییر کار کند. (دقیقاً مثلِ `queryVectorizeIndexForProbe` → `queryQdrantMemoryForProbe` برای حافظه.) سپس **fusion را production کن** (یا diagnostic_light را نگه دار ولی نتایجِ برداری واقعی بده).
- **routingِ خواندن:** بردارِ پرسش را یک‌بار embed کن (`embedVectorQuery`/`embedTextWithBgeM3`)، با centroidها مقایسه کن → موضوع(های) نزدیک → `target_shards` → فقط همان پروژه‌ها را کوئری کن، نتایج را merge.

### روتینگِ موضوعی (centroid)
- ۵ بردارِ centroid (میانگینِ بردارهای هر موضوع) در یک جدولِ کوچکِ D1 نگه دار؛ با cron تازه‌سازی. هنگامِ پرسش: کسینوسِ بردارِ پرسش با ۵ centroid → top-1/top-2 موضوع. هنگامِ نوشتن: موضوعِ سند از metadata/منبع یا همان centroid. (الگوی semantic-router.)
- fill-overflow: یک جدولِ کوچکِ D1 (`topic → active_project`، شمارش/بایت) تا وقتی پروژهٔ A پر شد (~۰٫۵GB) به B سوئیچ کند. خواندنِ یک موضوع = هر دو پروژه‌اش را کوئری + merge.

---

## ۵) الگوهایی که باید از کارِ Qdrant **عیناً تعمیم** دهی (قلبِ سازگاری)

توابعِ آماده در `worker.js` (grep کن) که Neon باید **هم‌شکلشان** را بسازد:
- آداپتور: `qdrantFetch`/`qdrantUpsertPoints`/`qdrantQueryPoints` → برای Neon: `neonQuery(connStr, sql, params)` با درایورِ سرورلس.
- ساختِ نقطه/payload: `buildQdrantMemoryPointPayload`/`buildQdrantMemoryPoint` → برای Neon: ردیفِ INSERT با ستون‌های schema (همهٔ فیلدها از `segment`/registry موجودند).
- نوشتن: `qdrantUpsertMemoryVector` → `neonUpsertCorpusVector(env, shard, segment, embedding)`.
- **سینکِ بادوام (نشانه Z):** ستونِ `qdrant_sync_status` روی `vector_segments`؛ dual-writeِ **خوش‌بینانه** (تلاشِ فوری → `synced`/`pending`)؛ تابعِ `flushPendingQdrantMemoryVectors` (re-embed + batch upsert، با تولیدِ بعدی + backstopِ no-jobsِ `handleVectorizeRunJobs`). برای Neon: `neon_sync_status` + `flushPendingNeonCorpusVectors`. **حتماً این را داشته باش** (وگرنه شکستِ نوشتن = شکافِ خاموشِ خواندن).
- **آینهٔ حذف + دامنهٔ تخلیه (نشانه Y/Z):** `qdrantMirrorDeleteMemoryVectorIfEnabled` بعد از **هر دو** `index.deleteByIds`ِ CF (در `submitImmediateVectorizeDeleteForPendingSegment` ~L6833 و مسیرِ run-deletes ~L9573). **نکتهٔ حیاتی:** فقط حذفِ **واقعیِ** سند را آینه کن؛ تخلیهٔ ظرفیتِ CF (نرم/سختِ ۴۵۰۰/۴۸۰۰) و فشرده‌سازی نباید به Neon آبشار کنند (سیگنالِ مقاوم: «owner هنوز فعال/معتبر است؟»). **قاعدهٔ تخلیهٔ CF دست‌نخورده می‌ماند** (`maybeRunGptMemoryCapacityEviction` و سقف‌ها را تغییر نده). توجه: تخلیهٔ ظرفیت الان فقط `gpt_memory` است؛ برای پیکره، تخلیه/سقفِ جدا (روی Neon) لازم نیست چون Neon بزرگ است — ولی حذفِ سندِ واقعی باید آینه شود.
- **اصلِ طلاییِ soft-fail:** شاخهٔ خواندنِ برداری **هرگز throw نکند** (کامنتِ ~L9620). هر کوئریِ Neon در try/catch؛ خطا → سقوطِ نرم به لغوی (FTS همیشه زنده). نوشتن fail-closed برای بُعد است (چکِ ۱۰۲۴).
- **فلگ‌گیتینگ:** همه پشتِ فلگِ `storage_policy` با پیش‌فرضِ خاموش (الگوی `isStoragePolicyEnabled(env, key, false)`). دیپلوی = بدونِ تغییرِ رفتار تا روشن‌کردن.
- **embed:** `embedTextWithBgeM3(env, text)` / `embedVectorQuery(env, policy, query)` (~L9626) — soft، بُعدچک ۱۰۲۴.
- **روتینگِ امن (مثلِ memory routes):** ادمین‌گِیتد (`isAdminRequest` ~L1775) + فلگ. مسیرهای کمکی: `/neon-corpus-status`, `/neon-corpus-backfill`, شاید `/neon-corpus-search` (تشخیصی).

---

## ۶) فلگ‌های پیشنهادی (`storage_policy`)
- `neon_corpus_write` (پیش‌فرض false) → dual-writeِ بردارِ scored_cache به Neon.
- `corpus_vector_backend` (پیش‌فرض `vectorize`) → خواندنِ شاخهٔ برداریِ سند از Neon وقتی `=neon`.
- `enable_corpus_vector_fusion` (پیش‌فرض false) → production‌کردنِ RRF (به‌جای diagnostic_light).
- `neon_corpus_topic_routing` (پیش‌فرض false در فاز اول → بعد centroid).

---

## ۷) فازبندیِ پیشنهادی (مثلِ memory، کم‌ریسک و برگشت‌پذیر)
1. **پایه/build:** `package.json` + درایورِ سرورلس + `neonQuery` helper + مسیرِ `/neon-corpus-status` (پینگِ هر ۱۰ پروژه با secret). تستِ اتصال.
2. **نوشتن (dual-write):** بلوکِ document_cache در `handleVectorizeRunJobs` (فلگ `neon_corpus_write`) + سینکِ بادوام (`neon_sync_status` + flush). روتینگِ موضوعی فعلاً ساده (یک پروژهٔ پیش‌فرض یا metadata.topic).
3. **backfill:** `handleQdrantMemoryBackfill`-معادل برای document_cache → بردارهای scored_cacheِ موجود را به Neon بریز (re-embed با همان مسیر، idempotent، bounded، dry-run).
4. **خواندن:** انتخابِ backend در `runHybridVectorBranchForIndex` (فلگ `corpus_vector_backend=neon`) + تستِ هم‌ترازیِ CF↔Neon روی دادهٔ واقعی + سپس `enable_corpus_vector_fusion`.
5. **روتینگِ موضوعی + centroid + target_shards + fill-overflow.**
6. **آینهٔ حذف (دامنه‌دار) + ریرنکِ `bge-reranker-base` (اختیاری).**

هر فاز: نشانهٔ نسخه (AA, AB, …) + `wrangler deploy --keep-vars` + تستِ دومعیاره (اعمال‌شد؟ رگرسیون؟) + کامیتِ جدا.

---

## ۸) ریسک‌ها/تصمیم‌های باز
- **گامِ build** (تصمیمِ اول با کاربر).
- **fill-overflow tracking** (جدولِ D1 شمارش/بایت per project) و کوئریِ دوپروژه‌ایِ هر موضوع + merge.
- **روتینگِ موضوعی** (centroid؛ سند تک‌موضوعی فرض می‌شود؟ پرسشِ چندموضوعی → fan-out به ۲ موضوع).
- **cold-start Neon** (scale-to-zero بعد ۵ دقیقه؛ کوئریِ اولِ هر پروژهٔ خوابیده تأخیر دارد) — برای جست‌وجوی تعاملی مهم. keep-alive با cron؟
- **سقفِ ۵GB** (مجموع روی پلنِ رایگانِ Neon — منبعِ رسمی: per-project ۰٫۵GB؛ منابعِ ثالث «۵GB aggregate»؛ در داشبورد بسنج). ~۴۰۰–۵۰۰k بردارِ ۱۰۲۴ با ایندکس.
- **production_fusion:** الان diagnostic_light؛ روشن‌کردنِ fusionِ واقعی رتبه‌بندیِ نتایج را عوض می‌کند — با تستِ کیفی.
- **بازنشستگیِ `bge_large_scored_en` در `runHybridVectorBranchesForResolvedScope`:** هنوز در فهرستِ branches هست (خالی، CF). هنگامِ کارِ خواندن می‌توان حذفش کرد (تک‌مدل).

---

## ۹) واقعیت‌های ضروریِ کد (برای ازسرگیریِ سرد)
- **مدل/بُعد:** `@cf/baai/bge-m3`، ۱۰۲۴، Cosine. ثابت‌ها: `QDRANT_EMBED_MODEL`/`QDRANT_EMBED_DIM` (الگو).
- **سیاستِ مدل:** `selectDesiredVectorPolicyForOwner` (~L6302) — همه → `m3_cache` (T).
- **گاردِ دامنه:** `handleVectorizePrepareOne` (~L10061) فقط `scored_cache` را بردار می‌کند (U).
- **نوشتنِ بردار:** `handleVectorizeRunJobs` (~L8285)؛ بلوکِ موفقِ gpt_memory (محلِ dual-writeِ Qdrant) الگوست؛ بلوکِ موازیِ document_cache بساز.
- **خواندنِ بردارِ سند:** `searchResolvedTextChunksHybrid` (~L19519) → `runHybridVectorBranchesForResolvedScope` (~L19300) → `runHybridVectorBranchForIndex` (grep). لغوی: `searchResolvedTextChunks` (~L19060، دست‌نزن). RRF: `dedupeAndMergeHybridCandidates` (k=60, `HYBRID_DEFAULT_RRF_WEIGHTS`).
- **حذفِ CF (محلِ آینه):** `submitImmediateVectorizeDeleteForPendingSegment` (~L6833) و مسیرِ run-deletes (~L9573) — هر دو `index.deleteByIds([segment.vector_id])`.
- **تخلیهٔ ظرفیتِ CF (دست‌نخورده):** `maybeRunGptMemoryCapacityEviction` (~L11561)، سقف `gpt_memory_vector_soft_cap=4500`/`hard_cap=4800` (`readGptMemoryCapacityPolicy` ~L11334). قفلِ `gpt_memory_vector_lifecycle` (C5).
- **embed (soft):** `embedVectorQuery` (~L9626)، `embedTextWithBgeM3` (آداپتورِ Qdrant).
- **فلگ‌ها:** `isStoragePolicyEnabled(env, key, false)` (~L23839)؛ جدولِ `storage_policy(key, value)`؛ ست با `INSERT OR REPLACE`.
- **ادمین:** `isAdminRequest` (~L1775)؛ هدر `X-Admin-Token` یا `?admin_token=`. مسیرها در dispatchِ `fetch` (~L450–700) با همان الگو اضافه می‌شوند.
- **بردارِ Qdrantِ حافظه (الگو برای کپی):** grep `qdrantUpsertMemoryVector`, `queryQdrantMemoryForProbe`, `flushPendingQdrantMemoryVectors`, `qdrantMirrorDeleteMemoryVectorIfEnabled`, `handleQdrantMemoryBackfill`, `buildQdrantMemoryPoint`.
- **D1 مرکزی:** `classical_text_index`؛ متنِ سند در ۹ شاردِ `DB_TEXT_01..09` (`cached_text_chunks`)؛ R2 هنوز فعال نشده (پلنِ $۵ — `R2_PHASE1_DESIGN.md`).
- **خواندنِ متنِ شاهد:** بعد از گرفتنِ ارجاعِ چانک از Neon، ورکر `readSelectedTextChunk` می‌زند (مثلِ memory) تا شاهدِ واقعی بسازد (قانونِ طلایی: نامزد ⟵ شاهد).

---

## ۱۰) اولین کارِ چتِ بعدی
1. تصمیمِ **گامِ build** را با کاربر قطعی کن (Neon-with-build در برابر Qdrant-for-corpus).
2. اگر Neon: کاربر ۱۰ connection-string را secret کند؛ تو فاز ۱ (پایه + `/neon-corpus-status`) را بساز/دیپلوی/تست کن.
3. سپس فازهای ۲→۶. هر فاز کوچک، فلگ‌گیتد، تستِ دومعیاره، کامیتِ جدا، نشانهٔ `AA…`.
4. **اول کد را با grep بخوان، بعد تغییر بده.** فارسی جواب بده. کلِ پاسخ در `show_widget` (راست‌چین، طبق `CLAUDE.md`).
