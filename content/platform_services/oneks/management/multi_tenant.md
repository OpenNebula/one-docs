---
title: "Multi-tenant Access to OneKS Elastic Kubernetes Clusters"
linkTitle: "Multi-tenant Access"
date: "2026-09-07"
description:
categories:
tags:
type: docs
weight: "6"
---

This guide describes recommended practices for providing multiple users or teams with controlled access to a shared Kubernetes Cluster deployed with **OpenNebula Elastic Kubernetes Service (OneKS)**.

The guidelines described in this guide assume that:

* OneKS has been installed and configured.  
* The Kubernetes Cluster has been created and reached the `RUNNING` state.  
* The Kubernetes administrator has retrieved the administrative kubeconfig.  
* Kubernetes API access has been verified.

The administrative kubeconfig retrieved from OneKS provides privileged access to the Kubernetes Cluster and should remain under the control of the Kubernetes administrator. It **should not** be distributed to application teams or tenant users.

Instead, each tenant should authenticate using a dedicated identity and receive only the Kubernetes permissions required to operate its workloads.

OneKS Cluster lifecycle operations remain a separate administrative responsibility. Creating or scaling node groups, upgrading the Kubernetes Cluster, recovering failed operations, and deleting the Cluster are performed through OneKS and depend on the user's OneKS and OpenNebula permissions.

## Multi-Tenant Access Model

A recommended shared-cluster model separates responsibilities as outlined in the following table:

| **Operation** | **OneKS / K8s Operator** | **Tenant User** |
| :---- | :---- | :---- |
| Retrieve administrative kubeconfig | Yes | No |
| Manage Kubernetes nodes | Yes | No  |
| Create/delete namespaces | Yes | No |
| Install CRDs or Cluster-wide operators | Yes | No |
| Manage ClusterRoles and ClusterRoleBindings | Yes | No |
| Manage tenant RBAC | Yes | No |
| Configure ResourceQuotas and LimitRanges | Yes | No |
| Configure tenant isolation policies | Yes | No |
| Deploy workloads in assigned namespace | Yes | Yes |
| Manage Services and ConfigMaps in assigned namespace | Yes | Yes |
| Manage application Secrets, if permitted | Yes | Yes |
| Create PersistentVolumeClaims | Yes | Yes |
| Access another tenant's namespace | Yes | No |
| Modify Cluster-wide storage or networking | Yes | No |
| Scale OneKS node groups | Yes | No, unless separately authorized in OneKS |
| Upgrade or delete the OneKS Cluster | Yes | No, unless separately authorized in OneKS |

Kubernetes recommends assigning permissions at namespace scope whenever possible and using `RoleBinding` instead of `ClusterRoleBinding` for tenant access. Cluster-wide resources should remain accessible only to privileged administrators.

## Example Scenario

Consider a OneKS Kubernetes Cluster shared by two teams:

`OneKS Kubernetes Cluster`

* `kube-system`  
  * `Operator managed`  
* `tenant-acme`  
  * `ACME developers`  
* `tenant-beta`  
  * `BETA developers`


The administrator keeps the OneKS administrative kubeconfig:

```
admin.conf
```

Tenant users receive independent credentials:

```
alice-acme.conf
bob-acme.conf
carol-beta.conf
```

Alice and Bob can manage applications in `tenant-acme`. 

Carol can manage applications in `tenant-beta`.

**None** of these users should be able to list nodes, change Cluster-wide RBAC, modify resources belonging to another tenant, or perform OneKS lifecycle operations.

### 1\. Create a Namespace for the Tenant

Create one or more namespaces for each tenant instead of placing tenant workloads in `default`. For example:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tenant-acme
  labels:
    tenant.opennebula.io/name: acme
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

Apply it using the administrative kubeconfig:

```shell
kubectl --kubeconfig admin.conf apply -f tenant-acme-namespace.yaml
```

Namespaces provide the primary Kubernetes API resource boundary for this shared-cluster model. Kubernetes recommends combining namespaces with RBAC and additional security controls rather than treating namespaces alone as sufficient isolation.

