+++
title = "arXiv Brief — 2026-09-15"
date = 2026-09-15T06:00:00Z
type = "arxiv"
tags = ["cs.CR", "cs.AI", "llm-security", "vulnerability-discovery"]
summary = "Adversarial issue reports steer automated repair agents into insecure patches, and a benchmark asks whether agents can find the vulnerable file at all."
+++

*This file is a format reference, not published content. It lives outside `content/` on purpose.*

*Every identifier below is real and resolves. That is deliberate: the previous version of this file
used invented arXiv IDs and DOIs to illustrate the shape, and a deep dive copied one of them,
changed a digit, and published it. Do not treat any identifier here as a template to adapt — see
hard constraint 9 in AGENTS.md.*

## In brief

- Both items measure LLM agents on security tasks rather than proposing one, and both find the
  agents weaker than their headline task scores suggest.
- The shared failure is context, not capability: an agent can repair a bug correctly and still be
  talked into an insecure implementation of the repair.

## Adversarial Testing of Automated Program Repair Agents for Security Vulnerabilities

- Builds SWEADV, 750 adversarial issue descriptions derived from 150 SWE-bench Verified repair
  tasks — five per task, covering command execution, deserialization, path traversal, denial of
  service and weak hashing.
- The attack surface is the issue text, not the code: a benign-looking bug report is written to push
  the agent toward a patch that passes the functional tests and is insecure.
- Measures exposure rather than defence, so it establishes that the channel works without
  establishing what closes it.

*Abstract only — full text not retrieved.*

Trad, F., Chen, S., Pham, H. V., Uddin, G., Ray, B. "Adversarial Testing of Automated Program Repair
Agents for Security Vulnerabilities." arXiv, 2026.
arXiv:2609.15963 — https://arxiv.org/abs/2609.15963

## Vulnerability Localization Benchmark: Measuring Agentic Security Analysis at Repository Scale

- Introduces VLoc Bench: 500 real vulnerabilities drawn from 290 repositories, six package
  ecosystems and 147 CWE categories.
- Separates localization from detection by pairing each repository snapshot with the one taken
  immediately after the security fix. The agent gets only a CWE description and read-only terminal
  access, must name the affected files on the vulnerable snapshot, and must report the weakness
  absent on the patched one.
- The paired-snapshot design is what stops an agent scoring well by pattern-matching on the shape of
  a fix rather than reasoning about the code.

*Abstract only — full text not retrieved.*

Priyanshu, A., Vijay, S., Majd, K., et al. "Vulnerability Localization Benchmark: Measuring Agentic
Security Analysis at Repository Scale." arXiv, 2026.
arXiv:2609.15939 — https://arxiv.org/abs/2609.15939

## Also published

- Surapani, R. K., et al. "Authorization Architectures for Tool-Using AI Agents." arXiv:2609.15906 —
  https://arxiv.org/abs/2609.15906
