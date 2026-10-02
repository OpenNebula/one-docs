## External Links

For external links, use the standard Markdown link syntax:

* Enclose the text to apply the link in square brackets `[Text Here]`
* Add the external link in standard brackets after the text `[Text Here](https://examplelink.com)`

For example:

```html
For additional options on installing Ansible, please visit the [Ansible Installation Guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html).
```

## Internal Links

When referring to other parts of the documentation use the `relref` shortcode. This helps ensure that internal links within the documentation do not get broken. Hugo resolves all `relref` instances when building the documentation and produces an error if an internal link cannot be properly resolved.

The `relref` shortcode syntax is as follows:

```html
[Validation with LLM Inferencing]({{% relref "solutions/ai_factory_blueprints/direct_ai_execution/llm_inference_certification" %}})
```

Use two curly brackets and a % sign to enclose the appropriate link inside double quotation marks. It is recommended to include the full path to the documentation file relative to (but not including) the `content/` directory. You may find the the `Copy Relative Path` option in the VScode right-click context menu useful. Adding `.md` to the end of the file is optional. 

The hash symbol can be used to refer to a subsection of a document (`md` must be included in this case). The subsection reference must be in lower case with spaces replaced by hyphens:

```html
[Front-end]({{% relref "software/installation_process/manual_installation/front_end_installation.md#frontend-installation" %}})
```

> [!NOTE]
>The full path to the documentation is not strictly needed. If the document is uniquely named, Hugo will resolve the link. However, if the document is likely to clash with other names the full path should be included. For example, multiple sections of the documentation include an `overview.md` file, if only `overview.md` is used in the `relref` shortcode, Hugo will fail to resolve the clashing names and produce an error.

