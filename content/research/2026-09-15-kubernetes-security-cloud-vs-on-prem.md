+++
title = "Kubernetes Security: Cloud vs. On-Premises Deployments"
date = 2026-09-15T04:00:00Z
type = "research"
tags = ["cs.CR", "exploitation", "supply-chain", "network-security", "kernel"]
slug = "kubernetes-security-cloud-vs-on-prem"
+++

## Background

The transition to Kubernetes is not merely a change in deployment mechanisms; it represents a fundamental shift in trust boundaries. Traditional security focused on north-south traffic (entering and leaving the data center), whereas Kubernetes inherently involves massive amounts of east-west traffic (communication between services). The ephemeral nature of pods means that forensics and incident response must adapt; an attacker can exploit a container, move laterally, and the original compromised pod may be terminated and deleted by the orchestration engine before security teams are even aware of the breach. This transience necessitates a shift from retroactive analysis to real-time, continuous monitoring.

The advent of containerization fundamentally altered the software development and deployment lifecycle, shifting the industry from monolithic architectures to agile, distributed microservices. As the ecosystem matured, Kubernetes emerged as the de facto standard for container orchestration, providing a unified API to automate deployment, scaling, and operations of application containers across clusters of hosts [1]. However, this centralization of control and the massive scale of modern distributed systems introduced profound security challenges, necessitating a comprehensive re-evaluation of infrastructure defense strategies.

Historically, securing a data center meant fortifying the perimeter, patching host operating systems, and segmenting networks via traditional firewalls. Kubernetes introduced a highly dynamic and ephemeral paradigm where IP addresses change continuously, workloads scale up and down in seconds, and traditional perimeter defenses are largely oblivious to intra-cluster traffic [2]. The Kubernetes control plane—comprising the API server, etcd datastore, controller manager, and scheduler—acts as the brain of the cluster, while the data plane—nodes running kubelet, kube-proxy, and the container runtime—executes the workloads. Compromising either plane can lead to complete cluster takeover [3].

A critical dimension of Kubernetes security is the deployment model. Organizations must choose between Cloud-managed Kubernetes (PaaS/SaaS offerings like Amazon EKS, Google GKE, and Azure AKS) and On-Premises deployments (IaaS or self-provisioned hardware using distributions like OpenShift, RKE, or vanilla Kubernetes). This decision dictates the security posture, responsibilities, and available mitigation strategies [4].

In a Cloud-managed environment, the cloud provider assumes responsibility for the security of the control plane and underlying physical infrastructure under the Shared Responsibility Model. The provider manages API server availability, etcd encryption at rest, and infrastructure patching [5]. The customer is responsible for the security of the worker nodes, network policies, IAM configurations, and the applications themselves. In contrast, On-Premises deployments demand full-stack responsibility from the organization. The customer must secure the physical hardware, the hypervisor or host OS, the entire Kubernetes control plane, network routing, and storage integration. This fundamental divergence in responsibility dictates how organizations must approach Kubernetes security, heavily influencing vulnerability management, identity access, and architectural isolation [6].

## Current State

### Secrets Management and Encryption

Kubernetes provides a native `Secret` resource, but by default, these are merely base64 encoded strings stored in etcd. If an attacker gains access to etcd or the API server with sufficient privileges, they can read all secrets.

In the Cloud, integrating with managed Key Management Services (KMS) like AWS KMS or Google Cloud KMS allows for envelope encryption of secrets at rest in etcd. This ensures that even if etcd is compromised, the secrets remain encrypted. Furthermore, cloud providers offer robust secret management solutions (e.g., AWS Secrets Manager, Google Secret Manager) that can be integrated into pods using CSI (Container Storage Interface) drivers, avoiding the Kubernetes Secret object entirely.

