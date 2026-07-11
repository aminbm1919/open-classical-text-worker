# WIRE_CONTRACT.md — قراردادِ لاغرِ پاسخ روی wire

> **چه چیزی به GPT می‌رسد و چه چیزی نمی‌رسد.** مرجعِ لایهٔ wire-slim (نشانه‌های `GS` + `HG`/`HH`/`HI`).
> پاسبانِ خودکار: `python tools/wire-check.py` — endpointهای زنده را نمونه می‌گیرد و هر انحراف (DRIFT=کلیدِ ناشناختهٔ نو، LEAK=بازگشتِ کلیدِ گِیت‌شده) را با exit 1 گزارش می‌کند. **بعد از هر تغییری در شکلِ پاسخ‌ها یک‌بار اجرا شود.**

## مکانیزم (کجای کد)
هر پاسخِ JSON از دکوراتورِ `attachPhaseZeroObservability` می‌گذرد (بنرِ `[05]` در `worker.js`). وقتی فلگِ `result_diagnostics_dev_mode` **خاموش** است (پیش‌فرض)، سه denylist فقط روی **کپیِ wire** اعمال می‌شوند — sessionِ ذخیره‌شده کامل می‌ماند (page-next و re-context سالم):
1. `RESPONSE_DIAGNOSTIC_SECTIONS` — بخش‌های سطحِ بالای تلمتری.
2. `RESULT_DIAGNOSTIC_FIELDS` — فیلدهای هر آیتم در `results`/`results_by_source`/`matches`/`chunk_map` (+ بازگشتی در `alternate_representations`) + فیلدهای bundleِ حافظه.
3. `MEMORY_SIDECAR_DIAGNOSTIC_FIELDS` — فیلدهای سطحِ بالای sidecar + اسلیمِ بازگشتیِ `bundle`/`bundle_summary`.
به‌علاوهٔ حذفِ هدفمند: دوقلوی `bundles`=`results` و `doc`ِ legacy (memory_context)، `note`ِ discovery.
روشن‌کردنِ فلگ (`/set-diagnostics-mode?enabled=1`، ادمین) همه را برمی‌گرداند.

## هستهٔ همیشگی (هر پاسخ)
`ok` · `result_kind` · `error_code` (فقط خطا) · `gpt_guide` (`what`/`can_do`/`how` + `next` + `preferred`/`also_possible` + `remedy` در خطا + `page_next` وقتی `has_more`) · `evidence_required` · `warnings`.

## قراردادِ هر result_kind (فلگ خاموش — راستی‌آزمایی‌شدهٔ زنده ۲۰۲۶-۰۷-۱۰)

### discovery (`/unified-search`، ~۱۸ کلیدِ سطحِ بالا)
هسته + `gpt_memory_sidecar` (لاغر) + `mode`/`query`/`sources`/`realms`/`count`/`page_size`/`has_more`/`next_position`/`search_session_id`/`session_cache_limit`/`low_confidence_held_back` + `results`.
**هر آیتم (~۲۶ کلید):** هویت (`title`/`source`/`url`/`lang`/`item_type`) + locatorها (`document_cache_key`/`source_ref`/`result_ref`/`parent_document_key`/`evidence_unit_key`/`preferred_read_owner`) + سیگنالِ سرتیتر (`score`/`value_score`/`final_rank`/`dedup_group_key`/`text_state`) + اجرایی (`read_hint`/`search_inside_hint`/`operation_ids`/`available_operations`/`preferred_next_operation`/`next_step`/`read_start`/`read_limit`/`mini_extractive_map`) + `snippet` + بازنمایی (`alternate_representations`/`canonical_work_id`/`representation_type`) + سیگنالِ dedupِ اجرایی (`suspected_duplicate_of`/`duplicate_recheck_required_on_read` — عمداً روی wire، HK).

