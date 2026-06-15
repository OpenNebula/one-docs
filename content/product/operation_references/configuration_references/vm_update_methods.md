---
title: 'Updating Virtual Machine Configuration'
linkTitle: 'Updating VM Configuration'
---
<!-- README before editing: This document contains an automatically generated table! -->
<!-- Add rows to the source CSV file to update the table, do not change the column structure! -->
<!-- Table source:  assets/tables/vm_update_methods.csv -->
<!-- Run the converter script from the root directory to regenerate the table: -->
<!-- Install dependencies first: python3 -m pip install openpyxl -->
<!-- python3 scripts/vm_update_methods_converter.py -->
<!-- You may edit the text above and below the table directly in this document. Do not edit the table here! -->

OpenNebula provides a powerful set of tools through the GUI, CLI and API that allow you to update Virtual Machine configuration on the fly, even while the VM is running. This flexibility enables you to optimize performance, adjust resource allocation, and manage your virtual infrastructure with ease. The following table details all the VM configuration update methods available with interface coverage and notes. Use the filter to find the methods relevant to your use case.

## VM Configuration Update Methods Reference

<!-- VM METHODS TABLE -->
{{< vm-methods-table >}}
<table id="data-spreadsheet" class="display" style="width:100%">
  <thead>
    <tr class="dt-layout-row">
      <th>SectionTracker</th>
      <th style="width: 22%;">Method</th>
      <th style="width: 13%;">Attribute</th>
      <th style="width: 12%;">Description</th>
      <th style="width: 12%;">Updating in RUNNING state</th>
      <th style="width: 12%;">Updating in POWEROFF state</th>
      <th style="width: 5%;">API</th>
      <th style="width: 5%;">CLI</th>
      <th style="width: 5%;">GUI</th>
      <th style="width: 20%;">Limitations/Notes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Compute</td>
      <td>one.vm.resize</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/CPU</span></td>
      <td>Changes VM CPU allocation factor</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Scheduler/resource allocation attribute; changes applied after power cycle for effective runtime impact</td>
    </tr>
    <tr>
      <td>Compute</td>
      <td>one.vm.resize</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/VCPU</span></td>
      <td>Changes VM virtual CPU count</td>
      <td>Partial</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>VCPU hotplug support required for live effect; otherwise applied after reboot</td>
    </tr>
    <tr>
      <td>Compute</td>
      <td>one.vm.resize</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/MEMORY</span></td>
      <td>Changes VM memory allocation</td>
      <td>Partial</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Memory hotplug support required for live effect; otherwise applied after reboot</td>
    </tr>
    <tr>
      <td>Disk</td>
      <td>one.vm.attach</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/DISK</span></td>
      <td>Attaches a disk to the VM</td>
      <td>Partial</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Disk hotplug support depends on disk bus/controller</td>
    </tr>
    <tr>
      <td>Disk</td>
      <td>one.vm.detach</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/DISK</span></td>
      <td>Detaches a disk from the VM</td>
      <td>Partial</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>May fail for active/system disks or unsupported buses</td>
    </tr>
    <tr>
      <td>Disk</td>
      <td>one.vm.diskresize</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/DISK</span></td>
      <td>Resizes VM disk</td>
      <td>Partial</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>May fail for active/system disks or unsupported buses</td>
    </tr>
    <tr>
      <td>Disk</td>
      <td>one.vm.disksaveas</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/DISK</span></td>
      <td>Saves VM disk as image</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>NIC</td>
      <td>one.vm.attachnic</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/NIC</span></td>
      <td>Attaches NIC to the VM</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>NIC</td>
      <td>one.vm.detachnic</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/NIC</span></td>
      <td>Detaches NIC from the VM</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>NIC</td>
      <td>one.vm.updatenic</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/NIC</span></td>
      <td>Updates VM NIC configuration</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>NIC</td>
      <td>one.vm.attachsg</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/NIC/SECURITY_GROUPS</span></td>
      <td>Attaches security group to VM NIC</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>NIC</td>
      <td>one.vm.detachsg</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/NIC/SECURITY_GROUPS</span></td>
      <td>Detaches security group from VM NIC</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>PCI</td>
      <td>one.vm.attachpci</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/PCI</span></td>
      <td>Attaches PCI device to the VM</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Only in POWER OFF state</td>
    </tr>
    <tr>
      <td>PCI</td>
      <td>one.vm.detachpci</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/PCI</span></td>
      <td>Detaches PCI device from the VM</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Only in POWER OFF state</td>
    </tr>
    <tr>
      <td>Snapshots</td>
      <td>one.vm.snapshotcreate</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/SNAPSHOT</span></td>
      <td>Creates VM snapshot</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>Snapshots</td>
      <td>one.vm.snapshotrevert</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/SNAPSHOT</span></td>
      <td>Reverts VM to snapshot state</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Only in POWER OFF state</td>
    </tr>
    <tr>
      <td>Snapshots</td>
      <td>one.vm.snapshotdelete</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/SNAPSHOT</span></td>
      <td>Deletes VM snapshot</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>Snapshots</td>
      <td>one.vm.disksnapshotcreate</td>
      <td class="truncated-attribute"><span class="cell-content">VM/SNAPSHOTS/SNAPSHOT</span></td>
      <td>Creates disk snapshot</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>Snapshots</td>
      <td>one.vm.disksnapshotdelete</td>
      <td class="truncated-attribute"><span class="cell-content">VM/SNAPSHOTS/SNAPSHOT</span></td>
      <td>Deletes disk snapshot</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>Snapshots</td>
      <td>one.vm.disksnapshotrevert</td>
      <td class="truncated-attribute"><span class="cell-content">VM/SNAPSHOTS/SNAPSHOT</span></td>
      <td>Reverts disk to snapshot state</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Only in POWER OFF state</td>
    </tr>
    <tr>
      <td>Snapshots</td>
      <td>one.vm.disksnapshotrename</td>
      <td class="truncated-attribute"><span class="cell-content">VM/SNAPSHOTS/SNAPSHOT</span></td>
      <td>Renames disk snapshot</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>Backups</td>
      <td>one.vm.backup</td>
      <td class="truncated-attribute"><span class="cell-content">VM/BACKUPS</span></td>
      <td>Creates VM backup</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>Backups</td>
      <td>one.vm.backupcancel</td>
      <td class="truncated-attribute"><span class="cell-content">VM/BACKUPS</span></td>
      <td>Cancels running VM backup job</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>Backups</td>
      <td>one.vm.restore</td>
      <td class="truncated-attribute"><span class="cell-content">VM/BACKUPS</span></td>
      <td>Restores VM disks/state from backup</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Only in POWER OFF state</td>
    </tr>
    <tr>
      <td>VM attributes</td>
      <td>one.vm.update</td>
      <td class="truncated-attribute"><span class="cell-content">VM/USER_TEMPLATE</span></td>
      <td>Updates VM user template</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Updates on the next power cycle</td>
    </tr>
    <tr>
      <td>VM attributes</td>
      <td>one.vm.rename</td>
      <td class="truncated-attribute"><span class="cell-content">VM/NAME</span></td>
      <td>Renames VM</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>VM attributes</td>
      <td>one.vm.chown</td>
      <td class="truncated-attribute"><span class="cell-content">VM/UID, VM/GID, VM/UNAME, VM/GNAME</span></td>
      <td>Changes VM ownership</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>VM attributes</td>
      <td>one.vm.chmod</td>
      <td class="truncated-attribute"><span class="cell-content">VM/PERMISSIONS</span></td>
      <td>Changes VM permissions</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>VM scheduled actions</td>
      <td>one.vm.schedadd</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/SCHED_ACTION</span></td>
      <td>Adds scheduled VM action</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>VM scheduled actions</td>
      <td>one.vm.schedupdate</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/SCHED_ACTION</span></td>
      <td>Updates scheduled VM action</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>VM scheduled actions</td>
      <td>one.vm.scheddelete</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/SCHED_ACTION</span></td>
      <td>Deletes scheduled VM action</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>Other</td>
      <td>one.vm.lock</td>
      <td class="truncated-attribute"><span class="cell-content">VM/LOCK</span></td>
      <td>Locks VM actions</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>Other</td>
      <td>one.vm.unlock</td>
      <td class="truncated-attribute"><span class="cell-content">VM/LOCK</span></td>
      <td>Unlocks VM actions</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>Other</td>
      <td>one.vm.exec</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/QEMU_GA_EXEC</span></td>
      <td>Executes command inside guest</td>
      <td>YES</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Requires guest agent</td>
    </tr>
    <tr>
      <td>Other</td>
      <td>one.vm.retryexec</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/QEMU_GA_EXEC</span></td>
      <td>Retries guest command</td>
      <td>YES</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Requires guest agent</td>
    </tr>
    <tr>
      <td>Other</td>
      <td>one.vm.cancelexec</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/QEMU_GA_EXEC</span></td>
      <td>Cancels guest command</td>
      <td>YES</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Requires guest agent</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/ARCH</span></td>
      <td>Defines guest CPU architecture</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Effectively immutable for existing VM</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/MACHINE</span></td>
      <td>Defines machine/chipset type used by hypervisor</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/KERNEL</span></td>
      <td>Defines kernel image for direct kernel boot</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume; direct kernel boot only</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/INITRD</span></td>
      <td>Defines initrd image for direct kernel boot</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume; direct kernel boot only</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/BOOTLOADER</span></td>
      <td>Defines external bootloader</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Not applicable/ignored in KVM</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/BOOTLOADER</span></td>
      <td>Defines VM boot device</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Reflected in OpenNebula UI; libvirt may resolve as default disk boot</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/KERNEL_CMD</span></td>
      <td>Defines kernel command line parameters</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume; direct kernel boot only</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/ROOT</span></td>
      <td>Defines guest root device</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume; direct kernel boot only</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/SD_DISK_BUS</span></td>
      <td>Defines bus type for SD disks</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume;</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/UUID</span></td>
      <td>Defines VM UUID</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/FIRMWARE</span></td>
      <td>Defines VM firmware/UEFI loader</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume; requires valid OVMF path</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/OS/FIRMWARE_FORMAT</span></td>
      <td>Defines firmware image format</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume with firmware</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/CPU_MODEL/MODEL</span></td>
      <td>Defines guest CPU model exposed to VM</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume if CPU model is valid for host</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/CPU_MODEL/FEATURES</span></td>
      <td>Defines guest CPU feature flags</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume if features are supported by host CPU</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/FEATURES/ACPI</span></td>
      <td>Enables ACPI support</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/FEATURES/PAE</span></td>
      <td>Enables Physical Address Extension support</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/FEATURES/APIC</span></td>
      <td>Enables APIC support</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/FEATURES/LOCALTIME</span></td>
      <td>Configures guest RTC clock mode</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/FEATURES/HYPERV</span></td>
      <td>Enables Hyper-V enlightenments</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/FEATURES/GUEST_AGENT</span></td>
      <td>Enables QEMU guest agent channel</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/FEATURES/VIRTIO_SCSI_QUEUES</span></td>
      <td>Configures virtio-scsi queue count</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/FEATURES/VIRTIO_BLK_QUEUES</span></td>
      <td>Configures virtio-blk queue count</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/FEATURES/IOTHREADS</span></td>
      <td>Configures disk IO threads</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/INPUT/TYPE</span></td>
      <td>Defines guest input device type</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/INPUT/BUS</span></td>
      <td>Defines guest input device bus</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/GRAPHICS/TYPE</span></td>
      <td>Defines graphics protocol/backend</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Template changes while running; applied after poweroff/resume. SPICE works with external clients, not FireEdge/Guacamole in this setup</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/GRAPHICS/LISTEN</span></td>
      <td>Defines graphics listen address</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/GRAPHICS/PASSWD</span></td>
      <td>Defines graphics console password</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume; password prompt works with external VNC/SPICE clients, not via FireEdge/Guacamole</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/GRAPHICS/KEYMAP</span></td>
      <td>Defines keyboard layout for graphics console</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/GRAPHICS/COMMAND</span></td>
      <td>Defines graphics command parameters</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Stored in template but not passed to libvirt domain XML in KVM</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/VIDEO/TYPE</span></td>
      <td>Defines virtual video adapter type</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>Live-applied; without VRAM/related options may fall back to default model such as cirrus</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/VIDEO/IOMMU</span></td>
      <td>Enables IOMMU support for video device</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/VIDEO/ATS</span></td>
      <td>Enables Address Translation Service for video device</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/VIDEO/VRAM</span></td>
      <td>Defines virtual video memory size</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/VIDEO/RESOLUTION</span></td>
      <td>Defines guest display resolution</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/RAW/DATA</span></td>
      <td>Defines raw hypervisor XML snippet</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Applied after poweroff/resume</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/RAW/DATA_VMX</span></td>
      <td>Defines VMX-specific raw configurationDefines VMX-specific raw configuration</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Not applicable to KVM; template-only/no effect</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/RAW/TYPE</span></td>
      <td>Defines hypervisor backend type</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Acts as driver selector; for KVM must be kvm</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/RAW/VALIDATE</span></td>
      <td>Enables raw XML validation</td>
      <td>NO</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>NO</td>
      <td>Template/validation behavior; not a live libvirt change</td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/BACKUP_CONFIG/FS_FREEZE</span></td>
      <td>Enables filesystem freeze during backup</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/BACKUP_CONFIG/KEEP_LAST</span></td>
      <td>Defines number of retained backups</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/BACKUP_CONFIG/BACKUP_VOLATILE</span></td>
      <td>Includes volatile disks in backup</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/BACKUP_CONFIG/MODE</span></td>
      <td>Defines backup mode</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
    <tr>
      <td>one.vm.updateconf</td>
      <td>one.vm.updateconf</td>
      <td class="truncated-attribute"><span class="cell-content">VM/TEMPLATE/BACKUP_CONFIG/INCREMENT_MODE</span></td>
      <td>Defines incremental backup mode</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td>YES</td>
      <td></td>
    </tr>
  </tbody>
</table>
{{< /vm-methods-table >}}