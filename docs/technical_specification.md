# مشخصات فنی (Technical Specification) — Open Classical Text Worker
### نسخهٔ `2.9.40-c.6-k-score-nonconsequential-wikisource-hint-fix`

> این سند، تابع‌به‌تابعِ کارخانه را مستند می‌کند. هر **ماشینِ اصلی** (handler) با کارتِ کامل و هر **ماشینِ کمکی** با ردیفِ «تابع | خط | نقش» می‌آید. در استعاره: هر تابع یک ماشین با ورودی/منطق/خروجی، و هر فراخوان یک لوله است. مجموعاً **۷۱۶ تابع** در **۱۵ زیرسامانه**. برای نمای کلان به `architecture.md` و برای جریان به `dfd.md` رجوع کنید.

## قراردادهای نگارش
- زبان فارسی؛ اسامی خاص به اصل (Cloudflare, Vectorize, D1, FTS5, marxists.org, …)؛ مفاهیم مهندسی + معادلِ انگلیسی در پرانتز.
- قالبِ کارتِ ماشینِ اصلی: **خط/نقش/ورودی→خروجی/منطق/انبار/لوله‌ها (← فراخوانده‌توسط، → فراخوان‌ها)**.
- شماره‌خط‌ها از تحلیلِ ایستای همین نسخه (c.6-k) استخراج شده‌اند.

## دو قانونِ طلایی (در همه‌جا اعمال می‌شوند)
1. **نامزد ⟵ شاهد:** کشف/جست‌وجو فقط نامزد می‌دهد؛ فقط `read`/`parse` شاهد می‌سازد.
2. **حافظه فقط بافتار است:** خروجی‌های `memory_context` بیرونِ RRF، امتیاز، حذفِ تکراری و استناد.

---

## بخش ۰ — ثابت‌ها، نقاط ورود و مسیریابی

### ثابت‌ها
- `WORKER_VERSION = "2.9.40-c.6-k-score-nonconsequential-wikisource-hint-fix"`
- `WORKER_MAX_READ_LIMIT = 20000` — سقفِ کاراکترِ هر خواندن.
- چهار عبارتِ Cron: `SCHEDULED_CRON_MARXISTS_MONTHLY_REINDEX="0 0 L */3 *"`، `SCHEDULED_CRON_GPT_MEMORY_VECTOR_MICROTASK="0 * * * *"`، `SCHEDULED_CRON_GPT_MEMORY_CAPACITY="17 */8 * * *"`، `SCHEDULED_CRON_CACHE_PRUNE_DAILY="33 2 * * *"`.

### دو نقطهٔ ورود
- **`fetch(request, env, ctx)`** (L10): همهٔ درخواست‌های HTTP؛ مسیر را با `normalizeRoute` نرمال و به هندلرها مسیر می‌دهد.
- **`scheduled(event, env, ctx)`** (L732): رویدادِ زمان‌بندی را با `ctx.waitUntil(runScheduledByCron(event, env))` در پس‌زمینه اجرا و بر پایهٔ عبارتِ cron به یکی از چهار کارِ نگه‌داری مسیر می‌دهد.

### جدولِ مسیر → هندلر (🔒 = نیازمندِ توکنِ ادمین)

| مسیر | هندلر | احراز |
|---|---|---|
| `/setup-db` | `setupDb` | 🔒 |
| `/index-status` | `indexStatus` | 🔒 |
| `/setup-text-db` | `setupTextDb` | 🔒 |
| `/reindex` | `(درون‌خطی)` | 🔒 |
| `/index-text` | `handleIndexText` | 🔒 |
| `/search-global-text` | `handleSearchGlobalText` |  |
| `/read-indexed-chunk` | `handleReadIndexedChunk` | 🔒 |
| `/setup-shards` | `setupShards` | 🔒 |
| `/shard-status` | `shardStatus` |  |
| `/hybrid-title-search` | `handleHybridTitleSearch` |  |
| `/hybrid-deep-search` | `handleHybridDeepSearch` |  |
| `/index-url` | `handleIndexUrl` | 🔒 |
| `/score-read-evidence` | `handleScoreReadEvidence` |  |
| `/setup-scoring` | `(درون‌خطی)` | 🔒 |
| `/setup-promotion` | `setupPromotionPolicy` | 🔒 |
| `/promotion-audit` | `handlePromotionAudit` |  |
| `/retention-status` | `handleRetentionStatus` |  |
| `/setup-memory` | `(درون‌خطی)` |  |
| `/memory-bootstrap` | `handleMemoryBootstrap` |  |
| `/memory-topics` | `handleMemoryTopics` |  |
| `/memory-read` | `handleMemoryRead` |  |
| `/memory-search` | `handleMemorySearch` |  |
| `/memory-write` | `handleMemoryWrite` |  |
| `/memory-versions` | `handleMemoryVersions` | 🔒 |
| `/setup-cache` | `setupCacheLayer` | 🔒 |
| `/setup-phase2-schema` | `setupPhaseTwoOneSchema` | 🔒 |
| `/cache-status` | `cacheStatus` |  |
| `/cache-integrity` | `handleCacheIntegrity` | 🔒 |
| `/setup-vectorize-preflight` | `setupVectorizePreflightFoundation` | 🔒 |
| `/reset-vectorize-preflight` | `handleResetVectorizePreflight` | 🔒 |
| `/vectorize-schema-audit` | `handleVectorizeSchemaAudit` |  |
| `/vectorize-status` | `handleVectorizeStatus` |  |
| `/vectorize-candidates` | `handleVectorizeCandidates` | 🔒 |
| `/vectorize-transition-owner` | `handleVectorizeTransitionOwner` | 🔒 |
| `/vectorize-mark-owner-deleted` | `handleVectorizeMarkOwnerDeleted` | 🔒 |
| `/vectorize-run-deletes` | `handleVectorizeRunDeletes` | 🔒 |
| `/vectorize-run-jobs` | `handleVectorizeRunJobs` | 🔒 |
| `/vectorize-memory-microtask` | `handleGptMemoryVectorMicrotaskRoute` | 🔒 |
| `/vectorize-memory-capacity-maintenance` | `handleGptMemoryCapacityMaintenanceRoute` | 🔒 |
| `/vectorize-memory-compact-write-window` | `handleGptMemoryWriteWindowCompactionRoute` | 🔒 |
| `/vectorize-query-probe` | `handleVectorizeQueryProbe` | 🔒 |
| `/vectorize-prepare-one` | `handleVectorizePrepareOne` | 🔒 |
| `/meta-search` | `handleUnifiedSearch` |  |
| `/unified-search` | `handleUnifiedSearch` |  |
| `/article-search` | `handleArticleSearch` |  |
| `/parse-document` | `handleParseDocument` |  |
| `/deep-search-source` | `handleDeepSearchSource` |  |
| `/search-source` | `handleSearchSource` |  |
| `/get-source` | `handleGetSource` |  |
| `/links` | `handleLinks` |  |
| `/search-text` | `handleSearchText` |  |
| `/read-chunk` | `handleReadChunk` |  |
| `/read` | `handleReadChunk` |  |
| `/search` | `handleSearchText` |  |
> توجه: مسیرهای جست‌وجو/خواندن/حافظهٔ روتین بدونِ توکن‌اند؛ نوشتنِ حافظه `MEMORY_WRITE_TOKEN` و مسیرهای ادمین `X-Admin-Token` می‌خواهند.

---
## بخش ۱ — هسته، مسیریابی و زمان‌بندی (Core / Routing / Scheduled)

«اتاقِ کنترلِ کارخانه». دو نقطهٔ ورود (`fetch`/`scheduled`) را مدیریت می‌کند و در c.6 چهار خطِ نگه‌داریِ خودکار را هدایت می‌کند.

##### `runScheduledByCron(event, env)`
- **خط:** L737 · **نقش:** مسیریابِ زمان‌بندی. عبارتِ `event.cron` را می‌خواند و به یکی از چهار کارِ نگه‌داری مسیر می‌دهد؛ عبارتِ ناشناخته → `unmapped_cron`. **لوله‌ها:** ← `scheduled` · → چهار `runScheduled*Only`.

##### `runScheduledGptMemoryVectorMicrotaskOnly(env, cron)`
- **خط:** L790 · **نقش:** cronِ ساعتیِ بردارسازیِ حافظه. `runGptMemoryQueuedVectorMicrotask` را با `require_lock:true` و `enforce_min_interval:true` و `dry_run:false` صدا می‌زند تا **یک** کارِ بردارِ حافظه را با قفل و حداقل‌فاصله پیش ببرد. **لوله‌ها:** → `runGptMemoryQueuedVectorMicrotask` (S14).

### ماشین‌های این زیرسامانه
| تابع | خط | نقش |
|---|---|---|
| `runScheduledMarxistsReindexOnly` | L764 | cronِ فصلی: بازایندکسِ کاتالوگِ marxists |
| `runScheduledGptMemoryCapacityOnly` | L819 | cronِ ۸‌ساعته: بررسی/تخلیهٔ ظرفیتِ بردارِ حافظه |
| `runScheduledCachePruneOnly` | L847 | cronِ روزانه: هرسِ کش‌های منقضی |
| `runScheduledMaintenance` | L875 | نگه‌داریِ ترکیبی (بازایندکس + هرس) — مسیرِ قدیمی |
| `runScheduledReindex` | L918 | بازایندکسِ هستهٔ marxists با اطمینان از وجودِ پایگاه |
| `requireDb` | L924 | تضمینِ وجودِ binding پایگاهِ مرکزی (در نبود، خطا) |
| `normalizeRoute` | L1842 | نرمال‌سازیِ مسیرِ ورودی (حذفِ اسلش/حروف) |
| `requireTextShards` | L2860 | تضمینِ وجودِ شاردهای متن |

---

## بخش ۲ — راه‌اندازی پایگاه و طرح‌واره (DB Setup / Schema)

«نصبِ خطِ تولید». جدول‌ها، ایندکس‌ها و سیاست‌های پیش‌فرض را می‌سازد. این ماشین‌ها هیچ قطعه/کاری تولید نمی‌کنند؛ فقط ساختار را آماده می‌کنند.

| تابع | خط | نقش |
|---|---|---|
| `setupCacheLayer` | L931 | ساختِ لایهٔ کش |
| `ensurePhaseTwoFourScoringSchema` | L1097 | تضمین/ساختِ Phase Two Four Scoring Schema |
| `ensureStoragePolicyTable` | L1189 | تضمین/ساختِ Storage Policy Table |
| `ensureCachePolicyDefaults` | L1199 | تضمین/ساختِ Cache Policy Defaults |
| `setupDb` | L1249 | ساختِ طرح‌وارهٔ پایگاهِ مرکزی |
| `setupTextDb` | L1848 | ساختِ طرح‌وارهٔ پایگاه‌های متن |
| `setupShards` | L2870 | ساختِ جدول‌های همهٔ ۹ شارد |
| `setupOneTextShard` | L3050 | ساختِ جدول‌های یک شارد |
| `setupPhaseTwoOneSchema` | L3161 | راه‌اندازی Phase Two One Schema |
| `ensurePhaseTwoOneSchema` | L3175 | تضمین/ساختِ Phase Two One Schema |
| `ensurePhaseTwoOnePolicyDefaults` | L3204 | تضمین/ساختِ Phase Two One Policy Defaults |
| `ensurePhaseTwoOneCentralSchema` | L3228 | تضمین/ساختِ Phase Two One Central Schema |
| `ensurePhaseTwoOneShardSchema` | L3317 | تضمین/ساختِ Phase Two One Shard Schema |
| `ensureColumn` | L3375 | افزودنِ ستون در صورتِ نبود |
| `setupShardsIfPossible` | L4608 | راه‌اندازی Shards If Possible |
| `ensurePromotionPolicyDefaults` | L4888 | تضمین/ساختِ Promotion Policy Defaults |
| `setupPromotionPolicy` | L4911 | ساختِ سیاستِ ترفیع |
| `setupJstorHumanAccessDb` | L25437 | ساختِ جدولِ نرخِ دسترسیِ JSTOR |

---

## بخش ۳ — کاتالوگ و ایندکسِ منبع (Source Catalog / Index)

«انبارِ ورودیِ مواد خام». از هستهٔ marxists.org پیمایش می‌کند و آثار را در `catalog_items` فهرست می‌کند.

##### `reindexMarxists(env, scope="core")`
- **خط:** L1362 · **نقش:** پیمایش و بازایندکسِ کاتالوگ. صفحه‌های دانه را می‌آورد، پیوندها را استخراج/یکتا و در `catalog_items` درج/به‌روزرسانی می‌کند. **انبار:** `D1` (`index_runs`,`catalog_items`) + marxists.org.

