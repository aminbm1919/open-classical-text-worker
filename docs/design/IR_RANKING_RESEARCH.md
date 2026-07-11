# مرجعِ پژوهشیِ وزن‌های بازیابی/رتبه‌بندی (برای تنظیمِ قاعده‌مندِ فیوژن)

> سنتزِ deep-research (۲۰۲۶-۰۷-۰۵، ۱۰۶ ایجنت، ۲۴ ادعا با رأیِ ۳-۰ تأیید). منابعِ اصلی: مقالهٔ RRF (Cormack و همکاران، SIGIR ۲۰۰۹)، monographِ BM25 (Robertson & Zaragoza ۲۰۰۹)، مستنداتِ Elasticsearch/Lucene/Weaviate. هدف: تعیینِ اصولیِ وزنِ dense↔lexical و درونِ lexical وزنِ عنوان/بدنه و رفتارِ فراوانی، برای متونِ نظریِ بلند که مفهوم در بدنه است نه عنوان.

## اعدادِ استاندارد (تأییدشده، high confidence)

| پارامتر | مقدارِ توصیه‌شده | منبع |
|---|---|---|
| RRF `k` | **60** (kِ بزرگ‌تر = تأثیرِ بیشترِ رتبه‌های پایین‌تر) | Cormack SIGIR'09 · Elastic RRF docs |
| روشِ ادغام | RRF روی **رتبه** نه امتیازِ خام → بی‌نیاز از نرمال‌سازی/تیونِ وزن؛ برای بایاسِ یک شاخه: **weighted RRF** = `weight × 1/(k+rank)` | Elastic weighted-RRF (GA در Stack 9.2) |
| اشباعِ فراوانی `k1` | **1.2** (پیش‌فرضِ Lucene/ES/Weaviate؛ بازهٔ R–Z: 1.2<k1<2؛ ES: 0.5–2.0) | R–Z §; Elastic Practical BM25 Part 2/3 |
| نرمالِ طول `b` | **0.75** پیش‌فرض؛ برای متنِ بلندِ تخصصی **پایین‌تر (~0.3–0.5)** | R–Z (0.5<b<0.8)؛ Elastic Part 3؛ Lv & Zhai SIGIR'11 |
| عنوان : بدنه | **۲×–۵×** (تفسیرِ replication در BM25F)؛ عددهای وبیِ ۱۰×–۳۸× مخصوصِ anchor-textِ وب‌اند، کپی نشوند | Robertson & Zaragoza §3.6 / §3.6.4؛ Table 3.1 |

## اصولِ کلیدی (چرا)
- **اشباعِ فراوانی حیاتی است:** BM25 با `tf/(k1+tf)` سهمِ هر ترم را به یک سقفِ مجانبی می‌رساند → «فصلی که واژه‌ای را ۱۰۰ بار تکرار کند نباید غالب شود». برخلافِ tf×idf (بی‌کران). — R&Z verbatim.
- **متنِ نظریِ بلند → bِ کمتر:** طولِ یک رساله نشانهٔ «تخصصی‌بودن روی یک موضوع» است نه پرحرفی (اسکوپ در برابر verbosity)؛ پس نباید به‌خاطرِ طول جریمه شود. Elastic Part 3 صریحاً patent/spec را مثال می‌زند؛ Capital هم همین دسته.
- **جای غلبهٔ dense:** وقتی مفهوم در بدنه است و در عنوان نیست، تطابقِ معناییِ برداری تنها لنگرِ قابل‌اتکاست؛ وزن‌دهیِ per-field lexical نمی‌تواند آن را تأمین کند → dense باید وزنِ بالاتری بگیرد برای کوئریِ مفهومی/بلند. (رزروِ غلبهٔ sparse برای نام/توکنِ نادر/دقیق.)
- **hybrid > هر کدام به‌تنهایی:** بهبودِ recall ~۱۰–۳۰٪ نسبت به هر شاخهٔ تنها (چند بنچمارک).
- **chunk/passage retrieval:** امبدِ کلِ سندِ بلند در یک بردار، جزئیاتِ عمیق را رقیق می‌کند (centroidِ مبهم)؛ پس بازیابیِ سطحِ passage لازم است. (ما این را داریم.)

## نگاشت به وورکرِ ما (`getProductionFusionPolicy` + scorerِ لغوی)

| مورد | توصیه | وورکرِ ما الان | حکم |
|---|---|---|---|
| RRF k | 60 | `rrf_k=60` | ✅ درست |
| dense در برابر lexical | dense ≥ lexical برای کوئریِ مفهومی | `vector_m3=1.00` < `lexical_internal=1.20` | ⚠️ برداری کم‌وزن |
| عنوان:بدنه | ۲×–۵× (میانه) | `termMatchScore`: title 0.8, body 0.55 ≈ ۱٫۴۵× | کمی پایین → ~۲× |
| اشباعِ فراوانی | k1≈1.2 | FTS5 `bm25()` اشباع دارد؛ scorerِ افزایشیِ سفارشی احتمالاً نه | بررسی/سقف‌گذاری |
| نرمالِ طول b | 0.75؛ بلند→0.3–0.5 | FTS5 bm25 پیش‌فرض (k1=1.2,b=0.75؛ در SQLite ثابت) | جبران از راهِ وزنِ برداری |
| chunk retrieval | بله | چانک + امبدِ سگمنت | ✅ همسو |

