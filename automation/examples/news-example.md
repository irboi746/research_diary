+++
title = "Daily Brief — 2026-09-10"
date = 2026-09-10T06:00:00Z
type = "news"
tags = ["cs.CR", "fuzzing", "memory-safety", "arxiv"]
+++

*This file is a format reference, not published content. It lives outside `content/` on purpose.*

## Directed Greybox Fuzzing Without Instrumentation

- Replaces compile-time instrumentation with hardware trace, removing the rebuild step that blocks
  fuzzing closed-source targets.
- Reports 2.3× higher path coverage than AFL++ on the Magma benchmark at equal CPU budget.
- The trace decoder is the bottleneck above 8 cores, which caps the approach on larger fleets.

Lovelace, A., Hopper, G. "Directed Greybox Fuzzing Without Instrumentation." arXiv, 2026.
arXiv:2609.01234 — https://arxiv.org/abs/2609.01234

## A Practical Cross-Core Side Channel on Recent Server Parts

- Demonstrates a cache-occupancy channel that survives the vendor's 2025 partitioning mitigation.
- Extracts an AES key from a co-resident VM in about 40 minutes without privileged access.
- Vendor has assigned a CVE; no microcode fix at time of writing.

Turing, A. et al. "A Practical Cross-Core Side Channel." USENIX Security 2026.
https://www.usenix.org/conference/usenixsecurity26/presentation/turing

## Also published

- Hamilton, M. "Formal Verification of a Bootloader." arXiv:2609.01300 —
  https://arxiv.org/abs/2609.01300
- Clarke, E. "Notes on Symbolic Execution at Scale." DEF CON 34 —
  https://media.defcon.org/DEF%20CON%2034/
