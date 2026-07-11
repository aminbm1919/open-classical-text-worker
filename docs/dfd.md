# نمودار جریان داده (Data Flow Diagram) — Open Classical Text Worker
### نسخهٔ `2.9.40-c.6-k` · سطوح ۰، ۱، ۲

> این سند جریانِ داده را در سه سطح نشان می‌دهد. در استعارهٔ کارخانه: **فرایند** = ماشین، **جریان** = لوله، **انبار** = مخزنِ داده. هر لوله منطقِ عبور دارد؛ به برخی داده‌ها اجازهٔ عبور می‌دهد، برخی را تغییرِ شکل/بسته‌بندی می‌کند تا برای مرحلهٔ بعد مساعد شود.

## نمادگذاری
- **فرایند (Process):** ماشینِ پردازنده (مستطیلِ گرد).
- **انبار داده (Data Store):** مخزن (استوانه/براکت).
- **موجودیتِ بیرونی (External Entity):** منبعِ بیرونِ کارخانه.
- **جریان (Flow):** پیکانِ جهت‌دارِ داده روی لوله.
- 🔒 = لولهٔ نیازمندِ احرازِ هویت.

---

## سطح ۰ — نمودار بافتار (Context Diagram)

```mermaid
flowchart LR
    GPT(["جی‌پی‌تیِ فلسفه"])
    EXT(["منابعِ بیرونی\nmarxists/gutendex/wikisource\njstor/core/arxiv/jina"])
    CRON(["زمان‌سنجِ Cloudflare\n۴ Cron"])
    P((("Worker chunking\nc.6-k")))
    D1[("D1: مرکزی + ۹ شارد")]
    VEC[("Vectorize: ۲ ایندکس")]
    AI(["Workers AI"])

    GPT -->|"درخواستِ اکشن (روتین/ادمین)"| P
    P -->|"نامزد / شاهد / بافتار"| GPT
    EXT -->|"HTML/JSON/Atom/PDF"| P
    P -->|"واکشیِ مقاوم"| EXT
    CRON -->|"رویدادِ زمان‌بندی"| P
    P <-->|"خواندن/نوشتن"| D1
    P <-->|"بردار/پرس‌وجو"| VEC
    P -->|"متن → embedding"| AI
```

---

## سطح ۱ — فرایندهای اصلی (۱۵ ماشینِ بزرگ)

```mermaid
flowchart TD
    GPT(["جی‌پی‌تی"])
    EXT(["منابعِ بیرونی"])
    CRON(["۴ Cron"])

    P1["P1 کشفِ یکپارچه\n(unified-search)"]
    P2["P2 کشفِ مقاله\n(article-search)"]
    P3["P3 تجزیه و کش\n(parse-document)"]
    P4["P4 جست‌وجوی درون‌متن\n(search-text)"]
    P5["P5 خواندن=شاهد\n(read-chunk)"]
    P6["P6 امتیاز/ترفیع\n(score-read-evidence)"]
    P7["P7 جست‌وجوی محلیِ شارد\n(search-global-text)"]
    P8["P8 چرخهٔ بردار\n(vectorize-*)"]
    P9["P9 حافظهٔ GPT\n(memory-*)"]
    P10["P10 نگه‌داریِ خودکار\n(scheduled crons)"]

    DC[("کشِ سند")]
    GC[("سند/قطعهٔ سراسری + شارد")]
    SS[("نشستِ جست‌وجو")]
    RE[("read_events")]
    MEM[("حافظهٔ GPT")]
    VS[("بردار: owner/segment/job")]
    MNT[("قفل/وضعیتِ نگه‌داری")]

    GPT --> P1 & P2 & P3 & P4 & P5 & P6 & P9
    EXT --> P1 & P2 & P3
    CRON --> P10

    P1 --> SS
    P1 -.->|"ضمیمهٔ موازی"| P9
    P2 --> P3
    P3 --> DC
    P4 --> DC & GC
    P4 --> P8
    P5 --> RE
    P5 --> DC & GC
    P6 --> RE
    P6 -->|"ترفیع"| DC & GC
    P7 --> GC
    P8 --> VS
    P8 --> AI(["Workers AI"])
    P8 --> VEC[("Vectorize")]
    P9 --> MEM
    P9 --> VS
    P10 --> MNT
    P10 -->|"بازایندکس"| GC
    P10 -->|"بردارسازیِ حافظه"| P8
    P10 -->|"هرسِ کش"| DC
```