### candidate (`/search-text`، `/parse-document` سندِ بلند)
مثلِ discovery + `source_url`/`total_chars`/`document_cache_key`/`extractive_map`؛ parse: `document_delivery`/`chunk_map`/`content`/`instruction_to_gpt`/`cache_read_hint`/`cache_ready_for_search`/`index_status` (HC).

### evidence (`/read-chunk`، ~۲۴ کلید)
هسته + ناوبری (`start`/`end`/`next_start`/`previous_start`/`document_complete`/`more_available`/`total_chars`/`total_chars_returned`/`truncated`/`limit`) + `continuation` (چهار گامِ پُرشده) + امتیاز (`read_event_id`/`read_event`/`score_required`/`score_status`/`read_event_score_status`) + locator (`document_cache_key`/`source_ref`/`source`/`source_url`) + `content` + `index_status` + در ری‌دایرکتِ merge: `merged_from_cache_key`/`merge_note` (HK).

### memory_context (`/memory-search`، ~۱۴ کلید)
هسته + `use_scope`/`external_evidence`/`score_required`/`memory_model`/`entry_mode`/`count` + `results` (بدونِ دوقلوی `bundles`).
**هر bundle (~۲۱ کلید):** `snippet`/`topics`/`memory_segment_ids`/`matched_segment_ids`/`read_hint`/`search_inside_hint`/`available_operations`/`preferred_next_operation`/`memory_bundle_confidence`/`confidence_tier`/`memory_bundle_id`/`document_key`/locatorها.

### write_result (memory write/rewrite/delete)
فقط هسته + `status`/`document_key`/`topic`/`transaction_id`/`segment_ids` (یا `new_segment_ids`/`replaced_segments`/`deleted_segment_ids`) — plannerها (`vectorization`/`protection`/`vector_lifecycle`/…) فقط dev.

### score_result
هسته + `read_event_id`/`score_status`/`value_score`/`score_reason`/`owner_type`/`owner_key`/`owner_apply_status`/`evidence_unit_key`/`is_english`.

### diagnostic (`/cache-status`، `/`، خطاها)
cache-status: فقط `discovery_cache`/`document_cache`/`scored_cache`. خطاها: `error`+`error_code`+`gpt_guide.remedy`. **404:** `available_routes` فقط روت‌های روتین (HI).

## چه چیزهایی فقط در dev-mode برمی‌گردند (خانواده‌های اصلی)
تلمتریِ رتبه/fusion/dedup (`ranking_idf`/`fusion`/`session_dedup`/`branch_*`/…) · شاخه‌های سرچِ درون‌متن (`lexical_branch`/`vector_branch`/`dedup`/`quality_reports`) · درونیاتِ خواندن/کش (`cache_read_update`/`owner_score`/`served_from`/`resolved_from`/چهارتایی‌های clamp/شناسه‌های شارد/`score_scale`/`scoring_note`/…) · درونیاتِ parse (`parser`/`cache_write_status`/`parse_attempts`/`cache_handoff`/…) · درونیاتِ score (`updated_owner`/`duplicate_recheck`/سیگنال‌های روتینگِ برداری) · موتورِ حافظه (`memory_vector_branch`/`memory_hygiene`/`bundling`/شمارنده‌ها/`confidence_signals`/`segment_summaries`/plannerهای write) · تلمتریِ کشف (`attempts`/`errors` با previewِ خام/`exa_cost_dollars`/…) · دامپ‌های cache-status (`storage_policy`/`deprecated_aliases`/تکرارها) · فهرستِ کاملِ روت‌ها در 404.

## قواعدِ نگه‌داری
1. فیلدِ تلمتریِ نو؟ همان‌جا واردِ denylistِ مناسب کن (الگو: denylist، نه allowlist — فیلدِ فراموش‌شده دیده می‌شود، نه حذفِ بی‌صدا).
2. فیلدِ عملیاتیِ نو برای GPT؟ به allowlistِ `tools/wire-check.py` و بخشِ مربوطهٔ همین سند اضافه کن.
3. بعد از هر دیپلویِ مؤثر بر پاسخ: `python tools/wire-check.py`.
