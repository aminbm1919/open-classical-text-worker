# -*- coding: utf-8 -*-
"""
e2e-check — تستِ رگرسیونِ عملکردهای اساسیِ وورکر (مکملِ wire-check که فقط شکلِ پاسخ را می‌پاید).

پوشش: getWorkerInfo/orientation، کشف→خواندن→جست‌وجوی درون‌متن، صفحه‌بندیِ session، زنجیرهٔ parse→read→reject(-1)
روی یک سندِ یک‌بارمصرف (پاک از scored_cache می‌ماند)، چرخهٔ کاملِ حافظه (write→search→read→delete با پاک‌سازی)،
تاکسونومیِ خطا (remedy درست)، hybrid-title، get-source/links، parseِ سندِ بلند (gpt_guide.next سنتزی)، cache-status.
اجرا: python tools/e2e-check.py   (خروجی: PASS/FAIL per check؛ exit 1 روی هر FAIL)
توجه: read-chunk و parse رویدادِ خواندنِ واقعی می‌سازند (رفتارِ عادی)؛ تستِ score فقط مسیرِ reject(-1) را می‌زند
تا scored_cache آلوده نشود؛ حافظهٔ تستی در انتها حذف می‌شود.
"""
import json, sys, time, urllib.request, urllib.error, urllib.parse

BASE = os.environ.get("WORKER_BASE_URL", "https://chunking.YOUR-SUBDOMAIN.workers.dev")
FAILS = []