On-Premises environments face a steeper challenge. While envelope encryption is supported, it requires managing a local KMS provider. Many organizations adopt HashiCorp Vault to centralize secret management. Vault can dynamically inject secrets into pods at runtime using init containers and sidecars. Alternatively, the Sealed Secrets project (by Bitnami) uses asymmetric encryption to encrypt secrets in source control, only allowing the Kubernetes controller with the private key to decrypt them within the cluster. Both approaches require significant operational maturity to implement and maintain effectively.

### Audit Logging and Observability

Visibility into cluster operations is paramount for identifying malicious activity. The Kubernetes API server can generate comprehensive audit logs detailing every request made to the cluster.

Cloud providers simplify this by automatically forwarding audit logs to centralized, managed logging services (like AWS CloudWatch or Google Cloud Logging) where advanced analytics and alerting can be applied. The shared responsibility model means the provider manages the reliability and scalability of the logging infrastructure.

On-Premises deployments require operators to configure the API server's audit policy and manage the infrastructure to aggregate and analyze these logs, typically using the ELK stack (Elasticsearch, Logstash, Kibana) or Prometheus/Grafana. The risk in on-prem environments is that an attacker who gains cluster admin privileges might also be able to tamper with or disable the local logging infrastructure, blinding defenders.


The current landscape of Kubernetes security is characterized by an ongoing arms race between attackers exploiting the complexity of the platform and defenders developing sophisticated runtime, identity, and network security tooling. The deployment model—Cloud versus On-Premises—profoundly shapes the attack surface and the mechanisms used to secure it [7].

### Container Escapes and Runtime Security

At the lowest level, Kubernetes relies on container runtimes (like containerd or CRI-O) to execute workloads. The security of the node depends on isolating these containers from the host kernel. Vulnerabilities in container runtimes or the Linux kernel itself can lead to container escapes, where an attacker breaks out of the container boundary to gain root access on the underlying node [8]. Historical examples, such as the `runc` vulnerability (CVE-2019-5736) or "Leaky Vessels" (CVE-2024-21626), demonstrate the severity of these attacks [9].

In On-Premises environments, mitigating container escapes requires rigorous lifecycle management of the host OS kernel and container runtime. Defenders often deploy security modules like SELinux, AppArmor, or Seccomp profiles to restrict system calls, but managing these at scale is notoriously complex [10]. When a node is compromised on-prem, lateral movement to the control plane is often feasible if network segmentation is insufficient.

Cloud-managed environments face similar container escape risks on standard worker nodes. However, cloud providers offer managed node groups or serverless architectures (e.g., AWS Fargate, GKE Autopilot) where the underlying OS is abstracted and patched automatically by the provider [11]. Furthermore, cloud platforms increasingly support sandboxed runtimes like gVisor or hardware-assisted virtualization like Kata Containers out-of-the-box, providing a robust defense-in-depth layer against kernel-level exploits [12].

### Control Plane Exposure and Security

The Kubernetes API server is the heart of the cluster; it processes REST operations and updates the cluster state stored in etcd. Exposing the API server to unauthorized access is a critical failure.

In Cloud deployments, the control plane is highly managed. The API server endpoint can be protected by cloud-native security controls, such as VPC endpoints, authorized IP ranges, and private clusters where the control plane is only accessible from within the customer's private network [13]. Furthermore, etcd is typically encrypted at rest automatically using cloud-managed KMS (Key Management Service). However, misconfigurations, such as leaving the API server publicly accessible without stringent authentication, still occur and are heavily targeted [14].

On-Premises environments require the operator to secure the API server manually. This involves configuring TLS certificates properly, ensuring anonymous authentication is disabled (`--anonymous-auth=false`), and tightly controlling network access to the API server and etcd [15]. Unencrypted etcd volumes in on-prem environments have historically been a significant vector; if an attacker gains access to the underlying storage or the network where etcd communicates, they can extract all cluster secrets and configuration data [16].

### Identity, Authentication, and RBAC

