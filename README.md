# OpenNebula 7.2 Documentation

This is the official repository of OpenNebula's technical documentation. This documentation is live at:
[http://docs.opennebula.io/7.2](http://docs.opennebula.io/7.2).

[OpenNebula](http://opennebula.io) is an open source platform delivering a simple but feature-rich and flexible solution to build and manage enterprise clouds for virtualized services, containerized applications and serverless computing.

## Get to Know more about OpenNebula

- Explore OpenNebula’s **Key Features** [on our website](https://opennebula.io/discover).
- Have a look at our [Introductory Datasheet](https://support.opennebula.pro/hc/en-us/articles/360036935791-OpenNebula-Key-Features-Datasheet).
- Browse our catalog of [Screencasts and Video-tutorials](https://opennebula.io/screencasts/).
- Download our [Technical White Papers](https://opennebula.io/docs-whitepapers/).
- See our [Documentation](https://docs.opennebula.io).
- Join our [Community Forum](https://forum.opennebula.io).
- Check our [Quick Start Guide](https://docs.opennebula.io/stable/getting_started/try_opennebula/).

## Contributing to the OpenNebula Documentation

If you find a problem in the documentation, or find something that needs updating, please create an issue in the [Main OpenNebula Repository](https://github.com/OpenNebula/one). Make sure to add the label `Documentation`. You are encouraged to fork this repo and send us pull requests if you are contributing new features!

To build the documentation, follow the [documentation build instructions](https://github.com/OpenNebula/one-docs/wiki/Build) in the Wiki. Details about how to contribute to the documentation, including style and structure guidance, can be found in the [Wiki for this repository](https://github.com/OpenNebula/one-docs/wiki).

### Edit in GitHub Codespaces

For quick edits from a browser, including on a phone or tablet:

1. Open the repository or your fork on GitHub and select the branch you want to edit.
2. Select **Code → Codespaces → Create codespace**.
3. Wait for the container setup and dependency installation to finish. Hugo starts automatically in the background while the editor opens. Once Hugo finishes its first build, view the documentation on port **1313** using **Open in Browser** in the **Ports** tab. If the preview opens earlier and returns **502**, wait for the build to finish and refresh it.
4. Edit files under `content/` and save them. The preview reloads automatically. Use the **Source Control** panel to commit and push your changes.

The container includes Hugo Extended 0.155.3, Go, Node.js 22, Dart Sass, and the repository's PostCSS dependencies. The first preview can take several minutes while Hugo downloads its modules and builds the site. A slow preview build continues in the background without blocking container setup.

To inspect server output, run `tail -f /tmp/opennebula-docs-preview.log` in the terminal. Hugo starts automatically when you resume the Codespace; reconnecting also checks the preview and starts it if necessary. To launch it manually in the background, run `bash .devcontainer/start-preview.sh`. To run it in the foreground and see its output directly, use `bash .devcontainer/serve.sh`.

If you add or change `.devcontainer/devcontainer.json` in an existing Codespace, including by switching branches, run **Codespaces: Rebuild Container → Rebuild** from the Command Palette to apply it. This is required once for changed lifecycle hooks; normal resumes reuse the existing container. If the preview log is missing, inspect **Codespaces: View Creation Log** for setup failures. A failed dependency installation prevents the startup hook from running.

You can use the same environment locally with Docker and the VS Code **Dev Containers** extension: open the repository and run **Dev Containers: Reopen in Container**. Open the forwarded port **1313** to view the preview.