| تابع | خط | نقش |
|---|---|---|
| `indexStatus` | L1304 | گزارشِ وضعیتِ ایندکس |
| `reindexMarxists` | L1362 | پیمایش و بازایندکسِ کاتالوگِ marxists |
| `getMarxistsSeedPaths` | L1429 | مسیرهای دانهٔ پیمایش |
| `saveCatalogItems` | L1456 | ذخیرهٔ پیوندهای کشف‌شده |
| `buildCatalogItem` | L1505 | ساختِ رکوردِ کاتالوگ از پیوند |
| `guessYearFromPath` | L1536 | حدسِ Year From Path |
| `guessItemType` | L1541 | حدسِ Item Type |
| `guessAuthorFromPath` | L1557 | حدسِ Author From Path |
| `searchCatalog` | L1566 | جست‌وجوی داخلِ کاتالوگ |
| `rankCatalogItems` | L1580 | رتبه‌بندیِ لغویِ کاتالوگ |
| `getMarxistsTextIndexCandidates` | L2198 | نامزدهای فصلِ متن‌کامل |
| `collectHtmlCandidatesFromSeeds` | L2230 | گردآوریِ Html Candidates From Seeds |

---

## بخش ۴ — شاردینگ متن (Text Sharding / Storage)

«انبارهای متنِ تک‌نسخه‌ای». متنِ سنگین فقط یک‌بار در یکی از ۹ شارد می‌نشیند؛ هنگام پُری، قطعه‌های کم‌ارزش بیرون می‌روند.

##### `searchAllTextShards(env, query, options)`
- **خط:** L3802 · **نقش:** جست‌وجوی لغویِ هم‌زمان روی همهٔ شاردها (قلمروِ `marxists_local`). پرس‌وجوی FTS5 می‌سازد، روی هر شارد اجرا و با `scoreShardLexicalResult` امتیاز و ادغام می‌کند. **انبار:** ۹ شارد (`local_text_chunks_fts`).

| تابع | خط | نقش |
|---|---|---|
| `scoreShardLexicalResult` | L2688 | امتیازِ Shard Lexical Result |
| `getTextShardBindings` | L2840 | کشفِ شاردهای متصل (DB_TEXT_01..09) |
| `shardStatus` | L3392 | گزارشِ سلامتِ شاردها — (c.6-k) `mode: internal_physical_shard_status`، پیش‌فرض `legacy_internal_index.included=false`، با `include_legacy=1` جدول‌های legacy فقط `diagnostic_only`/`architecture_layer=false` |
| `isLikelyStorageFullError` | L4550 | بررسیِ Likely Storage Full Error |
| `inferTierForPath` | L4616 | استنتاجِ Tier For Path |
| `normalizeTier` | L4635 | نرمال‌سازیِ Tier |
| `setStoragePolicyValue` | L4879 | setStoragePolicyValue |
| `getStoragePolicyValue` | L23196 | دریافتِ Storage Policy Value |
| `isStoragePolicyEnabled` | L23206 | بررسیِ Storage Policy Enabled |
| `getStoragePolicyInt` | L23211 | دریافتِ Storage Policy Int |
| `selectShardForCacheKey` | L24864 | نگاشتِ قطعیِ یک کلیدِ کش به یک شارد (هش‌محور) |

---
## بخش ۵ — کشفِ منبع به‌تفکیک سایت (Per-source Discovery)

بزرگ‌ترین سالن (۱۰۲ ماشین). «دریافتِ مواد خام از بیرون». الگوی مشترکِ همه «کشفِ مقاوم» است: چند «تلاش» (attempt) با پارامترهای گوناگون و در صورتِ شکست، پشتیبانِ `r.jina.ai`/`s.jina.ai`. خروجی همیشه **نامزد** است.

##### `handleSearchSource(url, env)`
- **خط:** L15370 · **نقش:** مسیریابِ جست‌وجوی تک‌منبعی. منبع را خوانده، URL را دامنه‌دار و به هندلرِ منبع (gutenberg/wikisource/jstor/core/arxiv/marxists) می‌فرستد. **لوله‌ها:** → همهٔ `handle*SearchSource`.

##### `handleArticleSearch(url, env)`
- **خط:** L20569 · **نقش:** تجمیع‌گرِ کشفِ مقالهٔ علمی. برای هر منبع با ضریبِ پیش‌واکشیِ نشست جست‌وجو می‌زند، نرمال/یکتا می‌کند و با `interleaveArticleResultsBySource` نتایج را درهم‌می‌بافد. **لوله‌ها:** → `handleCoreSearchSource`, `handleArxivSearchSource`.

##### `enforceJstorHumanRateLimit(request, url, env, details)`
- **خط:** L25497 · **نقش:** محدودیتِ نرخِ انسانی. شمارشِ ۱۰دقیقه/ساعت/روز را از `jstor_access_events` می‌خواند؛ از سقف رد شود → خطا، وگرنه رویداد را ثبت می‌کند. این مسیر فقط «یک سندِ انتخابیِ قانونی» را می‌خواند، بدونِ دورزدنِ دیوارِ پرداخت. **انبار:** `D1`.

### ماشین‌های کشف (به‌تفکیکِ نقش)
| تابع | خط | نقش |
|---|---|---|
| `handleDeepSearchSource` | L1631 | جست‌وجوی عمیقِ مبتنی بر s.jina.ai (marxists) |
| `buildMarxistsJinaQuery` | L1757 | ساختِ Marxists Jina Query |
| `extractMarxistsCandidatesFromJina` | L1767 | استخراجِ Marxists Candidates From Jina |
| `normalizeMarxistsPath` | L2259 | نرمال‌سازیِ Marxists Path |
| `resolveMarxistsReadablePath` | L2290 | حلِ Marxists Readable Path |
| `mapKnownMarxistsDownloadToHtml` | L2342 | نگاشتِ Known Marxists Download To Html |
| `isMarxistsLike` | L4938 | بررسیِ Marxists Like |
| `handleGutenbergSearchSource` | L15467 | کشف از gutendex.com با چند تلاش + ساده‌سازی |
| `buildGutenbergSearchAttempts` | L15537 | ساختِ Gutenberg Search Attempts |
| `handleMarxistsSearchSource` | L15579 | کشفِ marxists (کاتالوگ + پیمایشِ زنده) |
| `mergeMarxistsSearchResults` | L15669 | ادغامِ Marxists Search Results |
| `handleWikisourceSearchSource` | L15684 | کشف از Wikisource با MediaWiki API |
| `buildWikisourceSearchAttempts` | L15762 | ساختِ Wikisource Search Attempts |
| `handleWikisourceGetSource` | L15791 | هندلرِ مسیر Wikisource Get Source |
| `simplifyWikisourceSearchResult` | L15803 | ساده‌سازیِ Wikisource Search Result |
| `fetchWikisourceMetadata` | L15821 | واکشیِ Wikisource Metadata |
| `fetchWikisourceTextFromRequest` | L15866 | واکشیِ Wikisource Text From Request |
| `fetchWikisourceText` | L15871 | واکشیِ Wikisource Text |
| `getWikisourcePageInput` | L15922 | دریافتِ Wikisource Page Input |
| `getWikisourceLang` | L15944 | دریافتِ Wikisource Lang |
| `wikisourceApiUrl` | L15954 | wikisourceApiUrl |
| `wikisourcePageUrl` | L15962 | wikisourcePageUrl |
| `normalizeWikisourceTitle` | L15970 | نرمال‌سازیِ Wikisource Title |
| `normalizeWikisourceTitleForOperation` | L15974 | نرمال‌سازیِ Wikisource Title For Operation |
| `parseWikisourceUrl` | L15980 | تجزیهٔ Wikisource Url |
| `normalizeJstorUrl` | L16022 | نرمال‌سازیِ Jstor Url |
| `extractJstorSearchResults` | L16039 | استخراجِ Jstor Search Results |
| `extractJstorMetadata` | L16081 | استخراجِ Jstor Metadata |
| `extractMetaTags` | L16108 | استخراجِ Meta Tags |
| `collectMetaValues` | L16133 | گردآوریِ Meta Values |
| `getHtmlAttribute` | L16153 | دریافتِ Html Attribute |
| `extractHtmlTitle` | L16159 | استخراجِ Html Title |
| `resolveCoreParseTarget` | L16641 | حلِ Core Parse Target |
| `normalizeCoreRelevanceText` | L19396 | نرمال‌سازیِ Core Relevance Text |
| `cleanCoreAbstractLabel` | L19407 | پاک‌سازیِ Core Abstract Label |
| `passesCoreRelevanceGate` | L19456 | دروازهٔ ربط‌سنجیِ CORE |
| `interleaveArticleResultsBySource` | L20706 | درهم‌بافتنِ Article Results By Source |
| `groupArticleResultsBySource` | L20717 | گروه‌بندیِ Article Results By Source |
| `summarizeArticleCountsBySource` | L20728 | خلاصه‌سازیِ Article Counts By Source |
| `dedupeArticleResultsWithinSource` | L20736 | حذفِ تکراریِ Article Results Within Source |
| `normalizeArticleDiscoveryResults` | L20753 | نرمال‌سازیِ Article Discovery Results |
| `dedupeArticleResults` | L20778 | حذفِ تکراریِ Article Results |
| `handleCoreSearchSource` | L20795 | کشفِ متن‌کاملِ CORE با دروازهٔ ربط و یافتنِ PDF |
| `runCoreAttempts` | L20883 | اجرای Core Attempts |
| `buildCoreSearchAttempts` | L20962 | ساختِ Core Search Attempts |
| `getCoreApiKey` | L21031 | دریافتِ Core Api Key |
| `normalizeCoreSearchResults` | L21046 | نرمال‌سازیِ Core Search Results |
| `normalizeCoreUrl` | L21092 | نرمال‌سازیِ Core Url |
| `findCorePdfUrl` | L21111 | یافتنِ نشانیِ PDF در رکوردِ CORE |
| `normalizeCoreAuthors` | L21141 | نرمال‌سازیِ Core Authors |
| `handleCoreGetSource` | L21152 | هندلرِ مسیر Core Get Source |
| `handleArxivSearchSource` | L21211 | کشف از export.arxiv.org و تجزیهٔ Atom |
| `buildArxivSearchAttempts` | L21314 | ساختِ Arxiv Search Attempts |
| `isAdvancedArxivQuery` | L21362 | بررسیِ Advanced Arxiv Query |
| `escapeArxivQuotedPhrase` | L21366 | escapeArxivQuotedPhrase |
| `tokenizeArxivTerms` | L21374 | توکن‌سازیِ Arxiv Terms |
| `buildArxivSearchQuery` | L21383 | ساختِ Arxiv Search Query |
| `parseArxivAtomEntries` | L21391 | تجزیهٔ مدخل‌های Atomِ arXiv |
| `extractXmlTag` | L21439 | استخراجِ Xml Tag |
| `decodeXmlEntities` | L21444 | رمزگشاییِ Xml Entities |
| `normalizeArxivId` | L21453 | نرمال‌سازیِ Arxiv Id |
| `handleArxivGetSource` | L21461 | هندلرِ مسیر Arxiv Get Source |
| `fetchWithRetry` | L21487 | واکشیِ مقاوم با تلاشِ مجدد و درکِ محدودیتِ نرخ |
| `parseRetryAfterMs` | L21511 | تجزیهٔ Retry After Ms |
| `rateLimitAwareError` | L21528 | محدودیتِ نرخِ Limit Aware Error |
| `pageSizeHintForMetaSearch` | L21543 | pageSizeHintForMetaSearch |
| `handleMetaSearch` | L21547 | فراجست‌وجوی چندمنبعی |
| `normalizeMetaSearchResults` | L21649 | نرمال‌سازیِ Meta Search Results |
| `handleGetSource` | L21678 | مسیریابِ دریافتِ یک سند از منبع |
| `handleLinks` | L21746 | استخراجِ پیوندهای یک صفحهٔ marxists |
| `fetchMarxistsPage` | L22696 | واکشیِ صفحهٔ marxists پس از اعتبارسنجیِ مسیر |
| `validateMarxistsPath` | L22720 | اعتبارسنجیِ Marxists Path |
| `fetchGutenbergBook` | L22726 | واکشیِ Gutenberg Book |
| `simplifyGutenbergBook` | L22742 | ساده‌سازیِ Gutenberg Book |
| `listGutenbergReadableFormats` | L22772 | listGutenbergReadableFormats |
| `scoreGutenbergFormat` | L22796 | امتیازِ Gutenberg Format |
| `fetchBestGutenbergReadableText` | L22811 | واکشیِ Best Gutenberg Readable Text |
| `validateGutenbergUrl` | L22836 | اعتبارسنجیِ Gutenberg Url |
| `fetchReadableUrl` | L22850 | واکشیِ یک نشانیِ عمومی و تبدیل به متن |
| `extractLinks` | L22986 | استخراجِ پیوند از HTML |
| `rankLinks` | L23029 | رتبه‌بندیِ پیوند |
| `dedupeLinks` | L23070 | یکتاسازیِ پیوند |
| `extractCoreIdFromRef` | L24399 | استخراجِ Core Id From Ref |
| `extractCoreIdFromUrl` | L24404 | استخراجِ Core Id From Url |
| `extractArxivIdFromUrl` | L24409 | استخراجِ Arxiv Id From Url |
| `extractJstorStableId` | L24414 | استخراجِ Jstor Stable Id |
| `isJstorParseRequest` | L25459 | بررسیِ Jstor Parse Request |
| `jstorHumanLimitConfig` | L25466 | jstorHumanLimitConfig |
| `getJstorClientKey` | L25478 | دریافتِ Jstor Client Key |
| `handleJstorSearchSource` | L25568 | کشفِ مقاومِ JSTOR (HTML مرورگرمانند + پشتیبانِ Jina) |
| `handleJstorGetSource` | L25660 | هندلرِ مسیر Jstor Get Source |
| `fetchJstorTextFromRequest` | L25680 | واکشیِ Jstor Text From Request |
| `fetchJstorPageFromRequest` | L25690 | واکشیِ Jstor Page From Request |
| `buildJstorTargetUrl` | L25774 | ساختِ Jstor Target Url |
| `buildJstorBrowserHeaders` | L25831 | ساختِ Jstor Browser Headers |
| `searchJstorViaJina` | L25842 | جست‌وجوی سایتِ JSTOR از طریقِ s.jina.ai |
| `extractJstorCandidatesFromJina` | L25864 | استخراجِ Jstor Candidates From Jina |
| `extractJstorReaderMetadata` | L25909 | استخراجِ Jstor Reader Metadata |

