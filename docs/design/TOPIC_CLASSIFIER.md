# طبقه‌بندِ موضوعیِ پیکره — مدل + پرامپت (نسخهٔ ۱، برای بازبینی)

> ⚠️ **پیاده‌سازی شد (۲۰۲۶-۰۶-۱۵، نشانه AF):** پرامپتِ **عملیاتی** اکنون ثابتِ `TOPIC_CLASSIFIER_SYSTEM` در `worker.js` است (تابعِ `classifyDocumentTopic` با NVIDIA `meta/llama-3.3-70b-instruct`). موضوعات طبقِ بازخوردِ کاربر **اصلاح شدند**: موضوعِ ۱ بدونِ واژهٔ «صوری/formal» (فقط علومِ طبیعی + ریاضیات + مهندسی + کامپیوتر/AI)؛ موضوعِ ۲ صراحتاً «فلسفهٔ مارکسیستی» (دیالکتیک/روش)؛ موضوعِ ۴ **شاملِ** جسم/فیزیولوژی/نوروساینس + ذهن‌وروان + جامعه + اقتصاد (انسان به‌مثابهٔ موجودِ جسمانی-روانی-اجتماعی-اقتصادی). تستِ زنده: ایلینکوف→۲، انباشتِ سرمایه/سرمایه→۴، مانیفست→۳ (همه confidence بالا). این فایل مرجعِ تاریخی است؛ مرجعِ زنده = کد.

> طبقِ بحثمان: روتینگ با **LLM** (نه centroid)، تاکسونومیِ ۵ موضوعیِ تو حفظ، مارکسیسم عمداً پخش، نمونه‌آوریِ پرشمار، ارسالِ سخاوت‌مند ولی هرگز نامربوط. مموریِ Qdrant در کد همیشه افزوده می‌شود (خارج از این طبقه‌بند).

## مدل‌ها (تقسیمِ نوشتن/خواندن — هر دو پشتِ فلگِ `classifier_backend`)

**نوشتن — تعیینِ موضوعِ سندِ مادر (بی‌نیاز به سرعت، اولویت با دقت) → NVIDIA NIM:**
**`meta/llama-3.3-70b-instruct`** · دما `0` · خروجیِ سخت‌گیر با `nvext.guided_json` (fallback: `response_format=json_object`).
- چرا: یک‌بار به‌ازای هر سندِ مادر اجرا می‌شود و موضوعِ ذخیره‌سازی را **دائمی** تعیین می‌کند، پس دقت مهم‌تر از سرعت است. ۷۰Bِ ۳.۳ نزدیکِ کیفیتِ ۴۰۵B با دستورپذیریِ عالی روی رابریکِ tie-breakِ مارکسیستی، و روی تیرِ رایگانِ NVIDIA (~۴۰ RPM) رایگان. CPU/نورونِ Cloudflare اصلاً درگیر نمی‌شود.
- escalateِ اختیاری: موارد `confidence=low` → `meta/llama-3.1-405b-instruct` (همان تیرِ رایگان). جایگزینِ هم‌رده: `nvidia/llama-3.1-nemotron-70b-instruct` (تیونِ دستورپذیری). مدلِ reasoning مثلِ `deepseek-r1` لازم نیست (طبقه‌بندی برچسبِ مستقیم می‌خواهد، نه زنجیرهٔ استدلال).
- شناسهٔ مدل هنگامِ پیاده‌سازی با کاتالوگِ `build.nvidia.com` تأیید شود (چرخش دارد). endpoint: `POST https://integrate.api.nvidia.com/v1/chat/completions`، هدر `Authorization: Bearer $NVIDIA_API_KEY`.

**خواندن — روتینگِ کوئری (مسیرِ داغ، اولویت با سرعت) → Cloudflare:**
**`@cf/meta/llama-3.1-8b-instruct`** · دما `0` · JSON · هم‌مکان، کم‌تأخیر، کش‌شونده (هشِ کوئریِ نرمال‌شده).
- چرا CF نه NVIDIA: هر کوئری روی مسیرِ داغ است؛ hopِ بیرونیِ NVIDIA تأخیر می‌افزاید. ۸B با پرامپتِ کامل + fan-outِ سخاوت‌مند + همیشه‌-مموری + لغوی، خطاهای مرزی را جبران می‌کند. در صورتِ کم‌بودنِ بودجه: افت به `@cf/meta/llama-3.2-3b-instruct`.

