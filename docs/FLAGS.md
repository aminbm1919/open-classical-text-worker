# FLAGS.md — رجیستریِ فلگ‌ها و پیکربندیِ `storage_policy`

> منبعِ حقیقتِ فلگ‌ها. ساخته‌شده ۲۰۲۶-۰۷-۱۰ (نشانهٔ `HM`): ستونِ «پیش‌فرضِ کد» از اسکنِ فراخوان‌های `isStoragePolicyEnabled`/`getStoragePolicy*` در `worker.js`، ستونِ «زنده» از کوئریِ مستقیمِ D1 (جدولِ `storage_policy`). تغییرِ زنده: `/set-storage-policy?key=...&value=...` (ادمین). **این فایل snapshot است؛ پس از هر تغییرِ ماندگارِ فلگ، سطرش را به‌روز کن.** مقدارِ خالی/— یعنی تعریف‌نشده در آن ستون.


## دیباگ/قراردادِ wire

| کلید | پیش‌فرضِ کد | زنده | شرح |
|---|---|---|---|
| `result_diagnostics_dev_mode` | false | false | فلگِ دیباگِ سراسری (GS/HG..HI): روشن=کلِ تلمتری روی wire برمی‌گردد؛ خاموش=قراردادِ لاغر |

## خطِ لولهٔ ورود و R2 (R1..R5، HA..HD)

| کلید | پیش‌فرضِ کد | زنده | شرح |
|---|---|---|---|
| `deferred_ingest_enabled` | false | 1 | Incremental Ingest (HB..HD): سندِ بزرگ اول body-only در R2، ایندکس با درینِ کرون |
| `deferred_ingest_threshold_chars` | 250000 | 250000 | آستانهٔ معوّق‌سازیِ سندِ بزرگ (کاراکتر) |
| `ingest_drain_chars_per_tick` | 1500000 | 1500000 | بودجهٔ کاراکترِ هر تیکِ درینِ ایندکس |
| `ingest_drain_max_docs_per_tick` | 5 | 5 | سقفِ سند در هر تیکِ درین |
| `pathological_fetch_fuse_bytes` | 52428800 | 52428800 | فیوزِ بایتیِ واکشیِ بیمارگونه (HD) — تنها سقفِ سختِ بایت |
| `enable_r2_text_write` | false | 1 | نوشتنِ بدنهٔ متن در R2 (R1) |
| `enable_r2_text_read` | false | 1 | خواندنِ R2-first (R2) |
| `search_body_from_r2` | false | 1 | snippet/سرچ از بدنهٔ R2 (R3) |
| `embed_body_from_r2` | false | 1 | امبد از بدنهٔ R2 (R4) |
| `write_chunk_text_null` | false | 1 | S9/R5: درجِ چانکِ بی‌متن در D1 (contentless) |
| `enable_cache_fts_write` | false | 1 | نوشتنِ ایندکسِ FTSِ چانک‌های کش |

## dedup/SimHash (FN..FT، GX/GY)

| کلید | پیش‌فرضِ کد | زنده | شرح |
|---|---|---|---|
| `doc_fingerprint_compute` | false | 1 | روتِ محاسبهٔ SimHash (P0) |
| `doc_neardup_skip_embed` | false | 1 | P1: ردِ امبدِ سندِ تکراری (برگشت‌پذیر) |
| `doc_neardup_simhash_fuzzy` | false | 1 | لایهٔ فازیِ SimHash (تا doc_neardup_hamming_max) |
| `doc_neardup_hamming_max` | 3 | — | آستانهٔ فاصلهٔ همینگِ فازی (3/64) |
| `doc_neardup_len_tolerance_pct` | 2 | — | حداکثر اختلافِ طول برای mergeِ فازی (GY، درصد) |
| `doc_neardup_merge` | false | 1 | P3: ادغامِ مخربِ near-dup با تأیید |
| `doc_auto_merge` | false | 1 | ادغامِ خودکارِ اسنادِ هم‌هش در sweep/prepare (FR/FS) |
| `doc_merge_keep_backup` | false | — | بکاپِ R2 پیش از حذفِ merge (خاموش به تصمیمِ کاربر، FR) |

