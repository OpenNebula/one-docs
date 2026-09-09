---
title: "AMD GPU Passthrough"
linkTitle: "AMD GPUs"
date: "2026-09-09"
description:
categories:
pageintoc: "58"
tags: ['AI','AMD','ROCm']
weight: "8"
---

## Overview

This guide describes how to assign an AMD GPU directly to an OpenNebula Virtual Machine using PCI passthrough, install ROCm in the guest, and validate the configuration with PyTorch and vLLM. While the Virtual Machine is running, the assigned GPU is exclusively owned by the guest. The AMD GPU driver and ROCm user-space components are therefore installed in the guest, not on the Host.

The generic PCI passthrough configuration is described in the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}). Complete the IOMMU and VFIO device ownership configuration before proceeding with this guide. The AMD-specific VFIO binding and PCI monitoring values are configured below.

The commands below reproduce a validated environment with the following software:

| **Component** | **Validated Version** |
|-----------|-------------------|
| GPU | AMD Instinct MI325X (`1002:74a5`) |
| OpenNebula | 7.4.0 |
| Host | Ubuntu 22.04.5, kernel 6.5.0-45 |
| QEMU | 8.2.2 |
| Guest | Ubuntu 24.04.4, kernel 6.8.0-139 |
| AMD GPU Driver release | 30.30.4 |
| AMDGPU kernel module | 6.16.13 (DKMS) |
| ROCm | 7.2.4 |
| PyTorch | 2.9.1 for ROCm 7.2.4 |
| vLLM | 0.28.1rc1.dev516+g9ea8f3ffc.rocm723 |