The `restricted` Pod Security Standard prevents many workload configurations that are inappropriate for untrusted tenant applications, including privileged containers and several mechanisms for accessing the underlying Host.

### 2\. Define a Tenant Role

Avoid granting tenants `cluster-admin`.

Avoid adding tenant users to `system:masters`. Membership in `system:masters` bypasses normal RBAC restrictions and provides unrestricted superuser access.

Instead, define the exact API resources that a tenant needs. For example:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: tenant-developer
  namespace: tenant-acme
rules:

# Application workloads
- apiGroups: ["apps"]
  resources:
    - deployments
    - statefulsets
  verbs:
    - get
    - list
    - watch
    - create
    - update
    - patch
    - delete

# ReplicaSets are normally controlled by Deployments.
- apiGroups: ["apps"]
  resources:
    - replicasets
  verbs:
    - get
    - list
    - watch

# Batch workloads
- apiGroups: ["batch"]
  resources:
    - jobs
    - cronjobs
  verbs:
    - get
    - list
    - watch
    - create
    - update
    - patch
    - delete

# Pods and logs
- apiGroups: [""]
  resources:
    - pods
    - pods/log
  verbs:
    - get
    - list
    - watch

# Interactive troubleshooting
- apiGroups: [""]
  resources:
    - pods/exec
    - pods/portforward
  verbs:
    - create

# Application configuration
- apiGroups: [""]
  resources:
    - configmaps
    - secrets
  verbs:
    - get
    - list
    - watch
    - create
    - update
    - patch
    - delete

# Services
- apiGroups: [""]
  resources:
    - services
  verbs:
    - get
    - list
    - watch
    - create
    - update
    - patch
    - delete

# Persistent storage claims
- apiGroups: [""]
  resources:
    - persistentvolumeclaims
  verbs:
    - get
    - list
    - watch
    - create
    - update
    - patch
    - delete

# Tenant ServiceAccounts. No RBAC binding permissions are granted.
- apiGroups: [""]
  resources:
    - serviceaccounts
  verbs:
    - get
    - list
    - watch
    - create
    - update
    - patch
    - delete

# Application ingress
- apiGroups: ["networking.k8s.io"]
  resources:
    - ingresses
  verbs:
    - get
    - list
    - watch
    - create
    - update
    - patch
    - delete

# Horizontal Pod Autoscalers
- apiGroups: ["autoscaling"]
  resources:
    - horizontalpodautoscalers
  verbs:
    - get
    - list
    - watch
    - create
    - update
    - patch
    - delete

# Events for troubleshooting
- apiGroups: [""]
  resources:
    - events
  verbs:
    - get
    - list
    - watch
```

Apply it:

```shell
kubectl --kubeconfig admin.conf apply -f tenant-acme-role.yaml
```

This Role intentionally does **not** grant access to:

```
namespaces
nodes
persistentvolumes
storageclasses
customresourcedefinitions
clusterroles
clusterrolebindings
roles
rolebindings
resourcequotas
limitranges
networkpolicies
```

It also does not grant wildcard access to additional API groups. Therefore, Cluster API resources or other CRDs installed in the Cluster do not automatically become accessible to the tenant. Avoid rules such as:

```
apiGroups: ["*"]
resources: ["*"]
verbs: ["*"]
```

Wildcard permissions are particularly dangerous because they can automatically include API resources added to the Cluster in the future.

{{< alert title="Important Consideration for Secrets" color="primary" >}}A user allowed to create arbitrary Pods, Deployments, or similar workload resources should effectively be considered capable of accessing Secrets available to workloads in that namespace, even when direct `get secrets` permission is removed.

For example, a user could create a Pod that mounts an existing Secret. For this reason, **do not place privileged platform credentials or highly privileged ServiceAccounts inside tenant namespaces**. Kubernetes explicitly identifies workload creation as a potential privilege-escalation path within a namespace.{{< /alert >}} 

### 3\. Bind the Role to a Tenant Group

Permissions should preferably be assigned to groups rather than individually to every user.

For example, using the following tenant group name:

```yaml
oneks:tenant-acme:developers
```

Kubernetes does not provide Group objects to create. Group membership is supplied by the configured authentication mechanism. For OIDC, configure the identity provider and Kubernetes group-claim mapping so that the resulting group name, including any configured prefix, matches the RoleBinding subject below. For client certificates, the group name is included in the certificate subject’s organization (O) field.

Bind this group to the tenant Role:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: tenant-acme-developers
  namespace: tenant-acme
subjects:
- kind: Group
  name: oneks:tenant-acme:developers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: tenant-developer
  apiGroup: rbac.authorization.k8s.io
```