## بردارِ پیکره (Neon، AG..AR)

| کلید | پیش‌فرضِ کد | زنده | شرح |
|---|---|---|---|
| `corpus_vector_backend` | vectorize | neon | بک‌اندِ بردارِ پیکره: neon (زنده) / vectorize (CF، بازنشسته) |
| `neon_corpus_write` | false | 1 | نوشتنِ بردارِ پیکره در Neon (AI) |
| `neon_corpus_drain` | false | 1 | درینِ کرونِ صفِ امبدِ پیکره (AJ) |
| `neon_corpus_auto_enqueue` | false | 1 | صف‌کردنِ خودکارِ سندِ scored برای امبد (AM) |
| `enable_neon_corpus_delete` | false | 1 | حذفِ تضمینیِ بردارِ Neon (tombstone، AN) |
| `enable_corpus_vector_fusion` | false | 1 | RRFِ productionِ بردار+لغوی در unifiedSearch (AL) |
| `enable_unscored_document_cache_vectorization` | false | — | امبدِ سندِ امتیازنخورده (خاموش=فقط scored) |
| `neon_project_capacity_bytes` | 524288000 | — | ظرفیتِ هر پروژهٔ Neon (500MB) |
| `neon_capacity_evict_fraction` | 0.9 | — |  |
| `neon_project_primary_fill_target` | 250000 | — |  |
| `enable_scored_cache_neon_eviction` | true | — | evictionِ ظرفیتیِ scored روی Neon (GC) |
| `scored_cache_eviction_docs_per_run` | 4 | — |  |
| `query_router_cf_model` | @cf/meta/llama-3.2-3b-instruct | — | مدلِ CF llama روترِ موضوعِ کوئری (AK) |
| `embedding_backend` | hf | hf | بک‌اندِ امبدِ نوشتن (hf=NVIDIA bge-m3) |

## بردار/حافظهٔ GPT (Qdrant)

| کلید | پیش‌فرضِ کد | زنده | شرح |
|---|---|---|---|
| `memory_vector_backend` | vectorize | qdrant | بک‌اندِ بردارِ حافظه: qdrant (زنده) / vectorize |
| `enable_qdrant_memory` | false | true | شاخهٔ برداریِ حافظه روی Qdrant |
| `qdrant_memory_write` | false | true | نوشتنِ بردارِ حافظه در Qdrant |
| `gpt_memory_open_write` | true | true | نوشتنِ حافظه بدونِ توکن (DI، two-tier) |
| `gpt_memory_defer_new_segment_vectors` | false | 1 | HF: تأخیرِ امبدِ سگمنتِ نو (جذبِ churn) |
| `gpt_memory_new_vector_delay_minutes` | 720 | 720 | تأخیرِ امبدِ سگمنتِ نو (دقیقه؛ 720=12h) |
| `gpt_memory_queued_embedding_delay_minutes` | 10 | 10 |  |
| `gpt_memory_vector_soft_cap` | — | 4500 | سقفِ نرمِ بردارِ حافظه (GA/GB از بودجهٔ Qdrant) |
| `gpt_memory_vector_hard_cap` | — | 4800 | سقفِ سختِ بردارِ حافظه |
| `qdrant_vector_capacity_bytes` | 805306368 | 805306368 | بودجهٔ Qdrant |
| `qdrant_bytes_per_memory_vector` | 6144 | 6144 |  |
| `gpt_memory_vector_min_score_default` | 0.35 | 0.35 |  |
| `gpt_memory_bundle_confidence_rel_ratio` | 0.8 | 0.8 |  |
| `gpt_memory_bundle_min_confidence` | 0 | 0 |  |