| `normalizeWikisourceLang(lang)` | L16156 | نرمال‌سازیِ کدِ زبانِ Wikisource (c.6-k) |
| `stripDuplicateWikisourceLangPrefix(title)` | L16162 | حذفِ پیشوندِ زبانِ دوگانه از عنوان (c.6-k) |
| `normalizeWikisourceTarget(lang, title)` | L16179 | ساختِ هدفِ متعارفِ Wikisource (c.6-k) |
| `canonicalizeWikisourceRef(ref)` | L16195 | متعارف‌سازیِ ارجاع به `wikisource:lang:title` (c.6-k) |

---

## بخش ۶ — تجزیه و کشِ سند (Parse Document / Document Cache)

«سالنِ تجزیه و انبارِ میانی». یک سند را واکشی/تجزیه، قطعه‌بندی و در کشِ منبع‌محور می‌نویسد. کش **کش-اول، دارای بررسیِ یکپارچگی و خودترمیم** است.

##### `handleParseDocument(request, url, env)`
- **خط:** L16219 · **نقش:** هندلرِ اصلیِ تجزیه. هویتِ کش را می‌سازد و **اول کش را می‌خواند**؛ در نبود، هدف را حل، (در صورتِ JSTOR) نرخ را اعمال، با `parseTargetWithJinaFallback` متن را می‌گیرد، قطعه‌بندی و با `writeDocumentCache` می‌نویسد. **انبار:** `D1` + شارد + منبعِ بیرونی. **لوله‌ها:** → `readDocumentCache`, `resolveParseDocumentTarget`, `enforceJstorHumanRateLimit`, `parseTargetWithJinaFallback`, `makeCacheStorageChunks`, `writeDocumentCache`.

##### `readDocumentCache(env, identity)`
- **خط:** L24607 · **نقش:** خواندنِ کش-اول. ردیفِ `ready` را می‌خواند؛ منقضی→علامتِ انقضا؛ یکپارچگی را می‌سنجد و در صورتِ خرابی `markDocumentCacheBroken` می‌زند؛ وگرنه قطعه‌ها را از شارد می‌خواند. **انبار:** `D1` + شارد.

### ماشین‌های تجزیه/کش
| تابع | خط | نقش |
|---|---|---|
| `applyPromotionToDocumentCacheOwner` | L5048 | اعمالِ Promotion To Document Cache Owner |
| `loadSegmentTextForDocumentCache` | L7958 | بارگذاریِ Segment Text For Document Cache |
| `applyScoreToDocumentCacheOwner` | L11834 | اعمالِ Score To Document Cache Owner |
| `buildCacheSearchInsideHint` | L16165 | ساختِ Cache Search Inside Hint |
| `buildCacheReadHint` | L16180 | ساختِ Cache Read Hint |
| `buildParseDocumentCacheHandoff` | L16195 | ساختِ Parse Document Cache Handoff |
| `resolveParseDocumentTarget` | L16571 | تعیینِ نشانیِ قابل‌تجزیه بسته به منبع |
| `fetchCoreWorkForParse` | L16684 | واکشیِ Core Work For Parse |
| `unwrapCoreRawWorks` | L16748 | بازکردنِ Core Raw Works |
| `extractCoreFullTextFromRaw` | L16758 | استخراجِ Core Full Text From Raw |
| `buildCoreParseUrlCandidates` | L16783 | ساختِ Core Parse Url Candidates |
| `parseInlineDocumentText` | L16852 | تجزیهٔ Inline Document Text |
| `parseTargetWithJinaFallback` | L16867 | تجزیهٔ متن (مستقیم → r.jina.ai) |
| `looksLikeReaderErrorPage` | L16890 | تشخیصِ Like Reader Error Page |
| `parseUrlWithJinaReader` | L16900 | تجزیهٔ Url With Jina Reader |
| `findDocumentSearchChunks` | L16937 | یافتنِ Document Search Chunks |
| `scoreDocumentMatch` | L17032 | امتیازِ Document Match |
| `sliceDocumentChunk` | L17065 | برشِ Document Chunk |
| `makeDocumentChunkMap` | L17080 | ساختِ Document Chunk Map |
| `getParseDocumentDirectUrl` | L17104 | دریافتِ Parse Document Direct Url |
| `normalizePossiblyEncodedUrl` | L17130 | نرمال‌سازیِ Possibly Encoded Url |
| `decodeBase64UrlToString` | L17148 | رمزگشاییِ Base64 Url To String |
| `validatePublicHttpUrl` | L17158 | اعتبارسنجیِ ضدِ SSRF |
| `normalizeDoi` | L17189 | نرمال‌سازیِ Doi |
| `buildDocumentCacheResolvedChunks` | L18717 | ساختِ Document Cache Resolved Chunks |
| `loadDocumentCacheSampleForDuplicateRecheck` | L20380 | بارگذاریِ Document Cache Sample For Duplicate Recheck |
| `normalizeCoreWork` | L21057 | نرمال‌سازیِ Core Work |
| `getTextForDocumentCacheKey` | L21852 | دریافتِ Text For Document Cache Key |
| `buildParseDocumentReadHintFromUrl` | L23738 | ساختِ Parse Document Read Hint From Url |
| `buildParseDocumentSearchInsideHint` | L23748 | ساختِ Parse Document Search Inside Hint |
| `buildParseDocumentContinuation` | L23760 | ساختِ Parse Document Continuation |
| `buildDocumentCacheIdentity` | L24339 | ساختِ کلیدِ منبع‌محورِ کش (core:id:/arxiv:id:/marxists:path:/…) |
| `getParseDocumentDirectUrlSafe` | L24391 | دریافتِ Parse Document Direct Url Safe |
| `normalizeCacheTitle` | L24395 | نرمال‌سازیِ Cache Title |
| `canonicalizePublicUrlForCache` | L24419 | canonicalizePublicUrlForCache |
| `makeCacheStorageChunks` | L24431 | برشِ متن به قطعه (~۲۴هزار کاراکتر، زیرِ سقفِ ۲MB) |
| `normalizeDocumentCacheKeyInput` | L24442 | نرمال‌سازیِ Document Cache Key Input |
| `inspectDocumentCacheIntegrity` | L24446 | بررسیِ یکپارچگیِ فیزیکیِ کش |
| `handleCacheIntegrity` | L24572 | مسیرِ ادمینِ بررسیِ یکپارچگیِ کش |
| `markDocumentCacheBroken` | L24597 | علامتِ خرابیِ کش (پایهٔ خودترمیمی) |
| `writeDocumentCache` | L24696 | نوشتنِ متنِ تجزیه‌شده در کش (شارد + رجیستری) |
| `inferSourceFromCacheKey` | L24850 | استنتاجِ Source From Cache Key |
| `inferSourceFromSourceRef` | L24854 | استنتاجِ Source From Source Ref |
| `resolveDocumentCacheTtlDays` | L24870 | تعیینِ TTL بر پایهٔ منبع/امتیاز |
| `buildCacheReport` | L24880 | ساختِ Cache Report |
| `markDocumentCacheRead` | L24890 | علامت‌گذاریِ Document Cache Read |
| `incrementDocumentCacheSeen` | L24941 | incrementDocumentCacheSeen |
| `pruneExpiredCaches` | L24952 | هرسِ کش‌های منقضی |
| `cacheStatus` | L25010 | گزارشِ وضعیتِ کش — (c.6-k) `mode: cache_architecture_status` با سه لایهٔ `discovery_cache`/`document_cache`/`scored_cache` + `document_cache_shards` و `deprecated_aliases` |
| `mergePhaseOneCacheReports` | L25241 | ادغامِ Phase One Cache Reports |
| `buildPhaseOneCacheReports` | L25268 | ساختِ Phase One Cache Reports |

---

## بخش ۷ — جست‌وجوی ترکیبی و لغویِ محلی (Hybrid / Lexical Local Search)

«سالنِ جست‌وجوی درون‌متن». روی متنِ کش/شارد دو شاخه را اجرا و تلفیق می‌کند: لغوی (FTS5 + امتیازِ میدانی) و برداری (نزدیک‌ترین همسایه). خروجی نامزد است؛ خواندن شاهد می‌سازد.

##### `handleSearchText(url, env)`
- **خط:** L22229 · **نقش:** «جست‌وجوی درون متنِ انتخاب‌شده». دامنه را با `resolveSearchScope` حل، `searchResolvedTextChunksHybrid` را اجرا و با `projectResultForGpt` به نامزد تبدیل می‌کند. **انبار:** شارد/کش + (اختیاری) Vectorize.

##### `handleReadChunk(url, env)`
- **خط:** L22363 · **نقش:** «خواندنِ قطعه» — تبدیلِ نامزد به **شاهد**. **(c.6-k گاردِ مالکیت):** اگر `cache_chunk_id` بدونِ مالک بیاید → `ambiguous_cache_chunk_id_requires_owner`؛ اگر مالک ناهماهنگ باشد → `read_owner_mismatch`. در غیرِ این صورت بسته به نوعِ مالک `markDocumentCacheRead`/`markGlobalChunkRead` و سپس `createReadEvent` با `evidence_scope:"selected_chunk"` می‌زند. **انبار:** `D1` (`read_events`) + شارد/کش.