Apply it:

```shell
kubectl --kubeconfig admin.conf apply -f tenant-acme-rolebinding.yaml
```

With external authentication, additional users can be assigned to the corresponding identity-provider group without changing the RoleBinding. With client certificates, each user must receive a certificate containing the required group membership; changing that membership requires issuing a new certificate.

The same pattern can be repeated for other access levels:

```
oneks:tenant-acme:developers
oneks:tenant-acme:viewers
oneks:tenant-beta:developers
oneks:tenant-beta:viewers
```

For example, a read-only `tenant-viewer` Role could grant only:

```
verbs:
  - get
  - list
  - watch
```

and omit Secrets.

### 4\. Configure Resource Limits

RBAC controls **what** a tenant can do. It does not control **how much** of the Cluster the tenant can consume. Use `ResourceQuota` for each tenant namespace. For example:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
  namespace: tenant-acme
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    requests.storage: 100Gi
    pods: "25"
    services: "10"
    secrets: "50"
```

Kubernetes ResourceQuota objects restrict aggregate resource consumption at namespace scope and help prevent one tenant from consuming an excessive share of a shared Cluster.

#### GPU Quotas:

When GPU resources are available in the Cluster, they can also be allocated per tenant.

For example:

```yaml
spec:
  hard:
    requests.nvidia.com/gpu: "2"
```

This limits the namespace to workloads requesting a maximum aggregate total of two `nvidia.com/gpu` extended resources. Kubernetes supports ResourceQuota for extended resources such as GPUs.

### 5\. Define Default Container Limits

Pair ResourceQuota with a `LimitRange`. For example:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: tenant-default-limits
  namespace: tenant-acme
spec:
  limits:
  - type: Container
    defaultRequest:
      cpu: 100m
      memory: 128Mi
    default:
      cpu: "1"
      memory: 1Gi
    max:
      cpu: "2"
      memory: 4Gi
```

Without defaults, workloads that do not specify CPU or memory requests and limits can be rejected when corresponding ResourceQuota constraints are active. A LimitRange can provide these defaults automatically.

### 6\. Isolate Tenant Network Traffic

Namespaces do not automatically isolate pod networking. By default, Kubernetes networking permits communication between Pods unless a network policy implementation restricts it. Kubernetes recommends starting multi-tenant environments with deny-by-default policies and then explicitly allowing required communication.

First deny ingress and egress:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: tenant-acme
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

Allow communication between Pods belonging to the same namespace:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
  namespace: tenant-acme
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  - from:
    - podSelector: {}
  egress:
  - to:
    - podSelector: {}
```

Then explicitly permit DNS:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: tenant-acme
spec:
  podSelector: {}

  policyTypes:
  - Egress

  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
```

Check the DNS Pod labels used by the actual Cluster before applying the DNS example:

```shell
kubectl --kubeconfig admin.conf get pods -n kube-system --show-labels
```

Additional egress or ingress must then be explicitly enabled according to application requirements.

NetworkPolicy enforcement depends on the Kubernetes CNI plugin. Creating a NetworkPolicy object has no isolation effect when the installed CNI does not implement NetworkPolicy.

The operator should therefore verify NetworkPolicy enforcement before relying on it as a tenant security boundary.

### 7\. Provide Dedicated User Credentials

#### Recommended Production Model: External Authentication