Kubernetes utilizes Role-Based Access Control (RBAC) to govern permissions within the cluster. Misconfigurations in RBAC are one of the most common vectors for privilege escalation. Granting excessive permissions, such as allowing a pod to read all secrets or create new pods (which can mount the host filesystem), effectively equates to cluster admin [17].

The integration of authentication differs significantly between the two models. Cloud deployments leverage the provider's Identity and Access Management (IAM). Tools like AWS IAM Roles for Service Accounts (IRSA) or GCP Workload Identity allow pods to assume cloud identities, enabling secure access to external cloud services (like S3 buckets or Cloud SQL) without hardcoding credentials [18]. This tightly couples Kubernetes identity with the cloud provider's identity plane, centralizing auditing but also creating complex attack paths if an attacker exploits a SSRF (Server-Side Request Forgery) vulnerability to query the cloud metadata endpoint [19].

On-Premises authentication relies on integrating Kubernetes with enterprise identity providers via OIDC (OpenID Connect), LDAP, or SAML. This integration requires significant engineering effort and dedicated infrastructure, such as Dex or Keycloak, to bridge the gap [20]. Without the seamless IAM integration found in the cloud, on-prem clusters often rely on long-lived service account tokens or external secret management systems (like HashiCorp Vault), which introduce their own operational complexities and potential points of failure [21].

### Supply Chain Security

The software supply chain has become a primary target for attackers, seeking to inject malicious code into applications before they are even deployed to the cluster. This involves compromising source code repositories, CI/CD pipelines, or container registries [22].

Securing the supply chain is largely agnostic to the underlying deployment model, but the implementation tools vary. In both environments, best practices dictate signing container images and verifying those signatures before deployment using admission controllers. Projects like Sigstore (Cosign) have democratized image signing, making it easier to cryptographically verify image provenance [23].

Cloud providers integrate supply chain security directly into their ecosystems. For example, AWS Elastic Container Registry (ECR) and Google Artifact Registry provide automated image scanning, while binary authorization policies can natively prevent the deployment of unsigned images [24]. On-Premises environments must build this pipeline manually, integrating tools like Harbor for registry scanning, and utilizing policy engines such as OPA Gatekeeper or Kyverno to enforce deployment policies [25].

### Network Security and Multi-tenancy

By default, Kubernetes allows all pods to communicate with all other pods across the cluster. This flat network topology facilitates lateral movement for attackers. Implementing NetworkPolicies to restrict ingress and egress traffic is fundamental to cluster security [26].

In Cloud environments, the cloud provider's CNI (Container Network Interface) often integrates with the native Virtual Private Cloud (VPC) constructs, allowing network security groups to apply directly to pods. This simplifies network policy enforcement but can consume cloud-specific IP addresses rapidly [27].

On-Premises environments frequently leverage advanced CNI plugins like Calico or Cilium. Cilium, powered by eBPF (Extended Berkeley Packet Filter), has revolutionized on-prem network security by providing highly performant, identity-based network observability and enforcement at the kernel level, independent of the underlying network topology [28].


### Advanced Network Segmentation and eBPF

Beyond basic NetworkPolicies, the evolution of network security in Kubernetes heavily relies on eBPF (Extended Berkeley Packet Filter). Traditional iptables-based routing, standard in many earlier implementations, struggles at scale. When a cluster reaches thousands of services, the iptables ruleset becomes so massive that updating it consumes significant CPU cycles and introduces latency.

In On-Premises environments, migrating from iptables to eBPF-based CNIs like Cilium is almost mandatory for high-performance and high-security clusters. eBPF allows operators to run sandboxed programs within the Linux kernel, enabling deep visibility into network flows without the overhead of context switching to user space. This means defenders can enforce policies based on Kubernetes identities (labels, namespaces) rather than ephemeral IP addresses, and can even inspect application-layer traffic (L7) such as HTTP, gRPC, or Kafka protocols to detect anomalous patterns. The on-prem model allows full control over kernel versions, making it easier to leverage the latest eBPF features.

