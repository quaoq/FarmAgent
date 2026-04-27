# RAG Implementation Blueprint (When Documents Are Available)

This is the implementation plan for adding **document-grounded RAG** to FarmAgent once you have a real document corpus.

Current repo can run without document RAG; this blueprint shows how to add it professionally.

## 1) When to enable RAG

Enable RAG when farm-relevant knowledge is too large/volatile for static prompts:
- SOP manuals,
- agronomy and treatment protocols,
- equipment/maintenance manuals,
- policy/compliance docs,
- historical incident logs.

If no such corpus exists, do not force RAG into experiments.

## 2) Recommended architecture (hybrid + auditable)

1. **Document ingestion**
   - Parse PDF/HTML/Markdown.
   - Structure-aware chunking (section-aware, table-safe).
   - Metadata tagging: `doc_id`, section, source, date/version, topic, locale.

2. **Elasticsearch hybrid retrieval**
   - BM25 lexical retrieval.
   - Dense vector retrieval with `knn`.
   - Fuse with **RRF** for robust ranking and less manual weighting.
   - Optional third branch: sparse semantic retriever.

3. **Reranking stage**
   - Re-rank top 30–100 with cross-encoder or late interaction.
   - Keep top 4–8 evidence passages.

4. **Grounded generation**
   - Inject only top evidence into prompt context.
   - Require citation-style source mentions in traces.
   - Add abstain behavior when evidence is weak/contradictory.

5. **Measurement and traceability**
   - Retrieval: Recall@k, MRR/nDCG.
   - Answer: correctness + faithfulness/groundedness.
   - Infra: index version, retrieval latency, citation coverage.

## 3) How to integrate with this FarmAgent codebase

### Existing hooks to use
- Family strategy layer: `rsare/research_suite/families.py`
- Strategy context injection: `rsare/research_suite/strategies.py`
- Per-run execution + metadata: `rsare/research_suite/executor.py`
- Suite matrix control: `rsare/research_suite/suite_runner.py`

### Suggested implementation path
1. Add `documents_rag` settings to `ResearchAgentProfileConfig`.
2. Add `rsare/research_suite/document_rag.py` (ES client + retrieval pipeline).
3. In `executor.py`, before `agent.run(...)`, retrieve top evidence and append to strategy context.
4. Emit RAG telemetry fields in `telemetry`:
   - `rag_queries`, `rag_hits`, `rag_latency_ms`, `rag_index_version`, `rag_citation_count`.
5. Add experiment packs:
   - `*_rag_off`
   - `*_rag_on_hybrid`

## 4) SOTA-practical enhancements

- Multi-query rewrite (2–4 variants) + RRF over query branches.
- Optional HyDE for zero-shot dense retrieval.
- Metadata-aware filtering (machine type, crop phase, date validity).
- Contradiction check between retrieved passages before action-heavy tool calls.

## 5) Paper-safe experimental framing

Use ablations, not absolute claims:
- RAG OFF vs RAG ON-hybrid,
- with/without reranker,
- with/without A2A typed experts.

Keep:
- fixed seeds,
- fixed index snapshot/version hash,
- same scenario matrix across conditions.

## 6) Reproducibility rules

- Version the index build recipe (chunking + embedding model + source hashes).
- Log every retrieval call (query, filters, top docs, scores).
- Freeze model IDs per run.
- Export trace artifacts with source evidence.

## 7) Phased rollout

Phase 1:
- Ingestion + ES hybrid retrieval + prompt injection.

Phase 2:
- Reranker + telemetry + runbook commands.

Phase 3:
- Query expansion/HyDE + deeper ablations + grounding analysis.

## 8) Primary references

- RAG (Lewis et al.): https://arxiv.org/abs/2005.11401  
- FLARE / Active Retrieval-Augmented Generation: https://arxiv.org/abs/2305.06983  
- Self-RAG: https://arxiv.org/abs/2310.11511  
- HyDE (Precise Zero-Shot Dense Retrieval): https://arxiv.org/abs/2212.10496  
- ColBERTv2: https://arxiv.org/abs/2112.01488  
- Elasticsearch kNN docs: https://www.elastic.co/docs/solutions/search/vector/knn  
- Elasticsearch RRF docs: https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