## کشف/منابع

| کلید | پیش‌فرضِ کد | زنده | شرح |
|---|---|---|---|
| `enable_exa_marxists_discovery` | false | true | Exa کشفِ اصلیِ marxists (CY/CZ) |
| `marxists_admit_to_document_cache` | — | true | پذیرشِ صفحهٔ marxists به document_cache (BU) |
| `marxists_admit_default_score_50` | true | — | پذیرشِ صفحهٔ marxists با امتیازِ 50 (BV) |
| `marxists_internal_search_unified` | — | true | یکپارچگیِ hybrid-deep با document_cache (BW) |
| `arxiv_relevance_sort` | true | — | FL: مرتب‌سازیِ ربطِ arXiv |
| `arxiv_zero_result_fallback` | true | — | FL: فالبکِ صفر-نتیجه |
| `arxiv_html_read` | true | — | FM: خواندنِ HTMLِ بومیِ arXiv |
| `route_via_unified` | true | 1 | جذبِ روت‌های legacy (article/meta/search-source) به هندلرِ unified |
| `unified_absorb_enabled` | true | — | جذبِ کلیِ روت‌ها به unified (DF) |

## رتبه‌بندی/dedupِ نشست

| کلید | پیش‌فرضِ کد | زنده | شرح |
|---|---|---|---|
| `ranking_idf_v2` | true | — | وزن‌دهیِ IDF در رتبه (EH/EI/EJ) |
| `ranking_dense_weight` | 1.25 | 1.25 | وزنِ شاخهٔ برداری در RRF (FK؛ 1.25 نگه‌داشتنی) |
| `ranking_phrase_tier` | true | 1 | سیگنالِ tierِ عبارت-در-عنوان (FW) |
| `ranking_topicality_tier` | true | — | مرتب‌سازیِ نهاییِ tierمحور (EL) |
| `rrf_decorrelate_internal` | true | — | ادغامِ خانواده‌های همبستهٔ کش در یک سیگنالِ RRF (EK) |
| `cross_source_work_dedup` | true | — | dedupِ سطحِ اثرِ بین-منبعی (EV) |
| `work_level_dedup` | true | — | dedupِ سطحِ اثر |
| `work_hierarchy_metadata` | true | — | متادیتای سلسله‌مراتب (canonical_work_id) |
| `drop_no_topical_from_session` | true | — | حذفِ نتایجِ بی‌ربط از session |
| `page_hide_tier0` | true | — | صفحه‌بندی: پنهان‌کردنِ tier0 |
| `page_limit_low_coverage_tier1` | true | — | صفحه‌بندی: محدودسازیِ tier1ِ کم‌پوشش |
| `lexical_persian_normalize` | false | true | نرمال‌سازیِ فارسیِ توکنایزر |
| `lexical_prefix_match` | false | true | تطبیقِ پیشوندیِ لغوی |
| `lexical_title_boost` | false | true | تقویتِ عنوانِ لغوی |
| `fts_title_column` | false | true | ستونِ عنوان در FTS |

## کش/امتیاز/ترفیع/ظرفیت

