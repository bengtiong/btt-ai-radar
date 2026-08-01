---
name: Retrieval-Augmented Generation (RAG)
quadrant: Techniques
ring: Adopt
status: unchanged
tags: [llm, rag, search]
date: 2026-08-01
---

Grounding LLM responses in retrieved documents rather than relying on
parametric knowledge alone. Now a default pattern for question-answering over
private or fast-changing data.

## Why this ring

Mature, well-understood, and broadly effective for reducing hallucination and
keeping answers current. Adopt as the baseline for knowledge-grounded apps.

## Notes

Invest in retrieval quality (chunking, hybrid search, reranking) — most RAG
failures are retrieval failures, not generation failures.
