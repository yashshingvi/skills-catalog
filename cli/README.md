# skillsctl

CLI tool for installing skills, agents, workflows, and rules from an Enterprise Skills Catalog.

## Installation

```bash
pip install skillsctl
```

## Quick Start

```bash
# Search the catalog
skillsctl search slack

# Install a skill
skillsctl install send-slack-notification

# Install multiple items with dependencies
skillsctl install send-slack-notification slack-ops-agent --with-deps

# List installed items
skillsctl list

# Update an item
skillsctl update send-slack-notification

# Sync all installed items to latest versions
skillsctl sync

# Remove an item
skillsctl remove send-slack-notification
```

## Configuration

By default, `skillsctl` connects to `http://localhost:8000`. Override with:

```bash
# CLI flag
skillsctl --source https://catalog.company.com install my-skill

# Environment variable
export SKILLSCTL_SOURCE=https://catalog.company.com

# Or set in skills.yaml
```

## Lockfile

`skillsctl` maintains a `skills.yaml` file in your project root:

```yaml
source: https://catalog.company.com
installed:
  send-slack-notification: "2.1.0"
  http-request: "1.3.0"
  slack-ops-agent: "1.0.0"
```

Installed files are saved to `.skills/{category}/{name}.md`.
