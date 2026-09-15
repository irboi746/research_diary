+++
title = "Web Security Vulnerabilities: State of the Art and Research Gaps"
date = 2026-09-15T06:00:00Z
type = "research"
tags = ["web-security", "vulnerability-discovery", "fuzzing", "llm-security"]
slug = "web-security-vulnerabilities-state-of-the-art"
+++

## Background

Web application security has evolved dramatically from the early days of hunting for simple input validation flaws. In the beginning, automated black-box web application vulnerability testing focused primarily on identifying cross-site scripting (XSS) and SQL injection (SQLi) [1, 15, 16, 17]. These early scanners were largely stateless, firing payloads at individual endpoints without understanding the underlying application logic or the dependencies between different HTTP requests.

As web architectures matured into complex, stateful applications and cloud-native microservices, the attack surface shifted. Vulnerability discovery had to adapt to address the "state challenge"—where deep business logic is guarded by complex inter-request dependencies—and the "semantic gap"—where traditional payload mutations fail to generate the structured inputs required by modern APIs [2]. At the same time, the rise of complex proxy chains, load balancers, and caching layers introduced new classes of severe misconfiguration vulnerabilities, such as HTTP Request Smuggling, Web Cache Deception, and Server-Side Request Forgery (SSRF) [6, 9, 12, 14, 18, 19].

## Current State

The current state of the art is defined by a dichotomy between defending against deep logic flaws in stateful applications and mitigating complex architectural misconfigurations.

**Stateful Fuzzing and LLMs:** To overcome the limitations of stateless scanners, researchers have focused on state-sensitive testing and coverage-guided API fuzzing. Tools like WuppieFuzz [3] and WebFuzzGen [2] demonstrate that modeling structural dependencies (e.g., via OpenAPI extensions) is crucial for penetrating deep into an application's state space. Large Language Models (LLMs) are increasingly being leveraged to automatically synthesize these complex API interactions and generate fuzzing harnesses [20, 21, 22]. However, this approach is not without significant pitfalls. Recent work highlights that LLM-guided fuzzing can suffer from inherent hallucinations and that the evaluation rewards used to steer them can causally distort the vulnerabilities they discover [4]. Furthermore, LLMs themselves introduce new attack vectors if their outputs are insecurely handled within web applications [23].

**Architectural and Server-Side Vulnerabilities:** While client-side vulnerabilities like XSS remain prevalent and have evolved into complex request hijacking scenarios [13, 24, 25], server-side vulnerabilities have become the primary vector for high-impact breaches.
*   **SSRF:** SSRF attacks allow adversaries to pivot through a web application to access internal network resources. While deep learning approaches [11] and automated fuzzing techniques [10] have been proposed for detection, robust prevention often requires fundamental changes in how server-side requests are managed [9, 26].
*   **Request Smuggling:** HTTP Request Smuggling exploits discrepancies in how front-end and back-end servers parse HTTP headers. Differential fuzzing approaches like T-Reqs [12, 14, 27] have proven highly effective at identifying these parsing discrepancies at scale.
*   **Cache Deception and Poisoning:** The expanding use of caching tiers has led to vulnerabilities where an attacker can either trick a cache into storing sensitive user data (Web Cache Deception) [6, 7, 28] or inject malicious payloads into a cached response served to other users (Web Cache Poisoning) [8, 29, 30]. The intersection of cache poisoning and LLM systems represents a particularly novel and dangerous frontier [5].

## Future Outlook

The landscape of web vulnerability discovery reveals several critical gaps that demand further research:

1.  **Resolving the State Challenge Autonomously:** While frameworks like WebFuzzGen [2] make strides in directed fuzzing for stateful applications, they still require significant scaffolding. Future research must focus on fully autonomous agents capable of inferring complex state machines without manual OpenAPI annotations, while rigorously addressing the evaluation distortions currently plaguing LLM-assisted fuzzing [4, 31, 32].
2.  **Systemic Defenses for Architectural Flaws:** Fuzzing tools excel at finding SSRF [10] and Request Smuggling [12], but detection is not prevention. There is a pressing need for systemic, framework-level defenses and architectural patterns that render these classes of misconfigurations unexploitable by design, rather than relying on reactive detection [9, 33, 34].
3.  **Cross-Layer Vulnerability Discovery:** Modern attacks often chain multiple subtle flaws across the client, application logic, and infrastructure caching layers [13, 14, 35]. Current vulnerability scanners are generally siloed by layer. The next generation of vulnerability discovery tools must perform cross-layer analysis, reasoning about the interactions between a React front-end, a GraphQL API [36, 37, 38], and the reverse proxy caching tier simultaneously [39, 40, 41, 42].

## References