### ماشین‌های لغوی/ترکیبی
| تابع | خط | نقش |
|---|---|---|
| `handleIndexText` | L1942 | ایندکسِ متن در شاردها (ادمین) |
| `handleSearchGlobalText` | L2051 | جست‌وجوی متنِ سراسری روی شاردها |
| `handleReadIndexedChunk` | L2130 | خواندنِ یک قطعهٔ ایندکس‌شده |
| `makeTextChunks` | L2461 | برشِ متن با هم‌پوشانی |
| `findChunkBoundary` | L2497 | یافتنِ Chunk Boundary |
| `normalizeTextForIndex` | L2514 | نرمال‌سازیِ Text For Index |
| `extractTitleFromText` | L2523 | استخراجِ Title From Text |
| `buildFtsQuery` | L2538 | ساختِ پرس‌وجوی FTS5 |
| `uniqueFtsTerms` | L2545 | یکتاسازیِ Fts Terms |
| `quoteFtsValue` | L2563 | نقل‌قولِ Fts Value |
| `buildFtsQueryAnd` | L2567 | ساختِ Fts Query And |
| `buildFtsQueryOr` | L2573 | ساختِ Fts Query Or |
| `minimumShouldMatchCount` | L2584 | minimumShouldMatchCount |
| `uniqueNormalizedTerms` | L2593 | یکتاسازیِ Normalized Terms |
| `countTermOccurrencesForRelevance` | L2609 | شمارشِ Term Occurrences For Relevance |
| `hasTermsInSameSentenceText` | L2613 | بررسیِ Terms In Same Sentence Text |
| `lexicalFieldScore` | L2627 | امتیازِ لغویِ میدانی |
| `passesMinimumLexicalGate` | L2682 | دروازهٔ Minimum Lexical Gate |
| `makeSnippet` | L2749 | ساختِ Snippet |
| `handleHybridTitleSearch` | L3446 | جست‌وجوی ترکیبیِ مبتنی بر عنوان |
| `searchGlobalDocumentsByTitle` | L3518 | جست‌وجوی Global Documents By Title |
| `mergeTitleCandidates` | L3571 | ادغامِ Title Candidates |
| `handleHybridDeepSearch` | L3603 | جست‌وجوی عمیقِ ترکیبی |
| `buildUrlContext` | L4055 | ساختِ Url Context |
| `handleIndexUrl` | L4091 | هندلرِ مسیر Index Url |
| `collectTermPositions` | L17005 | گردآوریِ Term Positions |
| `tokenizeSearchTerms` | L17023 | توکن‌سازیِ Search Terms |
| `rangesOverlapEnough` | L17059 | rangesOverlapEnough |
| `firstMatchIndexForResolvedChunk` | L18068 | یافتنِ اولین Match Index For Resolved Chunk |
| `buildMiniExtractiveMapFromResolvedChunk` | L18084 | ساختِ Mini Extractive Map From Resolved Chunk |
| `normalizeResolvedTextChunkSearchItem` | L18105 | نرمال‌سازیِ Resolved Text Chunk Search Item |
| `searchResolvedTextChunks` | L18189 | شاخهٔ لغویِ خالص روی قطعه‌های حل‌شده |
| `normalizeHybridLexicalCandidate` | L18309 | نرمال‌سازیِ Hybrid Lexical Candidate |
| `rangesOverlapRatio` | L18486 | rangesOverlapRatio |
| `searchResolvedTextChunksHybrid` | L18644 | هستهٔ جست‌وجوی ترکیبی (لغوی + برداری + تلفیق) |
| `lexicalScoreContribution` | L19532 | lexicalScoreContribution |
| `getTextForSourceRef` | L21836 | دریافتِ Text For Source Ref |
| `resolveSelectedTextTargetForSearch` | L21976 | حلِ Selected Text Target For Search |
| `inferSearchScopeKind` | L21998 | استنتاجِ Search Scope Kind |
| `buildResolvedTextUnitFromSearchTarget` | L22008 | ساختِ Resolved Text Unit From Search Target |
| `chunkSelectedTextForResolvedSearch` | L22041 | chunkSelectedTextForResolvedSearch |
| `resolveSearchScope` | L22107 | حل‌کنندهٔ دامنه (از ارجاع/کلید/شناسه به قطعه‌های حل‌شده) |
| `extractiveMapFromResolvedResults` | L22134 | extractiveMapFromResolvedResults |
| `buildExtractiveMap` | L22161 | ساختِ Extractive Map |
| `makeSearchInsideCandidate` | L22190 | ساختِ Search Inside Candidate |
| `getTextForSource` | L22500 | دریافتِ Text For Source |
| `searchText` | L22874 | جست‌وجوی Text |
| `splitParagraphsWithOffsets` | L22951 | تقسیمِ Paragraphs With Offsets |

---
## بخش ۸ — چرخهٔ حیاتِ بردارسازی (Vectorization Lifecycle)

«خطِ تولیدِ بردار». متنِ مالکان (کشِ سند، قطعهٔ سراسری، قطعهٔ حافظه) را به بردار تبدیل و در Vectorize نگه می‌دارد. اصلِ طراحی **جداسازیِ مرحله‌ها**: آماده‌سازی هرگز embedding صدا نمی‌زند؛ فقط اجرا embedding/upsert می‌کند. دو مدل: `bge-m3` (چندزبانه، شاملِ فارسی) و `bge-large-en` (انگلیسیِ امتیازخورده).

##### `handleVectorizePrepareOne(url, env)`
- **خط:** L9811 · **نقش:** آماده‌سازیِ یک مالک. قطعه‌ها را طرح، تکراری‌بودن را بررسی، و قطعه/کارِ `pending` را درج می‌کند. **هرگز** embedding یا upsert نمی‌کند. **انبار:** `D1`.

##### `handleVectorizeRunJobs(url, env)`
- **خط:** L8094 · **نقش:** اجرای کارهای معلق. کار را می‌یابد، **هشِ محتوا را اعتبارسنجی** می‌کند، با `claimVectorizationJob` قفل می‌کند، با `env.AI.run(model)` بردار می‌سازد و در Vectorize `upsert` می‌کند؛ در خطای سهمیه زمانِ ازسرگیری می‌دهد. **انبار:** `D1` + Workers AI + Vectorize.

### ماشین‌های بردار (شناسه/طرح/اجرا/انتقال/حذف/کاوش/فشرده‌سازی)
| تابع | خط | نقش |
|---|---|---|
| `compactVectorIndexToken` | L2798 | فشرده‌سازیِ Vector Index Token |
| `makeCompactVectorId` | L2806 | ساختِ Compact Vector Id |
| `describeCompactVectorId` | L2827 | توصیفِ Compact Vector Id |
| `vectorPreflightSafeTableName` | L5270 | vectorPreflightSafeTableName |
| `vectorPreflightPolicy` | L5278 | vectorPreflightPolicy |
| `setupVectorizePreflightFoundation` | L5321 | ساختِ پایهٔ طرح‌وارهٔ بردار و ثبتِ ایندکس‌ها/مدل‌ها |
| `handleResetVectorizePreflight` | L5752 | هندلرِ مسیر Reset Vectorize Preflight |
| `handleVectorizeSchemaAudit` | L5829 | هندلرِ مسیر Vectorize Schema Audit |
| `vectorPreflightSchemaAudit` | L5845 | vectorPreflightSchemaAudit |
| `vectorPreflightTableExists` | L5922 | vectorPreflightTableExists |
| `handleVectorizeStatus` | L5927 | گزارشِ وضعیتِ بردار |
| `resolveVectorLanguageAuthority` | L6074 | تعیینِ مرجعِ زبانِ مالک |
| `selectDesiredVectorPolicyForOwner` | L6111 | انتخابِ مدلِ مطلوبِ مالک (m3 یا bge-large) بر پایهٔ زبان/امتیاز |
| `estimateVectorSegmentCount` | L6166 | تخمینِ Vector Segment Count |
| `handleVectorizeCandidates` | L6174 | فهرستِ نامزدهای بردارسازی |
| `vectorPreflightSchemaReadiness` | L6392 | vectorPreflightSchemaReadiness |
| `normalizeVectorOwnerType` | L6399 | نرمال‌سازیِ Vector Owner Type |
| `normalizeVectorPrepareDryRun` | L6407 | نرمال‌سازیِ Vector Prepare Dry Run |
| `makeVectorSegmentKey` | L6413 | ساختِ Vector Segment Key |
| `makeVectorJobId` | L6434 | ساختِ Vector Job Id |
| `vectorSegmentStep` | L6438 | vectorSegmentStep |
| `planVectorSegmentsFromCachedChunks` | L6442 | طرحِ قطعه‌های بردار از قطعه‌های کش |
| `submitImmediateVectorizeDeleteForPendingSegment` | L6623 | ثبتِ Immediate Vectorize Delete For Pending Segment |
| `fetchDocumentCacheChunksForVectorPrepare` | L7088 | واکشیِ Document Cache Chunks For Vector Prepare |
| `countExistingVectorRows` | L7104 | شمارشِ Existing Vector Rows |
| `findDuplicateVectorSegment` | L7138 | یافتنِ Duplicate Vector Segment |
| `makeVectorContentRegistryKey` | L7188 | ساختِ Vector Content Registry Key |
| `validateVectorSegmentForPrepare` | L7198 | اعتبارسنجیِ Vector Segment For Prepare |
| `upsertVectorSegmentMetadata` | L7216 | درج/به‌روزرسانیِ Vector Segment Metadata |
| `ensureVectorizationJobMetadata` | L7334 | تضمین/ساختِ Vectorization Job Metadata |
| `ensureVectorizationJobForSegment` | L7362 | تضمین/ساختِ Vectorization Job For Segment |
| `cleanupFailedVectorPrepare` | L7367 | cleanupFailedVectorPrepare |
| `updateVectorOwnerStateAfterPrepare` | L7410 | به‌روزرسانیِ Vector Owner State After Prepare |
| `normalizeVectorTransitionDryRun` | L7495 | نرمال‌سازیِ Vector Transition Dry Run |
| `resolveVectorTransitionOwner` | L7501 | حلِ Vector Transition Owner |
| `summarizeVectorLifecycleCounts` | L7539 | خلاصه‌سازیِ Vector Lifecycle Counts |
| `inspectVectorOwnerLifecycle` | L7577 | بازرسیِ Vector Owner Lifecycle |
| `insertVectorTransitionLog` | L7629 | درجِ Vector Transition Log |
| `updateVectorOwnerStateAfterTransition` | L7638 | به‌روزرسانیِ Vector Owner State After Transition |
| `normalizeVectorRunOptions` | L7699 | نرمال‌سازیِ Vector Run Options |
| `getVectorizeIndexBinding` | L7733 | دریافتِ Vectorize Index Binding |
| `isQuotaLikeVectorRunError` | L7741 | تشخیصِ خطای سهمیه/Neuron |
| `looksLikeVectorCapacityError` | L7746 | تشخیصِ خطای پُریِ ظرفیتِ Vectorize |
| `vectorRunResumeAfter` | L7757 | vectorRunResumeAfter |
| `extractEmbeddingVector` | L7761 | استخراجِ بردار از پاسخِ Workers AI |
| `findPendingVectorizationJob` | L7772 | یافتنِ کارِ معلق |
| `claimVectorizationJob` | L7934 | قفلِ یک کارِ بردار با run_id |
| `loadSegmentTextForVectorRun` | L7997 | بارگذاریِ Segment Text For Vector Run |
| `markVectorJobFailed` | L8004 | علامت‌گذاریِ Vector Job Failed |
| `refreshVectorOwnerStateAfterRun` | L8025 | به‌روزرسانیِ Vector Owner State After Run |
| `normalizeVectorDeleteDryRun` | L8554 | نرمال‌سازیِ Vector Delete Dry Run |
| `normalizeVectorDeleteReason` | L8560 | نرمال‌سازیِ Vector Delete Reason |
| `normalizeVectorDeleteScope` | L8566 | نرمال‌سازیِ Vector Delete Scope |
| `normalizeVectorDeleteOptions` | L8572 | نرمال‌سازیِ Vector Delete Options |
| `vectorSegmentTerminalDeleteStatus` | L8593 | vectorSegmentTerminalDeleteStatus |
| `vectorSegmentCanBeMarkedForDelete` | L8598 | vectorSegmentCanBeMarkedForDelete |
| `vectorJobDeleteStatusForReason` | L8603 | vectorJobDeleteStatusForReason |
| `updateVectorContentRegistryStatusForSegment` | L8607 | به‌روزرسانیِ Vector Content Registry Status For Segment |
| `markOwnerVectorsForDelete` | L8618 | علامتِ حذفِ همهٔ بردارهای یک مالک |
| `handleVectorizeMarkOwnerDeleted` | L8739 | علامتِ حذفِ بردارهای مالک (مرحلهٔ ۱) |
| `extractVectorizeMutationId` | L8788 | استخراجِ Vectorize Mutation Id |
| `isVectorDeleteConfigMissingStatus` | L8794 | بررسیِ Vector Delete Config Missing Status |
| `claimVectorDeleteSegment` | L8829 | قفل/برداشتِ Vector Delete Segment |
| `hasMoreVectorDeleteWork` | L8853 | بررسیِ More Vector Delete Work |
| `syncVectorOwnerStateAfterDelete` | L8863 | syncVectorOwnerStateAfterDelete |
| `handleVectorizeRunDeletes` | L8869 | حذفِ بردار از Vectorize (مرحلهٔ ۲) |
| `normalizeVectorQueryProbeOptions` | L9148 | نرمال‌سازیِ Vector Query Probe Options |
| `resolveVectorQueryIndexPolicy` | L9170 | حلِ Vector Query Index Policy |
| `embedVectorQuery` | L9233 | تولیدِ بردارِ پرس‌وجو با Workers AI |
| `summarizeEmbeddingResponseShape` | L9253 | خلاصه‌سازیِ Embedding Response Shape |
| `extractVectorizeMatches` | L9261 | استخراجِ Vectorize Matches |
| `queryVectorizeIndexForProbe` | L9271 | پرس‌وجوی Vectorize Index For Probe |
| `vectorMatchMetadata` | L9289 | vectorMatchMetadata |
| `vectorMatchId` | L9296 | vectorMatchId |
| `vectorMatchScore` | L9301 | vectorMatchScore |
| `resolveVectorMatchToSegment` | L9309 | حلِ Vector Match To Segment |
| `loadVectorOwnerRegistryForCandidate` | L9339 | بارگذاریِ Vector Owner Registry For Candidate |
| `parseVectorProbeSourceParts` | L9364 | تجزیهٔ Vector Probe Source Parts |
| `loadVectorSemanticPreview` | L9380 | بارگذاریِ Vector Semantic Preview |
| `makeVectorSemanticCandidateFromSegment` | L9393 | ساختِ Vector Semantic Candidate From Segment |
| `handleVectorizeQueryProbe` | L9459 | کاوشِ تشخیصیِ ایندکس (نزدیک‌ترین همسایه) |
| `handleVectorizeTransitionOwner` | L9678 | انتقالِ مالک بین مدل‌ها/لایه‌ها |
| `buildVectorTransitionPlan` | L10088 | ساختِ Vector Transition Plan |
| `storeVectorLanguageSignalIfReady` | L10109 | ذخیرهٔ Vector Language Signal If Ready |
| `runAdminWriteWindowVectorCompaction` | L11522 | فشرده‌سازیِ بردارِ پنجرهٔ نوشتنِ ادمین (تازه در c.6) |
| `maybeRunAdminWriteWindowVectorCompaction` | L11689 | اجرای مشروطِ فشرده‌سازیِ پنجرهٔ نوشتن (تازه در c.6) |
| `normalizeHybridVectorMode` | L18234 | نرمال‌سازیِ Hybrid Vector Mode |
| `queryVectorizeIndexForHybrid` | L18290 | پرس‌وجوی نزدیک‌ترین همسایه برای جست‌وجوی ترکیبی |
| `normalizeHybridVectorCandidate` | L18332 | نرمال‌سازیِ Hybrid Vector Candidate |
| `runHybridVectorBranchForIndex` | L18361 | اجرای شاخهٔ برداری روی یک ایندکس |
| `runHybridVectorBranchesForResolvedScope` | L18429 | اجرای Hybrid Vector Branches For Resolved Scope |