For production Clusters with multiple human users, Kubernetes recommends integrating an external authentication system such as OIDC instead of distributing static ServiceAccount tokens or long-lived client certificates.

A typical model is:

```
Corporate Identity Provider
          │
alice@example.com
groups:
  oneks:tenant-acme:developers
          │
Kubernetes Authentication
          │
RoleBinding
          │
tenant-developer
          │
tenant-acme namespace
```

The user's kubeconfig identifies the Kubernetes API endpoint and uses the configured authentication mechanism to obtain credentials.

Group membership can be managed centrally through the identity provider. Removing a user from a group affects access once their credentials reflect the updated membership. An already-issued OIDC ID token can continue to authorize access until it expires because Kubernetes validates the token without querying the identity provider for current group membership. Use short-lived ID tokens to limit this delay.

#### Client Certificate Example

For environments where OIDC is not available, short-lived X.509 client certificates can be used as an alternative.

This is useful for demonstrating the complete tenant onboarding process, but it should not be treated as the preferred production identity solution. Kubernetes client certificates cannot normally be individually revoked and Kubernetes recommends short credential lifetimes when this authentication mechanism is used.

The following example creates a credential for:

```
User:  alice@example.com
Group: oneks:tenant-acme:developers
```

Generate Alice's private key:

```shell
openssl genrsa -out alice.key 3072
```

Create a certificate signing request:

```shell
openssl req \
  -new \
  -key alice.key \
  -out alice.csr \
  -subj '/CN=alice@example.com/O=oneks:tenant-acme:developers'
```

Create a Kubernetes `CertificateSigningRequest`:

```shell
CSR_NAME="tenant-acme-alice-$(date +%s)"
CSR_DATA="$(base64 < alice.csr | tr -d '\n')"

cat <<EOF | kubectl --kubeconfig admin.conf apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: ${CSR_NAME}
spec:
  request: ${CSR_DATA}
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400
  usages:
  - client auth
EOF
```

Review the request before approving it:

```shell
kubectl --kubeconfig admin.conf get csr "${CSR_NAME}" -o yaml
```

Approve it:

```shell
kubectl --kubeconfig admin.conf certificate approve "${CSR_NAME}"
```

Certificate approval and signing are separate steps. Wait for the signing controller to populate the signed certificate before retrieving it:

```shell
kubectl --kubeconfig admin.conf wait \
  --for=jsonpath='{.status.certificate}' \
  "certificatesigningrequest/${CSR_NAME}" \
  --timeout=120s
```

If this command times out, inspect the CertificateSigningRequest and resolve any signing errors before continuing.

Retrieve the signed certificate:

```shell
kubectl --kubeconfig admin.conf \
  get csr "${CSR_NAME}" -o jsonpath='{.status.certificate}' \
  | base64 -d > alice.crt
```

The certificate requested in this example requests a one-day lifetime. The actual certificate lifetime is also subject to the Cluster signer's configuration.

### 8\. Create the Tenant Kubeconfig

Obtain the Kubernetes API endpoint from the administrative kubeconfig:

```shell
SERVER="$( kubectl --kubeconfig admin.conf config view --raw \
  -o jsonpath='{.clusters[0].cluster.server}' )"
```

Extract the Kubernetes CA certificate:

```shell
kubectl --kubeconfig admin.conf config view --raw \
  -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' \
  | base64 -d > cluster-ca.crt
```

Create a new kubeconfig containing only the Cluster connection and Alice's credentials:

```shell
kubectl config --kubeconfig alice-acme.conf \
  set-cluster oneks-cluster --server="${SERVER}" \
  --certificate-authority=cluster-ca.crt --embed-certs=true
```

Add Alice's identity:

```shell
kubectl config --kubeconfig alice-acme.conf \
  set-credentials alice@example.com \
  --client-certificate=alice.crt \
  --client-key=alice.key \
  --embed-certs=true
```

Create a context that automatically targets the tenant namespace:

```shell
kubectl config \
  --kubeconfig alice-acme.conf \
  set-context tenant-acme \
  --cluster=oneks-cluster \
  --user=alice@example.com \
  --namespace=tenant-acme
```

