# Homelab CI/CD with Kubernetes — Architecture and Process Documentation

## 1. Project overview

This project implements a complete CI/CD pipeline that builds applications, publishes container images, and automates deployment to a Kubernetes cluster (k3s) running on a Lubuntu VM hosted on a Windows PC, following the **GitOps** pattern. All provisioning is done as code (Ansible), with no manual steps, ensuring full reproducibility.

**Portfolio goal:** demonstrate competency in infrastructure as code, Kubernetes, GitOps, pipeline security, and hybrid (Windows/Linux) environment integration.

---

## 2. Overall architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  GitHub (environments)                                          │
│  ├── app          (application source code)                     | 
│  └── manifests     (Kubernetes manifests / GitOps)              │
└───────────────┬───────────────────────────────────────────────┘
                │  push/PR
                ▼
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Actions (CI)                                            │
│  1. Checkout code                                                │
│  2. Automated tests                                              │
│  3. Build Docker image                                           │
│  4. Push to ghcr.io (GitHub Container Registry)                  │
│  5. Update image tag in repo-manifests                          │
└───────────────┬───────────────────────────────────────────────┘
                │  ArgoCD watches repo-manifests
                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Windows PC (physical host)                                     │
│  └── Lubuntu VM                                                 │
│        ├── k3s (Kubernetes cluster)                              │
│        │     ├── ArgoCD        → syncs and applies manifests    │
│        │     ├── ingress-nginx → HTTP/HTTPS routing              │
│        │     ├── cert-manager  → TLS certificates                │
│        │     └── production app (pods)                           │
│        └── Tailscale (secure private network)                    │
└─────────────────────────────────────────────────────────────────┘
                ▲
                │  SSH (via ed25519 key)
                │
┌─────────────────────────────────────────────────────────────────┐
│  Control Node (Ansible)                                         │
│  Windows + WSL2 (Ubuntu) — provisions and configures the VM      │
└─────────────────────────────────────────────────────────────────┘
```

**Summarized flow:** you (or a collaborator) run `git push` → GitHub Actions builds and publishes the image → updates the manifest → ArgoCD, running inside the cluster, detects the change and applies it automatically, without anyone needing to run `kubectl apply` manually.

---

## 3. Components and why each was chosen

| Component | Function | Why this choice |
|---|---|---|
| **WSL2 (Windows)** | Ansible control node | Ansible doesn't run natively on Windows; WSL2 is the standard industry solution |
| **Ansible** | Provisioning and configuration as code | Idempotent, agentless (only needs SSH), industry standard for server configuration |
| **k3s** | Lightweight Kubernetes distribution | Low resource consumption, ideal for 16GB of RAM, yet 100% compatible with the standard Kubernetes API |
| **Tailscale** | Private network between GitHub Actions and the VM | Avoids exposing ports on the router; encrypted peer-to-peer connection |
| **GitHub Actions** | CI engine | Free for repositories, native integration with ghcr.io |
| **ghcr.io** | Container image registry | Free, no need for self-hosted infrastructure |
| **ArgoCD** | GitOps (CD) engine | Industry standard; the cluster "pulls" changes instead of exposing external write access |
| **ingress-nginx** | HTTP/HTTPS traffic routing | Most widely used and documented ingress controller |
| **cert-manager** | Automatic TLS certificate issuance | Automates renewal, avoids manual certificates |

---

## 4. Repository structure

### 4.1. `homelab-infra` (provisioning)
```
homelab-infra/
├── README.md
├── ansible.cfg
├── inventory/
│   └── hosts.yml
├── group_vars/
│   └── all.yml
├── playbooks/
│   ├── site.yml
│   ├── 01-prereqs.yml
│   ├── 02-k3s-install.yml
│   ├── 03-argocd-install.yml
│   └── 04-tailscale.yml
└── roles/
    ├── k3s/
    ├── argocd/
    └── tailscale/
```

### 4.2. `repo-app` (application code)
```
app/
├── src/
├── Dockerfile
├── tests/
└── .github/
    └── workflows/
        └── ci.yml
```

### 4.3. `repo-manifests` (GitOps — desired cluster state)
```
manifests/
├── apps/
│   ├── base/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── kustomization.yaml
│   └── overlays/
│       └── production/
│           └── kustomization.yaml
└── argocd/
    └── application.yaml