---

## بخش ۹ — امتیازدهی، ترفیع و نگه‌داری (Scoring / Promotion / Retention)

«کنترلِ کیفیت». خواندنِ واقعی را به `read_event` ثبت، امتیازِ ارزش را می‌گیرد، و تصمیمِ ترفیعِ نگه‌داری می‌گیرد. امتیازدهی **خنثی‌نسبت‌به‌تکرار** است و `fetch_count` را زیاد نمی‌کند؛ ترفیع فقط پرچمِ نگه‌داری می‌گذارد و بر دیده‌شدن/رتبه/حذف/بردار/RRF اثر ندارد.

##### `handleScoreReadEvidence(request, url, env)`
- **خط:** L10164 · **نقش:** ثبتِ امتیازِ ارزش (۱ تا ۱۰۰) برای یک شاهد. فقط رویدادهای `evidence`؛ **(c.6-k)** owner رویداد را با `expected_owner_key` مقایسه می‌کند و در ناهماهنگی `score_owner_mismatch`+`score_rejected=true` می‌دهد؛ خنثی‌نسبت‌به‌تکرار؛ پیش از ترفیع بازبینیِ تکرار می‌کند و در «تکرارِ تأییدشده» ترفیع را مسدود می‌کند. **انبار:** `D1`. **لوله‌ها:** → `maybeRunDuplicateRecheckBeforeScorePromotion`, `applyScoreToGlobalChunkOwner`.

### ماشین‌های امتیاز/ترفیع/رتبه
| تابع | خط | نقش |
|---|---|---|
| `makeReadEventId` | L4714 | ساختِ Read Event Id |
| `normalizeScoreValue` | L4719 | نرمال‌سازیِ Score Value |
| `buildScoreScale` | L4725 | ساختِ Score Scale |
| `buildEvidenceUnitKey` | L4729 | ساختِ Evidence Unit Key |
| `buildReadEventResponse` | L4748 | ساختِ Read Event Response |
| `createReadEvent` | L4772 | ثبتِ رویدادِ خواندن (تولیدِ شاهد، result_kind=evidence) |
| `markGlobalChunkRead` | L4836 | به‌روزرسانیِ fetch_count اینجا (نه در امتیازدهی) |
| `getPromotionPolicy` | L4928 | سیاستِ ترفیع (آستانه: marxists۶۰/پیش‌فرض۷۰/خیلی‌بالا۸۵) |
| `sourceFamilyFromRow` | L4966 | sourceFamilyFromRow |
| `promotionThresholdForSourceFamily` | L4971 | آستانهٔ ترفیعِ خانوادهٔ منبع |
| `cachePriorityRank` | L4978 | cachePriorityRank |
| `computeLastActivity` | L4985 | محاسبهٔ Last Activity |
| `buildPromotionKeysForOwner` | L4999 | ساختِ Promotion Keys For Owner |
| `computePromotionDecision` | L5026 | تصمیمِ ترفیع بر پایهٔ امتیاز/خانوادهٔ منبع/آستانه |
| `applyPromotionToGlobalChunkOwner` | L5061 | اعمالِ پرچم‌های نگه‌داری (بی‌اثر بر رتبه/حذف/بردار/RRF) |
| `applyPromotionToReadEvent` | L5074 | اعمالِ Promotion To Read Event |
| `handlePromotionAudit` | L5084 | حسابرسیِ ترفیع |
| `handleRetentionStatus` | L5182 | گزارشِ ترتیبِ حذف (retention) |
| `applyScoreToGlobalChunkOwner` | L11911 | اعمالِ امتیاز به قطعهٔ سراسری |
| `computeDateProximityScore` | L15121 | محاسبهٔ Date Proximity Score |
| `branchRankSortScore` | L17312 | branchRankSortScore |
| `computeValueScoreTiebreak` | L17393 | محاسبهٔ Value Score Tiebreak |
| `hybridPrimaryScore` | L18536 | hybridPrimaryScore |
| `isScoredOrPromotedOwner` | L18967 | بررسیِ Scored Or Promoted Owner |
| `canonicalPromotionUnitKeyForGlobalRow` | L18975 | canonicalPromotionUnitKeyForGlobalRow |
| `parsePathFromPromotionUnitKey` | L18987 | تجزیهٔ Path From Promotion Unit Key |
| `collectScoredGlobalContentUnits` | L19087 | گردآوریِ Scored Global Content Units |
| `searchScoredGlobalChunks` | L19226 | جست‌وجوی Scored Global Chunks |
| `coreTermMatchScore` | L19481 | coreTermMatchScore |
| `termMatchScore` | L19497 | termMatchScore |
| `baseRelevanceScoreForNeutralMerge` | L19553 | baseRelevanceScoreForNeutralMerge |
| `scoreUnifiedResult` | L19689 | امتیازِ Unified Result |
| `sessionDedupPrimaryScore` | L20012 | sessionDedupPrimaryScore |
| `maybeRunDuplicateRecheckBeforeScorePromotion` | L20562 | بازبینیِ تکرار پیش از ترفیع (پل به S12) |
| `attachEvidenceScope` | L25172 | افزودنِ Evidence Scope |

---

## بخش ۱۰ — شاخهٔ برداری در جست‌وجوی ترکیبی (Hybrid Vector Branch)

«اتصالِ جست‌وجوی محلی به ایندکسِ برداری». بردارِ پرس‌وجو را (با کشِ درون‌نشست) می‌سازد، ایندکس را می‌زند و نامزدهای برداری را برای تلفیق آماده می‌کند.

| تابع | خط | نقش |
|---|---|---|
| `makeHybridQueryContext` | L18274 | ساختِ بافتارِ پرس‌وجوی ترکیبی (نگهدارندهٔ کشِ embedding) |
| `getOrEmbedHybridQuery` | L18282 | بردارِ پرس‌وجو را از کشِ نشست می‌گیرد یا می‌سازد |
| `exactHybridIdentityKey` | L18496 | کلیدِ هویتِ دقیق برای تطبیقِ نامزد |
| `canMergeHybridCandidates` | L18505 | امکان‌سنجیِ ادغام |
| `mergeHybridCandidates` | L18562 | ادغامِ نامزدِ لغوی و برداریِ یک واحد |
| `buildHybridChunkContinuation` | L23801 | ساختِ Hybrid Chunk Continuation |

---

## بخش ۱۱ — رتبه‌بندیِ تلفیقیِ وزن‌دار (Production Weighted RRF Fusion)

«مرتب‌سازیِ نهاییِ خطِ تولید». چند فهرستِ رتبه‌بندی را با «تلفیقِ رتبهٔ متقابلِ وزن‌دار» ادغام می‌کند. این مرحله نامزد را به شاهد بدل نمی‌کند و `value_score` را فقط شکنندهٔ تساوی می‌داند.

##### `applyProductionWeightedRrfRanking(candidates, options)`
- **خط:** L17428 · **نقش:** رتبه‌بندیِ نهایی. شاخه‌ها را استنتاج، رتبهٔ درون‌شاخه‌ای را تعیین، امتیازِ RRF را محاسبه و مرتب می‌کند: `weighted_rrf_score → unified_rank_score → امتیازِ محتوایی`. **لوله‌ها:** ← `handleUnifiedSearch`.

##### `getProductionFusionPolicy(options)`
- **خط:** L17198 · **نقش:** سیاستِ تلفیق. `rrf_k=60`، `external_weight_shift=0.15`؛ وزن‌ها: scored_cache=۱.۲۰، marxists/readable=۰.۹۵+شیفت، wikisource/gutenberg=۰.۹۰+شیفت، discovery/core=۰.۸۵+شیفت، arxiv=۰.۸۰+شیفت.

### ماشین‌های تلفیق
| تابع | خط | نقش |
|---|---|---|
| `roundNumber` | L17246 | گردکردنِ Number |
| `normalizeFusionBranchName` | L17253 | نرمال‌سازیِ Fusion Branch Name |
| `addFusionBranch` | L17257 | افزودنِ Fusion Branch |
| `candidateHasReadableHint` | L17262 | candidateHasReadableHint |
| `inferCandidateFusionBranches` | L17269 | استنتاجِ شاخه‌های تلفیقِ یک نامزد |
| `rankCandidatesWithinFusionBranches` | L17333 | تعیینِ رتبهٔ هر نامزد در هر شاخه |
| `fusionBranchFamily` | L17366 | fusionBranchFamily |
| `computeMultiSignalBonus` | L17377 | پاداشِ حضور در چند شاخه (سقف ۰.۰۱۰) |
| `computeDuplicateSuspicionAdjustment` | L17385 | تعدیلِ منفیِ ظنِ تکرار (سقف ۰.۰۰۵) |
| `computeWeightedRrfForCandidate` | L17400 | محاسبهٔ امتیازِ RRF یک نامزد (وزن/(k+رتبه)) |
| `weightedRrfFromFusionSources` | L18548 | weightedRrfFromFusionSources |

---
## بخش ۱۲ — حذفِ تکراری و ظنِ نشست (Session Dedup / Duplicate Suspicion)

«بازرسیِ تکراری». دو لایه: حذفِ سختِ هویت‌محور (قطعی) و علامتِ ظنِ نرم (که حذف نمی‌کند، فقط برچسب می‌زند و پیش از کش بازبینی می‌کند).

##### `applySessionWideDedupAndSuspicion(candidates, options)`
- **خط:** L20198 · **نقش:** هستهٔ پاک‌سازی. (۱) حذفِ سخت با ۸ کلیدِ هویت (`source_ref`,`document_cache_key`,`canonical_url`,`url`,`doi`,`source_id`,`result_ref`,`dedup_group_key`)؛ (۲) ظنِ نرم با آستانهٔ ۰.۲۸ که نامزد را برچسب می‌زند ولی نگه می‌دارد. **لوله‌ها:** ← `handleUnifiedSearch`.