Activate the context:

```shell
kubectl config \
  --kubeconfig alice-acme.conf \
  use-context tenant-acme
```

Restrict access to the local credentials:

```shell
chmod 600 alice.key alice-acme.conf
```

The resulting file contains Alice's credentials only:

```
alice-acme.conf
```

It does **not** contain the credentials copied from `admin.conf`.

This distinction is essential. A tenant kubeconfig is not simply a renamed copy of the OneKS administrative kubeconfig.

### 9\. Verify Tenant Permissions Before Distribution

The administrator should test every tenant role before distributing credentials.

Using impersonation, verify that the expected group can deploy applications:

```shell
kubectl --kubeconfig admin.conf \
  auth can-i create deployments -n tenant-acme \
  --as=alice@example.com \
  --as-group=oneks:tenant-acme:developers
```

Expected result:

```
yes
```

Check access to another namespace:

```shell
kubectl --kubeconfig admin.conf \
  auth can-i get pods -n tenant-beta \
  --as=alice@example.com \
  --as-group=oneks:tenant-acme:developers
```

Expected result:

```
no
```

Check node access:

```shell
kubectl --kubeconfig admin.conf \
  auth can-i get nodes \
  --as=alice@example.com \
  --as-group=oneks:tenant-acme:developers
```

Expected result:

```
no
```

Check cluster-wide RBAC administration:

```shell
kubectl --kubeconfig admin.conf \
  auth can-i create clusterroles \
  --as=alice@example.com --as-group=oneks:tenant-acme:developers
```

Expected result:

```
no
```

Check namespace administration:

```shell
kubectl --kubeconfig admin.conf \
  auth can-i create namespaces \
  --as=alice@example.com \
  --as-group=oneks:tenant-acme:developers
```

Expected result:

```
no
```

Check Cluster API resources explicitly if those APIs are present:

```shell
kubectl --kubeconfig admin.conf \
  auth can-i get machines.cluster.x-k8s.io --all-namespaces \
  --as=alice@example.com \
  --as-group=oneks:tenant-acme:developers
```

Expected result:

```
no
```

Finally, test using Alice's actual kubeconfig:

```shell
kubectl --kubeconfig alice-acme.conf get pods
```

and:

```shell
kubectl --kubeconfig alice-acme.conf get pods -n kube-system
```

The first command should succeed. The second should return an authorization error.

A useful final inspection is:

```shell
kubectl --kubeconfig alice-acme.conf \
  auth can-i --list -n tenant-acme
```

### 10\. Credentials for Automation

Human users and automated workloads should not share credentials. For CI/CD or other automation, create a dedicated ServiceAccount:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ci-deployer
  namespace: tenant-acme
```

Bind it only to the permissions required by the automation:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ci-deployer
  namespace: tenant-acme
subjects:
- kind: ServiceAccount
  name: ci-deployer
  namespace: tenant-acme
roleRef:
  kind: Role
  name: tenant-developer
  apiGroup: rbac.authorization.k8s.io
```

When external automation requires a ServiceAccount token, prefer short-lived TokenRequest credentials instead of creating permanent ServiceAccount token Secrets:

```shell
kubectl --kubeconfig admin.conf \
  create token ci-deployer -n tenant-acme --duration=1h
```

Kubernetes recommends TokenRequest-based short-lived ServiceAccount credentials instead of static, non-expiring ServiceAccount token Secrets. ServiceAccounts are intended primarily for workloads and automation rather than human authentication.

### 11\. Keep OneKS Lifecycle Administration Separate

Kubernetes tenant access does not need to imply access to the OneKS management layer.

The Kubernetes administrator can allow a tenant to deploy applications without granting permissions to:

```
Create OneKS clusters
Delete OneKS clusters
Create node groups
Resize node groups
Upgrade clusters
Recover clusters
Retrieve the administrative OneKS kubeconfig
```

OneKS manages worker capacity through node groups, while Kubernetes workload access is performed through the Cluster kubeconfig. These should be treated as distinct authorization surfaces.