| کلید | پیش‌فرضِ کد | زنده | شرح |
|---|---|---|---|
| `cache_search_mode` | fts | fts | حالتِ سرچِ کش: fts (فاز 2) یا like |
| `enable_document_cache_read` | true | true |  |
| `enable_document_cache_write` | true | true |  |
| `enable_cache_prune` | true | true | هرسِ روزانهٔ کش (کرون) |
| `enable_cache_promotion` | false | true | ترفیعِ خودکارِ سندِ امتیازبالا |
| `promotion_threshold_default` | 70 | 70 | آستانهٔ ترفیع به scored (70) |
| `promotion_threshold_marxists` | 60 | 60 | آستانهٔ ترفیعِ marxists (60) |
| `promotion_threshold_very_high` | 85 | 85 | آستانهٔ خیلی‌بالا (85) |
| `cache_min_retention_read_days` | 30 | 30 |  |
| `cache_ttl_discovery_days` | 3 | 3 |  |
| `max_prune_documents_per_run` | 50 | 50 |  |
| `enable_search_session_cache_read` | true | true |  |
| `enable_search_session_cache_write` | true | true |  |
| `max_cached_results_per_search` | 100 | 100 |  |
| `max_payload_json_chars` | 3000 | 3000 | سقفِ JSONِ هر نتیجهٔ session |
| `max_snippet_preview_chars` | 1200 | 1200 |  |
| `max_abstract_preview_chars` | 1200 | 1200 |  |
| `shard_full_char_cap` | 40000000 | — |  |
| `d1_capacity_bytes` | 5368709120 | — | ظرفیتِ فرضیِ D1 برای eviction |
| `r2_capacity_bytes` | 10737418240 | — | ظرفیتِ فرضیِ R2 |
| `enable_r2_d1_capacity_eviction` | true | — | evictionِ ظرفیتیِ R2/D1 |
| `r2_d1_capacity_evict_fraction` | 0.9 | — |  |
| `r2_d1_eviction_docs_per_run` | 4 | — |  |

## سایرِ کلیدها (باجت‌های ریزِ حافظه، TTLها، سقف‌های متفرقه)

| کلید | پیش‌فرضِ کد | زنده | شرح |
|---|---|---|---|
| `disable_gpt_memory_capacity_eviction` | false | false |  |
| `disable_gpt_memory_immediate_vector_delete` | false | false |  |
| `disable_gpt_memory_immediate_vectorization` | false | false |  |
| `disable_gpt_memory_vector_microtask` | false | false |  |
| `disable_gpt_memory_write_window_compaction` | false | false |  |
| `enable_gpt_memory_capacity_eviction` | true | true |  |
| `enable_gpt_memory_immediate_vector_delete` | true | true |  |
| `enable_gpt_memory_immediate_vectorization` | true | true |  |
| `enable_gpt_memory_vector_microtask` | true | true |  |
| `enable_gpt_memory_write_window_compaction` | true | true |  |
| `gpt_memory_capacity_evict_fraction` | 0.9 | 0.9 |  |
| `gpt_memory_capacity_hard_fraction` | 0.97 | 0.97 |  |
| `gpt_memory_compaction_max_combined_chars` | 1800 | 1800 |  |
| `gpt_memory_compaction_max_embedding_calls` | 1 | 1 |  |
| `gpt_memory_compaction_max_groups_per_invocation` | 1 | 1 |  |
| `gpt_memory_compaction_max_immediate_deletes` | 1 | 1 |  |
| `gpt_memory_compaction_max_segment_chars` | 700 | 700 |  |
| `gpt_memory_compaction_max_source_segments` | 5 | 5 |  |
| `gpt_memory_compaction_max_upserts` | 1 | 1 |  |
| `gpt_memory_compaction_min_source_segments` | 2 | 2 |  |
| `gpt_memory_compaction_only_admin_written` | true | true |  |
| `gpt_memory_compaction_only_unprotected` | true | true |  |
| `gpt_memory_compaction_same_document_key_required` | true | true |  |
| `gpt_memory_compaction_scan_last_admin_segments` | 10 | 10 |  |
| `gpt_memory_compaction_trigger_every_admin_segments` | 5 | 5 |  |
| `gpt_memory_eviction_active_unprotected_min_age_hours` | 24 | 24 |  |
| `gpt_memory_eviction_allow_active_unprotected` | true | true |  |
| `gpt_memory_eviction_max_deletes_per_invocation` | 4 | 4 |  |
| `gpt_memory_eviction_protected_exempt` | true | true |  |
| `gpt_memory_eviction_submit_immediate_delete` | true | true |  |
| `gpt_memory_eviction_terminal_first` | true | true |  |
| `gpt_memory_immediate_max_embedding_calls` | 1 | 1 |  |
| `gpt_memory_immediate_max_prepare_segments` | 20 | 20 |  |
| `gpt_memory_immediate_max_upserts` | 1 | 1 |  |
| `gpt_memory_immediate_max_vector_deletes` | 1 | 1 |  |
| `gpt_memory_microtask_lock_ttl_seconds` | 180 | 180 |  |
| `gpt_memory_microtask_max_embedding_calls` | 1 | 1 |  |
| `gpt_memory_microtask_max_upserts` | 1 | 1 |  |
| `gpt_memory_microtask_min_interval_seconds` | 540 | 540 |  |

