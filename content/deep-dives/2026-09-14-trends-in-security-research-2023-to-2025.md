+++
title = "Trends in Security Research (2023-2025)"
date = 2026-09-14T18:12:49Z
type = "deep-dives"
tags = ["web-security", "llm-security", "fuzzing", "cryptography", "usenix", "defcon", "blackhat", "arxiv", "off-by-one"]
slug = "trends-in-security-research-2023-to-2025"
+++

## Background

The landscape of cybersecurity research has evolved rapidly from 2023 to 2025, driven by the emergence of new technologies and the continuous cat-and-mouse game between attackers and defenders. Traditional domains like web security and cryptography have seen significant shifts due to the centralization of web infrastructure and the necessity of preserving privacy in computations. Concurrently, the explosive growth of Large Language Models (LLMs) has introduced a completely new attack surface, while automated vulnerability discovery via fuzzing has become more sophisticated, leveraging AI and specialized runtime environments to scale operations. This deep dive synthesizes the trends across these four critical areas—web security, LLM security, fuzzing, and cryptography—drawing from top-tier venues such as USENIX Security.

## Current State

### Web Security
In 2023, web security research heavily focused on the implications of complex web architectures and prototype vulnerabilities. The discovery of prototype pollution leading to remote code execution in Node.js demonstrated that backend vulnerabilities remain a critical threat [1]. Cookie integrity also received significant attention, with studies showing that security mechanisms previously considered robust can be bypassed [2].

By 2024, the focus shifted towards the centralization of web infrastructures and platform threats. Researchers highlighted how shared infrastructure magnifies vulnerabilities, leading to comprehensive studies on web platform threats [3] and vulnerability-oriented testing specifically designed for RESTful APIs [4].

In 2025, we observe a growing concern around the integration of complex web services and hidden inconsistencies. Novel HTTP Desync vulnerabilities were discovered using gray-box testing, showing that the boundaries between different web services and load balancers are often porous [5]. Similarly, cross-app attacks in integration platforms demonstrated widespread vulnerabilities in OAuth 2.0 deployments [6].

### LLM Security
The security of Large Language Models has been the most volatile research area. In 2023, the focus was primarily on privacy and data leakage. Researchers demonstrated that code generation models, such as those used in GitHub Copilot, could regurgitate sensitive personal information [7]. The community also assessed the security implications of using LLMs as code assistants, finding that while they introduce some low-level bugs, the overall security impact in controlled settings was measurable [8].

As defenders introduced more robust guardrails in 2024, attackers pivoted to uncovering deeper vulnerabilities. Studies like PentestGPT showcased the dual-use nature of LLMs, empowering automated penetration testing [9].

By 2025, the research community is dealing with "agentic" LLMs that can autonomously interact with web tools. Studies have shown the emerging threat of web-enabled LLMs, which can be manipulated to conduct sophisticated cyberattacks [10]. Furthermore, researchers have revealed hidden weaknesses in the refusal boundaries of aligned LLMs, demonstrating that safety alignment is still an unsolved problem [11].

### Fuzzing
Automated vulnerability discovery via fuzzing has matured significantly. In 2023, the trend was exploring greybox fuzzing at scale and for multi-language systems. Innovations like FISHFUZZ introduced input prioritization strategies to catch deeper bugs, while PolyFuzz addressed the challenges of fuzzing multi-language software systems holistically [12, 13].

In 2024, fuzzing techniques became highly specialized. Research such as OptFuzz demonstrated optimization path guided fuzzing for JavaScript JIT compilers [14], and specialized frameworks were developed for fuzzing complex environments like BusyBox [15], showing a shift from generic fuzzing to highly targeted, environment-aware approaches.

Moving into 2025, the integration of LLMs into the fuzzing pipeline marked a paradigm shift. LLMs were used to synthesize input generators, enabling the low-cost and comprehensive fuzzing of non-textual inputs [16]. Concurrently, traditional fuzzing continued to evolve for emerging targets, with frameworks like Waltzz performing WebAssembly runtime fuzzing using stack-invariant transformations [17].

### Cryptography
The cryptography domain has been heavily influenced by the transition to privacy-preserving computation. In 2023, much of the research analyzed zero-knowledge accumulators, with Curve Trees providing practical and transparent solutions without trusted setups [18]. Other work focused on optimizing Fully Homomorphic Encryption (FHE) with the introduction of compilers like HECO [19].

In 2024, the focus expanded to the practical security of cryptographic hardware and side-channels. The GoFetch attack demonstrated how data memory-dependent prefetchers could be bypassed via cryptographic side-channels, highlighting the gap between theoretical security and hardware implementation flaws [20].

In 2025, zero-knowledge proofs (ZKPs) and multi-party computation (MPC) have become highly prominent, driven by privacy demands in machine learning and distributed systems. Researchers proposed scalable collaborative zk-SNARKs and applied them to fully distributed proof delegation, aiming to minimize computational overhead [21]. Meanwhile, practical vulnerabilities in cryptographic libraries, such as X.509DoS, continued to be uncovered and mitigated [22].

## Future Outlook

The trajectory from 2023 to 2025 suggests a future where AI is both the primary weapon and the main target. The community must address the fundamental insecurities of LLM agents before they are widely deployed in critical infrastructure. Fuzzing will likely become increasingly AI-driven, though the computational costs of LLM integration remain a bottleneck. In web security, the boundaries between client, server, and third-party integrations will continue to blur, requiring more holistic analysis frameworks. Finally, cryptography will face the dual challenge of rolling out hardware-resilient cryptographic implementations and making advanced privacy-preserving computations practical for everyday use.

