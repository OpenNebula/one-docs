---
title: "Creating Custom Applications"
linkTitle: "Creating Custom Applications"
date: "2026-10-01"
description: "Create OneKS application and component definitions for Helm-based applications."
categories:
tags:
weight: "3"
type: docs
---

OneKS applications are declarative YAML definitions around Helm charts. A definition supplies catalog metadata, Helm coordinates and values, optional user inputs, dependencies, and lifecycle steps. OneKS validates all definitions when the service starts and exposes valid application definitions through its REST API.

## Catalogue Layout

The installed catalog is located under:

```default
/var/lib/one/oneks/charts
```

Definitions are separated by their role:

```text
/var/lib/one/oneks/charts/
├── applications/
│   └── my-application-v1.2.3.yaml
└── components/
    └── my-component-v1.0.0.yaml
```

* **Applications** are public root definitions. Users can select and install them directly.
* **Components** are private building blocks. They can only be installed as dependencies of an application or another component.

Every definition needs a globally unique, stable `id`. Generate a new identifier for a new definition instead of reusing the ID of another version or chart.

{{< alert title="Important" type="warning" >}}
OneKS uses the current catalog definition to build both installation and deletion plans. Keep the root application and all of its component definitions available and compatible until every release that uses them has been uninstalled.
{{< /alert >}}

## Minimal Application

The following definition exposes a Helm chart as a public application and uses one user input in its Helm values:

```yaml
id: 7da3bb1d-a047-4d26-a12d-685c6ef5092e
repo: https://charts.example.com
chart: example-server
version: 1.2.3

metadata:
  name: Example Server
  description: Example web service managed by OneKS.
  documentationUrl: https://docs.example.com/example-server
  about:
    - title: Verify the installation
      description: Inspect the Pods created by the release.
      steps:
        - title: List Pods
          code: kubectl get pods -n ${releaseName}

userInputs:
  - name: replicas
    description: Number of application replicas.
    type: number
    default: 2
    match:
      type: number
      values:
        min: 1
        max: 10

defaultValuesContent: |
  replicaCount: ${replicas}

installDefaults:
  releaseName: example-server
  targetNamespace: example-server
  createNamespace: true
```

Place the file in `applications/`, restart OneKS, and confirm that it is visible:

```shell
systemctl restart opennebula-ks.service
oneks list apps
oneks show app 7da3bb1d-a047-4d26-a12d-685c6ef5092e
```

If OneKS ignores the definition, inspect the service journal for a schema, placeholder, dependency, or YAML error:

```shell
journalctl -u opennebula-ks.service
```

## Definition Structure

### Identity and Helm Source

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Stable unique string used by the catalog and API. A UUID is recommended. |
| `chart` | Yes | Helm chart name, or a complete OCI chart reference such as `oci://registry.example.com/charts/my-chart`. |
| `version` | Yes | Exact chart version to install. |
| `repo` | No | Helm repository URL. Omit it when `chart` is a complete OCI reference. |
| `authSecret` | No | Name of the Kubernetes Secret used by the Helm controller to authenticate to a private chart repository. |
| `defaultValuesContent` | No | YAML mapping passed to Helm as the release values. |
| `installDefaults` | No for applications | Default release name, target namespace, and namespace-creation behavior. All three child fields are required when this object is present. |

`defaultValuesContent` must parse as a YAML object. YAML aliases are not accepted in catalog definitions or in the embedded values.

Root applications may omit `installDefaults`; the caller must then provide the release name and target namespace. A component referenced through `dependencies` must have valid `installDefaults`, because components are installed non-interactively.

Release names and namespaces must be valid RFC 1123 names. Release names must also be unique across the root and component releases already managed in the target K8s Cluster.

### Metadata Information

`metadata.name` is required. The standard presentation fields are:

| **Field** | **Description** |
|-------|-------------|
| `name` | Human-readable catalog name. |
| `description` | Short explanation shown in the catalog and installed-release details. |
| `documentationUrl` | HTTPS link to the application's upstream documentation. |
| `about` | One or more post-installation help sections. |

The `about` field is a list of recursive content items. Every item, whether at the top level or nested under `steps`, can contain `title`, `description`, `code`, and another `steps` list with the same structure. In an installed application's Sunstone details, `${releaseName}` in any `code` field is replaced with the actual release name.

Metadata is presentation data; its placeholders are not used to render Helm values or lifecycle resources.