```

**Why three separate repositories?** Separation of concerns — this is the recommended GitOps practice. The application code repository should not have direct write permissions to the cluster; only the manifests repository is watched by ArgoCD.

---

## 5. Complete step-by-step process

### Phase 1 — Environment preparation
1. Install WSL2 on the Windows host
2. Install Ansible inside WSL2
3. Generate an SSH key pair (`ed25519`) inside WSL2
4. Copy the public key to the Lubuntu VM (`ssh-copy-id`)
5. Validate passwordless SSH connectivity

### Phase 2 — VM provisioning (via Ansible)
1. Define the VM in `inventory/hosts.yml`
2. Run `01-prereqs.yml` — updates packages, disables swap (Kubernetes requirement)
3. Run `02-k3s-install.yml` — installs k3s as a single server, disabling the default `traefik` and `servicelb`
4. Run `03-argocd-install.yml` — creates the `argocd` namespace and applies the official manifest
5. Run `04-tailscale.yml` — connects the VM to the private Tailscale network
6. Fetch the generated `kubeconfig` and save it locally (outside of version control)

All of this triggered with a single command:
```bash
ansible-playbook -i inventory/hosts.yml playbooks/site.yml
```

### Phase 3 — ArgoCD configuration
1. Access ArgoCD (via `kubectl port-forward` or internal Ingress)
2. Register `repo-manifests` as the synchronization source
3. Create the ArgoCD `Application` resource pointing to `apps/overlays/production`
4. Enable `auto-sync` (automatic synchronization on every detected change in Git)

### Phase 4 — CI pipeline (GitHub Actions)
Workflow flow (`repo-app/.github/workflows/ci.yml`):
1. **Trigger:** push to the `main` branch or PR
2. **Checkout** the code
3. **Automated tests** (unit tests, lint)
4. **Build** the Docker image
5. **Vulnerability scan** (Trivy) before pushing — fails the pipeline if a critical CVE is found
6. **Push** the image to `ghcr.io/your-user/app:commit-sha`
7. **Automatic update** of the image tag in `repo-manifests` (via an automated commit made by Actions itself, using a token with permissions restricted to that repository only)

### Phase 5 — Continuous delivery (CD via ArgoCD)
1. ArgoCD detects the change in `repo-manifests` (polling or webhook)
2. Compares the desired state (Git) against the actual cluster state
3. Automatically applies the difference (internal `kubectl apply`, managed by ArgoCD)
4. ArgoCD dashboard shows status: `Synced` / `Healthy`

### Phase 6 — Observation and validation
1. Check rollout: `kubectl rollout status deployment/app`
2. Access the application via Ingress (internal domain or Tailscale)
3. Validate the TLS certificate issued by cert-manager
4. Check logs and events: `kubectl logs`, `kubectl get events`

---

## 6. Pipeline security (highlights for the portfolio)

- **No cluster credentials are ever exposed publicly** — ArgoCD pulls changes from the inside out; there's no need to open write ports to the internet
- **SSH keys are never committed to version control** — protected via `.gitignore` and, in a real production setup, stored in a secrets vault (e.g., GitHub Secrets, Vault)
- **Vulnerability scanning (Trivy)** runs before any image reaches the registry
- **GitHub Actions tokens with minimal permissions** (principle of least privilege) — the token that updates `repo-manifests` only has write access to that specific repository
- **Tailscale** replaces direct exposure of SSH/K8s ports to the internet

---

## 7. Known limitations and architecture decisions

- **Cluster is not 24/7:** the VM is only active when the PC is powered on. This is documented as a conscious choice ("ephemeral infrastructure, provisioned on demand"), not a hidden limitation
- **Single-node k3s:** there is no real high availability; the project's focus is to demonstrate the CI/CD and GitOps flow, not cluster resilience (this can be evolved later with multiple nodes)
- **No fixed public domain:** internal TLS certificates (via `mkcert`) or restricted access via Tailscale, since there is no stable public IP

---

## 8. Possible next steps (project evolution)

1. Add observability (Prometheus/Grafana or VictoriaMetrics)
2. Add runtime security policies (Kyverno)
3. Expand to multi-node (more VMs on the same machine, if resources allow)
4. Simulate incidents with Chaos Mesh and document recovery time
5. Write an operations runbook and a simulated post-mortem

---

## 9. Quick glossary

- **CI (Continuous Integration):** automation of code build, testing, and packaging
- **CD (Continuous Delivery/Deployment):** automation of delivering the application to the target environment
- **GitOps:** a practice where Git is the single source of truth for infrastructure state; an agent (ArgoCD) syncs the cluster with what is described in the repository
- **Idempotency:** the property of an operation that produces the same result no matter how many times it is executed
- **Ingress:** a Kubernetes resource that manages external access to services, typically via HTTP/HTTPS