##### `runDuplicateSuspicionRecheck(env, input)`
- **خط:** L20510 · **نقش:** بازبینی با متنِ واقعی پیش از کشِ امتیازخورده؛ اطمینان ≥۰.۷۵ → تکرارِ تأییدشده، ≤۰.۲۵ → پاک، میان → نامطمئن (موقتاً مجاز با علامت). **انبار:** `D1`/شارد.

### ماشین‌های حذف/ظن
| تابع | خط | نقش |
|---|---|---|
| `dedupeAndMergeHybridCandidates` | L18602 | حذفِ تکراریِ And Merge Hybrid Candidates |
| `dedupeUnifiedResults` | L19744 | حذفِ تکراریِ نتایجِ یکپارچه |
| `normalizeSessionDedupText` | L19756 | نرمال‌سازیِ Session Dedup Text |
| `normalizeSessionDedupUrl` | L19765 | نرمال‌سازیِ Session Dedup Url |
| `sessionDedupTokenSet` | L19780 | sessionDedupTokenSet |
| `sessionJaccard` | L19785 | شباهتِ ژاکاردِ توکنیِ نشست |
| `normalizeWorkTitleForDuplicateSuspicion` | L19808 | نرمال‌سازیِ Work Title For Duplicate Suspicion |
| `sessionTokenArray` | L19818 | sessionTokenArray |
| `buildWorkTitleAliases` | L19822 | ساختِ نام‌های مستعارِ اثرِ کلاسیک |
| `containmentSimilarity` | L19849 | containmentSimilarity |
| `bestWorkTitleAliasSimilarity` | L19864 | bestWorkTitleAliasSimilarity |
| `isGenericSuspicionTitle` | L19875 | بررسیِ Generic Suspicion Title |
| `extractSessionDedupPhrases` | L19884 | استخراجِ Session Dedup Phrases |
| `sessionPhraseOverlap` | L19898 | sessionPhraseOverlap |
| `hasClassicalWorkAliasHit` | L19907 | بررسیِ Classical Work Alias Hit |
| `sessionDedupSlugText` | L19922 | sessionDedupSlugText |
| `normalizeCandidateIdentityForSessionDedup` | L19927 | نرمال‌سازیِ Candidate Identity For Session Dedup |
| `buildSessionHardDedupKeys` | L19997 | ساختِ Session Hard Dedup Keys |
| `mergeSessionArrays` | L20025 | ادغامِ Session Arrays |
| `mergeHardDuplicateCandidates` | L20037 | ادغامِ دو نامزدِ قطعاً تکراری |
| `canCompareForSoftDuplicateSuspicion` | L20064 | امکان‌سنجیِ Compare For Soft Duplicate Suspicion |
| `computeMetadataDuplicateSuspicion` | L20088 | اطمینانِ ظنِ فراداده |
| `markDuplicateSuspicion` | L20159 | برچسبِ ظن (حذف نمی‌کند) |
| `buildDuplicateRecheckContextForCandidate` | L20295 | ساختِ Duplicate Recheck Context For Candidate |
| `extractDuplicateSuspicionContext` | L20312 | استخراجِ Duplicate Suspicion Context |
| `loadSearchSessionCandidatePayloadForRecheck` | L20353 | بارگذاریِ Search Session Candidate Payload For Recheck |
| `loadGlobalChunkSampleForDuplicateRecheck` | L20406 | بارگذاریِ Global Chunk Sample For Duplicate Recheck |
| `loadOwnerSampleForDuplicateRecheck` | L20432 | بارگذاریِ Owner Sample For Duplicate Recheck |
| `extractRecheckPhrases` | L20449 | استخراجِ Recheck Phrases |
| `buildDuplicateRecheckFingerprint` | L20461 | ساختِ Duplicate Recheck Fingerprint |
| `phraseSetOverlap` | L20477 | phraseSetOverlap |
| `compareDuplicateRecheckFingerprints` | L20484 | compareDuplicateRecheckFingerprints |

---

## بخش ۱۳ — جست‌وجوی یکپارچه و نشست (Unified Search / Search Sessions)

«هماهنگیِ خطِ تولیدِ اصلیِ کشف» و انجماد/صفحه‌بندیِ نتایج.

##### `handleUnifiedSearch(request, url, env)`
- **خط:** L17549 · **نقش:** هندلرِ مرکزی. اگر درخواستِ صفحهٔ نشست بود همان را برمی‌گرداند؛ وگرنه از قلمروهای پیش‌فرضِ **c.6-k** (`discovery_cache,document_cache,scored_cache,external` — که `marxists_local` از آن خارج و در صورتِ درخواستِ صریح فقط با diagnostic `legacy_internal_index: deprecated_ignored_by_cache_architecture` نادیده می‌شود) نامزد جمع، ضمیمهٔ حافظه را **موازی** می‌سازد (`runUnifiedGptMemorySidecarSafely`)، دروازهٔ ربط می‌زند، با `applySessionWideDedupAndSuspicion` پاک، با `applyProductionWeightedRrfRanking` رتبه و با `createSearchSession` منجمد می‌کند؛ منابعِ کُند را با `ctx.waitUntil` به‌تعویق می‌اندازد. **انبار:** `D1` + شاردها + (اختیاری) Vectorize + منابع. **لوله‌ها:** → `collectCacheAwareResultsForSources`, `runUnifiedGptMemorySidecarSafely`, `applySessionWideDedupAndSuspicion`, `applyProductionWeightedRrfRanking`, `createSearchSession`.

### ماشین‌های یکپارچه/نشست
| تابع | خط | نقش |
|---|---|---|
| `runUnifiedBranchSafely` | L17487 | اجرای Unified Branch Safely |
| `makeUnifiedBranchFailure` | L17506 | ساختِ Unified Branch Failure |
| `collectCacheAwareResultsForSources` | L17891 | گردآوریِ نتایجِ کش‌آگاه |
| `finalizeMixedSearchResults` | L17965 | نهایی‌سازیِ Mixed Search Results |
| `parseSearchRealmsForSpecialized` | L17979 | تجزیهٔ Search Realms For Specialized |
| `searchDiscoverySessionCache` | L17986 | جست‌وجوی Discovery Session Cache |
| `searchDocumentTextCache` | L18763 | منبعِ نامزد: کشِ متنِ سند |
| `fetchLocalChunkTextForGlobalRow` | L18997 | واکشیِ Local Chunk Text For Global Row |
| `chunkTextFromLocalRow` | L19021 | chunkTextFromLocalRow |
| `fetchLocalChunkTextsForGlobalRows` | L19036 | واکشیِ Local Chunk Texts For Global Rows |
| `resolveGlobalUnitChunks` | L19153 | حلِ Global Unit Chunks |
| `searchExternalSourcesForUnified` | L19311 | منبعِ نامزد: منابعِ بیرونی |
| `splitSearchTerms` | L19386 | تقسیمِ Search Terms |
| `findTermPositionsForRelevance` | L19413 | یافتنِ Term Positions For Relevance |
| `hasTermsInProximityText` | L19432 | بررسیِ Terms In Proximity Text |
| `combinedUnifiedRank` | L19538 | combinedUnifiedRank |
| `firstFiniteNumber` | L19545 | یافتنِ اولین Finite Number |
| `sortUnifiedResultsByNeutralBaseRelevance` | L19599 | مرتب‌سازیِ Unified Results By Neutral Base Relevance |
| `countMatchedTermsInItem` | L19627 | شمارشِ Matched Terms In Item |
| `hasExactQueryPhraseInItem` | L19644 | بررسیِ Exact Query Phrase In Item |
| `passesDiscoveryCacheRelevanceGate` | L19659 | دروازهٔ Discovery Cache Relevance Gate |
| `passesUnifiedSearchRelevanceGate` | L19681 | دروازهٔ ربط‌سنجیِ نهایی |
| `unifiedResultKey` | L19706 | unifiedResultKey |
| `attachSearchSessionToJsonResponse` | L23908 | افزودنِ Search Session To Json Response |
| `maybeReturnSearchSessionPage` | L23943 | اجرای مشروطِ Return Search Session Page |
| `createSearchSession` | L24110 | انجمادِ نتایج (سرآیند + payload در search_session_results) |
| `appendResultsToSearchSession` | L24203 | افزودنِ نتایجِ منابعِ کُند به نشست |
| `readSearchSessionPage` | L24281 | خواندنِ صفحهٔ نشستِ منجمد (منقضی→۴۱۰) |

---

## بخش ۱۴ — حافظهٔ اختصاصیِ جی‌پی‌تی (GPT Memory)

«دفترچهٔ یادداشتِ بافتارِ پروژه» — بزرگ‌ترین زیرسامانه (۱۱۷ ماشین، با بیشترین رشد در c.6). مدلِ آن **قطعه‌محور و افزایشی** است. قانونِ طلایی صریح است: **حافظه فقط بافتار است** — خروجی‌ها `result_kind:"memory_context*"`، `evidence_required:false`، `score_required:false`، `weighted_rrf_score:null`. در c.6 یک **لایهٔ بردارسازیِ خودکارِ کراندار** (microtask ساعتی + ظرفیت + فشرده‌سازی) افزوده شده.

##### `handleMemoryWrite / Append / Rewrite / Delete` (همه پشتِ `MEMORY_WRITE_TOKEN`)
- **خط:** L12945 / L12971 / L13174 / L13359 · **نقش:** نوشتن/افزودن/بازنویسی/حذفِ حافظه. محتوا را به قطعه می‌شکنند، در `gpt_memory_segments` می‌نویسند، تراکنش ثبت و سند را لمس می‌کنند؛ در c.6 می‌توانند `maybeImmediateVectorizeNewGptMemorySegments` را برای کارِ بردارِ فوری صدا بزنند. **انبار:** `D1` (`gpt_memory_*`).

##### `buildGptMemorySidecar(env, options)` · `runUnifiedGptMemorySidecarSafely(...)`
- **خط:** L14616 / L17521 · **نقش:** ضمیمهٔ بافتارِ موازی برای جست‌وجوی یکپارچه. صریحاً `evidence_required:false`، `score_required:false`، `weighted_rrf_score:null` و فقط واجدبودنِ سنجاق را علامت می‌زند. در c.6 این ضمیمه در سطحِ بالا و موازی اجرا می‌شود تا مسیرِ نامزد را کُند نکند.

##### `runGptMemoryQueuedVectorMicrotask(env, options)` (تازه در c.6)
- **خط:** L10856 · **نقش:** هستهٔ بردارسازیِ خودکارِ حافظه. سیاست را می‌خواند، صفِ کارها را می‌شمارد، **قفلِ نگه‌داری** می‌گیرد و **حداقل‌فاصله** را رعایت می‌کند، سپس **یک** کار را embedding/upsert می‌کند و قفل را آزاد می‌کند؛ در غیرِ این صورت `skipped_lock_busy`/`skipped_min_interval`. **انبار:** `D1` (`maintenance_locks`/`state`, `vectorization_jobs`) + Workers AI + Vectorize. **لوله‌ها:** ← `runScheduledGptMemoryVectorMicrotaskOnly`.