### User Inputs

Declare installation-time parameters in `userInputs`. Each item supports:

| **Field** | **Required** | **Description** |
|-------|----------|-------------|
| `name` | Yes | Unique parameter name. It also becomes an available `${name}` placeholder. |
| `type` | Yes | `string`, `number`, `bool`, `list`, `tuple`, `map`, or `object`. |
| `description` | No | Help text shown to the user. |
| `default` | No | Default value. Its YAML type must match the declared input type. |
| `mandatory` | No | If `true`, installation fails when no value or default is available. |
| `sensitive` | No | Marks credentials or secrets so clients can avoid displaying their value. Do not put sensitive values in `default`. |
| `match` | No | Additional validation, such as a string regular expression, numeric `min` or `max`, or a set of allowed values. |

Use the input name as a placeholder anywhere outside `metadata`. If a placeholder occupies the complete YAML value, its native type is preserved. Embedded placeholders are converted to strings:

```yaml
userInputs:
  - name: enabled
    type: bool
    default: true
  - name: hostname
    type: string
    mandatory: true

defaultValuesContent: |
  feature:
    enabled: ${enabled}
    endpoint: https://${hostname}/api
```

### Built-in Placeholders

OneKS recognizes these placeholders in chart fields, values, dependencies, and lifecycle steps:

| **Placeholder** | **Value** |
|-------------|-------|
| `${chartId}` | Stable ID of the definition being resolved. |
| `${releaseName}` | Helm release name. |
| `${resourceNamePrefix}` | Release-derived prefix limited for Kubernetes resource names. Long release names are shortened deterministically. |
| `${targetNamespace}` | Namespace selected for the release. |
| `${createNamespace}` | Boolean namespace-creation option. |
| `${<user-input-name>}` | Validated value supplied for a declared user input. |

An unknown placeholder makes the definition invalid. Quote a larger scalar when YAML syntax requires it, but leave a complete placeholder unquoted when its native boolean, numeric, list, or object type must be retained.

## Reusable Components and Dependencies

Define an internal component with its own Helm coordinates and mandatory installation defaults:

```yaml
id: d1647511-7993-4813-b33a-95643a421c26
repo: https://charts.example.com
chart: example-database
version: 4.5.6

metadata:
  name: Example Database

installDefaults:
  releaseName: example-database
  targetNamespace: example-database
  createNamespace: true
```

Save this file under `components/`, then reference its ID from an application:

```yaml
dependencies:
  - chartId: d1647511-7993-4813-b33a-95643a421c26
```

Dependencies can have their own dependencies. OneKS validates the complete graph, rejects missing components, application-to-application dependencies, cycles, and duplicate component release names, and installs the resolved components before the root application. During uninstall, it processes the root and its components in reverse order.

## Lifecycle Steps

Use `preInstall`, `postInstall`, and `preUninstall` for Kubernetes resources or checks that cannot be expressed as Helm values:

* `preInstall` runs before the chart is installed.
* `postInstall` runs after the chart is installed.
* `preUninstall` runs before the chart is deleted.

Each item requires a descriptive `name` and one operation:

| **Operation** | **Purpose** |
|-----------|---------|
| `apply` | Apply a Kubernetes manifest. |
| `wait` | Wait for a named resource to be created or to meet a condition. A `timeout` is required. |
| `patch` | Patch a named resource using `json`, `merge`, or `strategic` patch type. |
| `delete` | Delete a named resource, optionally controlling `ignoreNotFound`, `wait`, and `timeout`. |
| `shell` | Run a shell fragment. Use this only when the declarative operations cannot represent the action. |

For example:

```yaml
preInstall:
  - name: Create application configuration
    apply:
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: ${resourceNamePrefix}-config
        namespace: ${targetNamespace}
      data:
        mode: production

  - name: Wait for application configuration
    wait:
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: ${resourceNamePrefix}-config
        namespace: ${targetNamespace}
      timeout: 60s
```

Resources created by `apply` steps are deleted automatically when the application is uninstalled. Set `retain: true` on an apply step only when the resource must survive uninstall:

```yaml
postInstall:
  - name: Create persistent application data
    retain: true
    apply:
      apiVersion: v1
      kind: PersistentVolumeClaim
      metadata:
        name: ${resourceNamePrefix}-data
        namespace: ${targetNamespace}
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 10Gi
```

Retained resources become the operator's responsibility and must be removed manually when they are no longer needed.
