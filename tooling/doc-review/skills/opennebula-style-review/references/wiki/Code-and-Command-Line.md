Code and CLI commands can be added to the document using the [Fenced Codeblock Syntax](https://www.markdownguide.org/extended-syntax/#fenced-code-blocks). The codeblock is opened and closed by three backticks - ``` - you should also include the intended highlighting style after the opening backticks.

## CLI commands

Ideally the user should be able to copy commands directly from the example and run them in the terminal without editing. If manual editing is required by the user, highlight the necessary user inputs (such as usernames, VM IDs or IP addresses) using a placeholder in delimiting chevrons:

```
ssh -L 8443:<VM_IP>:8443 <user>@<REMOTE_IP>
```

Use lower case placeholders for textual inputs such as usernames and upper case placeholders for numerical IDs and IP addresses.

CLI commands should not include terminal prompts such as `root@jumphost:~$` since this interferes with the user copying and pasting the command. Only include prompts in command line examples to explicitly show the user how the prompt should appear. For example, if you intend to show the user what they should expect to see on the command line after invoking a virtual environment.

**CLI Commands with Output Examples**:

CLI commands and output examples should always be presented in separate fenced codeblocks to allow the user to copy the command directly and visually differentiate the command and output (which receive different formatting). Use the `shell` language identifier for the CLI command and the `default` language identifier for the output:

````
```shell
kubectl -n dynamo-cloud get deploy,pod,svc
```
```default
NAME                                                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/dynamo-platform-dynamo-operator-controller-manager   1/1     1            1           27h
deployment.apps/dynamo-platform-nats-box                             1/1     1            1           27h
```
````

## Code and Configuration Files

Code and configuration file examples should be given the appropriate language identifier for the example. The following list shows the language identifiers currently used in the OpenNebula documentation:

* `json` - JSON
* `python` - Python
* `ruby` - Ruby
* `go` - Google Go
* `yaml` - YAML
* `xml` - XML
* `jsx` - React JSX
* `hcl` - HashiCorp Configuration Language (TerraForm)
* `ini` - INI configuration file
* `text` - Text file

## Examples

CLI command:

````
```shell
onevm terminate --hard <ID>
```
````

CLI output:

````
```default
### Report
OpenNebula 7.0 was installed
Sunstone is running on:
  http://192.168.1.130/
Use following to login:
  user: oneadmin
  password: ZMCoOWUsBg
```
````

JSON file:

````
```json
{
  "VM": {
    "NAME": "service_1",
    "ID": "9",
    "TEMPLATE": {"NIC": []}
  }
}
```
````

Python file:

````
```python
import pyone

one = pyone.OneServer("http://one:2633/RPC2", session="oneadmin:onepass" )
hostpool = one.hostpool.info()
host = hostpool.HOST[0]
id = host.ID
```
````

JavaScript file:

````
```javascript
const deps = require('../../package.json').dependencies
const sharedDeps = ({ eager = false } = {}) => ({
   react: {
       singleton: true,
       eager,
       requiredVersion: deps.react,
     },
     // Add other dependencies here as needed
   }) 
module.exports = sharedDeps
```
````