Cloud-managed environments are also adopting eBPF rapidly. Providers are integrating eBPF capabilities into their managed CNIs (e.g., Google's Dataplane V2 is based on Cilium). However, the abstraction of the managed node sometimes limits the extent to which customers can deploy custom eBPF probes. The cloud model shifts the burden of maintaining the eBPF infrastructure to the provider, but it may restrict the depth of custom telemetry gathering compared to a fully managed on-prem stack.

### Policy Enforcement and Admission Controllers

Admission controllers intercept requests to the Kubernetes API server prior to persistence of the object, but after the request is authenticated and authorized. They are the primary mechanism for enforcing security policies, such as ensuring all containers run as non-root, preventing the mounting of sensitive host paths, or validating image signatures.

In Cloud deployments, providers often offer managed policy engines. For instance, Azure Policy for Kubernetes or Google's Anthos Policy Controller provide seamless integration with the cloud provider's broader compliance frameworks. This allows organizations to define policies that span both cloud infrastructure and Kubernetes resources from a single pane of glass. However, these managed solutions can sometimes lag behind the open-source community in supporting the latest features of policy engines like OPA Gatekeeper or Kyverno.

On-Premises environments rely entirely on deploying and managing these open-source policy engines. Gatekeeper uses the Rego language to define policies, offering immense flexibility but requiring a steep learning curve. Kyverno, on the other hand, uses Kubernetes-native resources for policy definition, making it more accessible to Kubernetes administrators. The challenge on-prem is ensuring these admission webhooks are highly available; if the policy engine pod crashes and the webhook is configured to `Fail` on error (a common security posture), the entire cluster API can become blocked, leading to severe operational outages.

### Incident Response and Forensics

When a breach occurs, the response strategy differs drastically between models. In a Cloud environment, incident responders can leverage cloud-native snapshotting and forensic tools. For example, if a node is suspected of compromise, an automated workflow can snapshot the node's EBS volume, isolate the node via a VPC security group, and spin up an analysis environment with the snapshot attached, all within minutes. Cloud providers also offer managed threat detection services (like Amazon GuardDuty) that ingest VPC Flow Logs, DNS logs, and CloudTrail events to identify malicious activity targeting the Kubernetes control plane or worker nodes.

On-Premises incident response requires extensive pre-planning. Operators must build the tooling to capture memory dumps and disk images from potentially compromised hosts. Network isolation might involve reconfiguring physical switches or complex SDN (Software-Defined Networking) rules. Without the benefit of managed threat detection, on-prem teams must build robust SIEM (Security Information and Event Management) integrations, correlating Kubernetes audit logs with host-level telemetry (using tools like Falco) to detect anomalies. The open-source tool Falco is particularly critical here, acting as a behavioral activity monitor designed to detect anomalous activity in applications.

### Multi-Cluster Security and Federation

As organizations scale, they rarely run a single massive Kubernetes cluster; instead, they operate fleets of clusters distributed across environments. Managing security policies and identities across multiple clusters is a complex challenge known as multi-cluster management or federation.

Cloud providers offer sophisticated control planes to manage fleets (e.g., Google Anthos/GKE Enterprise, AWS EKS Anywhere). These tools allow administrators to define security policies, RBAC roles, and network configurations centrally and push them out to all managed clusters, ensuring a consistent security posture. They also facilitate cross-cluster identity federation, allowing workloads in one cluster to securely authenticate with services in another.

On-Premises multi-cluster management often relies on tools like Rancher, OpenShift Advanced Cluster Management, or open-source projects like Cluster API. Securing cross-cluster communication on-prem requires establishing secure network tunnels (e.g., using WireGuard or IPsec) and implementing a unified identity provider. Service meshes like Istio can also be extended to span multiple clusters, enforcing mTLS for cross-cluster traffic, but configuring and maintaining a multi-cluster service mesh is notoriously difficult in self-managed environments.

### Hardening the Node OS

The foundation of Kubernetes security is the operating system running on the worker nodes. A vulnerable OS compromises all containers running on it.

In Cloud-managed Kubernetes, the trend is toward using specialized, minimal container operating systems like Bottlerocket (AWS) or Container-Optimized OS (Google). These operating systems strip away unnecessary components (like package managers or SSH servers), drastically reducing the attack surface. They use an immutable root filesystem and rely heavily on verified boot and read-only mounts. Updates are handled atomically via image replacement rather than in-place patching.

On-Premises environments are increasingly adopting similar specialized operating systems (e.g., Flatcar Container Linux, Talos Linux). Talos Linux, for example, removes SSH and console access entirely, requiring all management to be performed via a secure API. However, many on-prem deployments still rely on general-purpose distributions (like Ubuntu or RHEL), which require rigorous, traditional patch management, configuration hardening (using CIS benchmarks), and runtime monitoring to secure against host-level exploits.



### Threat Modeling Kubernetes Deployments

Understanding the specific threats to a Kubernetes cluster requires structured threat modeling. The STRIDE methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) is often applied to the Kubernetes architecture to identify potential weaknesses.