## References

[1] Mikhail Shcherbakov, et al., "Silent Spring: Prototype Pollution Leads to Remote Code Execution in Node.js," USENIX Security 2023. https://www.usenix.org/conference/usenixsecurity23/presentation/shcherbakov
[2] Marco Squarcina, et al., "Cookie Crumbles: Breaking and Fixing Web Session Integrity," USENIX Security 2023. https://www.usenix.org/conference/usenixsecurity23/presentation/squarcina
[3] Pedro Bernardo, et al., "Web Platform Threats: Automated Detection of Web Security Issues With WPT," USENIX Security 2024. https://www.usenix.org/conference/usenixsecurity24/presentation/bernardo
[4] Wenlong Du, et al., "Vulnerability-oriented Testing for RESTful APIs," USENIX Security 2024. https://www.usenix.org/conference/usenixsecurity24/presentation/du
[5] Keran Mu, et al., "The Silent Danger in HTTP: Identifying HTTP Desync Vulnerabilities with Gray-box Testing," USENIX Security 2025. https://www.usenix.org/conference/usenixsecurity25/presentation/mu
[6] Kaixuan Luo, et al., "Universal Cross-app Attacks: Exploiting and Securing OAuth 2.0 in Integration Platforms," USENIX Security 2025. https://www.usenix.org/conference/usenixsecurity25/presentation/luo-kaixuan
[7] Liang Niu, et al., "CodexLeaks: Privacy Leaks from Code Generation Language Models in GitHub Copilot," USENIX Security 2023. https://www.usenix.org/conference/usenixsecurity23/presentation/niu
[8] Gustavo Sandoval, et al., "Lost at C: A User Study on the Security Implications of Large Language Model Code Assistants," USENIX Security 2023. https://www.usenix.org/conference/usenixsecurity23/presentation/sandoval
[9] Gelei Deng, et al., "PentestGPT: Evaluating and Harnessing Large Language Models for Automated Penetration Testing," USENIX Security 2024. https://www.usenix.org/conference/usenixsecurity24/presentation/deng
[10] Hanna Kim, et al., "When LLMs Go Online: The Emerging Threat of Web-Enabled LLMs," USENIX Security 2025. https://www.usenix.org/conference/usenixsecurity25/presentation/kim-hanna
[11] Jiahao Yu, et al., "Mind the Inconspicuous: Revealing the Hidden Weakness in Aligned LLMs' Refusal Boundaries," USENIX Security 2025. https://www.usenix.org/conference/usenixsecurity25/presentation/yu-jiahao
[12] Han Zheng, et al., "FISHFUZZ: Catch Deeper Bugs by Throwing Larger Nets," USENIX Security 2023. https://www.usenix.org/conference/usenixsecurity23/presentation/zheng
[13] Wen Li, et al., "PolyFuzz: Holistic Greybox Fuzzing of Multi-Language Systems," USENIX Security 2023. https://www.usenix.org/conference/usenixsecurity23/presentation/li-wen
[14] Jiming Wang, et al., "OptFuzz: Optimization Path Guided Fuzzing for JavaScript JIT Compilers," USENIX Security 2024. https://www.usenix.org/conference/usenixsecurity24/presentation/wang-jiming
[15] Asmita, et al., "Fuzzing BusyBox: Leveraging LLM and Crash Reuse for Embedded Bug Unearthing," USENIX Security 2024. https://www.usenix.org/conference/usenixsecurity24/presentation/asmita
[16] Kunpeng Zhang, et al., "Low-Cost and Comprehensive Non-textual Input Fuzzing with LLM-Synthesized Input Generators," USENIX Security 2025. https://www.usenix.org/conference/usenixsecurity25/presentation/zhang-kunpeng
[17] Lingming Zhang, et al., "Waltzz: WebAssembly Runtime Fuzzing with Stack-Invariant Transformation," USENIX Security 2025. https://www.usenix.org/conference/usenixsecurity25/presentation/zhang-lingming
[18] Matteo Campanelli, et al., "Curve Trees: Practical and Transparent Zero-Knowledge Accumulators," USENIX Security 2023. https://www.usenix.org/conference/usenixsecurity23/presentation/campanelli
[19] Alexander Viand, et al., "HECO: Fully Homomorphic Encryption Compiler," USENIX Security 2023. https://www.usenix.org/conference/usenixsecurity23/presentation/viand
[20] Boru Chen, et al., "GoFetch: Breaking Constant-Time Cryptographic Implementations Using Data Memory-Dependent Prefetchers," USENIX Security 2024. https://www.usenix.org/conference/usenixsecurity24/presentation/chen-boru
[21] Xuanming Liu, et al., "Scalable Collaborative zk-SNARK and Its Application to Fully Distributed Proof Delegation," USENIX Security 2025. https://www.usenix.org/conference/usenixsecurity25/presentation/liu-xuanming
[22] Bing Shi, et al., "X.509DoS: Exploiting and Detecting Denial-of-Service Vulnerabilities in Cryptographic Libraries using Crafted X.509 Certificates," USENIX Security 2025. https://www.usenix.org/conference/usenixsecurity25/presentation/shi-bing
