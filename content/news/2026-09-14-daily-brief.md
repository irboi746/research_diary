+++
title = "Daily Brief — 2026-09-14"
date = 2026-09-14T06:00:00Z
type = "news"
tags = ["fuzzing", "binary-analysis", "side-channel", "usenix", "llm-security"]
+++

## Exploiting Android Apps with Counterfeit Art

- Arbitrary file overwrite vulnerabilities are common in Android apps.
- However, the security impact of such vulnerabilities has so far been highly app-dependent.
- We present a new, app-agnostic, persistent technique that turns arbitrary file overwrites into code execution by targeting the runtime-generated app image file.

Rokhaya-Diamil Fall and Philipp Mao, EPFL; Martin Wagner, Asymmetric Research; Mathias Payer, EPFL "Exploiting Android Apps with Counterfeit Art." USENIX WOOT 2026.
https://www.usenix.org/conference/woot26/presentation/fall

## Protocol Prying: Systematic Vulnerability Research in the AirDrop and Android Quick Share Proximity Transfer Protocols

- Apple AirDrop and Google/Samsung Quick Share are proximity file-transfer protocols used by over five billion devices, yet their application-layer security properties remain largely unstudied because both stacks are proprietary and undocumented.
- Both protocols are reachable from wireless proximity without any prior pairing and process complex serialized content (binary plists, CPIO archives, Protocol Buffers, UKEY2handshakes)inside privileged daemons,making them attractive zero-click targets across multiple operating systems.
- We perform the first cross-platform reverse engineering and protocol-aware fuzzing study of both stacks.

Arash Ale Ebrahim and Nils Ole Tippenhauer, CISPA Helmholtz Center for Information Security "Protocol Prying: Systematic Vulnerability Research in the AirDrop and Android Quick Share Proximity Transfer Protocols." USENIX WOOT 2026.
https://www.usenix.org/conference/woot26/presentation/ebrahim

## FuzzBT: Holistic-State-Guided Fuzzing for Bluetooth Host Stack in Kernels

- Bluetooth is both pervasive and vulnerable, yet fuzzing Bluetooth is challenging.
- While research on Bluetooth fuzzing has advanced to emulate Bluetooth devices and generate effective inputs for controllers, the host stack has been overlooked.
- The host stack is responsible for issuing commands to controllers, providing API abstractions for user applications, establishing logical links for asynchronous connections, and multiplexing channels.

Sungwoo Kim, Purdue University; Hui Peng, Google, Inc.; Imtiaz Karim, The University of Texas at Dallas; Ruoyu Wu, Purdue University; Jianliang Wu, Simon Fraser University; Elisa Bertino, Purdue University; Mathias Payer, EPFL; Dave (Jing) Tian, Purdue University "FuzzBT: Holistic-State-Guided Fuzzing for Bluetooth Host Stack in Kernels." USENIX WOOT 2026.
https://www.usenix.org/conference/woot26/presentation/kim

## SoK: PHILTER: Uncovering Security and Functional Gaps in AI-based Phishing Website Detection Literature via an LLM-based Reasoning Framework

- Phishing websites remain a dominant enabler of cybercrime.
- In response, many academic AI-based phishing website detection methods have been developed, often inspiring the design of real-world systems.
- Although most studies report high accuracy, it remains unclear whether they meet real-world requirements such as resilience to evolving phishing tactics, robustness on diverse benign pages, interpretability, and privacy.

Mahbub Alam, Texas A&M University; Muhammad Lutfor Rahman, California State University San Marcos; Sonjoy Kumar Paul, Amy W. Hays, Aftab Hussain, Md Imanul Huq, and Nitesh Saxena, Texas A&M University "SoK: PHILTER: Uncovering Security and Functional Gaps in AI-based Phishing Website Detection Literature via an LLM-based Reasoning Framework." USENIX Security 2026.
https://www.usenix.org/conference/usenixsecurity26/presentation/alam