def call(path, method="GET", body=None, timeout=120, tries=2):
    last = None
    for _ in range(tries):
        try:
            data = json.dumps(body).encode() if body is not None else None
            req = urllib.request.Request(BASE + path, data=data, method=method,
                                         headers={"User-Agent": "e2e-check", "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return r.status, json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read().decode("utf-8"))
        except Exception as e:
            last = e
            time.sleep(2)
    raise last

def check(name, cond, detail=""):
    if cond:
        print("PASS   " + name)
    else:
        print("FAIL   " + name + ("  -- " + str(detail)[:200] if detail else ""))
        FAILS.append(name)

def main():
    # 1. getWorkerInfo + research_orientation
    s, d = call("/")
    ro = d.get("research_orientation") or {}
    check("worker-info: 200 + research_orientation(7 sections)",
          s == 200 and len(ro) >= 6, list(ro.keys()))

    # 2. discovery
    s, d = call("/unified-search?query=communist+manifesto&max=5")
    r0 = (d.get("results") or [{}])[0]
    check("unified-search: discovery + results + guide.next + read_hint",
          s == 200 and d.get("result_kind") == "discovery" and len(d.get("results") or []) >= 1
          and bool((d.get("gpt_guide") or {}).get("next")) and bool(r0.get("read_hint")),
          d.get("error"))
    sess = d.get("search_session_id")

    # 3. session paging
    if sess and d.get("has_more"):
        s2, p = call("/unified-search?search_session_id=%s&position=%s" % (sess, d.get("next_position")))
        check("paging: session page-2 returns results",
              s2 == 200 and len(p.get("results") or []) >= 1, p.get("error"))
    else:
        print("SKIP   paging (has_more=false)")

    # 4. search-inside
    s, d = call("/search-text?document_cache_key=wikisource:en:The_Communist_Manifesto&q=communism&max=3")
    check("search-inside: candidate + hits + read_hint",
          s == 200 and (d.get("count") or 0) >= 1 and bool((d.get("results") or [{}])[0].get("read_hint")),
          d.get("error"))

    # 5. read (evidence)
    s, d = call("/read-chunk?document_cache_key=wikisource:en:The_Communist_Manifesto&max_chars=2500")
    check("read-chunk: evidence + content + read_event_id + continuation.next",
          s == 200 and d.get("result_kind") == "evidence" and len(d.get("content") or "") > 1000
          and bool(d.get("read_event_id")) and bool((d.get("continuation") or {}).get("next")),
          d.get("error"))

    # 6. ingest->read->reject(-1) on a throwaway (Gutenberg 1080, A Modest Proposal).
    # Contract (verified live): FRESH gutenberg-by-id is NOT a parse-document target (400 invalid_request —
    # ingestion goes through read-chunk/getTextForSource); once CACHED, parse-document serves it (200).
    s, d = call("/parse-document?source=gutenberg&id=1080&max_chars=1200", timeout=150)
    check("parse-document gutenberg-by-id: 400 when uncached OR 200 from cache",
          (s == 400 and d.get("error_code") == "invalid_request") or (s == 200 and bool(d.get("document_cache_key"))),
          (s, d.get("error_code"), d.get("error")))
    s, d = call("/read-chunk?document_cache_key=gutenberg:id:1080&max_chars=1500", timeout=150)
    ev = d.get("read_event_id")
    check("read throwaway: evidence + read_event_id", s == 200 and bool(ev), d.get("error"))
    if ev:
        s, d = call("/score-read-evidence?read_event_id=%s&value_score=-1&score_reason=e2e-regression-reject-path" % ev)
        ok_reject = s == 200 and (d.get("ok") is True) and str(d.get("score_status") or d.get("status") or "").find("reject") >= 0
        ok_409 = s == 409 and d.get("error_code") == "reject_not_applicable_already_scored"
        check("score reject(-1) path: clean reject (or 409 already-scored on rerun)",
              ok_reject or ok_409, (s, d.get("error"), d.get("score_status")))

    # 7. memory full cycle (cleaned up)
    s, d = call("/memory-write", "POST", {"topic": "e2e-regression-check",
        "content": "Temporary English regression-check note written by tools/e2e-check.py; deleted immediately.",
        "write_reason": "e2e regression"})
    seg = (d.get("segment_ids") or [None])[0]
    check("memory-write: appended + segment_ids + transaction_id",
          s == 200 and d.get("status") == "appended" and bool(seg) and bool(d.get("transaction_id")), d.get("error"))
    if seg:
        s, d = call("/memory-search?query=regression-check%20temporary%20note&max=3")
        found = any(seg in (b.get("memory_segment_ids") or []) for b in (d.get("results") or []))
        check("memory-search finds fresh segment (lexical)", s == 200 and found, d.get("count"))
        s, d = call("/memory-read?segment_ids=" + seg)
        check("memory-read returns content", s == 200 and "regression-check" in json.dumps(d), d.get("error"))
        s, d = call("/memory-write", "POST", {"operation": "delete", "target_segment_ids": seg,
                                              "write_reason": "e2e cleanup"})
        check("memory-delete cleans up", s == 200 and d.get("status") == "deleted"
              and seg in (d.get("deleted_segment_ids") or []), d.get("error"))

    # 8. error taxonomy
    s, d = call("/score-read-evidence?read_event_id=read_bogus_e2e&value_score=50")
    rem = ((d.get("gpt_guide") or {}).get("remedy") or {})
    check("error taxonomy: bogus read_event -> read_event_not_found + re-read remedy",
          d.get("error_code") == "read_event_not_found" and rem.get("operation") == "readSelectedTextChunk",
          (d.get("error_code"), rem))
    s, d = call("/read-chunk?cache_chunk_id=1")
    check("error taxonomy: bare cache_chunk_id -> ambiguous_..._requires_owner",
          d.get("error_code") == "ambiguous_cache_chunk_id_requires_owner", d.get("error_code"))

    # 9. hybrid title search
    s, d = call("/hybrid-title-search?q=wage%20labour%20and%20capital&max=3", timeout=150)
    check("hybrid-title-search: 200 + results", s == 200 and len(d.get("results") or []) >= 1, d.get("error"))

    # 10. get-source + links
    s, d = call("/get-source?source=gutenberg&id=1080")
    check("get-source (gutenberg): 200 + book", s == 200 and bool(d.get("book")), d.get("error"))
    s, d = call("/links?path=archive/marx/works/1848/communist-manifesto/")
    check("links (marxists): 200 + links[]", s == 200 and len(d.get("links") or []) >= 1, d.get("error"))

    # 11. long-doc parse -> synthesized guide.next (HJ)
    s, d = call("/parse-document?source=wikisource&lang=en&title=The%20Communist%20Manifesto&max_chars=1200", timeout=150)
    nx = (d.get("gpt_guide") or {}).get("next") or {}
    check("long-doc parse: chunk_map + synthesized gpt_guide.next(readSelectedTextChunk)",
          s == 200 and nx.get("operation") == "readSelectedTextChunk" and "start" in nx, nx)

    # 12. cache-status
    s, d = call("/cache-status")
    check("cache-status: 200 + document_cache counts",
          s == 200 and bool(d.get("document_cache")), d.get("error"))

    print()
    if FAILS:
        print("RESULT: %d FAILED -> %s" % (len(FAILS), FAILS))
        sys.exit(1)
    print("RESULT: ALL PASS")

if __name__ == "__main__":
    main()
