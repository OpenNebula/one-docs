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
3. Wait for the container setup and dependency installation to finish. The Hugo live server starts automatically, and Codespaces opens the documentation preview when port **1313** is ready. If it does not open, use **Open in Browser** for that port in the **Ports** tab.
4. Edit files under `content/` and save them. The preview reloads automatically. Use the **Source Control** panel to commit and push your changes.

The container includes Hugo Extended 0.155.3, Go, Node.js 22, Dart Sass, and the repository's PostCSS dependencies. The first preview may take longer while Hugo downloads its modules.

To inspect server output, run `tail -f /tmp/opennebula-docs-preview.log` in the terminal. If the server stops, restart it with `bash .devcontainer/serve.sh`. It also starts automatically when you resume the Codespace.

You can use the same environment locally with Docker and the VS Code **Dev Containers** extension: open the repository and run **Dev Containers: Reopen in Container**. Open the forwarded port **1313** to view the preview.


