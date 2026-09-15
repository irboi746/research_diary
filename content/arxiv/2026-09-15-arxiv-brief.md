+++
title = "arXiv Brief — 2026-09-15"
date = 2026-09-15T06:00:00Z
type = "arxiv"
tags = ["cs.CR", "cs.AI", "cs.SE", "llm-security", "fuzzing", "supply-chain", "vulnerability-discovery"]
summary = "New perspectives on LLM agent security: a census of the Model Context Protocol ecosystem, attacks via gated memories and contextual bias, and LLM-guided smart contract fuzzing."
+++

## In brief

- LLM agents face new attack surfaces: the Model Context Protocol (MCP) registry is plagued by silent drift and unauthenticated exposure, while gated memory parameters can harbor backdoors without altering the model's backbone.
- Automated code review tools are shown to be susceptible to contextual bias, where attackers can manipulate PR metadata to bypass vulnerability detection.
- Fuzzing research leverages LLMs to guide state exploration in smart contracts, generating Vulnerable Function Call Sequences to overcome combinatorial redundancy.

## Same Name, Different Server: A Security Census of Silent Drift in the Model Context Protocol Ecosystem

- Scans the public Model Context Protocol (MCP) registry, analyzing 14,353 servers to identify security risks in the ecosystem connecting LLM applications to external tools.
- Finds that 51.1% of multi-version servers change their advertised capabilities between versions, with 40.6% doing so silently and 4.2% redirecting endpoints while keeping their registry identity.
- Demonstrates that unauthenticated network exposure is the dominant threat (9.57%), and that silent drift correlates strongly with high-severity findings (odds ratio of 2.96).

*Abstract only — full text not retrieved.*

"Same Name, Different Server: A Security Census of Silent Drift in the Model Context Protocol Ecosystem." arXiv, 2026.
arXiv:2609.14119 — https://arxiv.org/abs/2609.14119

## Measuring and Exploiting Contextual Bias in LLM-Assisted Security Code Review

- Investigates the framing effect in LLM-based Automated Code Review (ACR) systems, evaluating whether adversaries can exploit PR metadata to bypass security checks.
- Tests 33 CVEs across 20 real-world projects against Claude Code and CodeRabbit, showing that template-based direct biasing attempts are ineffective and raise suspicion.
- Introduces an iterative, LLM-assisted refinement attack that successfully bypasses detection in 97% of cases by exploiting the asymmetry between offline attacker refinement and one-shot defender checks.

*Abstract only — full text not retrieved.*

"Measuring and Exploiting Contextual Bias in LLM-Assisted Security Code Review." arXiv, 2026.
arXiv:2603.18740 — https://arxiv.org/abs/2603.18740

## EchoFuzz: Empowering Smart Contract Fuzzing with Large Language Models

- Proposes EchoFuzz, an LLM-guided fuzzing framework that uses chain-of-thought analysis to generate Vulnerable Function Call Sequences (VFCS) for smart contracts.
- Uses LLMs with real-time feedback to adaptively steer the fuzzer towards uncovered branches, addressing the challenge of combinatorial redundancy in state transitions.
- Reports a 29% increase in branch coverage and 62% more vulnerabilities detected compared to state-of-the-art methods, finding 37 previously unknown bugs in real contracts.

*Abstract only — full text not retrieved.*

"EchoFuzz: Empowering Smart Contract Fuzzing with Large Language Models." arXiv, 2026.
arXiv:2609.14475 — https://arxiv.org/abs/2609.14475

## BadEngram: Backdoor Attack on Gated Memory Components in LLMs

- Explores a new attack surface in open-weight models that use gated parametric memories, demonstrating that modifying these components can implant trigger-dependent behavior.
- Shows that BadEngram achieves 96.6% Attack Success Rate (ASR) on triggered inputs in a controlled model while maintaining 99.6% clean accuracy and only 0.1% false activation.
- Validates the vulnerability at production scale on Qwen3.8-Flash-Next's Per-Layer Embedding subsystem, achieving 50.4% to 60.0% ASR on standard benchmarks without altering the backbone execution graph.

*Abstract only — full text not retrieved.*

"BadEngram: Backdoor Attack on Gated Memory Components in LLMs." arXiv, 2026.
arXiv:2609.13478 — https://arxiv.org/abs/2609.13478

## Also published

- "The Agentic Company OS: Substrate Inversion for Sustained Enterprise Agent Deployment." arXiv:2609.13334 — https://arxiv.org/abs/2609.13334
- "Converting Sequenced Fuzzy Cognitive Maps to Causal Virtual Worlds with Large Video Generators." arXiv:2609.14985 — https://arxiv.org/abs/2609.14985
- "Vibe Patenting: Evaluating LLM Judges for Professional Patent-Drafting Agents." arXiv:2609.13422 — https://arxiv.org/abs/2609.13422
- "Toward Self-Adaptive Physical AI: Can LLM Agents Manage Long-Horizon Physical Tasks?" arXiv:2609.13436 — https://arxiv.org/abs/2609.13436
- "Root-Cause Attribution Is a Search Problem: Continual Search for Long-Horizon Agent Failures." arXiv:2609.13463 — https://arxiv.org/abs/2609.13463
- "OrchSLM: Probing the Dynamics of Small Language Model Orchestration." arXiv:2609.13470 — https://arxiv.org/abs/2609.13470
