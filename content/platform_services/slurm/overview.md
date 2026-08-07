---
title: "Elastic Slurm Overview"
linkTitle: "Overview"
weight: 2
type: docs
---

{{< alert title="Work In Progress" type="primary" >}}
This Elastic Slurm appliance and documentation are currently under development. Please contact the [OpenNebula sales and customer support team](https://opennebula.io/contact/) if you would like to arrange a demonstration of OpenNebula's Slurm integration.
{{< /alert >}} 

The OpenNebula Elastic Slurm Service enables the deployment of scalable Slurm Clusters using preconfigured OpenNebula appliances and OneFlow.

Slurm is an open source, fault-tolerant, and highly scalable workload manager and job scheduling system for executing AI and HPC workloads on Linux Clusters. It allocates compute resources to workloads, starts and monitors jobs on the assigned nodes, and manages pending jobs through scheduling queues. Slurm operates without kernel modifications and is largely self-contained.

OpenNebula provides multiple appliances for deploying a Slurm Cluster:

* [**OneSlurm Service**](https://marketplace.opennebula.io/appliance/8ce164d5-3cce-42a7-b9a7-0e8133ef92c6): Slurm Cluster manager for KVM Hosts, orchestrated by OneFlow.
* [**Slurm Controller**](https://marketplace.opennebula.io/appliance/db17c081-969f-45e0-9c8b-e0f7236c15aa): Manages Cluster coordination and scheduling.
* [**Slurm Worker**](https://marketplace.opennebula.io/appliance/c03f8c40-39bb-42cd-a9d5-781f59846b57): Provides the compute capacity used to run jobs.

The appliances are designed to operate together as roles within a OneFlow service. The controller publishes the information required to coordinate the Cluster through OneGate, while worker nodes automatically retrieve this information and join the Cluster.

This architecture allows worker capacity to be added or removed through OneFlow, providing a foundation for elastic Slurm Clusters managed through OpenNebula.

For deployment instructions, configuration options, and operational details, refer to the [Slurm Wiki Documentation](https://github.com/OpenNebula/one-apps/wiki/slurm_intro).