---

## سطح ۲ — خطوطِ لولهٔ کلیدی

### خط ۱ — جست‌وجوی یکپارچه (unified-search) با ضمیمهٔ موازیِ حافظه

```mermaid
flowchart TD
    REQ["درخواست + q"] --> SESS{"درخواستِ صفحهٔ\nنشست است؟"}
    SESS -->|بله| PAGE["readSearchSessionPage\n(منقضی→۴۱۰)"]
    SESS -->|نه| GATHER["جمعِ نامزد از قلمروهای پیش‌فرض:\ndiscovery_cache · document_cache\n· scored_cache · external\n(marxists_local منسوخ: نادیده، فقط diagnostic)"]
    GATHER --> SIDE["runUnifiedGptMemorySidecarSafely\n(موازی، context_only)"]
    GATHER --> GATE["passesUnifiedSearchRelevanceGate\n(دروازهٔ ربط)"]
    GATE --> DEDUP["applySessionWideDedupAndSuspicion\n(حذفِ سخت + ظنِ نرم)"]
    DEDUP --> RRF["applyProductionWeightedRrfRanking\n(تلفیقِ وزن‌دار)"]
    RRF --> FREEZE["createSearchSession\n(انجماد نتایج)"]
    SIDE -.->|"ضمیمهٔ بافتار"| OUT
    FREEZE --> OUT["نامزدها + sidecar"]
```
لوله‌ها: «دروازهٔ ربط» نامزدهای بی‌ربط را عبور نمی‌دهد؛ «dedup» تکراری‌های قطعی را ادغام و مشکوک‌ها را برچسب می‌زند؛ «RRF» ترتیب می‌دهد؛ «انجماد» نتیجه را برای صفحه‌بندی ثابت می‌کند. ضمیمهٔ حافظه از لولهٔ جداگانهٔ موازی می‌آید و **هرگز** وارد لولهٔ نامزد/RRF نمی‌شود.

### خط ۲ — تجزیهٔ سند (parse-document)

```mermaid
flowchart TD
    IN["source + url/doi/id"] --> ID["buildDocumentCacheIdentity\n(کلیدِ منبع‌محور)"]
    ID --> CACHE{"readDocumentCache\n(کش-اول + یکپارچگی)"}
    CACHE -->|"hit"| HANDOFF
    CACHE -->|"miss/خراب"| TARGET["resolveParseDocumentTarget"]
    TARGET --> JSTOR{"JSTOR؟"}
    JSTOR -->|بله| RL["enforceJstorHumanRateLimit 🔒نرخ"]
    JSTOR -->|نه| FETCH
    RL --> FETCH["parseTargetWithJinaFallback\n(مستقیم → r.jina.ai)"]
    FETCH --> CHUNK["makeCacheStorageChunks\n(~۲۴هزار کاراکتر، زیرِ سقفِ ۲MB)"]
    CHUNK --> WRITE["writeDocumentCache\n(شارد + رجیستری)"]
    WRITE --> HANDOFF["buildParseDocumentCacheHandoff\n(راهنمای جست‌وجو/خواندن)"]
```

### خط ۳ — خواندن، امتیاز، ترفیع (read → score → promotion)

