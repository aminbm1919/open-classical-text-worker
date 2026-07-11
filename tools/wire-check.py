# -*- coding: utf-8 -*-
"""
wire-check — پاسبانِ قراردادِ لاغرِ wire (مرجع: WIRE_CONTRACT.md، نشانهٔ HO).

چه می‌کند: چند endpointِ زندهٔ فقط‌خواندنی/کم‌اثر را صدا می‌زند و کلیدهای سطحِ بالای پاسخ (و کلیدهای
آیتمِ اولِ results) را با allowlistِ قرارداد مقایسه می‌کند.
- کلیدِ ناشناخته => DRIFT (تلمتریِ نو که از denylist فرار کرده یا فیلدِ عمدیِ نو که باید واردِ قرارداد شود)
- کلیدِ گِیت‌شده که برگشته => LEAK (فلگ روشن مانده یا denylist شکسته)
پیش‌فرض فرض می‌کند فلگِ result_diagnostics_dev_mode خاموش است؛ اگر روشن باشد همه‌چیز LEAK دیده می‌شود.

اجرا:  python tools/wire-check.py
خروجیِ موفق: هر خط PASS؛ کدِ خروج 0. هر DRIFT/LEAK => کدِ خروج 1.
توجه: read-chunk یک read_event واقعی می‌سازد و fetch_count را بالا می‌برد (رفتارِ عادیِ سیستم).
"""
import os, json, sys, urllib.request, urllib.parse

BASE = "https://chunking.YOUR-SUBDOMAIN.workers.dev"

# کلیدهای همیشه-مجازِ سراسری (دکوراتورِ phase-zero)
GLOBAL_OK = {
    "ok", "result_kind", "error_code", "gpt_guide", "evidence_required", "evidence_scope",
    "warnings", "warning", "note", "mode", "query", "count", "error",
}

CHECKS = [
    {
        "name": "unified-search (discovery)",
        "url": "/unified-search?query=communist+manifesto&max=3",
        "top_ok": {
            "gpt_memory_sidecar", "sources", "realms", "session_cache_limit", "search_session_id",
            "next_position", "has_more", "low_confidence_held_back", "page_size", "results",
        },
        "item_ok": {
            "result_kind", "evidence_required", "origin_realm", "source", "title", "id", "path", "url",
            "lang", "item_type", "document_cache_key", "read_start", "read_limit", "score", "text_state",
            "value_score", "has_full_text", "pdf_url", "next_step", "source_ref", "result_ref",
            "available_operations", "operation_ids", "preferred_next_operation", "read_hint",
            "search_inside_hint", "mini_extractive_map", "parent_document_key", "evidence_unit_key",
            "dedup_group_key", "preferred_read_owner", "final_rank", "alternate_representations",
            "merged_representation_count", "representation_type", "canonical_work_id", "snippet",
            "abstract", "authors", "year", "doi", "suspected_duplicate_of",
            "duplicate_recheck_required_on_read", "merged_from_cache_key", "merge_note",
        },
    },
    {
        "name": "search-text (search-inside, candidate)",
        "url": "/search-text?document_cache_key=wikisource:en:The_Communist_Manifesto&q=communism&max=3",
        "top_ok": {
            "search_session_id", "next_position", "has_more", "page_size", "results", "next_step",
            "source", "source_url", "source_ref", "total_chars", "document_cache_key", "extractive_map",
        },
        "item_ok": None,  # همان item_okِ unified استفاده می‌شود (پایین merge می‌کنیم)
    },
    {
        "name": "read-chunk (evidence)",
        "url": "/read-chunk?document_cache_key=wikisource:en:The_Communist_Manifesto&max_chars=1500",
        "top_ok": {
            "document_complete", "more_available", "start", "end", "next_start", "previous_start",
            "total_chars_returned", "truncated", "source", "source_url", "source_ref", "limit",
            "total_chars", "document_cache_key", "read_event_score_status", "continuation",
            "read_event_id", "score_required", "score_status", "read_event", "content", "index_status",
            "merged_from_cache_key", "merge_note", "document_delivery", "search_needed",
        },
        "item_ok": set(),
    },
    {
        "name": "memory-search (memory_context)",
        "url": "/memory-search?query=ranking&max=2",
        "top_ok": {"gpt_memory_sidecar", "external_evidence", "score_required", "use_scope",
                   "memory_model", "results", "entry_mode"},
        "item_ok": {
            "result_kind", "evidence_required", "origin_realm", "external_evidence", "score_required",
            "use_scope", "memory_document_key", "document_key", "memory_bundle_id", "source_ref",
            "result_ref", "matched_segment_ids", "memory_segment_ids", "topics", "snippet", "read_hint",
            "search_inside_hint", "available_operations", "preferred_next_operation",
            "memory_bundle_confidence", "confidence_tier",
        },
    },
    {
        "name": "cache-status (diagnostic)",
        "url": "/cache-status",
        "top_ok": {"discovery_cache", "document_cache", "scored_cache"},
        "item_ok": set(),
    },
    {
        "name": "404 (unknown route)",
        "url": "/definitely-not-a-route",
        "top_ok": {"available_routes"},
        "item_ok": set(),
        "expect_admin_routes_hidden": True,
    },
]