وزن‌های فعلیِ فیوژن (`getProductionFusionPolicy`, external_weight_shift=0.15):
`lexical_internal 1.20 · vector_m3 1.00 · vector_bge_large 1.15 · internal_cache_hybrid 1.15 · document_cache 1.10 · scored_cache 1.20 · marxists_local 1.10 · external_* 0.95..1.10 +0.15`

## پیشنهادِ اصلاح (به‌ترتیبِ اثر، کم‌ریسک اول)
1. **بالابردنِ وزنِ شاخهٔ برداری** (`vector_m3` از 1.0 به ~1.2–1.35، حداقل هم‌ترازِ lexical) — مهم‌ترین اهرم؛ وقتی Capital با sem≈0.569 بازیابی می‌شود، همین آن را برنده می‌کند. پشتِ فلگ + برگشت‌پذیر.
2. **اشباعِ فراوانی در scorerِ لغویِ سفارشی** اگر با تکرارِ تک‌ترم بی‌کران رشد می‌کند (الگوی `tf/(k1+tf)`). `coverageBonus`ِ فعلی پهنای ترمِ *متمایز* را پاداش می‌دهد (خوب)؛ نگرانی فقط تکرارِ یک ترم.
3. **نسبتِ عنوان:بدنه ~۲×** — نه بیشتر (برای این متون مفهوم در عنوان نیست؛ boostِ زیادِ عنوان بدرتبه می‌کند).
4. **bِ کمتر برای متنِ بلند** اگر مسیرِ FTS اجازه دهد؛ وگرنه از راهِ #۱ جبران.

**پیش‌نیازِ Marx فراتر از وزن:** حتی با وزنِ برداریِ بالاتر، اگر شاخهٔ برداری Capital را *بازیابی* نکند (recall/تنکیِ پیکره + topK=5 + فیلترِ دامنه) فایده ندارد. پس دو کارِ مکمل: (الف) وزنِ برداری، (ب) پهن‌کردنِ recall برداری (topK/scope) + رشدِ پیکره.

## نکاتِ روش‌شناختی / احتیاط
- RRF قطعیاً بهینه نیست: Bruch و همکاران (TOIS 2023, arXiv:2210.11934) نشان دادند ترکیبِ convex/خطیِ tuned با ~۴۰ نمونهٔ قضاوت‌شده از RRF بهتر می‌شود. **ما دادهٔ قضاوت نداریم** → weighted-RRF با k=60 انتخابِ امنِ اصولی.
- تفسیرِ replication در BM25F فقط برای نسخهٔ **simple (bِ یکنواخت)** دقیق است؛ نسخهٔ variable-b معادلِ تکرارِ لفظی نیست → از آن به‌عنوانِ *شهود* برای تعیینِ boost استفاده کن، نه اتحادِ دقیق.
- عددهای وبیِ عنوان (v_title=38.4/13.5 در TREC-2003) anchor-text-heavy وب‌اند — برای پیکرهٔ full-textِ علومِ‌انسانی کپی نشوند.

## سؤالاتِ باز (نیازِ evalِ محلی)
1. نسبتِ دقیقِ dense↔lexicalِ بهینه برای full-textِ فلسفه/نظری؟ منابع فقط جهت را می‌دهند؛ عددِ کالیبره نیازِ یک evalِ کوچکِ قضاوت‌شده روی پیکرهٔ Marx/Capital دارد.
2. اندازه/همپوشانیِ chunk بهینه برای مفهومِ عمیقِ بدنه؟ و تجمیعِ امتیازِ chunk→document (max/sum/top-k) قبل یا بعد از RRF؟
3. برای پیکرهٔ بدونِ anchor stream، boostِ عنوان بینِ ~۲× و عددهای افراطیِ وب کجا می‌نشیند؟
4. آیا سوییچ به BM25L/BM25+ برای متنِ کتاب‌طولی بهتر از صرفاً کم‌کردنِ b است؟ (و آیا در مسیرِ Lucene/Vectorizeِ ما موجود است؟)

## منابعِ کلیدی
- Cormack, Clarke, Büttcher — RRF, SIGIR 2009: `cormack.uwaterloo.ca/cormacksigir09-rrf.pdf`
- Robertson & Zaragoza — The Probabilistic Relevance Framework: BM25 and Beyond (2009): `staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf`
- Elastic — RRF: `elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion`
- Elastic — weighted RRF: `elastic.co/search-labs/blog/weighted-reciprocal-rank-fusion-rrf`
- Elastic — Practical BM25 Part 2/3 (k1,b): `elastic.co/blog/practical-bm25-part-2...` / `...part-3...`
- Elastic — combined_fields (BM25F): `elastic.co/docs/reference/query-languages/query-dsl/query-dsl-combined-fields-query`
- Weaviate — keyword/BM25F: `docs.weaviate.io/weaviate/concepts/search/keyword-search`
- Bruch et al. — analysis of fusion (TOIS 2023): `arXiv:2210.11934`
- Lv & Zhai — "When documents are very long, BM25 fails!" (SIGIR 2011, BM25L)
