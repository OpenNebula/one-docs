# Structuring the Document

## Frontmatter

Hugo uses frontmatter to define document titles, the appearance and order in the Table of Contents (ToC) and associated metadata such as descriptions and tags. 

The frontmatter is contained between YAML frontmatter delimiters (`---`) at the start of the document. The following is a minimal frontmatter example: 

```yaml
---
title: "Kubernetes Quick Start with OneKS"
linkTitle: "Kubernetes with OneKS"
date: "2026-07-29"
type: docs
weight: 4
---
```

The following table outlines the frontmatter fields and their purpose:

| **Field** | **Mandatory?** | **Purpose** |
|-------|---------|-----------|
| `title` | YES | The title as it will appear at the top of the document |
| `linkTitle` | SUGGESTED | The title as it will appear in the left hand ToC (often shortened) |
| `date` | NO | The date that the documentation was authored** |
| `weight` | SUGGESTED | Defines the sorting order of pages or sections in the left hand ToC |
| `tags` | NO | Tags for defining topics (not currently exposed) |
| `cardTitle` | NO | This can be used to use a different title in the section summary card |

## Headings

Headings follow the standard [markdown heading syntax](https://www.markdownguide.org/basic-syntax/), with hashes `#` to define the header level. 

| **Markdown**             | **HTML**                   | **Rendered**              |
|--------------------------|----------------------------|---------------------------|
| `# Heading level 1`	     | `<h1>Heading level 1</h1>`	| <h1>Heading level 1</h1>  |
| `## Heading level 2`	   | `<h2>Heading level 2</h2>`	| <h2>Heading level 2</h2>  |
| `### Heading level 3`	   | `<h3>Heading level 3</h3>`	| <h3>Heading level 3</h3>  |
| `#### Heading level 4`   | `<h4>Heading level 4</h4>`	| <h4>Heading level 4</h4>  |
| `##### Heading level 5`	 | `<h5>Heading level 5</h5>`	| <h5>Heading level 5</h5>  |
| `###### Heading level 6` | `<h6>Heading level 6</h6>` | <h6>Heading level 6</h6>  |

There is no need for a level 1 header in the markdown of OpenNebula documentation. The title in the frontmatter serves as the level 1 header. Principal sections of a document should be outlined by level 2 headers (`##`), these will appear in the right hand ToC for quick navigation. Subsections with level 3 or more will not appear in the right hand ToC, but are useful for delineating subsections, use accordingly.

## Tutorials and How-tos

In the introduction, provide basic information about the tutorial:

* What the reader will do (e.g. deploy an Edge cluster from an OpenNebula Front-end)  
* What the reader will achieve (e.g. a working Edge cluster ready for testing)  
* Approximately how long it should take to do

Ideally, tutorials should include only a single pathway for the reader to follow. Thus in a tutorial we can include the main high-level steps near the top of the document, for example:

> To install an OpenNebula Front-end using miniONE, we’ll need to complete the following high-level steps:
> 1. Prepare the AWS VM where we’ll install miniONE.
> 2. Update the OS in the VM.
> 3. Download and run the miniONE script.
> 4. Verify the installation.

In the document itself, if possible try to make the subsection headings coincide with, or reference, the high-level steps. For instance, for the above example the title of the first section might be “Step 1: Prepare the VM in AWS.”

In the above example, the high-level steps divide the document into four parts. In the document itself (whether tutorial or how-to), it’s good practice to reinforce each of these parts by following this basic structure:

1. At the beginning, briefly state the goal of the high-level step (even if being redundant).  
2. List and describe the actions required (optionally you can divide them into substeps, e.g. 1.1, 1.2 etc.)  
3. At the end, describe the result, e.g. “At this point, the OpenNebula Front-end should be up and running”.

In other words, for each part reinforce the goal and the outcome.

## Explanation

At or near the beginning of the document, state the scope of the document as briefly and clearly as possible, e.g. “This page provides a high-level overview of the OpenNebula cloud model, architecture and components.” Optionally specify if the document addresses a more specific need.

If possible, structure the document so it explains high-level concepts first, then gradually goes into lower-level explanation. However, include as little technical description as possible, instead providing links to reference documentation.

When writing, try to determine if the reader could benefit from a *definition* of the subject, or of individual elements in the doc. A definition is not an example, nor a statement of what something *does*, but a statement of what something *is*; it expresses the essential nature of something. Don’t hesitate to include definitions of external components if necessary, for example “Ansible is a Python application for IT automation. It can deploy software, configure systems \[etc.\],” or “The OpenNebula OneFlow API is a RESTful service used to create, control and monitor services \[etc.\].”

## Reference

Reference documents are not intended to be read sequentially but to be consulted, as when you consult a dictionary.

A reference document is the final, authoritative source for information within the documentation. In IT, the authority of a reference document is derived from the source code itself.

A reference document focuses on description, but can include definitions and short examples.

It does not try to explain, but to *describe* and sometimes to *define*.

Ideally it should maintain a standard format throughout the document, like a dictionary. To achieve this, it may be useful to structure the information in tables or predefined paragraph styles.

Reference documents should be complete. The reader should know that the document is the most complete description of its subject. A good example in the OpenNebula docs is the [Virtual Machines States Reference](https://docs.opennebula.io/stable/integration_and_development/references/vm_states.html). At the beginning it states that it is a *complete reference*, and links to other docs where the reader may find simplified explanations of its subject. It then uses a standardized format (a table) to list all VM states and provide an explanation for each.