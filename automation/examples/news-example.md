+++
title = "Conference Brief — 2026-09-10"
date = 2026-09-10T06:00:00Z
type = "news"
tags = ["exploitation", "protocol-analysis", "fuzzing", "usenix"]
summary = "An app-agnostic route from arbitrary file overwrite to code execution on Android, and the first cross-platform look at AirDrop and Quick Share."
+++

*This file is a format reference, not published content. It lives outside `content/` on purpose.*

*Every identifier below is real and resolves. That is deliberate: the previous version of this file
used invented IDs to illustrate the shape, and a deep dive copied one, changed a digit, and
published it. Do not treat any identifier here as a template to adapt — see hard constraint 9 in
AGENTS.md.*

## In brief

- Both items target privileged code reached without user interaction: one through a file the runtime
  regenerates, one through daemons that parse untrusted input from anyone in wireless range.
- The pattern to watch is proximity and background services being treated as trusted input paths.

## Exploiting Android Apps with Counterfeit Art

- Arbitrary file overwrite is a common Android bug class whose impact has until now depended on
  which file a given app happened to expose, making it hard to rate.
- The technique targets the runtime-generated app image instead of an app-specific file, which makes
  the escalation to code execution work across apps rather than one at a time, and persist.
- Generality is the contribution here; the write-up does not quantify how many shipping apps are
  reachable this way.

Fall, R.-D., Mao, P., EPFL; Wagner, M., Asymmetric Research; Payer, M., EPFL. "Exploiting Android
Apps with Counterfeit Art." USENIX WOOT 2026.
https://www.usenix.org/conference/woot26/presentation/fall

## Protocol Prying: Systematic Vulnerability Research in the AirDrop and Android Quick Share Proximity Transfer Protocols

- First cross-platform reverse engineering and protocol-aware fuzzing of both proximity transfer
  stacks, which are proprietary and undocumented despite running on a reported five billion devices.
- The exposure is that both are reachable from wireless proximity with no prior pairing, and both
  parse layered serialized formats — binary plists, CPIO archives, protocol buffers, UKEY2
  handshakes — inside privileged daemons, which is a zero-click surface by construction.
- Fuzzing a reverse-engineered protocol bounds coverage by how completely the stack was recovered,
  so absence of findings in a region is not evidence about it.

Ale Ebrahim, A., Tippenhauer, N. O., CISPA Helmholtz Center for Information Security. "Protocol
Prying: Systematic Vulnerability Research in the AirDrop and Android Quick Share Proximity Transfer
Protocols." USENIX WOOT 2026.
https://www.usenix.org/conference/woot26/presentation/ebrahim

## Also published

- Yu, Z. et al. "DRVFuzz: Data-Sensitive RISC-V CPU Fuzzing." USENIX Security 2026 —
  https://www.usenix.org/conference/usenixsecurity26/presentation/yu-zehong
- Jia, Z. et al. "PANGOLIN: Fuzzing Multilingual IoT Firmware with LLM-Driven Code Analysis."
  USENIX Security 2026 — https://www.usenix.org/conference/usenixsecurity26/presentation/jia-zhipeng
