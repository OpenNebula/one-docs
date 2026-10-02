# OpenNebula Documentation

Welcome to the OpenNebula documentation repository. 

This repository contains the documentation for the OpenNebula system. The documentation is updated here as part of a Docs-as-Code process to keep the documentation in line with the evolving OpenNebula system.

## Contributing to the Documentation

* If you are contributing to the documentation as an external collaborator, **please FORK this repository** and **create a new branch** for your documentation updates. 
* If you are contributing to the documentation as an **OpenNebula developer or a partner with write access** to this repository, **please CLONE this repository** and **create a new branch** for your documentation updates.

The documentation is written in [Markdown](https://www.markdownguide.org/) and built using Hugo with the Docsy theme. While making documentation updates, to ensure they render correctly, it is recommended to build and preview the documentation locally. Follow the [Documentation Build Guide](https://github.com/OpenNebula/one-docs/wiki/Build) for details.

The guidelines below in this document give guidance for style, formatting, links, images and adding code blocks. 

Once you have completed your documentation updates, submit a pull request targetting the relevant [version branch or master branch](#documentation-versioning) and request a review from the appropriate member of the OpenNebula development team. 

## Creating and Editing Documentation

The OpenNebula documentation is written using numerous guidelines and standards. The following pages give style and formatting guidance for different documentation aspects:

* [Document Type](https://github.com/OpenNebula/website/wiki/Document-Type)
* [Writing Style](https://github.com/OpenNebula/website/wiki/Writing-Style)
* [Capitalization](https://github.com/OpenNebula/website/wiki/Capitalization)
* [Spelling](https://github.com/OpenNebula/website/wiki/Spellikng)
* [Links and References](https://github.com/OpenNebula/website/wiki/Links-and-References)
* [Images](https://github.com/OpenNebula/website/wiki/Images)
* [Code and Command Line](https://github.com/OpenNebula/website/wiki/Code-and-Command-Line)
* [Branding](https://github.com/OpenNebula/website/wiki/Branding)

## Quick Reference

The following details a recommended workflow for creating new documentation.

### 1. Consider the type of documentation you are creating:

  Which document type are you creating? Refer to the [Document Type Guide](https://github.com/OpenNebula/website/wiki/Document-Type) and consider the following things:

  * Who is it for?
    * A new user or an advanced user?
    * An engineer or an administrator?

  * What is the aim of the documentation?
    * Describe concepts or system architecture - **Explanatory documentation**
    * Teaching a user how to do something new - **Tutorial**
    * Describing a procedure for an advanced user to achieve a specific aim - **How-to guide**
    * Outlining arguments or parameters of an API - **Reference**

### 2. Structure the document 

Consider how to structure the document following the [Document Structure Guide](https://github.com/OpenNebula/website/wiki/Document-Structure). Keep in mind the following considerations:

* Include an introduction that states the aim of the documentation
* Follow a linear structure as much as possible - i.e. a single execution path, avoid options where possible
* Fix versions: avoid advising the user to "install the latest version" since future versions might change or break functionality

### 3. Include links to internal and external documentation

Refer to other parts of the OpenNebula documentation using the `relref` shortcode:

```html
Please see the [Installation Guide]({{% relref "software/installation_process/manual_installation/overview.md" %}}) for more details.
```

Refer to external documentation or websites with the standard Markdown syntax:

```html
Visit the [Hugo Documentation](https://gohugo.io/documentation/) for details.
```

Refer to the Wiki guide about [Links and References](https://github.com/OpenNebula/website/wiki/Links-and-References) for more details.

### 4. Include images, code and CLI commands as needed

#### Images

Include screenshots to show the user UI elements they should use or demonstrate what they should see after an operation. High resolution PNG is preferred for screenshots. Include conceptual or system diagrams if needed, preferably in SVG format.

Use the image shortcode syntax to include the image:

```
{{< image path="/images/ISO/00-onepoc_arch.svg" alt="OnePOC Arch" align="center" width="80%" >}}
```

We recommend that the images are normally centered and cover a maximum of 80%-90% of the container, which makes the text easier to follow. Please refer to the [Documentation Images Guide](https://github.com/OpenNebula/website/wiki/Images) for more details.

#### Code and CLI commands

Code and CLI commands can be added to the document using the [Fenced Codeblock Syntax](https://www.markdownguide.org/extended-syntax/#fenced-code-blocks). The codeblock is opened and closed by three backticks - ``` - you should also include the intended highlighting style after the opening backticks. Refer to the [Code and Command Line Guide](https://github.com/OpenNebula/website/wiki/Code-and-Command-Line) for more details. 

**CLI commands**:

For CLI commands, ideally the user should be able to copy and paste the command and execute it without editing. Therefore, do not include command line prompts in commands intended for the user to copy and paste. Only include prompts if you intend to demonstrate to the user how the prompt should appear (for example after invoking a virtual environment). You should also separate command CLI commands intended for the user to run and their example output. Use the `shell` language identifier for CLI commands and `default` for their example output. 

Where the user input to the command is required, highlight with closing `<chevrons>` the required input. Use lower case for textual input such as usernames and use upper case for numerical IDs or IP addresses, e.g.:

```
onetemplate instantiate <TEMPLATE_ID> --name <vm_name> --nic <vnet_name>
``` 

CLI command and output example:

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

**Code and Configuration Files**:

For code and configuration files, use the appropriate language identifier for the code block, the most common in the OpenNebula documentation include:

* `json` - JSON
* `python` - Python
* `ruby` - Ruby
* `yaml` - YAML
* `xml` - XML

Similarly to the command line, use `<chevrons>` to highlight where user input is required: 

Python code block example:

````
```python
import pyone

one = pyone.OneServer("http://one:2633/RPC2", session="<username>:<password>" )
hostpool = one.hostpool.info()
host = hostpool.HOST[0]
id = host.ID
```
````

JSON file example:

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

## Language

Finally, ensure that the documentation conforms to the language style guide by referring to the following guidelines:

* [Capitalization](https://github.com/OpenNebula/website/wiki/Capitalization)
* [Spelling](https://github.com/OpenNebula/website/wiki/Capitalization)
* [Writing Style](https://github.com/OpenNebula/website/wiki/Writing-Style)

## Documentation Versioning

Versioning of the documentation is achieved using separate branches for each release, while the latest documentation is maintained in the `master` branch. The documentation corresponding to the most recent versions of OpenNebula is contained is maintained in the following branches:

* OpenNebula dev:
    * [master](https://github.com/OpenNebula/website/tree/master) - this is where the latest updates exist
* OpenNebula 7.2:
    * [one-7.4](https://github.com/OpenNebula/website/tree/one-7.4)
    * [one-7.4-maintenance](https://github.com/OpenNebula/website/tree/one-7.4-maintenance)
* OpenNebula 7.2:
    * [one-7.2](https://github.com/OpenNebula/website/tree/one-7.2)
    * [one-7.2-maintenance](https://github.com/OpenNebula/website/tree/one-7.2-maintenance)
* OpenNebula 7.0:
    * [one-7.0](https://github.com/OpenNebula/website/tree/one-7.0)
    * [one-7.0-maintenance](https://github.com/OpenNebula/website/tree/one-7.0-maintenance)

Maintenance branches are used for maintenance releases of major version updates. Documentation related to bug fixes and backported features from later versions are included in the maintenance branches. Maintenance branches are merged into their respective major branches upon the release of a maintenance update.

The documentation for versions 6.10 and lower is maintained in a [separate repository](https://github.com/OpenNebula/docs).