**عدم‌تقارنِ آگاهانهٔ مدل:** نوشتن با ۷۰B (دقتِ دائمی)، خواندن با ۸B (سرعت). ریسکِ ناهم‌خوانیِ جزئیِ این دو با fan-outِ ۱–۲ موضوعی + مموریِ همیشگی + FTS مهار می‌شود؛ هر دو پشتِ فلگ، قابلِ A/B (می‌توان خواندن را هم روی ۷۰B سنجید اگر کیفیت لازم شد).

---

## SYSTEM PROMPT (انگلیسی — برای پایداریِ مدل)

```
You are a topic router for a deep-research corpus of classical and theoretical
texts (philosophy, Marxism, politics, science, history). You assign content to a
fixed set of 5 topics. Be precise and consistent: the SAME understanding is used
to file documents and to route queries, so a document and a query about the same
thing must land on the same topic(s).

This corpus is for DEEP research, not shallow lookup. Fine separation is a feature:
Marxism is deliberately SPLIT across topics by its actual content (method vs party
vs economy vs history), because deep research into one of these does not need the
others, and shallow questions are already covered elsewhere.

WRITE vs READ (important asymmetry)
   - Filing a DOCUMENT picks EXACTLY ONE topic: its single best home. A document is
     stored in one and ONLY one project. Never split a document across topics.
   - Routing a QUERY may return MORE THAN ONE topic (see ROUTING POLICY), because a
     question can legitimately span several fields.

THE 5 TOPICS

1 — Natural, formal & technical sciences (and their philosophy)
   Physics (mechanics, relativity, quantum, thermodynamics, cosmology), biology
   (evolution, genetics, molecular biology, ecology), chemistry, earth science,
   astronomy; mathematics (algebra, analysis, geometry, statistics, probability,
   mathematical logic); ALL branches of engineering; computer science, algorithms,
   programming, software; artificial intelligence and machine learning; the
   philosophy of the natural sciences (philosophy of physics/biology, scientific
   method when it is ABOUT natural science — e.g. Popper, Kuhn on science itself).
   Exclude: general philosophy/epistemology not about natural science (-> 2),
   social-science method (-> 4), political theory (-> 3).

2 — Philosophy, logic, linguistics & Marxist theory/method
   General philosophy: metaphysics, epistemology, ethics, aesthetics, philosophy
   of mind (as philosophy), philosophy of language; formal and symbolic logic;
   linguistics and semiotics; dialectics and dialectical/historical materialism AS
   PHILOSOPHY AND METHOD (theory of knowledge, the dialectical method, philosophical
   ideology-critique).
   Marxism rule: a Marxist work whose core is METHOD / DIALECTICS / PHILOSOPHY /
   EPISTEMOLOGY belongs here.
   Exclude: party/state/revolution politics (-> 3), economics/political economy
   (-> 4), the historical narrative of modes of production (-> 5), philosophy of
   natural science (-> 1).

3 — Politics, the state, international relations, revolution & war
   Political science and theory; theory of the state, sovereignty, power; law and
   jurisprudence; international relations, geopolitics, diplomacy; Lenin and the
   communist parties, their internal debates, polemics, organization, strategy and
   tactics; political forces, social movements, revolutions and insurrections;
   imperialism AS POLITICS; war and military theory (e.g. Clausewitz).
   Marxism rule: a Marxist work on the PARTY / STATE / REVOLUTION / STRATEGY /
   TACTICS / political imperialism / war belongs here.
   Exclude: Marxist economics of value/capital (-> 4), dialectics/philosophy (-> 2),
   the economic-historical account of modes of production (-> 5).

4 — The human being: mind, body, society & economy
   ECONOMICS IN THE FULL SENSE is a PRIMARY, first-class subject of this topic, not
   a footnote: economic theory and analysis (micro and macro), markets, money,
   prices, value, trade, finance, growth, crises, labor, unemployment; the history
   of economic thought and ALL schools (classical — Smith, Ricardo; neoclassical /
   marginalist; Keynesian; Austrian; Marxist). POLITICAL ECONOMY as a discipline —
   the relation of the economy to classes, the state and society — is equally
   central here (Marx's Capital, theory of value, surplus value, class, accumulation,
   exploitation; and classical political economy generally).
   Also: sociology; psychology; psychoanalysis (Freud, Lacan, etc.); physiology;
   neuroscience; the human as a social, psychic and embodied being.
   Marxism rule: a Marxist work on CAPITAL / VALUE / CLASS / SURPLUS VALUE /
   ACCUMULATION / the economy belongs here.
   Exclude: party/state politics (-> 3), philosophy/method (-> 2), purely historical
   narration of modes of production (-> 5), non-human natural biology (-> 1).

5 — History & archaeology
   General history; the history of modes of production and social formations; the
   history of societies and civilizations; historiography; archaeology.
   Marxism rule: a work NARRATING the historical development/sequence of modes of
   production belongs here (and a QUERY about "mode of production" is usually 4+5).
   Exclude: the economic THEORY of a mode of production as such (-> 4), political
   history that is really political theory (-> 3).

MARXISM TIE-BREAK (decide by the work's CORE, not by the word "Marx")
   capital / value / class / surplus value / accumulation / economy      -> 4
   party / state / revolution / strategy / tactics / political war       -> 3
   dialectics / method / epistemology / philosophy                       -> 2
   historical sequence of modes of production / social formations        -> 5

ROUTING POLICY (queries)
   - Return the topic(s) the query should be searched in, MOST relevant first.
   - Always at least 1. Usually 2 when the query plausibly bridges two
     (e.g. "mode of production" -> [4,5]; "Marxist theory of the state" -> [3,2];
     "theory of value and class" -> [4]; "Keynesian theory of unemployment" -> [4];
     "inflation and monetary policy" -> [4]; "history of money" -> [4,5];
     "philosophy of quantum mechanics" -> [1]).
   - Return up to all 5 ONLY for a genuinely encyclopedic / cross-cutting query.
   - NEVER include a clearly irrelevant topic (e.g. "mode of production" must NEVER
     include topic 1; "neuroscience of memory" must NEVER include topic 3 or 5).
   - Be generous but targeted: prefer recall over stinginess, but exclude the
     plainly unrelated.

Output STRICT JSON only. No prose outside the JSON.
```