# کلیدهایی که با فلگِ خاموش هرگز نباید دیده شوند (نمونهٔ نگهبان از هر خانوادهٔ گِیت‌شده)
MUST_BE_GONE = {
    "diagnostics", "source_reports", "fusion", "ranking_idf", "session_dedup", "branch_reports",
    "lexical_branch", "vector_branch", "dedup", "quality_reports", "cache_read_update", "owner_score",
    "served_from", "resolved_from", "score_scale", "scoring_note", "shard_name", "parse_attempts",
    "updated_owner", "duplicate_recheck", "memory_vector_branch", "memory_hygiene", "bundling",
    "bundles", "vectorization", "write_window_compaction", "vector_lifecycle", "protection",
    "token_policy", "attempts", "errors", "storage_policy", "deprecated_aliases", "search_sessions",
    "shard_cache", "document_cache_shards", "exa_cost_dollars", "selected_admissions", "auto_warm",
}

def fetch(url, tries=3):
    last = None
    for _ in range(tries):
        req = urllib.request.Request(BASE + url, headers={"User-Agent": "wire-check", "X-Routine-Token": os.environ.get("ROUTINE_TOKEN", "")})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # پاسخ‌های 4xx هم بدنهٔ JSONِ قراردادی دارند (error_code/remedy) — همان را چک می‌کنیم
            return json.loads(e.read().decode("utf-8"))
        except Exception as e:  # قطعیِ گذرای شبکه (IncompleteRead/timeout) — دوباره
            last = e
    raise last

def main():
    unified_item_ok = CHECKS[0]["item_ok"]
    failures = 0
    for c in CHECKS:
        try:
            d = fetch(c["url"])
        except Exception as e:
            print("ERROR  %-38s fetch failed: %s" % (c["name"], e))
            failures += 1
            continue
        top = set(d.keys())
        allowed = GLOBAL_OK | c["top_ok"]
        drift = sorted(k for k in top - allowed if k not in MUST_BE_GONE)
        leak = sorted(top & MUST_BE_GONE)
        item_allowed = c["item_ok"] if c["item_ok"] else unified_item_ok
        idrift, ileak = [], []
        res = d.get("results")
        if isinstance(res, list) and res and isinstance(res[0], dict):
            ikeys = set(res[0].keys())
            idrift = sorted(k for k in ikeys - item_allowed if k not in MUST_BE_GONE)
            ileak = sorted(ikeys & MUST_BE_GONE)
        extra = ""
        if c.get("expect_admin_routes_hidden"):
            routes = d.get("available_routes") or []
            adminy = [r for r in routes if "setup" in r or "vectorize" in r or r in ("/reindex", "/index-url", "/index-status", "/memory-bootstrap")]
            if adminy:
                extra = " ADMIN-ROUTES-EXPOSED:%s" % adminy
        if drift or leak or idrift or ileak or extra:
            failures += 1
            print("FAIL   %-38s%s" % (c["name"], extra))
            if leak:   print("        LEAK  top:   %s" % leak)
            if drift:  print("        DRIFT top:   %s" % drift)
            if ileak:  print("        LEAK  item:  %s" % ileak)
            if idrift: print("        DRIFT item:  %s" % idrift)
        else:
            print("PASS   %-38s top=%d" % (c["name"], len(top)))
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