### ماشین‌های حافظه (نوشتن/خواندن/جست‌وجو/ضمیمه/بردارسازیِ خودکار/ظرفیت/فشرده‌سازی)
| تابع | خط | نقش |
|---|---|---|
| `normalizeGptMemoryVectorText` | L5258 | نرمال‌سازیِ Gpt Memory Vector Text |
| `loadActiveGptMemorySegmentsForVectorization` | L6487 | بارگذاریِ Active Gpt Memory Segments For Vectorization |
| `planVectorSegmentsFromGptMemorySegments` | L6515 | planVectorSegmentsFromGptMemorySegments |
| `summarizeGptMemoryVectorPlan` | L6564 | خلاصه‌سازیِ Gpt Memory Vector Plan |
| `loadSegmentTextForGptMemory` | L6584 | بارگذاریِ Segment Text For Gpt Memory |
| `runImmediateGptMemoryVectorDeleteSubmissions` | L6739 | اجرای Immediate Gpt Memory Vector Delete Submissions |
| `markGptMemorySegmentVectorsForLifecycleChange` | L6824 | علامت‌گذاریِ Gpt Memory Segment Vectors For Lifecycle Change |
| `handleGptMemoryVectorizePrepareOne` | L6895 | هندلرِ مسیر Gpt Memory Vectorize Prepare One |
| `recoverGptMemoryRunnerUnsupportedJobs` | L7844 | بازیابیِ Gpt Memory Runner Unsupported Jobs |
| `parseGptMemoryProtectionInput` | L10318 | تجزیهٔ Gpt Memory Protection Input |
| `parseGptMemoryProtectReason` | L10343 | تجزیهٔ Gpt Memory Protect Reason |
| `buildGptMemoryProtectionAudit` | L10349 | حسابرسیِ محافظتِ حافظه (تازه در c.6) |
| `buildGptMemoryVectorizationC6AStatus` | L10368 | ساختِ Gpt Memory Vectorization C6 A Status |
| `buildGptMemoryVectorizationC6BStatus` | L10379 | ساختِ Gpt Memory Vectorization C6 B Status |
| `buildImmediateGptMemoryVectorDeleteDisabledStatus` | L10390 | ساختِ Immediate Gpt Memory Vector Delete Disabled Status |
| `parseGptMemoryImmediateVectorDeleteDecision` | L10413 | تجزیهٔ Gpt Memory Immediate Vector Delete Decision |
| `buildImmediateGptMemoryVectorizationDisabledStatus` | L10439 | ساختِ Immediate Gpt Memory Vectorization Disabled Status |
| `parseGptMemoryImmediateVectorizationDecision` | L10469 | تجزیهٔ Gpt Memory Immediate Vectorization Decision |
| `markQueuedGptMemoryVectorJobsDelay` | L10508 | علامت‌گذاریِ Queued Gpt Memory Vector Jobs Delay |
| `maybeImmediateVectorizeNewGptMemorySegments` | L10568 | بردارسازیِ فوریِ قطعه‌های تازه (در صورتِ فعال‌بودن) (تازه در c.6) |
| `ensureGptMemoryC6DMaintenanceTables` | L10692 | ساختِ جدول‌های نگه‌داریِ c.6 (maintenance_locks/state) (تازه در c.6) |
| `readGptMemoryVectorMicrotaskPolicy` | L10791 | خواندنِ سیاستِ microtask (سقفِ embedding/upsert/فاصله/TTL قفل) (تازه در c.6) |
| `getGptMemoryVectorQueueCounts` | L10807 | شمارشِ کارهای معلقِ سررسیده/آینده (تازه در c.6) |
| `handleGptMemoryVectorMicrotaskRoute` | L10940 | مسیرِ دستیِ اجرای microtaskِ بردارِ حافظه (تازه در c.6) |
| `ensureGptMemoryCapacityEvictionSchema` | L10954 | تضمین/ساختِ Gpt Memory Capacity Eviction Schema |
| `ensureGptMemoryWriteWindowCompactionSchema` | L11009 | تضمین/ساختِ Gpt Memory Write Window Compaction Schema |
| `readGptMemoryCapacityPolicy` | L11063 | خواندنِ سیاستِ ظرفیتِ حافظه (تازه در c.6) |
| `inspectGptMemoryVectorCapacity` | L11082 | بازرسیِ ظرفیتِ بردارِ حافظه (تازه در c.6) |
| `selectGptMemoryCapacityEvictionCandidate` | L11144 | انتخابِ نامزدِ تخلیه هنگام پُریِ ظرفیت (تازه در c.6) |
| `submitGptMemoryCapacityEviction` | L11207 | ثبتِ تخلیهٔ ظرفیت در capacity_eviction_log (تازه در c.6) |
| `maybeRunGptMemoryCapacityEviction` | L11290 | اجرای مشروطِ تخلیهٔ ظرفیتِ بردارِ حافظه (تازه در c.6) |
| `handleGptMemoryCapacityMaintenanceRoute` | L11347 | مسیرِ دستیِ نگه‌داریِ ظرفیتِ حافظه (تازه در c.6) |
| `isAdminAuthoredGptMemoryWrittenBy` | L11360 | بررسیِ Admin Authored Gpt Memory Written By |
| `readGptMemoryWriteWindowCompactionPolicy` | L11365 | خواندنِ Gpt Memory Write Window Compaction Policy |
| `buildGptMemoryWriteWindowCompactionDisabledStatus` | L11389 | ساختِ Gpt Memory Write Window Compaction Disabled Status |
| `loadRecentAdminMemorySegmentsForCompaction` | L11403 | بارگذاریِ Recent Admin Memory Segments For Compaction |
| `buildGptMemoryAggregateText` | L11458 | ساختِ متنِ تجمعیِ حافظه برای بردارِ بسته‌ای (تازه در c.6) |
| `makeGptMemoryCompactionGroupKey` | L11518 | ساختِ Gpt Memory Compaction Group Key |
| `handleGptMemoryWriteWindowCompactionRoute` | L11712 | مسیرِ دستیِ فشرده‌سازیِ پنجرهٔ نوشتن (تازه در c.6) |
| `resolveGptMemoryAggregateVectorToBundle` | L11719 | حلِ بردارِ تجمعی به بستهٔ حافظه (تازه در c.6) |
| `normalizeGptMemoryAggregateVectorHit` | L11735 | نرمال‌سازیِ Gpt Memory Aggregate Vector Hit |
| `markGptMemoryAggregateVectorsForSourceSegmentsChanged` | L11796 | علامت‌گذاریِ Gpt Memory Aggregate Vectors For Source Segments Changed |
| `setupMemoryDb` | L12148 | ساختِ پایهٔ طرح‌وارهٔ حافظه |
| `setupGptMemorySegmentSchema` | L12259 | راه‌اندازی Gpt Memory Segment Schema |
| `ensureGptMemoryC6PolicyDefaults` | L12392 | سیاست‌های پیش‌فرضِ حافظهٔ c.6 (تازه در c.6) |
| `ensureDefaultGptMemoryDocuments` | L12501 | تضمین/ساختِ Default Gpt Memory Documents |
| `migrateLegacyMemoryDocsToSegments` | L12540 | مهاجرتِ memory_docs قدیمی به مدلِ قطعه‌ای |
| `isMemoryWriteRequest` | L12675 | نگهبانِ نوشتن (بررسیِ MEMORY_WRITE_TOKEN) |
| `handleMemoryBootstrap` | L12717 | بارگذاریِ بافتارِ اولیه در آغازِ گفت‌وگو |
| `handleMemoryTopics` | L12768 | فهرستِ موضوع‌ها |
| `handleMemoryRead` | L12792 | خواندنِ حافظه (با segment_id/topic) + markMemorySegmentRead |
| `handleMemorySearch` | L12892 | جست‌وجوی حافظه (لغوی+برداری) → memory_context_candidate |
| `handleMemoryVersions` | L13443 | تاریخچهٔ نسخه‌های یک سند |
| `readMemoryWriteInput` | L13511 | خواندنِ Memory Write Input |
| `normalizeMemoryDocType` | L13533 | نرمال‌سازیِ Memory Doc Type |
| `normalizeMemoryVisibility` | L13547 | نرمال‌سازیِ Memory Visibility |
| `normalizeMemorySlug` | L13557 | نرمال‌سازیِ Memory Slug |
| `normalizeMemoryTopic` | L13567 | نرمال‌سازیِ Memory Topic |
| `normalizeMemoryDocumentKey` | L13573 | نرمال‌سازیِ Memory Document Key |
| `memoryDocumentKeyForDocType` | L13583 | memoryDocumentKeyForDocType |
| `buildMemoryTopicDateLabel` | L13589 | ساختِ Memory Topic Date Label |
| `makeMemoryTransactionId` | L13594 | ساختِ Memory Transaction Id |
| `makeMemorySegmentId` | L13601 | ساختِ Memory Segment Id |
| `splitMemoryContentIntoSegments` | L13608 | برشِ محتوا به قطعهٔ حافظه |
| `nextMemoryAppendIndex` | L13647 | یافتنِ بعدیِ Memory Append Index |
| `touchGptMemoryDocument` | L13657 | لمس/به‌روزرسانیِ Gpt Memory Document |
| `loadActiveMemorySegments` | L13665 | بارگذاریِ Active Memory Segments |
| `loadActiveGptMemorySegments` | L13709 | بارگذاریِ Active Gpt Memory Segments |
| `buildGptMemorySourceRef` | L13723 | ساختِ Gpt Memory Source Ref |
| `buildGptMemoryBundleRef` | L13727 | ساختِ Gpt Memory Bundle Ref |
| `memorySegmentToResolvedTextChunk` | L13731 | memorySegmentToResolvedTextChunk |
| `normalizeGptMemoryVectorMode` | L13800 | نرمال‌سازیِ Gpt Memory Vector Mode |
| `parseGptMemoryHybridOptions` | L13808 | تجزیهٔ Gpt Memory Hybrid Options |
| `buildGptMemoryVectorPolicy` | L13837 | ساختِ Gpt Memory Vector Policy |
| `getGptMemoryVectorReadiness` | L13854 | دریافتِ Gpt Memory Vector Readiness |
| `shouldRunGptMemoryVectorBranch` | L13897 | شرطِ Run Gpt Memory Vector Branch |
| `resolveGptMemoryVectorSegmentToActiveMemory` | L13904 | حلِ Gpt Memory Vector Segment To Active Memory |
| `queryGptMemoryVectorBranch` | L13935 | پرس‌وجوی Gpt Memory Vector Branch |
| `normalizeGptMemoryVectorHit` | L14031 | نرمال‌سازیِ Gpt Memory Vector Hit |
| `mergeGptMemoryLexicalAndVectorHits` | L14089 | ادغامِ Gpt Memory Lexical And Vector Hits |
| `computeGptMemoryInternalFusionScore` | L14128 | محاسبهٔ Gpt Memory Internal Fusion Score |
| `searchGptMemoryResolved` | L14139 | هستهٔ جست‌وجوی حافظه (تلفیقِ درونی) |
| `parseUnifiedMemoryOptions` | L14256 | تجزیهٔ Unified Memory Options |
| `parseUnifiedMemoryPinningOptions` | L14281 | تجزیهٔ Unified Memory Pinning Options |
| `extractGptMemoryBundleConfidence` | L14307 | استخراجِ Gpt Memory Bundle Confidence |
| `getGptMemoryBundleObject` | L14325 | دریافتِ Gpt Memory Bundle Object |
| `buildPinnedGptMemoryContext` | L14330 | ساختِ Pinned Gpt Memory Context |
| `applyGptMemoryPinningPolicy` | L14366 | سیاستِ سنجاقِ بافتار (نه شاهد) |
| `extractGptMemorySidecarSegmentIds` | L14505 | استخراجِ Gpt Memory Sidecar Segment Ids |
| `ensureGptMemorySidecarReadHint` | L14528 | تضمین/ساختِ Gpt Memory Sidecar Read Hint |
| `compactGptMemorySidecarForSession` | L14538 | فشرده‌سازیِ Gpt Memory Sidecar For Session |
| `normalizeGptMemoryResolvedHit` | L14789 | نرمال‌سازیِ Gpt Memory Resolved Hit |
| `bundleGptMemoryHits` | L14854 | بسته‌سازیِ Gpt Memory Hits |
| `computeMemoryHitAffinity` | L14905 | محاسبهٔ Memory Hit Affinity |
| `buildGptMemoryBundle` | L14932 | ساختِ Gpt Memory Bundle |
| `buildMemoryBundleId` | L15026 | ساختِ Memory Bundle Id |
| `computeMemoryBundleConfidence` | L15032 | محاسبهٔ Memory Bundle Confidence |
| `hasMemoryReplacementRelation` | L15133 | بررسیِ Memory Replacement Relation |
| `loadMemorySegmentsByIds` | L15145 | بارگذاریِ Memory Segments By Ids |
| `loadMemoryTopicGroups` | L15166 | بارگذاریِ Memory Topic Groups |
| `memorySegmentSummary` | L15199 | memorySegmentSummary |
| `memorySegmentFull` | L15217 | memorySegmentFull |
| `parseMemoryIdList` | L15241 | تجزیهٔ Memory Id List |
| `compactMemoryContent` | L15267 | فشرده‌سازیِ Memory Content |
| `rankMemorySegments` | L15282 | رتبه‌بندیِ Memory Segments |
| `markMemorySegmentRead` | L15354 | به‌روزرسانیِ زمانِ خواندنِ قطعهٔ حافظه |
| `markMemoryDocRead` | L15362 | علامت‌گذاریِ Memory Doc Read |
| `persistGptMemorySidecarForSession` | L24023 | ذخیرهٔ Gpt Memory Sidecar For Session |
| `readGptMemorySidecarFromSearchSession` | L24074 | خواندنِ Gpt Memory Sidecar From Search Session |

