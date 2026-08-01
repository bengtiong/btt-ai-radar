---
name: Small Model Fine-Tuning
quadrant: Techniques
ring: Trial
status: moved-in
tags: [fine-tuning, slm, cost]
date: 2026-08-01
---

Fine-tuning smaller open-weight models for narrow tasks instead of paying for
large frontier models on every call. Attractive for latency, cost, and data
control.

## Why this ring

Tooling (LoRA/QLoRA, hosted fine-tuning) has matured enough to trial on
well-bounded tasks, but data curation and evaluation effort is non-trivial.