Refer to the [ROCm documentation](https://rocm.docs.amd.com/) and the [vLLM installation documentation](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/) before using a different software combination.

## Requirements

Before continuing, verify that:

* The AMD GPU is installed and visible on the Host.
* The GPU is supported by the ROCm release that will be installed in the guest. Refer to the [ROCm compatibility matrix](https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html).
* [IOMMU]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/#step-1-enable-the-iommu" %}}) and [VFIO device ownership]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/#vfio-device-ownership" %}}) are configured on the Host.
* The Host uses QEMU 8.2.2, or another QEMU version verified to expose the required PCIe atomic capabilities, and a Q35 machine type is available.
* An Ubuntu 24.04 Image with Python 3.12 is available.
* The Virtual Machine disk has at least 50 GB of capacity for ROCm and PyTorch, or 96 GB when testing vLLM with the 27B FP8 model used in this guide. The selected datastore must have enough capacity to provision this disk.
* The network selected for the Virtual Machine provides Internet access.

## Configure the Host

### Verify the QEMU Version

The virtual PCIe Root Port must advertise support for 32-bit, 64-bit, and 128-bit compare-and-swap atomic operations. The QEMU 6.2 packages originally supplied by Ubuntu 22.04 did not expose the required capabilities in the validated environment. QEMU 8.2.2 resolved the issue. Other QEMU versions must be verified independently.

Check the QEMU binary used by OpenNebula:

```shell
readlink -f /usr/bin/qemu-kvm-one
/usr/bin/qemu-kvm-one --version
```

On the validated Ubuntu 22.04 Host, QEMU 8.2.2 was installed from the Caracal Proposed pocket of the Ubuntu Cloud Archive:

```shell
sudo apt-get update
sudo apt-get install -y ubuntu-cloud-keyring software-properties-common
sudo add-apt-repository cloud-archive:caracal
sudo add-apt-repository cloud-archive:caracal-proposed
sudo apt-get update
sudo apt-get --simulate -t jammy-proposed/caracal install \
  qemu-system-x86 qemu-system-common \
  qemu-system-data qemu-utils qemu-block-extra
sudo apt-get install -y -t jammy-proposed/caracal \
  qemu-system-x86 qemu-system-common \
  qemu-system-data qemu-utils qemu-block-extra
/usr/bin/qemu-kvm-one --version
```

After installing the required packages, disable the Proposed pocket to prevent unrelated pre-release packages from being selected during future upgrades:

```shell
sudo add-apt-repository --remove cloud-archive:caracal-proposed
sudo apt-get update
```

{{< alert title="Warning" type="warning" >}}
Changing QEMU on an OpenNebula Host affects every KVM Virtual Machine on that Host. The Ubuntu Proposed pockets contain packages undergoing validation and are not intended as general production repositories. Inspect the simulated APT transaction and confirm that the selected package source and QEMU version are supported by the operating system and OpenNebula release before upgrading a production Host.
{{< /alert >}}

### Identify the AMD GPU Devices

List the installed AMD devices:

```shell
lspci -nn -d 1002:
```

Example output from the validated hardware:

```default
05:00.0 Processing accelerators [1200]: Advanced Micro Devices, Inc. [AMD/ATI] Aqua Vanjaram [Instinct MI325X] [1002:74a5]
```

Record the identifiers reported for each device intended for passthrough. For the validated hardware, these are:

| Field | Value |
|-------|-------|
| Vendor | `1002` |
| Device | `74a5` |
| Class | `1200` |

Verify the IOMMU group of every device intended for passthrough. Replace the example address with the address from your Host:

```shell
gpu=0000:05:00.0
group=$(basename "$(readlink "/sys/bus/pci/devices/$gpu/iommu_group")")

for device in /sys/kernel/iommu_groups/"$group"/devices/*; do
  lspci -nnk -s "$(basename "$device")"
done
```

Each assigned GPU must be isolated in a viable IOMMU group. Inspect every member of a group before binding it to VFIO.

### Prevent Host Driver Binding

On a Host dedicated to AMD GPU passthrough, prevent `amdgpu` from claiming the accelerators. Append the following parameters to the Host kernel command line:

```default
module_blacklist=amdgpu modprobe.blacklist=amdgpu
```

Also create `/etc/modprobe.d/blacklist-amdgpu.conf` with the following contents:

```default
blacklist amdgpu
```

Regenerate the GRUB configuration and initramfs, then reboot the Host:

```shell
sudo update-grub
sudo update-initramfs -u
sudo reboot
```

{{< alert title="Warning" type="warning" >}}
Blacklisting `amdgpu` prevents the Host from using every AMD GPU managed by that module. Do not apply this configuration when the Host requires another AMD GPU for its console or workloads.
{{< /alert >}}

### Bind the AMD GPU to VFIO

Install `driverctl`, load VFIO, and bind the selected GPU. Replace `05:00.0` with the address from your Host:

```shell
sudo apt-get install -y driverctl
sudo modprobe vfio
sudo modprobe vfio-pci
sudo driverctl set-override 0000:05:00.0 vfio-pci
```

The `modprobe` commands load the VFIO modules only for the current Host boot. To load them automatically after every reboot, create `/etc/modules-load.d/vfio.conf` with the following contents:

```default
vfio
vfio-pci
```

The `driverctl set-override` command shown above stores a persistent override and restores the `vfio-pci` binding after a Host reboot. For a temporary test that lasts only until the next reboot, use `--nosave` instead:

```shell
sudo driverctl --nosave set-override 0000:05:00.0 vfio-pci
```

Verify the binding:

```shell
lspci -nnk -s 05:00.0
```

The output must contain:

```default
Kernel driver in use: vfio-pci
```

### Configure OpenNebula Monitoring

On the Front-end, add the AMD vendor ID to the `filter` list in `/var/lib/one/remotes/etc/im/kvm-probes.d/pci.conf`. Restrict the configuration to the intended PCI addresses or use the device and class identifiers reported by `lspci`:

```default
filter:
  - "1002:74a5:1200"

short_address:
  - "05:00.0"
```

The example restricts discovery to the GPU model and address used in the validated environment. Replace the vendor, device, class, and address values with those reported by your Host. To expose multiple GPUs for automatic selection, bind every exposed device to `vfio-pci` before deployment.

As `oneadmin`, synchronize the monitoring probes and request a new monitoring cycle:

```shell
onehost sync --force
onehost forceupdate <host>
```

Verify that OpenNebula discovered the devices:

```shell
onehost show <host>
```

The AMD GPUs must appear in the **PCI Devices** section.

## Deploy the Virtual Machine

Add the following attributes to the Virtual Machine Template to assign a specific AMD GPU. Merge the `MODEL` and `MACHINE` values into existing `CPU_MODEL` and `OS` attributes when they are already defined:

```default
CPU_MODEL = [
  MODEL = "host-passthrough"
]

OS = [
  MACHINE = "q35"
]

PCI = [
  SHORT_ADDRESS = "05:00.0"
]
```

Replace the PCI address with the value from your environment. Size the CPU, memory, and disk according to the workload and the requirements listed above.

{{< alert title="Disk Persistence" type="info" >}}
Changes made inside a disk created from a non-persistent OpenNebula Image survive guest reboots, power-off operations, and resumes, but are discarded when the Virtual Machine is terminated. To retain the installed driver, ROCm environments, and downloaded models beyond the VM lifecycle, use a persistent Image or save the VM disk as a new Image before terminating the VM. Persistent Images can be used by only one Virtual Machine at a time.
{{< /alert >}}

For automatic device selection among multiple prepared GPUs, request the GPU by its vendor, device, and class identifiers instead. The following example uses the identifiers from the validated environment; replace them with the values reported by `lspci`:

```default
PCI = [
  VENDOR = "1002",
  DEVICE = "74a5",
  CLASS  = "1200"
]
```

Repeat the `PCI` section to assign multiple AMD GPUs to the same Virtual Machine. Multi-GPU workloads see separate ROCm devices; frameworks such as vLLM can combine them using tensor, pipeline, or data parallelism. Validate peer access and RCCL before using a multi-GPU configuration.

Do not use automatic selection unless every matching GPU exposed by PCI monitoring has been prepared for passthrough and bound to `vfio-pci`.

{{< alert title="Important" type="warning" >}}
Both Q35 and `host-passthrough` are required. Q35 provides the PCIe topology used to expose atomic operation capabilities. `host-passthrough` exposes the AVX and AVX2 CPU instructions required by ROCm libraries such as hipSPARSELt.
{{< /alert >}}

## Configure the Guest

After deploying the Virtual Machine, verify that the guest can see the assigned device:

```shell
lspci -nnk -d 1002:
```

### Install the AMD GPU Driver

Download and install the ROCm 7.2.4 repository package:

```shell
curl -fLO https://repo.radeon.com/amdgpu-install/7.2.4/ubuntu/noble/amdgpu-install_7.2.4.70204-1_all.deb
sudo apt-get install -y ./amdgpu-install_7.2.4.70204-1_all.deb
sudo apt-get update
```

Install the kernel headers, extra kernel modules, and AMD GPU driver:

```shell
sudo apt-get install -y "linux-headers-$(uname -r)" \
  "linux-modules-extra-$(uname -r)" amdgpu-dkms
dkms status
```

Reboot the guest operating system without stopping the OpenNebula Virtual Machine:

```shell
sudo reboot
```

After reconnecting, verify that `amdgpu` manages the device and that the KFD device exists:

```shell
lspci -nnk -d 1002:
id
ls -l /dev/kfd /dev/dri/renderD*
```

The user that runs ROCm applications must belong to the `render` and `video` groups. Commands run from a root shell do not require this membership. If either group is missing from the `id` output above, add it with:

```shell
sudo usermod -a -G render,video "$USER"
```

Group membership configured with `usermod` is persistent, but the user must start a new login session before it takes effect.

### Verify PCIe Atomic Operations

Identify the PCIe Root Port immediately above the assigned GPU:

```shell
lspci -t
```

Inspect its PCIe capabilities, replacing `00:02.0` if necessary:

```shell
sudo lspci -vv -s 00:02.0 | grep -E "AtomicOpsCap|AtomicOpsCtl"
```

The Root Port must advertise 32-bit, 64-bit, and 128-bit compare-and-swap atomic completer support. For example:

```default
AtomicOpsCap: Routing- 32bit+ 64bit+ 128bitCAS+
```

`Routing-` is expected for a Root Port directly connected to the assigned endpoint. The `32bit+`, `64bit+`, and `128bitCAS+` fields are the relevant capabilities.

Verify that the driver did not reject the device:

```shell
sudo dmesg | grep -E "amdgpu|PCIE atomic ops"
```

The output must not contain `PCIE atomic ops is not supported`.

### Install the ROCm Runtime

Install the ROCm compute and machine-learning libraries:

```shell
sudo apt-get install -y rocminfo amd-smi-lib rocm-hip-runtime \
  roctracer rocm-ml-libraries
```

Register the ROCm library path with the dynamic linker:

```shell
printf '%s\n' /opt/rocm/lib | sudo tee /etc/ld.so.conf.d/rocm.conf
sudo ldconfig
```

The file in `/etc/ld.so.conf.d/` makes the ROCm library path persistent. Running only with `LD_LIBRARY_PATH=/opt/rocm/lib` would affect the current command or shell session instead.

Verify the GPU with ROCm and AMD SMI:

```shell
/opt/rocm/bin/rocminfo
/opt/rocm/bin/amd-smi list
/opt/rocm/bin/amd-smi metric
```

`rocminfo` must report an agent for every assigned GPU, with the architecture and marketing name expected for the hardware. In the validated environment, it reported `gfx942` and `AMD Instinct MI325X`.

## Validate PyTorch (Optional)

This section provides an optional functional test of ROCm and the assigned GPU. Skip it if you intend to use only vLLM, which installs its own PyTorch build in a separate environment.

Install Python virtual environment support and create an isolated environment:

```shell
sudo apt-get install -y python3.12-venv
sudo python3.12 -m venv --clear /opt/pytorch-rocm
sudo chown -R "$USER":"$(id -gn)" /opt/pytorch-rocm
/opt/pytorch-rocm/bin/python -m pip install --upgrade pip setuptools wheel
```

Install the validated AMD Triton and PyTorch wheels:

```shell
/opt/pytorch-rocm/bin/pip install \
  'https://repo.radeon.com/rocm/manylinux/rocm-rel-7.2.4/triton-3.5.1%2Brocm7.2.4.gita272dfa8-cp312-cp312-linux_x86_64.whl' \
  'https://repo.radeon.com/rocm/manylinux/rocm-rel-7.2.4/torch-2.9.1%2Brocm7.2.4.lw.git39497456-cp312-cp312-linux_x86_64.whl'
```

Run a matrix multiplication on the GPU:

```shell
/opt/pytorch-rocm/bin/python - <<'PY'
import torch

print("PyTorch:", torch.__version__)
print("ROCm:", torch.version.hip)
print("GPU available:", torch.cuda.is_available())
print("GPU count:", torch.cuda.device_count())
print("GPU:", torch.cuda.get_device_name(0))

a = torch.randn((4096, 4096), device="cuda", dtype=torch.float16)
b = torch.randn((4096, 4096), device="cuda", dtype=torch.float16)
c = a @ b
torch.cuda.synchronize()

print("Result:", c.shape, c.dtype)
print("Finite:", torch.isfinite(c).all().item())
print("Allocated memory:", torch.cuda.memory_allocated() // 1024**2, "MiB")
PY
```

The test must report the expected number of assigned AMD GPUs, a finite result, and memory allocated on the GPU. The validated configuration assigned one GPU.

## Install and Validate vLLM

The vLLM ROCm wheel includes a different, binary-compatible PyTorch build. Install it in a separate environment. If you completed the optional PyTorch validation above, do not modify `/opt/pytorch-rocm`.

The `rocm723` suffix in the validated vLLM version identifies the ROCm version used to build the wheel. Although it differs from the ROCm 7.2.4 runtime installed above, this exact combination was validated in the environment described by this guide.

Install the required system libraries:

```shell
sudo apt-get install -y libopenmpi3t64 rocprofiler-sdk hsa-amd-aqlprofile
sudo ldconfig
```

Create the environment and install the vLLM build validated by this guide:

```shell
sudo python3.12 -m venv /opt/vllm-rocm
sudo chown -R "$USER":"$(id -gn)" /opt/vllm-rocm
/opt/vllm-rocm/bin/python -m pip install --upgrade uv

/opt/vllm-rocm/bin/uv pip install \
  --python /opt/vllm-rocm/bin/python \
  --pre 'vllm==0.28.1rc1.dev516+g9ea8f3ffc.rocm723' \
  --extra-index-url https://wheels.vllm.ai/rocm/9ea8f3ffc354901b740f0b31988900897b7221d7/rocm723 \
  --index-strategy unsafe-best-match
```

Check the installed packages and GPU platform:

```shell
/opt/vllm-rocm/bin/uv pip check --python /opt/vllm-rocm/bin/python

/opt/vllm-rocm/bin/python - <<'PY'
import torch
import vllm

print("vLLM:", vllm.__version__)
print("PyTorch:", torch.__version__)
print("ROCm:", torch.version.hip)
print("GPU available:", torch.cuda.is_available())
print("GPU:", torch.cuda.get_device_name(0))
print("Platform:", type(vllm.platforms.current_platform).__name__)
PY
```

The platform must be `RocmPlatform` and the expected AMD GPU name must be displayed. The validated output reported `AMD Instinct MI325X`.

### Serve a Model

The following command downloads and serves the official Qwen3.8-27B FP8 model. The model requires approximately 29 GB of disk space. Use it only on AMD GPUs with native FP8 support and sufficient memory:

```shell
sudo install -d -o "$USER" -g "$(id -gn)" /opt/huggingface

HF_HOME=/opt/huggingface \
/opt/vllm-rocm/bin/vllm serve Qwen/Qwen3.8-27B-FP8 \
  --host 127.0.0.1 \
  --port 8000 \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.80 \
  --max-num-seqs 64 \
  --language-model-only
```

Setting `HF_HOME` before a command affects only that command. To use the same model cache in future interactive sessions, add the following line to the user's shell startup file, such as `~/.profile`:

```shell
export HF_HOME=/opt/huggingface
```

The server command runs in the foreground and stops when its process or terminal session ends.

After the API server is ready, submit a request from another guest shell:

```shell
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen3.8-27B-FP8",
    "messages": [{
      "role": "user",
      "content": "Briefly explain the problem that OpenNebula solves."
    }],
    "temperature": 0,
    "max_tokens": 256
  }' | /opt/vllm-rocm/bin/python -m json.tool
```

Abbreviated sample output:

```json
{
    "id": "chatcmpl-9c90b06953b77407",
    "object": "chat.completion",
    "created": 1788960674,
    "model": "Qwen/Qwen3.8-27B-FP8",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "We need answer user: \"Briefly explain the problem that OpenNebula solves.\" Need concise. Need final. Explain OpenNebula is open-source cloud management platform; problem: managing heterogeneous virtualized/cloud infrastructures, resources, workloads, multi-tenancy, automation, avoiding manual provisioning, silos, underutilization. Brief.\n</think>\n\nOpenNebula solves the problem of managing complex, heterogeneous virtualized and cloud infrastructure. It provides a unified platform to automate provisioning, orchestrate resources, manage multi-tenancy, and improve utilization across private, public, or hybrid clouds."
            },
            "finish_reason": "stop"
        }
    ],
    "system_fingerprint": "vllm-0.28.1rc1.dev516+g9ea8f3ffc-460d843b",
    "usage": {
        "prompt_tokens": 64,
        "total_tokens": 188,
        "completion_tokens": 124
    }
}
```

### Run a Small Serving Benchmark

With the server still running, submit a reproducible synthetic workload:

```shell
HF_HOME=/opt/huggingface \
/opt/vllm-rocm/bin/vllm bench serve \
  --backend vllm \
  --base-url http://127.0.0.1:8000 \
  --model Qwen/Qwen3.8-27B-FP8 \
  --dataset-name random \
  --num-prompts 32 \
  --random-input-len 512 \
  --random-output-len 128 \
  --ignore-eos \
  --request-rate inf \
  --max-concurrency 8 \
  --seed 42
```

Sample output:

```
============ Serving Benchmark Result ============
Successful requests:                     32
Failed requests:                         0
Maximum request concurrency:             8
Benchmark duration (s):                  17.67
Total input tokens:                      16384
Total generated tokens:                  4096
Request throughput (req/s):              1.81
Output token throughput (tok/s):         231.75
Peak output token throughput (tok/s):    264.00
Peak concurrent requests:                16.00
Total token throughput (tok/s):          1158.76
---------------Time to First Token----------------
Mean TTFT (ms):                          438.50
Median TTFT (ms):                        480.17
P99 TTFT (ms):                           488.69
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          31.33
Median TPOT (ms):                        30.99
P99 TPOT (ms):                           33.71
---------------Inter-token Latency----------------
Mean ITL (ms):                           31.33
Median ITL (ms):                         30.99
P99 ITL (ms):                            31.47
==================================================
```

The validated single-GPU configuration completed all 32 requests without errors and produced approximately 232 output tokens per second. Results depend on the model, vLLM revision, VM configuration, and Host load.

## Troubleshooting

### PCIe Atomic Operations Are Not Supported

The guest driver fails to initialize the AMD GPU and the kernel log contains:

```default
amdgpu: PCIE atomic ops is not supported
```

Verify that the VM uses Q35 and inspect the atomic operation capabilities of the Root Port above the GPU. If the completer capabilities are absent, use a supported QEMU package that exposes them. QEMU 8.2.2 was validated for this guide.

### PyTorch Exits with Illegal Instruction

If `import torch` exits with `Illegal instruction`, inspect the Host or guest kernel log. In the validated environment, the fault occurred in `libhipsparselt.so` because the VM used the generic `qemu64` CPU model, which did not expose AVX or AVX2.

Set the following VM attribute:

```default
CPU_MODEL = [
  MODEL = "host-passthrough"
]
```

Restart the Virtual Machine for this change to take effect.

### The GPU Disappears After Restarting the Virtual Machine

On the validated multi-GPU platform, the assigned GPU occasionally stopped responding after the Virtual Machine was stopped and started again. This behavior may be specific to the hardware topology, where the GPUs had previously been joined, and should not be assumed to affect other AMD GPU configurations.

The observed symptoms were:

* The Host reported the assigned GPU with PCI revision `ff`.
* The GPU was absent from the guest `lspci` output.
* `/dev/kfd` and the DRM render nodes were absent.
* PyTorch reported `RuntimeError: No HIP GPUs are available`.
* The Host log contained `not ready after bus reset` followed by `giving up`.

If these symptoms occur, power off the Virtual Machine and reboot the Host during a maintenance window. Avoid repeatedly rebinding, removing, rescanning, or resetting the affected GPU before consulting the hardware vendor.

### A ROCm Shared Library Is Missing

If PyTorch fails with a missing ROCm library such as `libMIOpen.so.1`, verify that `rocm-ml-libraries` is installed and `/opt/rocm/lib` is registered with the dynamic linker.

The vLLM PyTorch wheel also requires MPI and profiling libraries from the guest operating system. Install the packages shown in the vLLM section if errors mention `libmpi_cxx.so.40`, `librocprofiler-sdk.so.1`, or `libhsa-amd-aqlprofile64.so.1`.

### No Tuned FP8 Kernel Configuration Is Available

When loading a recent FP8 model, vLLM can report:

```default
Using default W8A8 Block FP8 kernel config. Performance might be sub-optimal!
```

This warning is not a correctness failure. It means the vLLM wheel has no tuning file for the detected GPU and one or more matrix shapes in the model, so it uses a generic kernel configuration. Benchmark results can therefore be lower than the eventual performance of a tuned configuration.