| `parseMemoryHygieneOptions(url)` | L13802 | خواندنِ گزینه‌های بهداشت (`memory_scope`/`include_debug_memory`) (c.6-k) |
| `classifyGptMemorySegmentForRetrieval(seg)` | L13821 | طبقه‌بندیِ قطعه: debug/test → `project_context_eligible=false` (c.6-k) |
| `applyGptMemoryHygieneFilter(segments, opts)` | L13846 | فیلترِ حافظه‌های debug/test از بازیابیِ پیش‌فرض (c.6-k) |

---

## بخش ۱۵ — ابزارهای مشترک (Shared Utilities)

«جعبه‌ابزارِ مشترکِ کل کارخانه»: پاسخ‌سازی، امنیت، هش، متن/نشانی، کارتِ عملیات، رصدپذیری، و قفل‌های نگه‌داریِ c.6. تقریباً همه‌جا استفاده می‌شوند.

##### `json(data, status)`
- **خط:** L25050 · **نقش:** سازندهٔ پاسخِ استاندارد. اول `attachPhaseZeroObservability` را می‌افزاید، سپس `Response` با هدرهای CORS (شاملِ `X-Admin-Token`/`X-Memory-Write-Token`). **لوله‌ها:** ← تقریباً همهٔ هندلرها.

##### `isAdminRequest(request, url, env)` · `constantTimeEqual(a, b)`
- **خط:** L1715 / L1740 · **نقش:** احرازِ هویتِ ادمین با مقایسهٔ **زمان‌ثابتِ** توکن (ضدِ حملهٔ زمانی).

##### `tryAcquireMaintenanceLock(...)` · `releaseMaintenanceLock(...)` (تازه در c.6)
- **خط:** L10741 / L10766 · **نقش:** قفلِ هماهنگیِ نگه‌داری با TTL روی `maintenance_locks`؛ پایهٔ اجرای بدونِ‌تداخلِ cronها.

### ماشین‌های مشترک (پاسخ/امنیت/هش/متن/نشانی/کارت/رصدپذیری/قفل)
| تابع | خط | نقش |
|---|---|---|
| `cleanCandidateUrl` | L1812 | پاک‌سازیِ Candidate Url |
| `guessTitleNearUrl` | L1820 | حدسِ Title Near Url |
| `chapterNumberFromPath` | L2253 | chapterNumberFromPath |
| `saveIndexedDocumentAndChunks` | L2372 | نوشتنِ Indexed Document And Chunks |
| `simpleHash` | L2775 | هشِ رشتهٔ سبک |
| `simpleHash32` | L2786 | simpleHash32 |
| `byteLengthUtf8` | L2790 | محاسبهٔ طولِ Length Utf8 |
| `parseSelectedPaths` | L3978 | تجزیهٔ Selected Paths |
| `makeChunkCard` | L4671 | ساختِ Chunk Card |
| `extractMatchedTerms` | L4697 | استخراجِ Matched Terms |
| `makeConceptualHint` | L4708 | ساختِ Conceptual Hint |
| `parseEnglishSignalValue` | L6023 | تجزیهٔ English Signal Value |
| `inferActiveCacheRoleFromRow` | L6031 | استنتاجِ Active Cache Role From Row |
| `parseStoredEnglishGptSignal` | L6040 | تجزیهٔ Stored English Gpt Signal |
| `normalizeLanguageCode` | L6048 | نرمال‌سازیِ Language Code |
| `trustedMetadataLanguageForOwner` | L6056 | trustedMetadataLanguageForOwner |
| `placeholdersFor` | L6619 | placeholdersFor |
| `markSupersededM3SegmentsIfNeeded` | L7463 | علامت‌گذاریِ Superseded M3 Segments If Needed |
| `markSupersededM3JobsIfNeeded` | L7608 | علامت‌گذاریِ Superseded M3 Jobs If Needed |
| `getWorkersAIBinding` | L7728 | دریافتِ Workers AI Binding |
| `findDeleteSubmittedFinalizationCandidate` | L8798 | یافتنِ Delete Submitted Finalization Candidate |
| `findDeletePendingCandidate` | L8814 | یافتنِ Delete Pending Candidate |
| `readJsonOrFormBody` | L10290 | خواندنِ Json Or Form Body |
| `parseBooleanLike` | L10304 | تجزیهٔ Boolean Like |
| `parseExplicitBooleanLike` | L10310 | تجزیهٔ Explicit Boolean Like |
| `makeInternalUrl` | L10499 | ساختِ Internal Url |
| `makeMaintenanceRunId` | L10737 | ساختِ شناسهٔ اجرای نگه‌داری (تازه در c.6) |
| `getMaintenanceStateValue` | L10775 | دریافتِ Maintenance State Value |
| `setMaintenanceStateValue` | L10780 | setMaintenanceStateValue |
| `selectAdminWriteWindowCompactionGroup` | L11462 | انتخابِ Admin Write Window Compaction Group |
| `parseJsonBodySafely` | L12703 | تجزیهٔ Json Body Safely |
| `parseBoundedNumber` | L14250 | تجزیهٔ Bounded Number |
| `collectUniqueStrings` | L14486 | گردآوریِ Unique Strings |
| `computeAveragePairMetric` | L15086 | محاسبهٔ Average Pair Metric |
| `computeTermSetOverlap` | L15099 | محاسبهٔ Term Set Overlap |
| `computeQueryCoverageComplement` | L15108 | محاسبهٔ Query Coverage Complement |
| `round3` | L15141 | round3 |
| `safeJsonParseArray` | L15257 | safeJsonParseArray |
| `limitString` | L15277 | limitString |
| `collectAllowedOwnerKeysFromResolvedChunks` | L18242 | گردآوریِ Allowed Owner Keys From Resolved Chunks |
| `annotateSearchInsideHintQuery` | L18298 | برچسب‌زنیِ Search Inside Hint Query |
| `candidateOwnerKey` | L18474 | candidateOwnerKey |
| `candidateRange` | L18478 | candidateRange |
| `uniqueArray` | L18516 | یکتاسازیِ Array |
| `mergeRankObjects` | L18520 | ادغامِ Rank Objects |
| `ensureCandidateSearchInsideQuery` | L20188 | تضمین/ساختِ Candidate Search Inside Query |
| `coreResultKey` | L20950 | coreResultKey |
| `redactApiKey` | L21035 | پنهان‌سازیِ کلیدِ API در نشانی |
| `sleep` | L21524 | تأخیرِ |
| `parseOperationalSourceRef` | L21778 | تجزیهٔ ارجاعِ عملیاتی — (c.6-k) برای Wikisource ارجاعِ خراب را متعارف می‌کند (نه عبورِ خام) |
| `makeUrlForResolvedSourceRef` | L21809 | ساختِ Url For Resolved Source Ref |
| `getTextForCachedChunkId` | L21883 | دریافتِ Text For Cached Chunk Id |
| `getTextForGlobalChunkId` | L21927 | دریافتِ Text For Global Chunk Id |
| `htmlToText` | L23086 | تبدیلِ HTML به متن |
| `decodeHtmlEntities` | L23103 | رمزگشاییِ Html Entities |
| `cleanPlainText` | L23140 | پاک‌سازیِ Plain Text |
| `normalizeWhitespace` | L23149 | نرمال‌سازیِ Whitespace |
| `getSource` | L23155 | استخراجِ منبع از درخواست |
| `firstParam` | L23169 | یافتنِ اولین Param |
| `parsePositiveInt` | L23181 | تجزیهٔ Positive Int |
| `addDaysIso` | L23218 | افزودنِ Days Iso |
| `isoNowSql` | L23223 | isoNowSql |
| `parseSqlTime` | L23227 | تجزیهٔ Sql Time |
| `makeSessionId` | L23234 | شناسهٔ یکتای نشست |
| `normalizeForHash` | L23238 | نرمال‌سازیِ For Hash |
| `buildQueryHash` | L23242 | هشِ پرس‌وجو |
| `sourceFamilyForSource` | L23246 | sourceFamilyForSource |
| `capText` | L23253 | capText |
| `stableStringifySimple` | L23259 | stableStringifySimple |
| `safeParseJson` | L23268 | safeParseJson |
| `compactJson` | L23273 | فشرده‌سازیِ Json |
| `makeSafePayloadJson` | L23287 | ساختِ Safe Payload Json |
| `normalizeRefPart` | L23378 | نرمال‌سازیِ Ref Part |
| `buildSourceRef` | L23382 | ساختِ ارجاعِ منبع — (c.6-k) برای Wikisource اول `canonicalizeWikisourceRef` بعد return |
| `buildResultRef` | L23435 | ساختِ ارجاعِ نتیجه |
| `buildAvailableOperations` | L23450 | ساختِ کارتِ عملیات (گامِ بعدیِ مجاز) |
| `buildReadHint` | L23510 | راهنمای خواندن (start/limit) — (c.6-k) برای Wikisourceِ cached/scored ترجیحِ `document_cache_key`+`expected_owner_key`؛ `cache_chunk_id` تنها همراهِ مالک |
| `buildSearchInsideHint` | L23581 | ساختِ راهنمای جست‌وجوی درون‌متن — (c.6-k) همان canonicalizationِ Wikisource |
| `copyDefinedParamsFromUrl` | L23608 | copyDefinedParamsFromUrl |
| `mergeDefined` | L23617 | ادغامِ Defined |
| `normalizeReadLimit` | L23625 | نرمال‌سازیِ Read Limit |
| `buildLimitContract` | L23632 | ساختِ Limit Contract |
| `attachLimitContract` | L23645 | افزودنِ Limit Contract |
| `asAvailableOperation` | L23655 | asAvailableOperation |
| `unavailableContinuation` | L23660 | unavailableContinuation |
| `buildReadChunkTargetItem` | L23664 | ساختِ Read Chunk Target Item |
| `buildRangeContinuation` | L23696 | ساختِ Range Continuation |
| `buildCompleteDocumentContinuation` | L23792 | ساختِ Complete Document Continuation |
| `preferredOperationForItem` | L23828 | preferredOperationForItem |
| `enrichResultWithOperationCard` | L23834 | افزودنِ کارتِ عملیات به نتیجه |
| `projectResultForGpt` | L23854 | فرافکنیِ نتیجه به شکلِ استانداردِ مصرفِ GPT |
| `stripHeavyTextFields` | L23893 | حذفِ میدان‌های متنیِ سنگین |
| `attachPhaseZeroObservability` | L25064 | افزودنِ نسخه/نوعِ نتیجه/گزارش/هشدار به هر پاسخ |
| `inferResultKind` | L25125 | استنتاجِ نوعِ نتیجه |
| `decorateNestedResultKinds` | L25200 | برچسب‌زنیِ Nested Result Kinds |
| `decorateResultItem` | L25230 | برچسب‌زنیِ Result Item |
| `attachMinimalReports` | L25353 | افزودنِ Minimal Reports |
| `buildQualityReport` | L25388 | ساختِ Quality Report |
| `buildObservabilityWarnings` | L25413 | ساختِ Observability Warnings |

| `readExpectedOwnerKeyFromUrl(url)` | L23428 | خواندنِ `expected_owner_key` از درخواست (c.6-k) |
| `normalizeOwnerComparisonKey(key)` | L23432 | نرمال‌سازیِ کلیدِ مقایسهٔ مالک (c.6-k) |
| `cachedChunkOwnerCandidates(row)` | L23436 | استخراجِ نامزدهای مالکِ یک قطعهٔ کش (c.6-k) |
| `cachedChunkRowMatchesOwner(row, key)` | L23452 | تطبیقِ ردیفِ قطعهٔ کش با مالکِ موردانتظار (c.6-k) |

---

## پایان

این مشخصات همهٔ **۷۱۶ تابعِ** Worker را در **۱۵ زیرسامانه** پوشش می‌دهد. هر ماشینِ اصلی با کارتِ کامل و هر ماشینِ کمکی با ردیفِ «تابع | خط | نقش» مستند شده است (نقشِ ماشین‌های کمکی از قراردادِ نام‌گذاریِ توصیفیِ کد مشتق شده است). برای نمای کلان به `architecture.md` و برای جریان به `dfd.md` رجوع کنید.

> دو قانونِ طلایی که در سراسرِ کد اعمال می‌شوند: (۱) **نامزد ⟵ شاهد**؛ (۲) **حافظه فقط بافتار است**. و افزودهٔ کلیدیِ c.6: **بردارسازیِ خودکارِ کراندارِ قفل‌آگاهِ حافظه** از طریقِ چهار cron و جدول‌های نگه‌داری.