For a shared Kubernetes service, a recommended default is:

```
OneKS lifecycle operations       Operator only
Cluster-wide Kubernetes access   Operator only
Tenant namespace operations      Tenant users
```

Only delegate OneKS/OpenNebula management permissions when a user is intentionally acting as an infrastructure or Kubernetes service operator.

### 12\. Recommended Tenant Onboarding Workflow

For every new tenant, the Kubernetes administrator should perform the following process:

1. Create one or more dedicated tenant namespaces.  
2. Enforce the appropriate Pod Security Standard through namespace labels.  
3. Apply ResourceQuota.  
4. Apply LimitRange.  
5. Apply default network isolation.  
6. Define the tenant's allowed application operations.  
7. Create namespace-scoped RoleBindings.  
8. Associate tenant identities or groups with those RoleBindings.  
9. Create dedicated credentials or configure external authentication.  
10. Generate a tenant-specific kubeconfig.  
11. Verify permitted actions with `kubectl auth can-i`.  
12. Verify prohibited Cluster-wide and cross-tenant actions.  
13. Distribute only the tenant credentials.  
14. Keep the OneKS administrative kubeconfig private.  
15. Periodically review tenant RBAC and remove obsolete identities and bindings.

Kubernetes recommends regular RBAC reviews because old or excessive bindings can become privilege-escalation paths over time.

### 13\. Shared Cluster Isolation Has Limits

Namespace-based multi-tenancy should not be presented as equivalent to running each tenant in an independent Kubernetes Cluster.

Namespaces, RBAC, quotas, Pod Security, storage policy, and NetworkPolicy provide useful control-plane and workload isolation, but tenant containers can still share Kubernetes worker nodes and therefore the underlying operating system kernel.

Kubernetes documentation explicitly notes that container isolation is weaker than the hardware-level isolation provided by Virtual Machines.

For cooperative organizational teams, for example different departments sharing a corporate Kubernetes platform, namespace-based tenancy is often appropriate.

For mutually untrusted tenants, strict regulatory separation, or workloads requiring a strong security boundary, prefer separate OneKS Kubernetes Clusters:

```default
Shared cluster model

OneKS Cluster
├── Tenant A namespace
├── Tenant B namespace
└── Tenant C namespace
```

Versus:

```default
Strong isolation model

OneKS Cluster A
└── Tenant A

OneKS Cluster B
└── Tenant B

OneKS Cluster C
└── Tenant C
```

OneKS makes this second model particularly natural because independent Kubernetes Clusters can be provisioned and lifecycle-managed separately.

## Security Recommendations

For shared OneKS Kubernetes Clusters:

* Never distribute the administrative OneKS Kubernetes kubeconfig to tenant users.  
* Prefer externally authenticated individual identities for human users.  
* Never use a single shared tenant identity when individual accountability is required.  
* Prefer group-based RBAC.  
* Use namespace-scoped `RoleBinding` objects instead of `ClusterRoleBinding` wherever possible.  
* Never add tenant users to `system:masters`.  
* Avoid wildcard RBAC permissions.  
* Do not allow tenants to modify their own RBAC unless this delegation is intentional.  
* Keep ResourceQuota, LimitRange, tenant isolation NetworkPolicies, and namespace security configuration under operator control.  
* Treat users capable of creating workloads as capable of accessing credentials available to workloads in the same namespace.  
* Do not place privileged platform ServiceAccounts inside tenant namespaces.  
* Enforce Pod Security Standards.  
* Verify that the installed CNI actually enforces NetworkPolicy.  
* Apply CPU, memory, storage, object-count, and GPU quotas as appropriate.  
* Use short-lived credentials where possible.  
* Use ServiceAccounts for automation, not as the default identity mechanism for human users.  
* Periodically review RBAC bindings and remove access that is no longer required.  
* Keep OneKS/OpenNebula lifecycle permissions separate from Kubernetes application permissions.  
* Use independent OneKS Kubernetes Clusters when namespace isolation does not provide a sufficiently strong security boundary.