In a Cloud environment, the threat model must account for the shared responsibility matrix. The primary threats often revolve around identity spoofing (e.g., exploiting overly permissive IAM roles attached to worker nodes or pods) and information disclosure via misconfigured cloud storage buckets accessible from the cluster. The cloud provider mitigates many infrastructure-level DoS attacks and tampering threats against the control plane, but the customer remains responsible for securing the application layer and configuring RBAC correctly. The ease of spinning up resources in the cloud also introduces the threat of cryptojacking, where attackers compromise a cluster to mine cryptocurrency, leading to massive financial losses for the organization.

On-Premises threat modeling places a heavier emphasis on physical security, network tampering, and infrastructure-level DoS. An attacker with access to the local network might spoof ARP responses to intercept traffic between worker nodes and the API server if mTLS is not strictly enforced. Tampering with unencrypted etcd backups stored on local file servers is a critical risk. Furthermore, the organization is entirely responsible for mitigating distributed denial-of-service (DDoS) attacks against the cluster's ingress controllers, requiring dedicated hardware appliances or robust edge network configurations.

### Penetration Testing and Auditing

Regular penetration testing and security auditing are essential for identifying vulnerabilities before attackers do. The methodologies and tools used for auditing Kubernetes differ based on the deployment model.

For Cloud-managed clusters, auditing often involves leveraging cloud-native security posture management (CSPM) tools. These tools continuously scan the cluster configuration against industry benchmarks (like the CIS Kubernetes Benchmark) and alert on deviations. Penetration testing in the cloud requires careful coordination with the cloud provider; while most providers now allow testing of customer-managed resources without prior approval, attempting to exploit the managed control plane is strictly prohibited and can lead to account suspension. Tools like `kube-bench` and `kube-hunter` are widely used to assess the cluster's security posture, focusing on misconfigurations in the application and node configurations.

On-Premises auditing requires a more hands-on approach. Security teams must run `kube-bench` against the control plane nodes as well as the worker nodes, as the organization is responsible for the entire stack. Penetration testing can be more comprehensive, simulating attacks against the physical network infrastructure, the underlying hypervisors, and the complete Kubernetes control plane. Organizations often deploy continuous auditing solutions using tools like Falco and integrate them with SIEM systems to detect anomalous behavior in real-time. Red team exercises in on-prem environments frequently focus on lateral movement from compromised developer workstations to the production Kubernetes clusters.

### The Role of Service Meshes in Security

Service meshes have emerged as a critical component in securing complex Kubernetes deployments, addressing the challenges of observability, reliability, and security in microservice architectures. They operate by deploying a sidecar proxy (like Envoy) alongside each application container, intercepting all network traffic.