```mermaid
flowchart TD
    R["read-chunk + هدف"] --> OG{"گاردِ مالکیت (c.6-k):\ncache_chunk_id تنها است؟"}
    OG -->|"بله، بدونِ owner"| ERR["ambiguous_cache_chunk_id_requires_owner"]
    OG -->|"همراهِ owner معتبر"| RES["resolveSearchScope\n(source_ref/cache_key/chunk_id)"]
    RES -->|"owner ناهماهنگ"| MM["read_owner_mismatch"]
    RES --> MARK["markGlobalChunkRead /\nmarkDocumentCacheRead\n(fetch_count++ اینجا، نه امتیاز)"]
    MARK --> EV["createReadEvent\n(result_kind=evidence)"]
    EV --> OUT1["شاهد + read_event_id"]
    OUT1 --> SC["score-read-evidence + value_score"]
    SC --> SOG{"گاردِ مالکیتِ امتیاز (c.6-k):\nowner رویداد = موردانتظار؟"}
    SOG -->|نه| SRJ["score_owner_mismatch\nscore_rejected=true"]
    SOG -->|بله| NEUTRAL{"خنثی‌نسبت‌به‌تکرار\n(قبلاً امتیاز خورده؟)"}
    NEUTRAL -->|بله| SKIP["به‌روزرسانیِ مالک رد می‌شود"]
    NEUTRAL -->|نه| RECHK["maybeRunDuplicateRecheck\n(پیش از ترفیع)"]
    RECHK -->|"تکرارِ تأییدشده"| BLOCK["ترفیع مسدود"]
    RECHK -->|"پاک"| PROMO["computePromotionDecision\n(آستانه: marxists۶۰/پیش‌فرض۷۰/خیلی‌بالا۸۵)"]
    PROMO --> APPLY["پرچم‌های نگه‌داری:\nhard_ttl_disabled / timeless_until_pressure"]
```

### خط ۴ — چرخهٔ حیاتِ بردار (vectorize lifecycle)

```mermaid
flowchart TD
    PREP["prepare-one 🔒\n(فقط فراداده/کارِ معلق)"] --> SEG["vector_segments\n(range/hash)"]
    SEG --> JOB["vectorization_jobs = pending"]
    JOB --> RUN["run-jobs 🔒\n(اعتبارِ هش → claim)"]
    RUN --> EMB["env.AI.run(model)\nembedding"]
    EMB --> UP["Vectorize.upsert"]
    UP --> STATE["refreshVectorOwnerStateAfterRun"]
    RUN -.->|"خطای سهمیه"| PQ["paused_quota\n(ازسرگیریِ بعدی)"]
    TRANS["transition-owner 🔒"] --> SEG
    DEL["mark-deleted → run-deletes 🔒"] --> VEC[("Vectorize")]
```

### خط ۵ — جست‌وجوی ترکیبیِ محلی (لغوی + برداری)

```mermaid
flowchart TD
    Q["search-text + q"] --> SCOPE["resolveSearchScope\n(قطعه‌های حل‌شده)"]
    SCOPE --> LEX["searchResolvedTextChunks\n(شاخهٔ لغوی FTS5)"]
    SCOPE --> VECB{"vector_mode\nروشن/خودکار؟"}
    VECB -->|بله| EMBQ["getOrEmbedHybridQuery\n(کشِ درون‌نشست)"]
    EMBQ --> NN["queryVectorizeIndexForHybrid\n(نزدیک‌ترین همسایه)"]
    LEX --> MERGE["dedupeAndMergeHybridCandidates"]
    NN --> MERGE
    MERGE --> PROJ["projectResultForGpt\n(نامزد + گزارشِ شاخه‌ها)"]
```

### خط ۶ — حافظهٔ GPT (memory)

