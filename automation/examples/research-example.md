+++
title = "Directed Fuzzing: State of the Art"
date = 2026-09-10T06:00:00Z
type = "research"
tags = ["fuzzing", "vulnerability-discovery", "tooling"]
slug = "directed-fuzzing-state-of-the-art"
+++

*This file is a format reference, not published content. It lives outside `content/` on purpose.*

*Every identifier below is real and resolves. That is deliberate: an earlier version of this file
cited an invented arXiv ID, and a published deep dive then copied the DOI below, changed the year by
one, and shipped a reference that 404s. Do not treat any identifier here as a template to adapt —
see hard constraint 9 in AGENTS.md.*

## Background

Coverage-guided fuzzing became the default vulnerability discovery technique after AFL demonstrated
that cheap edge instrumentation plus a genetic loop outperformed symbolic approaches on real
targets [1]. Directed fuzzing narrows that loop toward specific program points.

## Current State

Three families dominate. Distance-based scheduling, introduced by AFLGo [2], computes a static
distance from each basic block to the target and biases seed selection toward shorter distances.
Constraint-guided approaches such as Beacon [3] prune paths that provably cannot reach the target.
A third line keeps the loop but changes what it is pointed at, prioritising inputs by how much of
the program they reach rather than by distance to one site [4].

The benchmarks disagree on which wins, largely because Magma and FuzzBench measure different things.

## Future Outlook

The open problem is target selection rather than target reaching: given a patch, deciding *which*
program points are worth directing at is still mostly manual.

## References

1. Zalewski, M. "American Fuzzy Lop." 2014. https://lcamtuf.coredump.cx/afl/
2. Böhme, M. et al. "Directed Greybox Fuzzing." CCS 2017. doi:10.1145/3133956.3134020 —
   https://doi.org/10.1145/3133956.3134020
3. Huang, H. et al. "Beacon: Directed Grey-Box Fuzzing with Provable Path Pruning." IEEE S&P 2022.
   https://doi.org/10.1109/SP46214.2022.9833751
4. Zheng, H. et al. "FISHFUZZ: Catch Deeper Bugs by Throwing Larger Nets." USENIX Security 2023.
   https://www.usenix.org/conference/usenixsecurity23/presentation/zheng