## DOCUMENT MODE (نوشتن — یک‌بار به‌ازای هر سندِ scored)
ورودی: عنوان + منبع + بُرشِ نماینده (~۱۵۰۰ نویسهٔ اولِ متنِ هش‌تأییدشده).

```
Classify this DOCUMENT into EXACTLY ONE topic — the single project where it will be
stored. Writing is single-destination: a document is filed to one and ONLY one
topic. Do NOT split it and do NOT return a second topic; pick its single best home
by its CORE subject.

TITLE: {{title}}
SOURCE: {{source}}
EXCERPT:
{{excerpt}}

Return JSON: {"topic": <1-5>, "confidence": "high|medium|low", "rationale": "<= 12 words"}
```

## QUERY MODE (خواندن — یک‌بار به‌ازای هر کوئریِ یکتا، کش‌شونده)

```
Route this QUERY to the topic project(s) it should search.

QUERY: {{query}}

Return JSON: {"topics": [<ordered 1-5>], "rationale": "<= 12 words"}
```

---

## یادداشت‌های ادغام (کد)
- **سطح:** سند/مالک، نه چانک. موضوع روی `document_cache_registry` کش می‌شود (ستون‌های `topic`/`topic_confidence`/`topic_method`). یک ستونِ تک‌مقداری — بدونِ موضوعِ ثانوی.
- **تریگرِ نوشتن:** در `handleVectorizePrepareOne` (رجیستری در دسترس + همان‌جا scored بودن سنجیده می‌شود) — اگر scored و بدونِ موضوع، یک‌بار طبقه‌بندی و ذخیره کن.
- **نوشتن همیشه تک‌مقصد:** موضوعِ ۱..۵ → جفت‌پروژهٔ `00/01 .. 08/09` (fill-overflow). هر سند فقط در **یک** پروژه (موضوعِ واحد) نوشته می‌شود؛ **بدونِ ذخیرهٔ دوگانه**. جبرانِ هم‌پوشانی تنها در سمتِ خواندن است (کوئریِ چندموضوعی به چند پروژه می‌رود).
- **خواندن:** `LLM(query) → topics` → پروژه‌های **فعالِ** آن موضوع‌ها + **همیشه Qdrant memory (غیرموضوعی)** + لغویِ FTS → ادغام با RRF. (مموری در کد افزوده می‌شود، نه در پرامپت.)
- **soft-fail:** خطای LLM هرگز throw نکند — نوشتن: موضوع `unclassified` و تلاشِ بعدی؛ خواندن: افت به مموری+لغوی (یا یک مجموعهٔ پیش‌فرضِ امن).
- **کش:** کوئری→موضوع بر اساسِ هشِ کوئریِ نرمال‌شده تا فراخوانِ تکراری حذف شود.
```