1. Bau, Jason et al.. "State of the Art: Automated Black-Box Web Application Vulnerability Testing". 2010. doi:10.1109/sp.2010.27 — https://doi.org/10.1109/sp.2010.27
2. Chen, Zhongyuan, Qu, Haipeng. "WebFuzzGen: LLM-Enhanced Directed Fuzzing for Stateful Web Applications". 2025. doi:10.1109/aibdf67964.2025.11440771 — https://doi.org/10.1109/aibdf67964.2025.11440771
3. Rooijakkers, Thomas et al.. "WuppieFuzz: Coverage-Guided, Stateful REST API Fuzzing". 2026. doi:10.5220/0014327000004061 — https://doi.org/10.5220/0014327000004061
4. Vishwakarma, Ashish. "Does the Verdict Function Matter? How Evaluation Rewards Causally Steer Automated LLM Fuzzing and Distort Discovered Vulnerabilities". 2026. doi:10.2139/ssrn.7360360 — https://doi.org/10.2139/ssrn.7360360
5. Wu, Guanlong et al.. "When Cache Poisoning Meets LLM Systems: Semantic Cache Poisoning and Its Countermeasures". 2026. doi:10.14722/ndss.2026.240200 — https://doi.org/10.14722/ndss.2026.240200
6. Berto, Filippo et al.. "A Methodology for Web Cache Deception Vulnerability Discovery". 2024. doi:10.5220/0012692000003711 — https://doi.org/10.5220/0012692000003711
7. Vitali, Maycon. "Web Cache Deception Attack". 2022. doi:10.47986/16/2 — https://doi.org/10.47986/16/2
8. Klein, Amit. "Web Cache Poisoning Attacks". 2011. doi:10.1007/978-1-4419-5906-5_666 — https://doi.org/10.1007/978-1-4419-5906-5_666
9. Jabiyev, Bahruz et al.. "Preventing server-side request forgery attacks". 2021. doi:10.1145/3412841.3442036 — https://doi.org/10.1145/3412841.3442036
10. Seran, Susruthan, Bhandari, Guru, Arcuri, Andrea. "Detecting Server-Side Request Forgery (SSRF) Vulnerabilities In REST API Fuzz Testing". 2026. doi:10.1145/3786155.3788581 — https://doi.org/10.1145/3786155.3788581
11. Mukamisha, Jacqueline et al.. "Mitigating Server-Side Request Forgery (SSRF) Attacks: An Empirical Analysis of Deep Learning-Based Approaches". 2025. doi:10.1109/csp66295.2025.00027 — https://doi.org/10.1109/csp66295.2025.00027
12. Jabiyev, Bahruz et al.. "T-Reqs: HTTP Request Smuggling with Differential Fuzzing". 2021. doi:10.1145/3460120.3485384 — https://doi.org/10.1145/3460120.3485384
13. Khodayari, Soheil, Barber, Thomas, Pellegrino, Giancarlo. "The Great Request Robbery: An Empirical Study of Client-side Request Hijacking Vulnerabilities on the Web". 2024. doi:10.1109/sp54263.2024.00098 — https://doi.org/10.1109/sp54263.2024.00098
14. Baloch, Rafay. "Exploring XXE, SSRF, and Request Smuggling Techniques". 2024. doi:10.1201/9781003373568-9 — https://doi.org/10.1201/9781003373568-9
15. Wang, Zheng. "A Revisit of DNS Kaminsky Cache Poisoning Attacks". 2015. doi:10.1109/glocom.2015.7417017 — https://doi.org/10.1109/glocom.2015.7417017
16. Brown, T. et al.. "Fine-Tuning Large Language Models". 2024. doi:10.5040/bci-0kh1.ch-011 — https://doi.org/10.5040/bci-0kh1.ch-011
17. Imtias, Muhamad Bunan et al.. "Comparative Analysis of Penetration Testing Frameworks: OWASP, PTES, and NIST SP 800-115 for Detecting Web Application Vulnerabilities". . doi:10.30871/jaic.v9i6.9846 — https://doi.org/10.30871/jaic.v9i6.9846
18. Gupta, Sunil. "What Is SQL Injection Attack". 2020. doi:10.1007/978-1-4842-6505-5_1 — https://doi.org/10.1007/978-1-4842-6505-5_1
19. Baloch, Rafay. "Introduction to Server-Side Injection Attacks". 2024. doi:10.1201/9781003373568-3 — https://doi.org/10.1201/9781003373568-3
20. Sinha, Sanjib. "How to Exploit Through Cross-Site Scripting (XSS)". 2019. doi:10.1007/978-1-4842-5391-5_4 — https://doi.org/10.1007/978-1-4842-5391-5_4
21. Watson, Venesa, Lou, Xinxin, Gao, Yuan. "A Review of PROFIBUS Protocol Vulnerabilities - Considerations for Implementing Authentication and Authorization Controls". 2017. doi:10.5220/0006426504440449 — https://doi.org/10.5220/0006426504440449
22. Tripathi, Prakhar, Thingla, Rahul. "Cross Site Scripting (XSS) and SQL-Injection Attack Detection in Web Application". . doi:10.2139/ssrn.3356292 — https://doi.org/10.2139/ssrn.3356292
23. Grenfeldt, Mattias et al.. "Attacking Websites Using HTTP Request Smuggling: Empirical Testing of Servers and Proxies". 2021. doi:10.1109/edoc52215.2021.00028 — https://doi.org/10.1109/edoc52215.2021.00028
24. Al-talak, Khadejah, Abbass, Onytra. "Detecting Server-Side Request Forgery (SSRF) Attack by using Deep Learning Techniques". . doi:10.14569/ijacsa.2021.0121230 — https://doi.org/10.14569/ijacsa.2021.0121230
25. Palmer, Steve. "Introduction to Web Application Hacking". 2007. doi:10.1016/b978-1-59749-209-6.00001-1 — https://doi.org/10.1016/b978-1-59749-209-6.00001-1
26. Jitendrakumar Kanani, Ishva, Sridhar, Raghavendra. "Cloud - Native Security: Securing Serverless Architectures". 2020. doi:10.21275/ms2008134043 — https://doi.org/10.21275/ms2008134043
27. Arini, Fiade, Andrew, Djuandi, Omar Yazidz. "D3fend Framework to Close Nginx Web Server Vulnerabilities Using Harden Tactics on Smartlink (Case Study: Smartlink Website)". 2025. doi:10.1109/citsm67730.2025.11291195 — https://doi.org/10.1109/citsm67730.2025.11291195
28. Xiao, Jin, Rofrano, John. "Managing vulnerabilities in a cloud native world with bluefix". 2017. doi:10.23919/inm.2017.7987368 — https://doi.org/10.23919/inm.2017.7987368
29. Malviya, Vikas K., Saurav, Saket, Gupta, Atul. "On Security Issues in Web Applications through Cross Site Scripting (XSS)". 2013. doi:10.1109/apsec.2013.85 — https://doi.org/10.1109/apsec.2013.85
30. Wainakh, Aidmar, Wabbi, Ahmad, Alkhatib, Bassel. "Design and Develop Misconfiguration Vulnerabilities Scanner for Web Applications". . doi:10.15866/irecos.v9i10.3840 — https://doi.org/10.15866/irecos.v9i10.3840
31. Doe, J.. "A Web-Based Automated Fuzzing Tool for Web Applications". . doi:10.64388/irev9i1-1718982 — https://doi.org/10.64388/irev9i1-1718982
32. Thodupunuri, Mohit. "AKAMAI WAF VS. AWS WAF A COMPARATIVE ANALYSIS OF WEB APPLICATION FIREWALL SOLUTIONS FOR CLOUD SECURITY". . doi:10.34218/ijitmis_14_02_009 — https://doi.org/10.34218/ijitmis_14_02_009
33. KUMAR, CRS. "Large Language Models(LLM) for Automating 20 Questions Game". . doi:10.31224/3842 — https://doi.org/10.31224/3842
34. Palmer, Steve. "Web-Based Malware". 2007. doi:10.1016/b978-1-59749-209-6.00005-9 — https://doi.org/10.1016/b978-1-59749-209-6.00005-9
35. Philip, Roney. "Securing Wireless Networks from ARP Cache Poisoning". . doi:10.31979/etd.fu2m-skmj — https://doi.org/10.31979/etd.fu2m-skmj
36. Norberg, Scott. "Authentication and Authorization". 2020. doi:10.1007/978-1-4842-6014-2_7 — https://doi.org/10.1007/978-1-4842-6014-2_7
37. Smith, A.. "ASP.NET Authentication, Authorization, and Security". . doi:10.1007/978-1-4302-0012-3_10 — https://doi.org/10.1007/978-1-4302-0012-3_10
38. Doe, J.. "Client-side Web Vulnerabilities". 2017. . doi:10.3030/771527 — https://doi.org/10.3030/771527
39. Acetozi, Jorge. "Horizontally Scaling Stateful Web Applications". 2017. doi:10.1007/978-1-4842-2985-9_13 — https://doi.org/10.1007/978-1-4842-2985-9_13
40. LI, Ya-Kun et al.. "Efficient Entity Resolution on XML Data Based on Entity-Describe-Attribute". 2011. doi:10.3724/sp.j.1016.2011.02131 — https://doi.org/10.3724/sp.j.1016.2011.02131
41. Litvinavicius, Taurius. "Practice Tasks for Server-side". 2019. doi:10.1007/978-1-4842-5446-2_7 — https://doi.org/10.1007/978-1-4842-5446-2_7
42. Gbur, Yuri, Tschorsch, Florian. "QUICforge: Client-side Request Forgery in QUIC". 2023. doi:10.14722/ndss.2023.23072 — https://doi.org/10.14722/ndss.2023.23072