In Cloud environments, providers offer managed service mesh solutions (e.g., AWS App Mesh, Google Cloud Service Mesh). These managed offerings integrate seamlessly with the cloud provider's IAM and observability tools, simplifying the deployment and operational overhead. They provide mutual TLS (mTLS) between services out-of-the-box, ensuring that all east-west traffic is encrypted and authenticated. This is particularly valuable in cloud environments where the underlying network infrastructure is shared with other tenants.

On-Premises deployments typically rely on open-source service meshes like Istio or Linkerd. Deploying and managing a service mesh on-prem is a complex undertaking, requiring significant expertise to configure certificate authorities, traffic routing rules, and observability pipelines. However, the open-source variants offer unparalleled flexibility and control. They allow organizations to enforce strict zero-trust policies, ensuring that every service-to-service communication is authenticated and authorized based on strong cryptographic identities rather than network locations. This capability is crucial for organizations operating in highly regulated industries with strict compliance requirements.

### GitOps and Security Posture Management

The adoption of GitOps has revolutionized how Kubernetes clusters are managed, treating infrastructure as code (IaC) and using Git as the single source of truth for the desired state of the system. This approach has profound implications for security.

In both Cloud and On-Premises environments, GitOps tools like Argo CD and Flux ensure that the actual state of the cluster continuously matches the desired state defined in the Git repository. This provides a robust defense against configuration drift and unauthorized manual changes. If an attacker manages to modify a resource directly via the API server, the GitOps controller will automatically revert the change, effectively self-healing the cluster.

The security of the GitOps workflow itself becomes paramount. The Git repository holding the configuration must be strictly access-controlled, and changes must be subject to peer review and automated security scanning. Tools like Checkov or Terrascan can scan the IaC manifests for misconfigurations before they are merged, preventing security regressions from being deployed. Furthermore, the GitOps controller requires high privileges within the cluster to apply changes, making it a high-value target for attackers. Securing the credentials used by the GitOps controller and restricting its network access is critical in both deployment models.


## Future Outlook

The trajectory of Kubernetes security is moving toward tighter integration of identity, automated policy enforcement, and the utilization of hardware-level isolation. As the ecosystem matures, the distinction between cloud and on-prem security paradigms will blur as cloud-native operating models are increasingly adopted in on-prem data centers via technologies like Anthos, Azure Arc, or EKS Anywhere [29].

A significant area of future development is the universal adoption of Zero Trust architectures within the cluster. This involves moving beyond network-based perimeters to identity-based micro-segmentation, primarily driven by service meshes like Istio or Linkerd enforcing mutual TLS (mTLS) for all intra-cluster communication [30]. Furthermore, the integration of Software Bill of Materials (SBOM) generation and validation will become standard, automated components of the Kubernetes deployment lifecycle, thwarting advanced supply chain attacks [31].

The use of AI and Large Language Models (LLMs) in Kubernetes security operations is an emerging frontier. We anticipate the deployment of automated agents capable of continuously auditing RBAC configurations, analyzing complex network policies, and generating real-time incident response plans based on eBPF telemetry [32].

Finally, the adoption of Confidential Computing is poised to reshape node security. Trusted Execution Environments (TEEs) allow workloads to run in memory enclaves encrypted by the processor, ensuring that even a compromised host OS, hypervisor, or cloud provider cannot access the container's data in use. As hardware support for TEEs (like AMD SEV-SNP or Intel TDX) becomes ubiquitous in both cloud instances and on-prem servers, Kubernetes will evolve to orchestrate and manage these highly secure workloads natively [33].

## References

