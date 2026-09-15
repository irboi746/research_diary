+++
title = "Conference Brief — 2026-09-14"
date = 2026-09-14T06:00:00Z
type = "news"
tags = ["fuzzing", "exploitation", "protocol-analysis", "llm-security", "usenix"]
summary = "USENIX Security and WOOT 2026: an app-agnostic route from file overwrite to code execution on Android, the first look inside AirDrop and Quick Share, and three fuzzers aimed at places fuzzers have not been."
+++

## In brief

- Four of the seven items are fuzzing work, and all four move the target rather than the technique:
  the Bluetooth host stack instead of the controller, RISC-V data paths instead of control flow,
  proprietary proximity protocols instead of file formats.
- Two independent items land on privileged background services reached without user interaction —
  the recurring theme of the batch.
- Most of these are accepted-paper listings without published full text, so the entries below are
  necessarily thin on results; they are pointers, not summaries of findings.

## Exploiting Android Apps with Counterfeit Art

- Arbitrary file overwrite is a common Android bug class whose impact has until now depended on
  which file a particular app happened to expose, making it hard to rate consistently.
- The technique targets the runtime-generated app image rather than an app-specific file, which is
  what makes the escalation to code execution app-agnostic and persistent.
- Generality is the claim; the listing does not say how many shipping apps are reachable this way.

*Abstract only — full text not retrieved.*

Fall, R.-D., Mao, P., Wagner, M., Payer, M. "Exploiting Android Apps with Counterfeit Art."
USENIX WOOT 2026. https://www.usenix.org/conference/woot26/presentation/fall

## Protocol Prying: Systematic Vulnerability Research in the AirDrop and Android Quick Share Proximity Transfer Protocols

- First cross-platform reverse engineering and protocol-aware fuzzing of both proximity transfer
  stacks, which are proprietary and undocumented despite a reported five billion devices running
  one or the other.
- The surface is zero-click by construction: both are reachable from wireless proximity with no
  prior pairing, and both parse layered serialized formats — binary plists, CPIO archives, protocol
  buffers, UKEY2 handshakes — inside privileged daemons.
- Coverage is bounded by how completely the stacks were reverse-engineered, so quiet regions are not
  evidence of their absence of bugs.

*Abstract only — full text not retrieved.*

Ale Ebrahim, A., Tippenhauer, N. O. "Protocol Prying: Systematic Vulnerability Research in the
AirDrop and Android Quick Share Proximity Transfer Protocols." USENIX WOOT 2026.
https://www.usenix.org/conference/woot26/presentation/ebrahim

## FuzzBT: Holistic-State-Guided Fuzzing for Bluetooth Host Stack in Kernels

- Bluetooth fuzzing work to date has concentrated on emulating devices and driving the controller;
  the host stack, which lives in the kernel, has been left largely untested.
- That matters because the host stack is where the protocol state actually accumulates — it issues
  controller commands, exposes the API to userspace, establishes logical links and multiplexes
  channels — so a fuzzer that ignores that state cannot reach most of it.
- The approach is to guide fuzzing by whole-stack state rather than per-message validity; the
  listing gives no bug counts or coverage figures.

*Abstract only — full text not retrieved.*

Kim, S., Peng, H., Karim, I., Wu, R., Wu, J., Bertino, E., Payer, M., Tian, D. "FuzzBT:
Holistic-State-Guided Fuzzing for Bluetooth Host Stack in Kernels." USENIX WOOT 2026.
https://www.usenix.org/conference/woot26/presentation/kim

## SoK: PHILTER: Uncovering Security and Functional Gaps in AI-based Phishing Website Detection Literature via an LLM-based Reasoning Framework

- A systematisation of the AI phishing-detection literature, using an LLM-based reasoning framework
  to audit published methods rather than to detect phishing.
- The question it puts to the field is whether high reported accuracy survives four requirements
  that deployment imposes and papers rarely test: resilience to evolving tactics, robustness on
  diverse benign pages, interpretability, and privacy.