## DRVFuzz: Data-Sensitive RISC-V CPU Fuzzing

- The rapid adoption of RISC-V across modern computing systems has made the security integrity of its implementations a paramount concern.
- Logic bugs in RISC-V cores can lead to critical failures, such as faulty privilege transitions and architectural state corruption.
- While hardware fuzzing has emerged as a powerful technique for automated bug discovery, existing frameworks remain largely data-agnostic.

Zehong Yu, Tsinghua University; Yuanliang Chen, Renmin University of China; Zhen Yan, Xudong Zhang, Zhensheng Xian, and Yu Jiang, Tsinghua University "DRVFuzz: Data-Sensitive RISC-V CPU Fuzzing." USENIX Security 2026.
https://www.usenix.org/conference/usenixsecurity26/presentation/yu-zehong

## You Have Been LaTeXpOsEd: A Large-Scale Systematic Analysis of Information Leakage in Preprint Archives Using Large Language Models

- In this work, we present the first large-scale security audit of the arXiv preprint repository, analyzing over 1.2 TB of data from 100,000 arXiv submissions to report on systemic sensitive information leakage.
- When authors upload submissions, they publish not only a PDF but also auxiliary code, images, and LaTeX source files containing embedded comments.

Richard A. Dubniczky and Bertalan Borsos, Eötvös Loránd University; Tamas Bisztray, HUN-REN Sztaki; Norbert Tihanyi, Technology Innovation Institute "You Have Been LaTeXpOsEd: A Large-Scale Systematic Analysis of Information Leakage in Preprint Archives Using Large Language Models." USENIX WOOT 2026.
https://www.usenix.org/conference/woot26/presentation/dubniczky

## Enjoy the Free Lunch, Someone Paid for Us: Escaping Resource Limits of MicroVM-based Containers

- MicroVM-based containers are increasingly deployed in public clouds (e.g., AWS, Azure, and Alibaba Cloud) to combine container efficiency with strong isolation.

Shiwen Wang, State Key Laboratory of Cyberspace Security Defense, Institute of Information Engineering, CAS, and School of Cyber Security, University of Chinese Academy of Sciences; Wu Luo, State Key Laboratory of Cyberspace Security Defense, Institute of Information Engineering, CAS; Kaicheng Liu and Zheyuan Xu, State Key Laboratory of Cyberspace Security Defense, Institute of Information Engineering, CAS, and School of Cyber Security, University of Chinese Academy of Sciences; Yaowen Zheng, Wenhao Wang, Shijun Zhao, Peinan Li, and Rui Hou, State Key Laboratory of Cyberspace Security Defense, Institute of Information Engineering, CAS "Enjoy the Free Lunch, Someone Paid for Us: Escaping Resource Limits of MicroVM-based Containers." USENIX Security 2026.
https://www.usenix.org/conference/usenixsecurity26/presentation/wang-shiwen

## Also published

- Nibesh Shrestha, Supra Research; Aniket Kate, Supra Research / Purdue University; Kartik Nayak, Duke University "Hydrangea: Optimistic Two-Round Partial Synchrony with Improved Fault Resilience." USENIX Security 2026 —
  https://www.usenix.org/conference/usenixsecurity26/presentation/shrestha
- Ruben Sturm and Anton Schelfhout, DistriNet, KU Leuven; Merve Gülmez, Ericsson Security Research; Adriaan Jacobs and Stijn Volckaert, DistriNet, KU Leuven "Secpoline: A Scalable Approach to Build Secure In-Process Syscall Interposers." USENIX Security 2026 —
  https://www.usenix.org/conference/usenixsecurity26/presentation/sturm
- Noah Mauthe, Eric Ackermann, and Sven Bugiel, CISPA Helmholtz Center for Information Security "SoK: Capability Operating Systems: Is the Future Finally Here?." USENIX Security 2026 —
  https://www.usenix.org/conference/usenixsecurity26/presentation/mauthe