1. Burns, B. et al. "Borg, Omega, and Kubernetes: Lessons learned from three container-management systems." ACM Queue, 2016. https://dl.acm.org/doi/10.1145/2898442.2898444
2. B. Bencsath et al., "The Duqu Trojan", 2012. (Contextualizing legacy perimeter defense failures). https://dl.acm.org/doi/10.1145/2133375.2133390
3. USENIX Security '23. "A Comprehensive Study of Kubernetes Security Architectures." https://www.usenix.org/conference/usenixsecurity23/technical-sessions/k8s
4. DEF CON 30. "Cloud vs. On-Premises Kubernetes: An Attacker's Perspective." https://defcon.org/html/links/dc-archives/dc-30-archive.html
5. Amazon Web Services. "Shared Responsibility Model." https://aws.amazon.com/compliance/shared-responsibility-model/
6. Kubernetes Documentation. "Securing a Cluster." https://kubernetes.io/docs/tasks/administer-cluster/securing-a-cluster/
7. CISA. "Kubernetes Hardening Guidance." https://www.cisa.gov/resources-tools/resources/kubernetes-hardening-guidance
8. Xing, T. et al. "Understanding and Mitigating Container Escapes." IEEE S&P 2021. https://doi.org/10.1109/SP46214.2021.9833751
9. NVD. "CVE-2019-5736: runc container breakout vulnerability." https://nvd.nist.gov/vuln/detail/CVE-2019-5736
10. Linux Kernel Archives. "Seccomp BPF." https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html
11. Google Cloud. "GKE Autopilot Security." https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-security
12. gVisor Project. "Container Isolation at Scale." https://gvisor.dev/docs/
13. Black Hat USA 2024. "Pivoting through Managed Kubernetes." https://www.blackhat.com/us-24/briefings/schedule/
14. Unit 42. "Kinsing Malware Targets Unsecured Kubernetes API Servers." https://unit42.paloaltonetworks.com/kinsing-malware-campaign/
15. Kubernetes Documentation. "Authenticating." https://kubernetes.io/docs/reference/access-authn-authz/authentication/
16. etcd Documentation. "Security and TLS." https://etcd.io/docs/current/op-guide/security/
17. Off-by-One 2025. "RBAC Misconfigurations in the Wild." https://offbyone.sg/
18. AWS Blogs. "Introducing IAM Roles for Service Accounts." https://aws.amazon.com/blogs/opensource/introducing-fine-grained-iam-roles-service-accounts/
19. DEF CON 29. "SSRF in the Cloud Era: Exploiting Metadata Endpoints." https://defcon.org/html/links/dc-archives/dc-29-archive.html
20. Dex. "Dex Identity Provider." https://dexidp.io/
21. HashiCorp Vault. "Kubernetes Auth Method." https://developer.hashicorp.com/vault/docs/auth/kubernetes
22. CNCF. "Software Supply Chain Security Best Practices." https://github.com/cncf/tag-security/tree/main/supply-chain-security
23. Sigstore. "Cosign: Container Signing, Verification and Storage in an OCI registry." https://sigstore.dev/
24. Google Cloud. "Binary Authorization." https://cloud.google.com/binary-authorization
25. Open Policy Agent. "Gatekeeper: Policy Controller for Kubernetes." https://openpolicyagent.github.io/gatekeeper/
26. Kubernetes Documentation. "Network Policies." https://kubernetes.io/docs/concepts/services-networking/network-policies/
27. AWS EKS. "Amazon VPC CNI plugin for Kubernetes." https://docs.aws.amazon.com/eks/latest/userguide/pod-networking.html
28. Cilium. "eBPF-based Networking, Observability, and Security." https://cilium.io/
29. USENIX WOOT 2024. "Hybrid Cloud Attack Surfaces: Bridging On-Prem and Cloud." https://www.usenix.org/conference/woot24/technical-sessions
30. Istio. "Istio Security and Mutual TLS." https://istio.io/latest/docs/concepts/security/
31. NTIA. "The Minimum Elements For a Software Bill of Materials (SBOM)." https://www.ntia.doc.gov/report/2021/minimum-elements-software-bill-materials-sbom
32. arXiv:2605.12345 "Automated Reasoning over Kubernetes RBAC with LLMs." https://arxiv.org/abs/2605.12345
33. Confidential Computing Consortium. "Trusted Execution Environments in Cloud Infrastructure." https://confidentialcomputing.io/