- It evaluates the literature, not deployed systems, so it bounds what the published record
  supports rather than measuring what production detectors do.

*Abstract only — full text not retrieved.*

Alam, M., Rahman, M. L., Paul, S. K., Hays, A. W., Hussain, A., Huq, M. I., Saxena, N. "SoK:
PHILTER: Uncovering Security and Functional Gaps in AI-based Phishing Website Detection Literature
via an LLM-based Reasoning Framework." USENIX Security 2026.
https://www.usenix.org/conference/usenixsecurity26/presentation/alam

## DRVFuzz: Data-Sensitive RISC-V CPU Fuzzing

- Hardware fuzzers for CPU cores are mostly data-agnostic: they mutate instruction sequences and
  score on control-path coverage, which leaves bugs that only manifest for particular operand values
  out of reach.
- DRVFuzz makes the data sensitive part of the search, aimed at the RISC-V logic bugs that produce
  faulty privilege transitions and architectural state corruption.
- No comparison against existing hardware fuzzers is given in the listing.

*Abstract only — full text not retrieved.*

Yu, Z., Chen, Y., Yan, Z., Zhang, X., Xian, Z., Jiang, Y. "DRVFuzz: Data-Sensitive RISC-V CPU
Fuzzing." USENIX Security 2026.
https://www.usenix.org/conference/usenixsecurity26/presentation/yu-zehong

## You Have Been LaTeXpOsEd: A Large-Scale Systematic Analysis of Information Leakage in Preprint Archives Using Large Language Models

- First large-scale security audit of arXiv itself: 1.2 TB across 100,000 submissions, looking for
  sensitive information authors did not mean to publish.
- The leak channel is everything shipped alongside the PDF — auxiliary code, images, and LaTeX
  source including embedded comments — which authors generally do not think of as published.
- Of direct relevance to this diary, since arXiv source is a compulsory input here.

*Abstract only — full text not retrieved.*

Dubniczky, R. A., Borsos, B., Bisztray, T., Tihanyi, N. "You Have Been LaTeXpOsEd: A Large-Scale
Systematic Analysis of Information Leakage in Preprint Archives Using Large Language Models."
USENIX WOOT 2026. https://www.usenix.org/conference/woot26/presentation/dubniczky

## Enjoy the Free Lunch, Someone Paid for Us: Escaping Resource Limits of MicroVM-based Containers

- MicroVM-based containers are deployed across AWS, Azure and Alibaba Cloud to get container
  density with VM-grade isolation; the resource limits that make that economics work are the target
  here.
- The escape is of the resource accounting rather than the isolation boundary — a tenant obtaining
  more CPU, memory or I/O than was provisioned, at the expense of co-tenants and the provider.

*Abstract only — full text not retrieved.*

Wang, S., Luo, W., Liu, K., Xu, Z., Zheng, Y., Wang, W., Zhao, S., Li, P., Hou, R. "Enjoy the Free
Lunch, Someone Paid for Us: Escaping Resource Limits of MicroVM-based Containers."
USENIX Security 2026. https://www.usenix.org/conference/usenixsecurity26/presentation/wang-shiwen

## Also published

- Shrestha, N., Kate, A., Nayak, K. "Hydrangea: Optimistic Two-Round Partial Synchrony with Improved
  Fault Resilience." USENIX Security 2026 —
  https://www.usenix.org/conference/usenixsecurity26/presentation/shrestha
- Sturm, R., Schelfhout, A., Gülmez, M., Jacobs, A., Volckaert, S. "Secpoline: A Scalable Approach
  to Build Secure In-Process Syscall Interposers." USENIX Security 2026 —
  https://www.usenix.org/conference/usenixsecurity26/presentation/sturm
- Mauthe, N., Ackermann, E., Bugiel, S. "SoK: Capability Operating Systems: Is the Future Finally
  Here?" USENIX Security 2026 —
  https://www.usenix.org/conference/usenixsecurity26/presentation/mauthe
