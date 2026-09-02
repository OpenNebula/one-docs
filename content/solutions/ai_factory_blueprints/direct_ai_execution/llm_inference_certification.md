---
title: "Inferencing with vLLM"
linkTitle: "Inferencing with vLLM"
date: "2025-10-28"
description:
categories:
pageintoc: "68"
tags: ['AI','vLLM']
weight: 4
---

The [vLLM](https://docs.vllm.ai/en/latest/) Inference Framework is a production-grade, high-performance inference engine designed for large-scale LLM serving.

The main characteristics of vLLM Inference Framework are:

- Supports single-node deployments with one or more GPUs.
- Uses Python’s native multiprocessing for multi-GPU inference.
- Does not require additional frameworks, such as Ray, unless deploying across multiple nodes, which is out of scope for this benchmarking task.

In this guide you will find the necessary steps and best practices to deploy the OpenNebula vLLM appliance and perform an inference benchmarking to check its performance.

## Before Starting 

Before starting this tutorial, you must complete the AI-factory deployment with either on-premises resources or cloud resources. Please complete one of the following guides relevant to your available resources:

* [AI Factory Deployment with On-premises hardware]({{% relref "/solutions/ai_factory_blueprints/deployment/cd_on-premises" %}})
* [AI Factory Deployment on Scaleway Cloud]({{% relref "solutions/ai_factory_blueprints/deployment/cd_cloud"%}})

## Deploying the vLLM Appliance

The vLLM appliance is available through the OpenNebula Marketplace, offering a [streamlined setup process](https://github.com/OpenNebula/one-apps/wiki/vllm_quick) suitable for both novice and experienced users.

To deploy the vLLM appliance for benchmarking, follow these steps:

1. Download the vLLM appliance from the marketplace:
    ``` shell
    onemarketapp export 'service_Vllm' vllm --datastore default
    ```

2. Configure the template for [GPU PCI passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}):
    ```shell
    onetemplate update vllm
    ```

    In this scenario, configure the template for GPU Passthrough to the VM, attach a NIC on a desired network (in our case we are using the `admin_net` network, but you can choose any of your preference) and adjust the CPU and memory to your requirements, for instance:

    ```shell
    PCI=[
        CLASS="0302",
        DEVICE="26b9",
        VENDOR="10de" ]
    NIC=[ NETWORK="admin_net" ]
    VCPU="32"
    CPU="32"
    MEMORY="32768"
    ```

    To find the relevant details from the command line, on the command line of the node where you will deploy the vLLM appliance run the following command:

    ```bash
    lspci -nn | grep -i nvidia
    ```

    This command outputs something similar to the following:

    ```bash
    c1:00.0 3D controller [0302]: NVIDIA Corporation AD102GL [L40S] [10de:26b9] (rev a1)
    ```

    Compare with the above PCI template section to match the corresponding template fields.

3. Instantiate the template. Keep the default attributes, only changing the LLM Model through the `ONEAPP_VLLM_MODEL_ID` input for each benchmark you do, which means that you will need to instantiate a different VM with the different models for the execution of each benchmark:
    ```shell
    onetemplate instantiate vllm --name vllm
    ```

4. Wait until the vLLM engine has loaded the model and the application is served. To confirm progress, access the VM via SSH and check the logs located in `/var/log/one-appliance/vllm.log`.

    4.1 To access the VM, run the following command:

    ```shell
    onevm ssh vllm
    ```

    While the vLLM appliance is initializing, you will see the following on the command line:

    ```default

    The list of available updates is more than a week old.
    To check for new updates run: sudo apt update


    ___   _ __    ___
    / _ \ | '_ \  / _ \   OpenNebula Service Appliance
    | (_) || | | ||  __/
    \___/ |_| |_| \___|


    3/3 Bootstrap step is in progress...

    * * * * * * * *
    * PLEASE WAIT *
    * * * * * * * *
    ```

    Once the vLLM appliance has initialized, it will change to this:

    ```default
    The list of available updates is more than a week old.
    To check for new updates run: sudo apt update


    ___   _ __    ___
    / _ \ | '_ \  / _ \   OpenNebula Service Appliance
    | (_) || | | ||  __/
    \___/ |_| |_| \___|


    All set and ready to serve 8)
    ```

    4.2 From inside the VM, check the logs in `/var/log/one-appliance/vllm.log`. You should see an output similar to this:

    ```default
    [...]

    (APIServer pid=2480) INFO 11-26 11:00:33 [api_server.py:1971] Starting vLLM API server 0 on http://0.0.0.0:8000
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:36] Available routes are:
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:44] Route: /openapi.json, Methods: HEAD, GET
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:44] Route: /docs, Methods: HEAD, GET
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:44] Route: /docs/oauth2-redirect, Methods: HEAD, GET
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:44] Route: /redoc, Methods: HEAD, GET
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:44] Route: /health, Methods: GET
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:44] Route: /load, Methods: GET
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:44] Route: /ping, Methods: POST
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:44] Route: /ping, Methods: GET
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:44] Route: /tokenize, Methods: POST
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:44] Route: /detokenize, Methods: POST
    (APIServer pid=2480) INFO 11-26 11:00:33 [launcher.py:44] Route: /v1/models, Methods: GET

    [...]

    ```

    At this point, the vLLM API is available. Perform a test it through curl, pointing to the port 8000 of the VM and querying the `v1/models` path:
    ```shell
    curl http://localhost:8000/v1/models | jq .
    ```

    You will retrieve a json response with the loaded models:
    ```json
    {
        "object": "list",
        "data": [
            {
            "id": "Qwen/Qwen2.5-1.5B-Instruct",
            "object": "model",
            "created": 1764154926,
            "owned_by": "vllm",
            "root": "Qwen/Qwen2.5-1.5B-Instruct",
            "parent": null,
            "max_model_len": 1024,
            "permission": [
                {
                "id": "modelperm-431ea3199da545b2a5cba62dc373ab53",
                "object": "model_permission",
                "created": 1764154926,
                "allow_create_engine": false,
                "allow_sampling": true,
                "allow_logprobs": true,
                "allow_search_indices": false,
                "allow_view": true,
                "allow_fine_tuning": false,
                "organization": "*",
                "group": null,
                "is_blocking": false
                }
            ]
            }
        ]
    }
    ```

    Additionally, the appliance includes a webchat app for interacting with the vLLM chat API. This web application is exposed through the VM `5000` port (see the [port forwarding instructions](#port-forwarding-for-remote-hardware) if you are running on remote hardware):

    {{< image path="/images/ai_factories/vllm_chatbot.png" alt="vLLM webchat" align="center" width="70%" mb="20px" border="false" >}} 

    If these verification steps are successful, the vLLM appliance is ready to run the benchmarks.

## LLM Inference Benchmarking

As industries adopt Large Language Models (LLMs), optimization and validation of their inference performance are critical aspects of the deployment. Efficient inference is essential to guarantee that LLMs deliver high-quality results while maintaining scalability, responsiveness, and cost-effectiveness.

The LLM Inference Benchmarks focus on measuring performance metrics during the model serving process rather than the quality of the generated result. Metrics assessed by this type of benchmarks include:
  - **Latency**: How fast the model responds to a request.
  - **Throughput**: The number of requests the model can handle per unit of time.
  - **Stability**: Model serving consistency under varying loads.

### Benchmark Environments

To test the vLLM appliance, the benchmark uses two similar environments, but with different GPU models:
- Benchmark environment 1: 1x NVIDIA L40S 48GB GPU cards
- Benchmark environment 2: 1x NVIDIA H100L 94GB GPU card

### Hardware Specification

#### Front-end Requirements

| Front-end  |
| :---- | :---- |
| Number of Zones | 1 |
| Cloud Manager | OpenNebula 7.0 |
| Server Specs | Supermicro Hyper A+ server, details in the [table below](#server-specifications) |
| Operating System | Ubuntu 24.04.2 LTS |
| High Availability | No (1 Front-end) |
| Authorization | Built-in |

#### Host Requirements

| Virtualization Hosts  |
| :---- | :---- |
| Number of Nodes | 1 |
| Server Specs | Supermicro Hyper A+ server, details in the [table below](#server-specifications) |
| Operating System | Ubuntu 24.04.2 LTS |
| Hypervisor | KVM |
| Special Devices | NVIDIA GPU cards, details in [table below](#server-specifications)|

#### Storage Specification

| Storage   |
| :---- | :---- |
| Type | Local disk |
| Capacity | 1 Datastore |

#### Network Requirements

| Network   |
| :---- | :---- |
| Networking | Bridge |
| Number of Networks | 1 networks: service |

#### Provisioning Model

| Provisioning Model  |
| :---- | :---- |
| Manual on-prem | The two servers have been manually provisioned and configured on-prem. |

#### Server Specifications

The server specifications are based on a two-server setup for each environment: one server operates as the OpenNebula frontend and the other one is the cluster for VMs host with the GPU cards attached. This setup is compatible with any OpenNebula setup having a host server with AI-ready NVIDIA GPUs.

| Parameter                | Environment 1                                 | Environment 2                                 |
|--------------------------|-----------------------------------------------|-----------------------------------------------|
| **GPU model**            | NVIDIA L40S 48GB                              | NVIDIA H100L 94GB                             |
| **Server model**         | Supermicro A+ Server AS -2025HS-TNR           | Supermicro A+ Server AS -2025HS-TNR           |
| **Architecture**         | amd64 (x86_64 bits)                           | amd64 (x86_64 bits)                           |
| **CPU Model**            | AMD(R) EPYC 9334 Processor @2.7GHz            | AMD (R) EPYC 9335 Processor @3.0GHz           |
| **CPU Vendor**           | AMD(R)                                        | AMD(R)                                        |
| **CPU Cores**            | 128 (2 socket × 32 cores, 2 threads per core) | 128 (2 socket × 32 cores, 2 threads per core) |
| **CPU Frequency**        | 2,7 GHz                                       | 3,0 GHz                                       |
| **NUMA Nodes**           | 2 (Node0: CPUs 0-63, Node1: CPUs 64-128)      | 2 (Node0: CPUs 0-63, Node1: CPUs 64-128)      |
| **L1d Cache**            | 2 MiB (64 instances)                          | 3 MiB (64 instances)                          |
| **L1i Cache**            | 2 MiB (64 instances)                          | 2 MiB (64 instances)                          |
| **L2 Cache**             | 64 MiB (64 instances)                         | 64 MiB (64 instances)                         |
| **L3 Cache**             | 256 MiB (8 instances)                         | 256 MiB (8 instances)                         |
| **BIOS Vendor**          | American Megatrends Inc. (AMI)                | American Megatrends Inc. (AMI)                |
| **BIOS Release Date**    | 10/07/2024                                    | 03/31/2025                                    |
| **BIOS Version**         | 3.0                                           | 3.5                                           |
| **BIOS Firmware Rev**    | 5.27                                          | 5.35                                          |
| **ROM Size**             | 32MB                                          | 32MB                                          |
| **Boot Mode**            | UEFI, ACPI supported                          | UEFI, ACPI supported                          |
| **Disks**                | 1 × NVMe (SAMSUNG MZQL215THBLA-00A07, 15TB)   | 1 × NVMe (KIOXIA KCD6XLUL15T3, 15TB)          |
| **Partitions**           | /boot/efi (1G), /boot (2G), LVM root (14T)    | /boot/efi (1G), /boot (2G), LVM root (14T)    |
| **Network**              | 1 × Intel X710 10G GbE                        | 1 × Intel X710 10G GbE                        |
| **RAM**                  | 1152 GB (24x48GB DDR5-4800)                   | 1536 GB (24x64GB DDR5-6400)                   |


### Benchmarks Models

The certification includes two LLM architectures — Qwen and Llama — each tested in two different parameter sizes.

Qwen Models:
- `Qwen/Qwen2.5-3B-Instruct`
- `Qwen/Qwen2.5-14B-Instruct`

Llama Models:
- `meta-llama/Llama-3.2-3B-Instruct`
- `meta-llama/Llama-3.2-7B-Instruct`

The benchmark process is based on [GuideLLM](https://github.com/vllm-project/guidellm), the native benchmarking tool provided by vLLM for optimizing and testing deployed models.

### Executing the Benchmarks

####  Running the Benchmark Scripts

Within the `/root` directory of the vLLM appliance, you will find [`benchmark.sh`](https://github.com/OpenNebula/one-apps/blob/ec3f5b740dc2a4201f8ed971f93beb195202bfef/appliances/Vllm/scripts/benchmark.sh) which executes GuideLLM CLI. This script automatically detects environment parameters, launches the benchmark using GuideLLM, and displays live updates of progress as well as results through the CLI. Specifically, the benchmark follows these steps:

- To test performance and stability, the script sends hundreds of requests in parallel.
- To run the benchmark, the script uses automatically-generated synthetic data with these values:
    - **Input prompt**: Average 511 tokens
    - **Output prompt**: Average 255 tokens
    - **Total samples**: 999
- GuideLLM identifies the throughput that the inference can handle.
- Once the throughput is identified, 9 additional runs are performed at a fixed requests-per-second rate (below the identified throughput) to determine stability and final results.

To run the benchmark, follow this procedure:

1. Connect to the vLLM appliance through ssh:
    ```shell
    onevm ssh vllm
    ```

2. Execute the benchmark script inside the appliance:
    ```shell
    ./benchmark.sh
    ```
    
    Once the benchmark is running, you will see this output:           

    {{< image path="/images/ai_factories/vllm_benchmark.png" alt="vLLM benchmark" align="center" width="90%" mb="20px" border="false" >}}

    There are more parameters available within the benchmarking such as warmups, number of steps, and seconds per step. These parameters are fixed but can be manually adapted if needed.

3. Once finished, the process outputs the results on the terminal and generates an HTML report with all given information in the `/root/benchmark_results` directory:

    {{< image path="/images/ai_factories/vllm_benchmark_results.png" alt="vLLM benchmark results" align="center" width="90%" mb="20px" border="false" >}}


### Benchmark Results

The following key performance metrics have been be tested for each model:

| Metric                            | Description                                                                              | Unit   |
|-----------------------------------|----------------------------------------------------------------------------------------  |--------|
| Request rate (throughput)         | Number of requests processed per second.                                                 | req/s  |
| Time to first token (TTFT)        | Time elapsed before the first token is generated.                                        | ms     |
| Inter-token latency (ITL or TPOT) | Average time between consecutive tokens during generation.                               | ms     |
| Latency                           | Time to process individual requests. Low latency is essential for interactive use cases. | ms     |
| Throughput                        | Number of requests handled per second. High throughput indicates good scalability.       | req/s  |

Different application types have distinct performance requirements. The following GuideLLM reference SLOs provide general benchmarks for evaluating inference quality (times for 99% of requests):

| Use Case                           | Req. Latency (ms) | TTFT (ms)  | ITL (ms) |
|------------------------------------|-------------------|------------|----------|
| Chat Applications              | -                 | ≤ 200      | ≤ 50     |
| Retrieval-Augmented Generation | -                 | ≤ 300      | ≤ 100    |
| Agentic AI                    | ≤ 5000            | -          | -        |
| Content Generation             | -                 | ≤ 600      | ≤ 200    |
| Code Generation               | -                 | ≤ 500      | ≤ 150    |
| Code Completion                | ≤ 2000            | -          | -        |

The following table contains the results of the benchmark for each model:

| Models                            | vCPUS | RAM    | GPU   | Throughput (req/s) | TTFT (ms) | ITL (ms) | TPOT (ms) | p99 TTFT (ms) | p99 ITL (ms) | p99 TPOT (ms) |
|-----------------------------------|--------|--------|-------|--------------------|------------|-----------|------------|----------------|---------------|----------------|
| Qwen/Qwen2.5-3B-Instruct          | 32     | 32 GB  | L40s  | 6.4                | 61.8       | 15.2      | 15.2       | 170            | 15.4          | 15.3           |
| Qwen/Qwen2.5-3B-Instruct          | 32     | 32 GB  | H100L | 34                 | 34         | 8.3       | 8.3        | 115            | 8.2           | 8.2            |
| Qwen/Qwen2.5-14B-Instruct         | 32     | 32 GB  | L40s  | -                  | -          | -         | -          | -              | -             | -              |
| Qwen/Qwen2.5-14B-Instruct         | 32     | 32 GB  | H100L | 20                 | 7000       | 0         | 0          | 7000           | 0             | 0              |
| meta-llama/Llama-3.1-3B-Instruct  | 32     | 32 GB  | L40s  | 3.3                | 59.7       | 13        | 12.9       | 87             | 13.1          | 13.1           |
| meta-llama/Llama-3.1-3B-Instruct  | 32     | 32 GB  | H100L | 30                 | 56         | 12        | 11.9       | 331            | 12.4          | 12.3           |


OpenNebula includes the obtained results in controlled environments, with given hardware and using specific models. This information can later be used to compare future results, assess deployments, and evaluate performance against known baselines.

{{< alert title="Tip" type="info" >}}
Alternatively, after validating your AI Factory with LLM Inference, you may choose to follow [Validation with AI-Ready Kubernetes]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}}).
{{< /alert >}}

## Next Steps

Before continuing with other AI Factory guides, you should undeploy the vLLM appliance to free up the GPU and system resources. On your OpenNebula Front-end machine run the following commands as the `oneadmin` user:

Find the ID of the vLLM VM:

```shell
onevm list
```

Then:

```shell
onevm terminate <vLLM_VM_ID>
```

Now that you have completed benchmarking your AI Factory deployment with the vLLM appliance, we recommend continuing with the following AI Factory guides:

* [Fine-Tuning on NVIDIA Slurm]({{% relref "solutions/ai_factory_blueprints/direct_ai_execution/nvidia_slurm" %}})
* [AI-ready Kubernetes Guide]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}})

## Port Forwarding for Remote Hardware

If you are running the vLLM on remote hardware, you will need to use port forwarding to forward port 5000 from the vLLM appliance VM to your local machine to access the web chat through a browser. 

Run `onevm list` to find the ID of the vLLM appliance, then run `onevm show <vLLM_VM_ID> | grep ETH0_IP` to show its IP address. Then from your local machine run the following command:

```shell
ssh -L 5000:<vLLM_VM_IP>:5000 <user>@<REMOTE_HOST_IP>
```

You can then access the chatbot by visiting `http://localhost:5000` in a web browser on your local machine. 
