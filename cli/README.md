# skillsctl

CLI tool for installing skills, agents, workflows, and rules from an [Enterprise Skills Catalog](https://github.com/yashshingvi/skills-catalog) server.

Think `npm install` but for enterprise knowledge — versioned markdown files that define reusable AI skills, agent prompts, operational runbooks, and compliance rules.

## Installation

```bash
pip install skillsctl
```

## Quick Start

```bash
# Install a skill — first run will prompt for your catalog URL and install directory
skillsctl install send-slack-notification --with-deps

# Or set the source upfront
export SKILLSCTL_SOURCE=https://catalog.your-company.com
skillsctl search slack
skillsctl install send-slack-notification --with-deps

# Install into a custom directory (flat, no category subfolder)
skillsctl install my-rule --path .claude/commands

# Set a project-wide default output directory
skillsctl config base-dir .claude     # → .claude/skills/… .claude/agents/… etc.
skillsctl config base-dir .windsurf   # → .windsurf/rules/… .windsurf/agents/… etc.
skillsctl config base-dir --unset     # reset to .skillsctl (default)

# List what's installed
skillsctl list

# Update everything to latest
skillsctl sync
```

## First-Run Setup

On the first run (when no `skills.yaml` is found), `skillsctl` interactively prompts for:

- **Catalog source URL** — your catalog server address (default: `http://localhost:8000`)
- **Default install directory** — where skill files are saved (default: `.skillsctl`, e.g. `.claude`)

```
Welcome to skillsctl! Let's get you set up.

Catalog source URL (http://localhost:8000): https://catalog.acme-corp.com
Default install directory (where skill files are saved) (.skillsctl): .claude

Config saved to skills.yaml. Files will be installed to .claude/{category}/
```

Config is saved to `skills.yaml` and reused on every subsequent run. Commands that don't need a server (`list`, `remove`, `config`) skip the prompt entirely.

## Commands

### `skillsctl install`

Download and save items from the catalog into your project.

```bash
# Install one or more items
skillsctl install send-slack-notification http-request

# Auto-install required dependencies
skillsctl install slack-ops-agent --with-deps

# Skip dependency resolution
skillsctl install send-email --no-deps

# Install to a custom path (flat, no category subfolder)
skillsctl install my-rule --path .claude/commands
```

Files are saved to `.skillsctl/{category}/{name}.md` by default and tracked in `skills.yaml`.

### `skillsctl config`

Set project-wide configuration stored in `skills.yaml`.

```bash
# Change the default install directory for all future installs
skillsctl config base-dir .claude      # saves to .claude/{category}/{name}.md
skillsctl config base-dir .windsurf    # saves to .windsurf/{category}/{name}.md

# Show the current value
skillsctl config base-dir

# Reset to default (.skillsctl)
skillsctl config base-dir --unset
```

### `skillsctl search`

Search the remote catalog.

```bash
skillsctl search "database"
skillsctl search "deploy" --category workflows
skillsctl search "auth" --tag security
```

### `skillsctl list`

Show all installed items from your `skills.yaml` lockfile.

```bash
skillsctl list
```

### `skillsctl update`

Update specific items to their latest catalog version.

```bash
skillsctl update send-slack-notification
skillsctl update http-request send-email
```

### `skillsctl sync`

Re-download all installed items, updating any that have newer versions.

```bash
skillsctl sync
```

### `skillsctl remove`

Remove installed items and clean up the lockfile.

```bash
skillsctl remove send-slack-notification
```

## Configuration

### Catalog Source

The catalog server URL is resolved in this order:

1. `--source` CLI flag: `skillsctl --source https://catalog.example.com install my-skill`
2. `source` field in `skills.yaml`
3. `SKILLSCTL_SOURCE` environment variable
4. Interactive prompt on first run (saved to `skills.yaml`)

### Lockfile (`skills.yaml`)

`skillsctl` maintains a lockfile in your project root that tracks the catalog source, configuration, and installed items with pinned versions:

```yaml
source: https://catalog.your-company.com
base_dir: .claude                        # optional — set via `skillsctl config base-dir`
installed:
  http-request: "1.3.0"                 # default path — bare string
  send-slack-notification: "2.1.0"
  slack-ops-agent: "1.0.0"
  my-rule:                              # installed with --path
    version: "1.0.0"
    path: .claude/commands              # custom flat path stored here
```

### Project Structure

After installing items with the default config:

```
your-project/
├── skills.yaml                              # lockfile (commit this)
├── .skillsctl/                              # default install directory (commit this)
│   ├── skills/
│   │   ├── http-request.md
│   │   └── send-slack-notification.md
│   ├── agents/
│   │   └── slack-ops-agent.md
│   └── rules/
│       └── no-direct-production-deploy.md
└── ... your code ...
```

With `skillsctl config base-dir .claude`:

```
your-project/
├── skills.yaml
├── .claude/
│   ├── skills/
│   │   └── http-request.md
│   └── agents/
│       └── slack-ops-agent.md
└── ... your code ...
```

Commit both `skills.yaml` and the install directory to version control so your entire team uses the same skills at the same versions.

## How It Works

```
┌─────────────────────────────┐
│  Skills Catalog Server      │
│  (FastAPI + in-memory index)│
│                             │
│  Serves .md files from any  │
│  git repo or local folder   │
└──────────────┬──────────────┘
               │
               │  REST API
               ▼
┌─────────────────────────────┐
│  skillsctl (this CLI)       │
│                             │
│  install / search / sync    │
│  remove / update / list     │
│  config                     │
│                             │
│  Writes .md files into      │
│  your project + lockfile    │
└─────────────────────────────┘
```

1. `skillsctl install <name>` calls `GET /api/v1/items/<name>` to fetch metadata
2. Downloads the raw `.md` file via `GET /api/v1/items/<name>/raw`
3. Saves it to `.skillsctl/{category}/{name}.md` (or custom path if `--path` is set)
4. Updates `skills.yaml` with the installed version
5. With `--with-deps`, recursively resolves and installs items listed in `requires`

## Setting Up a Catalog Server

See the [Skills Catalog](https://github.com/yashshingvi/skills-catalog) repo for the server that `skillsctl` connects to. The server indexes markdown files with YAML frontmatter and serves them via a REST API + web UI.

```bash
# Quick start
pip install fastapi uvicorn python-frontmatter watchdog pydantic pydantic-settings jinja2 aiofiles markdown packaging
uvicorn catalog.main:app --port 8000

# Or point at your org's git repo
CATALOG_CONTENT_REPO=https://github.com/your-org/playbooks.git uvicorn catalog.main:app --port 8000
```

## License

MIT
