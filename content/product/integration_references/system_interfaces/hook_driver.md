---
title: "Using Hooks"
date: "2025-02-17"
description:
categories:
pageintoc: "289"
tags:
weight: "9"
---

<a id="hooks"></a>

<!--# Using Hooks -->

The Hook subsystem enables the execution of custom scripts tied to a change in state in a particular resource or API call. This opens a wide area of automation for system administrators to tailor their cloud infrastructures. It also features a logging mechanism that allows a convenient way to query the execution history or to retry the execution of a given hook.

## Overview

The hook subsystem has two main components:

- **Hook Manager Driver**: it receives information about every event triggered by the OpenNebula service and publishes it to an event queue. Custom components can also use this queue to subscribe to OpenNebula events, [more information here]({{% relref "#hook-manager-events" %}}).
- **Hook Execution Manager** (HEM): it registers itself to the events that trigger the hooks defined in the system. When an event is received it takes care of executing the corresponding hook command.

{{< image path="/images/hooks-subsystem-architecture.svg" alt="Hook Subsystem" align="center" width="70%" mb="20px" border="false" >}}

Both components are started together with the OpenNebula service. Note that, provided the network communication is secure, you can grant network access to the event queue and hence deploy HEM in a different server.

## Configuration

### Hook Manager

Hook Manager configuration is set in the `HM_MAD` section in `/etc/one/oned.conf`. The configuration attributes are described below:

| Parameter   | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Executable  | Path of the hook driver executable, can be an absolute path or relative to $ONE_LOCATION/lib/mads (or /usr/lib/one/mads/ if OpenNebula was installed in /)                                                                                                                                                                                                                                                                                                                                                                                      |
| Arguments   | Arguments for the driver executable, the following values are supported:<br/><br/>- `--publisher-port`, `-p`: The port where the Hook Manager will publish the events reported by oned.<br/>- `--logger-port`,    `-l`: The port where the Hook Manager will receive information about hook executions.<br/>- `--hwm`,            `-h`: The HWM value for the publisher socket, more information can be found [here](http://zguide.zeromq.org/page:all#High-Water-Marks).<br/>- `--bind`,           `-b`: Address to bind the publisher socket. |

### Hook Execution Manager

Hook Execution Manager configuration is set in `/etc/one/onehem-server.conf`:

| Parameter             | Description                                                                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| debug_level           | Set the log debug level shown in `/var/log/one/onehem.log`                                                                                      |
| hook_base_path        | Base location to look for hook scripts when commands use a relative path (default value `/var/lib/one/remotes/hooks`)                           |
| remote_hook_base_path | Base location to look for hook scripts when commands use a relative path and `REMOTE="yes"` is specified (default value `'/var/lib/one-remotes/hooks'`) |
| subscriber_endpoint   | To subscribe for OpenNebula events, must match those in `HM_MAD` section of `oned.conf`.                                                        |
| replier_endpoint      | To send hook execution results (reply to events) to oned, it must match those in `HM_MAD` section of `oned.conf`.                               |
| concurrency           | Number of hooks executed simultaneously.                                                                                                        |

### Hook Log

You can check the execution results of a hook using the hook log. The hook log stores a record for each execution including the standard output and error of the command, as well as the arguments used. This information is used to retry the execution of a given record.

The number of execution log records stored in the database for each hook can be configured in oned.conf. For example, to keep only the last 10 execution records of each hook use `LOG_RETENTION = 10`. This value can be tuned taking into account the number of hooks and how many times hooks are executed:

```default
HOOK_LOG_CONF = [
    LOG_RETENTION = 10 ]
```

## Hook Types

There are two types of hooks: **API hooks** (triggered on API calls) and **State hooks** (triggered on state change). The main attributes for both types are described in the table below:

| Option          | Mandatory | Description                                                                              |
|-----------------|----------|-------------------------------------------------------------------------------------------|
| NAME            | YES      | The name of the hook.                                                                     |
| COMMAND         | YES      | The command that will be executed when hook is triggered. Typically a path to a script.   |
| ARGUMENTS       | NO       | The arguments that will be passed to the script when the hook is triggered.               |
| ARGUMENTS_STDIN | NO       | If `yes` the ARGUMENTS will be passed through STDIN instead of as command line arguments. |
| TYPE            | YES      | The hook type either `api` or `state`.                                                    |
| TIMEOUT         | NO       | Hook execution timeout. If not used the timeout is infinite.                              |

<a id="api-hooks"></a>

### API Hooks

The API hooks are triggered after the execution of an API call. The specific attributes for API hooks are listed below:

| Option   | Mandatory   | Description                                                                                                     |
|----------|-------------|-----------------------------------------------------------------------------------------------------------------|
| CALL     | YES         | The API call which triggers the hook. For more info about API calls please check [XML-RPC API section.]({{% relref "api#api" %}}) |

For API hooks, the `$API` keyword can be used in the `ARGUMENTS` attribute to get the information about the API call. If `$API` is used, a base64-encoded XML document containing the API call arguments and result will be passed to the hook command. The schema of the XML is [defined here](https://github.com/OpenNebula/one/blob/master/share/doc/xsd/api_info.xsd).

{{< alert title="Note" type="info" >}}
If the API method defined in `CALL` is an `allocate` or `delete`, the `$API` document will also include the template of the corresponding resource.{{< /alert >}} 

The following example defines an API hook that executes the command `/var/lib/one/remotes/hooks/log_new_user.rb` whenever a new user is created:

```default
NAME      = hook-API
TYPE      = api
COMMAND   = "log_new_user.rb"
ARGUMENTS = $API
CALL      = "one.user.allocate"
ARGUMENTS_STDIN = yes
```

<a id="state-hooks"></a>

### State Hooks

The State hooks are only available for **Hosts** and **Virtual Machines** and they are triggered on specific state transitions. The specific attributes to define State hooks are:

| Option    | Mandatory   | Description                                                                                                                                                             |
|-----------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| RESOURCE  | YES         | Type of the resource, supported values are `IMAGE`, `HOST` and `VM`.                                                                                                    |
| REMOTE    | NO          | If `yes` the hook will be executed in the Host that triggered the hook (for Host hooks) or in the Host where the VM is running (for VM hooks). Not used for Image hooks |
| STATE     | YES         | The state that triggers the hook.                                                                                                                                       |
| LCM_STATE | YES         | The LCM state that triggers the hook (Only for VM hooks)                                                                                                                |
| ON        | YES         | For `RESOURCE=VM`, shortcut to define common `STATE`/`LCM_STATE` pairs. Supported values are: PROLOG, RUNNING, SHUTDOWN, STOP, DONE, UNKNOWN, CUSTOM                    |

{{< alert title="Warning" type="warning" >}}
Note that `ON` is mandatory for VM hooks, use `ON=CUSTOM` with `STATE` and `LCM_STATE` to define hooks on specific state transitions.{{< /alert >}} 

For State hooks, `$TEMPLATE` can be used in the `ARGUMENTS` attribute to get the template (in XML format, base64 encoded) of the resource which triggered the hook. The XSD schema files for the XML document of each object are available [here](https://github.com/OpenNebula/one/tree/master/share/doc/xsd)

The following examples define two State hooks for VMs, Hosts, and images:

```default
# VM
NAME = hook-vm
TYPE = state
COMMAND = new_vm.rb
ARGUMENTS = $TEMPLATE
ON = PROLOG
RESOURCE = VM

# HOST
NAME = hook-host
TYPE = state
COMMAND = host-disabled.rb
STATE = DISABLED
RESOURCE = HOST
REMOTE = yes

# IMAGE
NAME = hook-image
TYPE = state
COMMAND = image-ready.rb
STATE = READY
RESOURCE = IMAGE
```

{{< alert title="Note" type="info" >}}
Check each resource guide for info about [Image states]({{% relref "../../../product/virtual_machines_operation/virtual_machines/images#images-states" %}}), [VM states]({{% relref "../../../product/operation_references/configuration_references/vm_states#vm-states" %}}) and [Host states]({{% relref "../../../product/operation_references/configuration_references/host_states#host-states" %}}){{< /alert >}} 

## Managing Hooks

Hooks can be managed via the CLI through the `onehook` command and the API. This section describes the common operations to control the life-cycle of a hook using the CLI.

### Creating Hooks

In order to create a new hook you need to create a hook template:

```default
$ cat > hook.tmpl << EOF
     NAME      = hook-vm
     TYPE      = state
     COMMAND   = vm-pending.rb
     ARGUMENTS = "\$TEMPLATE pending"
     ON        = CUSTOM
     RESOURCE  = VM
     STATE     = PENDING
     LCM_STATE = LCM_INIT
 EOF
```

Then, simply create the hook by running the following command:

```default
$ onehook create hook.tmpl
  ID: 0
```

We have just created a hook which will be triggered each time a VM switches to `PENDING` state.

{{< alert title="Note" type="info" >}}
Note that just one hook can be created for each trigger event.{{< /alert >}} 

### Checking Hook Execution

We can check the execution records of a hook by accessing its detailed information. For example, to get the execution history of the previous hook use `onehook show 0`:

```default
$ onevm create --cpu 1 --memory 2 --name test
  ID: 0
$ onehook show 0
  HOOK 0 INFORMATION
  ID                : 0
  NAME              : hook-vm
  TYPE              : state
  LOCK              : None

  HOOK TEMPLATE
  ARGUMENTS="$TEMPLATE pending"
  COMMAND="vm-pending.rb"
  LCM_STATE="LCM_INIT"
  REMOTE="NO"
  RESOURCE="VM"
  STATE="PENDING"

  EXECUTION LOG
    ID    TIMESTAMP    EXECUTION
    0     09/23 15:10  ERROR (255)
```

We can see that there is an execution which has failed with error code 255. To get more information about a specific execution use the `-e` option:

```default
$ onehook show 0 -e 0
  HOOK 0 INFORMATION
  ID                : 0
  NAME              : hook-vm
  TYPE              : state
  LOCK              : None

  HOOK EXECUTION RECORD
  EXECUTION ID      : 0
  TIMESTAMP         : 09/23 15:10:38
  COMMAND           : /var/lib/one/remotes/hooks/vm-pending.rb PFZNPgogIDxJR...8+CjwvVk0+ pending
  ARGUMENTS         :
  <VM>
  <ID>0</ID>
  <UID>0</UID>
  <GID>0</GID>
  <UNAME>oneadmin</UNAME>
  <GNAME>oneadmin</GNAME>
  <NAME>test</NAME>
  <PERMISSIONS>
      <OWNER_U>1</OWNER_U>
      <OWNER_M>1</OWNER_M>
      <OWNER_A>0</OWNER_A>
      <GROUP_U>0</GROUP_U>
      <GROUP_M>0</GROUP_M>
      <GROUP_A>0</GROUP_A>
      <OTHER_U>0</OTHER_U>
      <OTHER_M>0</OTHER_M>
      <OTHER_A>0</OTHER_A>
  </PERMISSIONS>
  <LAST_POLL>0</LAST_POLL>
  <STATE>1</STATE>
  <LCM_STATE>0</LCM_STATE>
  <PREV_STATE>1</PREV_STATE>
  <PREV_LCM_STATE>0</PREV_LCM_STATE>
  <RESCHED>0</RESCHED>
  <STIME>1569244238</STIME>
  <ETIME>0</ETIME>
  <DEPLOY_ID/>
  <MONITORING/>
  <TEMPLATE>
      <AUTOMATIC_REQUIREMENTS><![CDATA[!(PUBLIC_CLOUD = YES) & !(PIN_POLICY = PINNED)]]></AUTOMATIC_REQUIREMENTS>
      <CPU><![CDATA[1]]></CPU>
      <MEMORY><![CDATA[2]]></MEMORY>
      <VMID><![CDATA[0]]></VMID>
  </TEMPLATE>
  <USER_TEMPLATE/>
  <HISTORY_RECORDS/>
  </VM> pending
  EXIT CODE         : 255

  EXECUTION STDOUT


  EXECUTION STDERR
  ERROR MESSAGE --8<------
  Internal error No such file or directory - /var/lib/one/remotes/hooks/vm-pending.rb
  ERROR MESSAGE ------>8--
```

The `EXECUTION STDERR` message shows the reason for the hook execution failure, in this case because the script does not exist:

```default
Internal error No such file or directory - /var/lib/one/remotes/hooks/vm-pending.rb
```

{{< alert title="Important" type="info" >}}
The hook log can be queried and filtered according to several criteria by using `onehook log`. More info about the `onehook log` command can be found by running `onehook log --help`.{{< /alert >}} 

### Retrying Hook Executions

We are going to fix the previous error. Let’s first create the `vm-pending.rb` script and then retry the hook execution.

{{< alert title="Note" type="info" >}}
Note that any hook execution can be retried regardless of its result.{{< /alert >}} 

```default
$ vim /var/lib/one/remotes/hooks/vm-pending.rb
  #!/usr/bin/ruby
  puts "Executed!"

$ chmod 760 /var/lib/one/remotes/hooks/vm-pending.rb
$ onehook retry 0 0
$ onehook show 0
  HOOK 0 INFORMATION
  ID                : 0
  NAME              : hook-vm
  TYPE              : state
  LOCK              : None

  HOOK TEMPLATE
  ARGUMENTS="$TEMPLATE pending"
  COMMAND="vm-pending.rb"
  LCM_STATE="LCM_INIT"
  REMOTE="NO"
  RESOURCE="VM"
  STATE="PENDING"

  EXECUTION LOG
  ID       TIMESTAMP    RC    EXECUTION
  0        09/23 15:10  255   ERROR
  1        09/23 15:59    0   SUCCESS
```

Note the last successful execution record!

{{< alert title="Important" type="info" >}}
When a hook execution is retried, the same execution context is used, i.e., arguments and $TEMPLATE/$API values.{{< /alert >}} 

## Developing Hooks

The first thing you need to decide is the type of hook you are interested in, either API or STATE hooks. Each type of hook is triggered by a different event and requires/provides different runtime information.

In this section you’ll find two simple script hooks (in ruby) for each type. These examples are good starting points for developing custom hooks.

{{< alert title="Warning" type="warning" >}}
Note that the scripts below import some dependencies that need to be installed properly in the Front-end node. As most of the dependencies are OpenNebula dependencies, these can be used by adding the snippet below to your scripts:

```default
ONE_LOCATION = ENV['ONE_LOCATION']

if !ONE_LOCATION
    RUBY_LIB_LOCATION = '/usr/lib/one/ruby'
    GEMS_LOCATION     = '/usr/share/one/gems'
else
    RUBY_LIB_LOCATION = ONE_LOCATION + '/lib/ruby'
    GEMS_LOCATION     = ONE_LOCATION + '/share/gems'
end

if File.directory?(GEMS_LOCATION)
    Gem.use_paths(GEMS_LOCATION)
end

$LOAD_PATH << RUBY_LIB_LOCATION
```{{< /alert >}} 

### API Hook example

This script prints to stdout the result of one.user.create API call and the username of new user.

```ruby
# Hook template
#
# NAME = user-create
# TYPE = api
# COMMAND = "user_create.rb"
# ARGUMENTS = "$API"
# CALL = "one.user.allocate"

#!/usr/bin/ruby

require 'base64'
require 'nokogiri'

#api_info= Nokogiri::XML(Base64::decode64(STDIN.gets.chomp)) for reading from STDIN
api_info = Nokogiri::XML(Base64::decode64(ARGV[0]))

success = api_info.xpath("/CALL_INFO/RESULT").text.to_i == 1
uname   = api_info.xpath('//PARAMETER[TYPE="IN" and POSITION=2]/VALUE').text

if !success
    puts "Failing to create user"
    exit -1
end

puts "User #{uname} successfully created"
```

### State Hook Example (HOST)

This script prints to stdout when a Host is in error state.

```ruby
# Hook template
#
#NAME = host-error
#TYPE = state
#COMMAND = host_error.rb
#ARGUMENTS="$TEMPLATE"
#STATE = ERROR
#RESOURCE = HOST

#!/usr/bin/ruby

require 'base64'
require 'nokogiri'

#host_template = Nokogiri::XML(Base64::decode64(STDIN.gets.chomp)) for reading from STDIN
host_template = Nokogiri::XML(Base64::decode64(ARGV[0]))

host_id = host_template.xpath("//ID").text.to_i

puts "Host #{host_id} is in error state!!"
```

### State Hook Example (VM)

This script prints to stdout when a VM is in prolog state.

```ruby
# Hook template
#
#NAME = vm-prolog
#TYPE = state
#COMMAND = vm_prolog.rb
#ARGUMENTS = $TEMPLATE
#ON = PROLOG
#RESOURCE = VM

#!/usr/bin/ruby

require 'base64'
require 'nokogiri'

#vm_template = Nokogiri::XML(Base64::decode64(STDIN.gets.chomp)) for reading from STDIN
vm_template = Nokogiri::XML(Base64::decode64(ARGV[0]))

vm_id = vm_template.xpath("//ID").text.to_i

puts "VM #{vm_id} is in PROLOG state"
```

### State Hook Example (IMAGE)

This script prints to stdout the ID of an image when it is ready to use.

```ruby
# Hook template
#
# NAME = image-ready
# TYPE = state
# COMMAND = image_ready.rb
# STATE = READY
# RESOURCE = IMAGE
# ARGUMENTS = "$TEMPLATE"

#!/usr/bin/ruby

require 'base64'
require 'nokogiri'

#img_template = Nokogiri::XML(Base64::decode64(STDIN.gets.chomp)) for reading from STDIN
img_template = Nokogiri::XML(Base64::decode64(ARGV[0]))

img_id = img_template.xpath("//ID").text.to_i

puts "Image #{img_id} ready to use!!"
```

<a id="hook-manager-autostart"></a>

### A Complete Example: Autostart Hooks for KVM

OpenNebula creates *transient* KVM domains, i.e., they only exist while the domain is running. Therefore, the KVM autostart feature cannot be activated via *libvirt* configuration. This example shows how to implement VM autostart for the KVM hypervisor in OpenNebula using State hooks.

The hooks track Host reboots and resume VMs allocated to the Host that include the `AUTOSTART` attribute in their template. If `AUTOSTART=yes` the VM will be automatically restarted if it was running before the Host was rebooted, if `AUTOSTART=always` the VM will always be automatically restarted regardless of its previous state. This functionality is implemented by two State hooks: one for the `HOST` and one for the `VM` resource. The code for both hooks can be found in
`/var/lib/one/remotes/hooks/autostart/` folder.

To install the hooks, create a definition file for each one. The `autostart-host.tmpl` definition file for the Host hook will be as follows:

```default
NAME = autostart-host
TYPE = state
COMMAND = autostart/host
ARGUMENTS = $TEMPLATE
ARGUMENTS_STDIN = yes
RESOURCE = HOST
STATE = MONITORED
```

Similarly for the VM hook, the `autostart-vm.tmpl` definition file will be as follows:

```default
NAME = autostart-vm
TYPE = state
COMMAND = autostart/vm
ARGUMENTS = $TEMPLATE
ARGUMENTS_STDIN = yes
RESOURCE = VM
STATE = POWEROFF
LCM_STATE = LCM_INIT
ON = CUSTOM
```

Now you can create the hooks using these two files:

```default
$ onehook create autostart-host.tmpl
$ onehook create autostart-vm.tmpl
```

{{< alert title="Note" type="info" >}}
Note that any command can be specified in `COMMAND`, for debugging (`COMMAND="/usr/bin/echo"`) can be very helpful.{{< /alert >}} 

<a id="hook-manager-events"></a>

## Hook Manager Events

The Hook Manager publishes the OpenNebula events over a [ZeroMQ publisher socket](http://zguide.zeromq.org/page:all#Getting-the-Message-Out). This can be used for developing custom components that subscribe to specific events to perform custom actions.

### Hook Manager Messages

The Hook Manager sends two different types of messages:

> - **EVENT** messages: represent an OpenNebula event, which could potentially trigger a hook if the Hook Execution Manager is subscribed to it.
> - **RETRY** messages: represent a retry action of a given hook execution. These event messages are specific to the Hook Execution Manager.

Both messages have a **key** that can be used by the subscriber to receive messages related to a specific event class; and a **content** that contains the information related to the event **encoded in base64**.

#### Event Messages Format

There are two different types of EVENT messages, representing API and state events. The key format for both types are listed below:

| EVENT            | Key format                                                                                                                                                         |
|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| API              | `EVENT API <API_CALL> <SUCCESS>` (e.g. `EVENT API one.vm.allocate 1` or `Key: EVENT API one.hook.info 0`)                                                          |
| STATE (HOST)     | `EVENT STATE HOST/<STATE>/` (e.g. `EVENT STATE HOST/INIT/`)<br/><br/>`EVENT HOST <HOST_ID>/<STATE>/` (e.g. `EVENT HOST 0/INIT/`)                                   |
| STATE (VM)       | `EVENT STATE VM/<STATE>/<LCM_STATE>` (e.g. `EVENT STATE VM/PENDING/LCM_INIT`)<br/><br/>`EVENT VM <VM_ID>/<STATE>/<LCM_STATE>` (e.g. `EVENT VM 0/PENDING/LCM_INIT`) |
| CHANGE (SERVICE) | `EVENT SERVICE SERVICE_ID` (e.g. `EVENT SERVICE 0`)                                                                                                                |

Keys are used to subscribe to specific events. Note also that you do not need to specify the whole key, for example `EVENT STATE HOST/ERROR/` will subscribe for state changes to `ERROR` on the Hosts, while `EVENT STATE HOST/` will subscribe for all state changes of the Hosts.

The content of an event message is an XML document containing information related to the event. The XSD representing this content is available [here](https://github.com/OpenNebula/one/tree/master/share/doc/xsd).

#### Retry Messages Format

The key format of the retry messages is just the word `RETRY`, no more info is needed in the key. The retry messages content is an XML file with information about the execution to retry. The XSD representing this content is available [here](https://github.com/OpenNebula/one/tree/master/share/doc/xsd).

### Subscriber Script Example

Below is an example of a script which retrieves all the event messages and prints their key and their content:

```default
#!/usr/bin/ruby

require 'ffi-rzmq'
require 'base64'

@context    = ZMQ::Context.new(1)
@subscriber = @context.socket(ZMQ::SUB)

@subscriber.setsockopt(ZMQ::SUBSCRIBE, "EVENT")
@subscriber.connect("tcp://localhost:2101")

key = ''
content = ''

loop do
    @subscriber.recv_string(key)
    @subscriber.recv_string(content)

    puts "Key: #{key}\nContent: #{Base64.decode64(content)}"
    puts "\n===================================================================\n"
end
```

{{< alert title="Note" type="info" >}}
Note that the key and the content are read separately as [ZeroMQ envelopes](http://zguide.zeromq.org/page:all#Pub-Sub-Message-Envelopes) are used.{{< /alert >}} 