## کلیدهای زنده در D1 که در اسکنِ literalِ کد پیدا نشدند (64 کلید)

یا با کلیدِ پویا/داینامیک خوانده می‌شوند یا **legacy/بازنشسته‌اند** — به‌ویژه خانوادهٔ `vectorize_*`/`vector_*`ِ دورهٔ CF و `enable_vectorize*` که پس از مهاجرت به Neon/Qdrant مانده‌اند. نامزدِ پاک‌سازی با قانونِ «نامزد⟵شاهد» (اول تأییدِ نخواندنِ پویا):

`auto_warm_after_full`, `auto_warm_before_full`, `cache_ttl_arxiv_metadata_days`, `cache_ttl_arxiv_obtained_unread_days`, `cache_ttl_core_metadata_days`, `cache_ttl_core_obtained_unread_days`, `cache_ttl_gutenberg_metadata_days`, `cache_ttl_gutenberg_obtained_unread_days`, `cache_ttl_jstor_metadata_days`, `cache_ttl_jstor_obtained_unread_days`, `cache_ttl_marxists_obtained_unread_days`, `cache_ttl_wikisource_metadata_days`, `cache_ttl_wikisource_obtained_unread_days`, `enable_identity_column_writes`, `enable_mandatory_scoring`, `enable_read_events`, `enable_score_eviction`, `enable_score_route`, `enable_vectorize`, `enable_vectorize_actual_upsert`, `enable_vectorize_auto_mark`, `enable_vectorize_candidates_readonly`, `enable_vectorize_create_jobs`, `enable_vectorize_delete_lifecycle`, `enable_vectorize_preflight`, `enable_vectorize_preflight_schema`, `enable_vectorize_prepare_one`, `enable_vectorize_query_probe`, `enable_vectorize_run_jobs`, `enable_vectorize_transition_owner`, `gpt_memory_delete_retry_max_minutes`, `gpt_memory_delete_retry_min_minutes`, `gpt_memory_embedding_max_chars`, `gpt_memory_microtask_max_delete_batches`, `gpt_memory_retry_max_minutes`, `gpt_memory_retry_min_minutes`, `gpt_memory_vector_hard_cap`, `gpt_memory_vector_soft_cap`, `marxists_admit_to_document_cache`, `marxists_internal_search_unified`, `max_auto_warm_chunks_per_search`, `max_hash_backfill_chunks_per_run`, `max_prune_chunks_per_run`, `max_session_page_size`, `max_source_family_backfill_rows_per_run`, `vector_bge_large_embedding_dim`, `vector_bge_large_embedding_model`, `vector_bge_large_index_name`, `vector_m3_embedding_dim`, `vector_m3_embedding_model`, `vector_m3_index_name`, `vector_segment_overlap_chars`, `vector_segment_size_chars`, `vector_segmentation_policy_version`, `vectorize_bge_large_embedding_dim`, `vectorize_bge_large_embedding_model`, `vectorize_bge_large_index_name`, `vectorize_embedding_dim`, `vectorize_embedding_model`, `vectorize_m3_embedding_dim`, `vectorize_m3_embedding_model`, `vectorize_m3_index_name`, `vectorize_max_candidates_per_run`, `vectorize_min_chunk_chars`
