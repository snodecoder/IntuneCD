![PyPI - License](https://img.shields.io/pypi/l/IntuneCD?style=flat-square)
[![Downloads](https://static.pepy.tech/badge/intunecd)](https://pepy.tech/project/intunecd)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/IntuneCD?style=flat-square)
![PyPI](https://img.shields.io/pypi/v/IntuneCD?style=flat-square)
![Unit tests](https://github.com/almenscorner/IntuneCD/actions/workflows/unit-test.yml/badge.svg)
![Publish](https://github.com/almenscorner/IntuneCD/actions/workflows/pypi-publish.yml/badge.svg)

<p align="center">
  <img src="https://user-images.githubusercontent.com/78877636/204297420-4b5373a8-4864-4710-a4a5-802ea4ec08d5.png#gh-dark-mode-only" width="500" height="300">
</p>
<p align="center">
  <img src="https://user-images.githubusercontent.com/78877636/204501041-a7cc2321-8991-4abb-a622-97f72f19051f.png#gh-light-mode-only" width="500" height="300">
</p>

IntuneCD, short for Intune Continuous Delivery, is a powerful Python package designed to facilitate the backup and update of configurations in Intune. With a primary focus on seamless integration with pipelines, it enables users to maintain a comprehensive history of configuration changes and track specific setting modifications.

The core functionality of IntuneCD revolves around securely backing up Intune configurations to a Git repository within a DEV environment. It goes beyond simple backup capabilities by automatically detecting any alterations made to configurations and efficiently propagating those changes to the PROD Intune environment.

By leveraging IntuneCD, users can streamline their configuration management workflow, ensuring smooth and consistent deployment of settings while maintaining an auditable history of changes.

# Looking for a GUI?
Check out the front end for IntuneCD [here](https://github.com/almenscorner/intunecd-monitor)

***

### Getting started

For help getting started, check out [Getting started](https://github.com/almenscorner/IntuneCD/wiki/Getting-started).

Have a look at the [Wiki](https://github.com/almenscorner/IntuneCD/wiki) to find documentation on how to use and configure the tool.

For release notes, have a look [here](https://github.com/almenscorner/IntuneCD/releases).


### Get help

There are a number of ways you can get help,
- Open an [issue](https://github.com/almenscorner/IntuneCD/issues) on this GitHub repo
- Start a [discussion](https://github.com/almenscorner/IntuneCD/discussions) on this GitHub repo
- Ask a question on [Discord](https://discord.gg/msems)
- Ask a question on [Slack](https://join.slack.com/t/intunecd/shared_invite/zt-1nf255xvo-POv60XoewYfY65TH9~tV_g)
- Check the [FAQ](https://github.com/almenscorner/IntuneCD/wiki/FAQ)

### Script Content in Documentation

When generating documentation with the `--decode` flag, IntuneCD now automatically decodes and properly formats script content fields in markdown files. This feature applies to:

- PowerShell scripts (`scriptContent`)
- Proactive Remediation detection scripts (`detectionScriptContent`)
- Proactive Remediation remediation scripts (`remediationScriptContent`)

**Key features:**
- **Automatic language detection**: Scripts are analyzed to detect their language (PowerShell, Bash, Python, etc.)
- **Syntax highlighting**: Scripts are wrapped in markdown code blocks with appropriate language tags
- **Collapsible sections**: Script content is displayed in expandable `<details>` sections to keep documentation clean
- **Markdown safety**: Special markdown characters within scripts are properly escaped by the code block syntax

**Usage:**
```bash
IntuneCD-startdocumentation --path /path/to/backup --decode
```

Without the `--decode` flag, script content remains base64-encoded in the documentation as before.