```mermaid
flowchart TD
    BOOT["memory-bootstrap\n(بافتارِ اولیه)"] --> CTX["انتظارات/راهنماها"]
    WRITE["memory-write/append/rewrite 🔒MEMORY_WRITE_TOKEN"] --> SEG2["splitMemoryContentIntoSegments\n→ gpt_memory_segments"]
    SEG2 --> TXN["gpt_memory_transactions"]
    SEG2 -.->|"در صورتِ فعال‌بودن"| IMM["maybeImmediateVectorizeNewGptMemorySegments\n(کارِ بردارِ معلق)"]
    SRCH["memory-search"] --> HYG{"applyGptMemoryHygieneFilter (c.6-k):\nproject_context_eligible؟"}
    HYG -->|"debug/test"| DROP["فیلتر (پیش‌فرض memory_scope=project)"]
    HYG -->|"project"| RES2["searchGptMemoryResolved\n(لغوی + برداریِ حافظه)"]
    RES2 --> BUND["bundleGptMemoryHits\n(result_kind=memory_context_candidate)"]
    READ["memory-read"] --> MARKR["markMemorySegmentRead"]
```

### خط ۷ — نگه‌داریِ خودکارِ زمان‌بندی‌شده (scheduled, تازه در c.6)

```mermaid
flowchart TD
    EV["scheduled(event)"] --> BYC["runScheduledByCron\n(تطبیق عبارت cron)"]
    BYC -->|"0 0 L */3 *"| RX["بازایندکسِ marxists"]
    BYC -->|"0 * * * *"| MV["microtaskِ بردارسازیِ حافظه"]
    BYC -->|"17 */8 * * *"| CAP["ظرفیتِ بردارِ حافظه\n(تخلیه در صورتِ پُری)"]
    BYC -->|"33 2 * * *"| PRN["هرسِ کشِ منقضی"]
    MV --> LOCK{"tryAcquireMaintenanceLock\n+ حداقل‌فاصله"}
    LOCK -->|busy/زود| SKIP2["skip"]
    LOCK -->|آزاد| ONE["یک job: embedding+upsert\n→ releaseMaintenanceLock"]
    CAP --> EVICT["selectGptMemoryCapacityEvictionCandidate\n→ capacity_eviction_log"]
```
لوله‌های این خط منطقِ «اجازهٔ عبور» دارند: قفلِ مشغول یا حداقل‌فاصلهٔ نرسیده، کار را عبور نمی‌دهد (skip)؛ فقط وقتی هر دو آزاد باشند، **یک** واحدِ کوچک عبور می‌کند.

### خط ۸ — دکوراتورِ فازِ صفر: گاید + قراردادِ لاغرِ wire (GS/GN..GR/HG..HK)

هر پاسخِ JSON، پیش از خروج از کارخانه، از یک ماشینِ پایانیِ واحد می‌گذرد: `attachPhaseZeroObservability` (بنرِ `[05]` در `worker.js`).

```mermaid
flowchart TD
    H["هر هندلر → json(data)"] --> K["تشخیص/الصاقِ result_kind\n+ گیتِ کیفیتِ شاهد (GU: PDFِ خام/CAPTCHA → diagnostic)"]
    K --> G["ساختِ gpt_guide:\nnext (فراخوانِ پُرشده) · preferred/also_possible\npage_next (فقط وقتی has_more) · error_code+remedy (خطا)"]
    G --> S{"فلگِ result_diagnostics_dev_mode؟"}
    S -->|خاموش (پیش‌فرض)| SLIM["سه denylist روی نسخهٔ wire:\nبخش‌های تلمتری + فیلدهای هر آیتم + sidecar\n(+حذفِ دوقلوی bundles و docِ legacy)"]
    S -->|روشن| FULL["پاسخِ کامل با کلِ تلمتری"]
    SLIM --> HOIST["hoistِ فیلدهای حیاتی به بالای JSON"]
    FULL --> HOIST
    HOIST --> OUT["پاسخ به GPT"]
```

نکتهٔ صحت: denylistها فقط کپیِ wire را می‌تراشند؛ نتایجِ ذخیره‌شده در search-session کامل می‌مانند، پس page-next و بازسازیِ بافتارِ امتیازدهی هیچ دیتایی از دست نمی‌دهند. مرجع: `WIRE_CONTRACT.md` (+ پاسبانِ `tools/wire-check.py`).
