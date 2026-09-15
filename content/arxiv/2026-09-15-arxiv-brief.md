+++
title = "arXiv Brief — 2026-09-15"
date = 2026-09-15T06:00:00Z
type = "arxiv"
tags = ["cs.CR", "cs.AI", "cs.SE", "llm-security", "fuzzing", "supply-chain", "vulnerability-discovery"]
summary = "New perspectives on LLM agent security: a census of the Model Context Protocol ecosystem, attacks via gated memories and contextual bias, new attacks on agent architectures, and LLM-guided smart contract fuzzing."
+++

## In brief

- Agent architectures are increasingly targeted by new threat models. Research today introduces persistent memory poisoning attacks (PMPA), registration-time injection via deceptive agent descriptions, and information flow control (IFC) bypasses that leak private data.
- LLM agents face new attack surfaces: the Model Context Protocol (MCP) registry is plagued by silent drift and unauthenticated exposure, while gated memory parameters can harbor backdoors without altering the model's backbone.
- Automated vulnerability identification using LLMs shows progress, but evaluations confirm that agents struggle with repository-scale localization and remain susceptible to adversarial issues that guide them toward insecure patches.

## ActGuard: Pre-execution Action Auditing against Indirect Prompt Injection in LLM Agents

- Proposes a pre-execution action auditing framework, ActGuard, to defend LLM agents against indirect prompt injection (IPI) via tool outputs.
- Rather than broadly filtering external content, ActGuard constructs a local tool expectation and performs contrastive analysis to identify when an external payload causes the action to deviate.
- A verifier then masks only the localized malicious spans in the tool output and regenerates the action, achieving state-of-the-art attack reduction while preserving execution flexibility.

Wang, B., Gu, X., Wang, W., Yang, X., Li, H., Yin, R. "ActGuard: Pre-execution Action Auditing against Indirect Prompt Injection in LLM Agents." arXiv, 2026.
arXiv:2609.14987 — https://arxiv.org/abs/2609.14987

## When Malicious Instructions Persist: Persistent Memory Poisoning Attack on Harness-Based Agents

- Introduces Persistent Memory Poisoning Attack (PMPA) against harness-based agents (e.g., OpenClaw, Claude Code).
- The attack embeds instructions into benign external sources, tricking the agent into writing them into its persistent memory. These instructions persist across sessions and trigger malicious actions or privacy leakage later.
- Achieves high Injection Success Rates and Cross-session Attack Success Rates across different agents and LLMs, demonstrating that prompt-level defenses provide limited protection once memory is poisoned.

Huang, S., Zhang, J., Jia, H. "When Malicious Instructions Persist: Persistent Memory Poisoning Attack on Harness-Based Agents." arXiv, 2026.
arXiv:2609.13889 — https://arxiv.org/abs/2609.13889

## Exploring Automated Vulnerability Identification in JavaScript Code Using Large Language Models

- Evaluates Gemini 1.5 Flash, GPT-4o Mini, and DeepSeek-R1-Distill-Llama-8B on identifying vulnerabilities across five CWE categories in 1,125 JavaScript snippets.
- Finds that LLMs substantially outperform traditional SAST tools on snippet-level identification, with a fine-tuned Gemini 1.5 Flash reaching 60% accuracy (compared to near-zero for rule-based analyzers).
- Shows that fine-tuning, Chain-of-Thought, and few-shot prompting provide tangible improvements, although the approach still suffers from limited recall and uneven performance across vulnerability types.

Kaushik, M., Bhardwaj, I., Gupta, P., Jalote, P., Buduru, A. B. "Exploring Automated Vulnerability Identification in JavaScript Code Using Large Language Models." arXiv, 2026.
arXiv:2609.13816 — https://arxiv.org/abs/2609.13816

## Authorization Architectures for Tool-Using AI Agents

- Reviews 89 sources on authorization and security models for tool-using AI agents, identifying a critical gap in runtime enforcement and just-in-time authorization at policy enforcement points (PEPs).
- Introduces a principal hierarchy spanning users, operators, orchestrators, sub-agents, and tools, and examines issues like prompt injection as a mechanism that breaks this hierarchy by bypassing authorization.
- Proposes seven structural requirements and a four-layer reference architecture to ensure agent actions are traceable, delegable, and contestable.

Surapani, R. K., Kakitapelli, P. K. D., Morampudi, A., Padi, P. "Authorization Architectures for Tool-Using AI Agents." arXiv, 2026.
arXiv:2609.15906 — https://arxiv.org/abs/2609.15906

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

- Trad, F., Chen, S., Pham, H. V., Uddin, G., Ray, B. "Adversarial Testing of Automated Program Repair Agents for Security Vulnerabilities." arXiv:2609.15963 — https://arxiv.org/abs/2609.15963
- Stevanovic, O., Wachter, J. "Automating Attack Graph Construction for Agentic Pentesting. Towards Neuro-Symbolic Vulnerability Hunting." arXiv:2609.15523 — https://arxiv.org/abs/2609.15523
- Priyanshu, A., Vijay, S., Majd, K., He, X., Burch, F., Matsumoto, T., He, J., Saglam, B., Goldblatt, A., Yang, Z., Karbasi, A. "Vulnerability Localization Benchmark: Measuring Agentic Security Analysis at Repository Scale." arXiv:2609.15939 — https://arxiv.org/abs/2609.15939
- Shim, M., Karim, R. R., Jakkula, R., Zhou, K., Liu, X., Wang, X. E., Li, Z. "Confuse the Model, Control the Flow: Understanding and Mitigating Privacy Leakage from LLM Agents with Information Flow Control." arXiv:2609.14003 — https://arxiv.org/abs/2609.14003
- Yu, Z., Ma, H., Zhan, D., Zhang, H., Fang, H., Chang, E.-C. "Misleading the Planner through Deceptive Resumes: Registration-Time Injection in Centralized Multi-Agent Systems." arXiv:2609.15516 — https://arxiv.org/abs/2609.15516
- Cao, X., Szekeres, A., Faisal, F. E. "AutoTailor: Automatic, User-Aligned Capability Selection and Adaptation for Web Agents." arXiv:2609.13548 — https://arxiv.org/abs/2609.13548
- Feng, Y., Lin, R., Wen, M., Guo, Y., Ma, X., Wu, Y., Deng, X., Ji, S. "HazardAuditor: From Executable Threats to Safer Computer-Use Agents." arXiv:2609.15134 — https://arxiv.org/abs/2609.15134
- "The Agentic Company OS: Substrate Inversion for Sustained Enterprise Agent Deployment." arXiv:2609.13334 — https://arxiv.org/abs/2609.13334
- "Converting Sequenced Fuzzy Cognitive Maps to Causal Virtual Worlds with Large Video Generators." arXiv:2609.14985 — https://arxiv.org/abs/2609.14985
- "Vibe Patenting: Evaluating LLM Judges for Professional Patent-Drafting Agents." arXiv:2609.13422 — https://arxiv.org/abs/2609.13422
- "Toward Self-Adaptive Physical AI: Can LLM Agents Manage Long-Horizon Physical Tasks?" arXiv:2609.13436 — https://arxiv.org/abs/2609.13436
- "Root-Cause Attribution Is a Search Problem: Continual Search for Long-Horizon Agent Failures." arXiv:2609.13463 — https://arxiv.org/abs/2609.13463
- "OrchSLM: Probing the Dynamics of Small Language Model Orchestration." arXiv:2609.13470 — https://arxiv.org/abs/2609.13470
