# Enterprise Skills Catalog

A self-hosted catalog server + CLI for managing reusable skills, agents, workflows, and rules as markdown files. Drop `.md` files into any folder structure, and they're instantly searchable, browsable, and installable across your organization.

Think **npm for enterprise knowledge** — but powered by markdown and frontmatter.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  Your Org's Git Repo (skills, agents, rules, workflows)     │
│  github.com/acme-corp/playbooks                             │
│                                                             │
│  productivity/                                              │
│    tools/                                                   │
│      send-slack-notification.md                             │
│      http-request.md                                        │
│    agents/                                                  │
│      slack-ops-agent.md                                     │
│    rules/                                                   │
│      no-direct-production-deploy.md                         │
│    workflows/                                               │
│      onboard-new-employee.md                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │  CATALOG_CONTENT_REPO=https://github.com/acme-corp/playbooks.git
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Catalog Server (FastAPI)                                   │
│  https://catalog.acme-corp.com                              │
│                                                             │
│  • Auto-clones your repo on startup                         │
│  • Indexes all .md files into an in-memory store            │
│  • Watches for changes (live reload)                        │
│  • Periodic git pull (default: every 5 min)                 │
│  • REST API + dark-theme web UI                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┼───────────┐
           ▼           ▼           ▼
        Web UI       REST API     CLI
     (browse &     (integrate)   (install into
      search)                    your project)
```

---

## Quick Start (Local Development)

```bash
# 1. Clone this repo
git clone https://github.com/your-org/enterprise-skills-catalog.git
cd enterprise-skills-catalog

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add some markdown files to content/
#    (example files are already included)

# 4. Start the server
uvicorn catalog.main:app --port 8000

# 5. Open the UI
#    http://localhost:8000

# 6. Install the CLI
cd cli && pip install -e . && cd ..

# 7. Install a skill into your project
cd /path/to/your/project
skillsctl install send-slack-notification
```

---

## Pointing the Catalog at Your Org's Repo

The catalog server can serve content from **any git repository**. Your org maintains a repo of markdown files — the catalog clones it and serves it.

### Step 1: Create Your Content Repo

Create a git repo with any folder structure you like. Every `.md` file with valid frontmatter will be indexed.

```
acme-playbooks/
├── engineering/
│   ├── skills/
│   │   ├── send-slack-notification.md
│   │   ├── http-request.md
│   │   └── query-database.md
│   ├── agents/
│   │   ├── incident-responder.md
│   │   └── code-reviewer.md
│   └── workflows/
│       └── deploy-to-production.md
├── security/
│   ├── rules/
│   │   ├── no-direct-prod-deploy.md
│   │   └── require-2fa.md
│   └── policies/
│       └── data-retention.md
└── hr/
    └── workflows/
        └── onboard-new-employee.md
```

The folder structure is flexible — `category` is auto-inferred from the nearest known parent folder (`skills`, `agents`, `workflows`, `rules`, `tools`, `policies`, `templates`, `guides`). Or set it explicitly in frontmatter.

### Step 2: Run the Catalog Server

```bash
# Point at your repo
export CATALOG_CONTENT_REPO=https://github.com/acme-corp/playbooks.git
export CATALOG_CONTENT_BRANCH=main

# Optional: set sync interval (default: 300 seconds)
export CATALOG_SYNC_INTERVAL=60

# Optional: webhook secret for push-triggered refresh
export CATALOG_WEBHOOK_SECRET=your-secret-here

# Start
uvicorn catalog.main:app --host 0.0.0.0 --port 8000
```

The server will:
1. Clone the repo into `.content-cache/`
2. Index all `.md` files with valid frontmatter
3. Start watching for local changes
4. Pull from git every `CATALOG_SYNC_INTERVAL` seconds

### Step 3: Wire Up a Git Webhook (Optional)

For instant updates when someone pushes to the content repo, add a webhook:

**GitHub**: Settings → Webhooks → Add webhook
- **URL**: `https://catalog.acme-corp.com/api/v1/webhook/refresh`
- **Content type**: `application/json`
- **Secret**: same as `CATALOG_WEBHOOK_SECRET`
- **Events**: Just the push event

The catalog will pull and re-index within seconds of a push.

### Step 4: Tell Your Team

```bash
# Install the CLI
pip install skillsctl

# Point it at your catalog
export SKILLSCTL_SOURCE=https://catalog.acme-corp.com

# Browse and install
skillsctl search "slack"
skillsctl install send-slack-notification --with-deps
```

---

## Markdown File Format

Every `.md` file needs YAML frontmatter with at least `name` and `description`:

```yaml
---
name: send-slack-notification          # REQUIRED — unique slug
description: >                         # REQUIRED — 1-3 sentence summary
  Sends a formatted message to a Slack
  channel using the Slack Web API.
version: 2.1.0                         # optional (default: 1.0.0)
category: skills                       # optional (auto-inferred from folder)
tags: [slack, notifications, api]      # optional
author: platform-team                  # optional
deprecated: false                      # optional — hides from default listing
requires: [http-request]               # optional — dependency names
changelog: "v2.1: thread support"      # optional

# Agent-specific fields:
model: claude-sonnet-4-6               # optional — LLM model for agents
tools: [send-slack-notification]       # optional — tools the agent can use
---

# Your markdown content here

The body is rendered as HTML in the UI. For agents, the body
serves as the system prompt.
```

**Rules:**
- `name` and `description` are required — files missing them are skipped (with a log warning)
- Unknown frontmatter keys are silently ignored
- `category` is auto-inferred from the parent folder name if not set
- `deprecated: true` items are hidden from default listings but still searchable

---

## CLI Reference (`skillsctl`)

Install: `pip install skillsctl`

### Commands

```bash
# Search the catalog
skillsctl search <query>
skillsctl search "slack" --category skills --tag api

# Install items into your project
skillsctl install <name1> <name2> ...
skillsctl install send-slack-notification --with-deps    # resolves requires
skillsctl install slack-ops-agent --no-deps              # skip dependencies
skillsctl install my-rule --path .claude/commands        # one-off custom directory (flat)

# Set a project-wide default output directory
skillsctl config base-dir .claude     # all future installs → .claude/{category}/{name}.md
skillsctl config base-dir .windsurf   # or .windsurf/{category}/{name}.md
skillsctl config base-dir --unset     # reset to .skillsctl

# List installed items
skillsctl list

# Update a specific item to latest version
skillsctl update <name>

# Sync all installed items to latest
skillsctl sync

# Remove installed items
skillsctl remove <name1> <name2> ...
```

### Global Options

```bash
# Point at a specific catalog server
skillsctl --source https://catalog.acme-corp.com install my-skill

# Or set via environment variable
export SKILLSCTL_SOURCE=https://catalog.acme-corp.com
```

### `config base-dir` — set a project-wide default directory

Set it once and every install goes to `{dir}/{category}/{name}.md` automatically:

```bash
skillsctl config base-dir .claude     # → .claude/skills/…  .claude/agents/…  etc.
skillsctl config base-dir .windsurf   # → .windsurf/skills/… .windsurf/rules/… etc.
skillsctl config base-dir             # show current value
skillsctl config base-dir --unset     # reset to .skillsctl (default)
```

This writes `base_dir` to `skills.yaml` and is respected by all commands (`install`, `sync`, `update`, `remove`).

### `--path` — per-install override

For one-off installs into a specific directory (flat, no category subfolder):

```bash
# Install a rule directly into Claude Code's commands folder
skillsctl install no-direct-prod-deploy --path .claude/commands

# Install a prompt into a custom prompts directory
skillsctl install summarise-ticket --path src/prompts
```

Files are written flat as `{name}.md` — no category subfolder is added. The path is remembered per-item in `skills.yaml` so `sync`, `update`, and `remove` all pick it up automatically. Dependencies installed via `--with-deps` always go to the default `.skillsctl/{category}/` location.

### Lockfile (`skills.yaml`)

`skillsctl` maintains a `skills.yaml` in your project root:

```yaml
source: https://catalog.acme-corp.com
base_dir: .claude                  # optional — set via: skillsctl config base-dir .claude
installed:
  http-request: "1.3.0"
  send-slack-notification: "2.1.0"
  no-direct-prod-deploy:           # installed with --path (one-off override)
    version: "1.0.0"
    path: .claude/commands
```

You can also **generate this file from the UI**: select items on the catalog page, click "Download skills.yaml", place the file in your project root, then run `skillsctl sync` to install everything at once.

Installed files are saved to `.skillsctl/{category}/{name}.md` by default, or to the custom path stored in `skills.yaml`:

```
your-project/
├── skills.yaml
├── .skillsctl/
│   ├── skills/
│   │   ├── http-request.md
│   │   └── send-slack-notification.md
│   └── agents/
│       └── slack-ops-agent.md
├── .claude/
│   └── commands/
│       └── no-direct-prod-deploy.md   # installed with --path
└── ... your code ...
```

Commit `skills.yaml` and `.skillsctl/` to your repo so your team shares the same set of skills.

---

## REST API

All endpoints are under `/api/v1/`. Interactive docs at `/docs` (Swagger UI).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Server status, item count, watcher/git info |
| `GET` | `/api/v1/items` | List items (filter: `category`, `tags`, `author`, `deprecated`, `page`, `page_size`) |
| `GET` | `/api/v1/items/search?q=` | Full-text search + filters + pagination |
| `GET` | `/api/v1/items/{name}` | Get latest version of an item by name |
| `GET` | `/api/v1/items/{name}/versions` | All versions of an item (sorted descending) |
| `GET` | `/api/v1/items/{name}/raw` | Download the original `.md` file |
| `GET` | `/api/v1/items/bundle?items=a,b,c` | Batch download multiple items |
| `GET` | `/api/v1/items/by-path?path=` | Get item by exact file path |
| `POST` | `/api/v1/items/refresh` | Manual re-scan of content directory |
| `POST` | `/api/v1/webhook/refresh` | Git pull + re-index (for CI/CD webhooks) |
| `GET` | `/api/v1/tags` | All tags with usage counts (filter by `category`) |

### Examples

```bash
# List all skills
curl "https://catalog.acme-corp.com/api/v1/items?category=skills"

# Search for anything related to "slack"
curl "https://catalog.acme-corp.com/api/v1/items/search?q=slack&tags=api"

# Download a raw skill file
curl "https://catalog.acme-corp.com/api/v1/items/send-slack-notification/raw" -o skill.md

# Get all tags
curl "https://catalog.acme-corp.com/api/v1/tags"
```

---

## Web UI

The catalog includes a dark-themed web interface at the root URL (`/`).

**Catalog page (`/`)**
- Card grid with all items
- Search bar with full-text search
- Filter by category (pills) and tags
- Checkbox multi-select on cards → floating install panel with:
  - `skillsctl install <name1> <name2> ...` command with one-click copy
  - **Download `skills.yaml`** button — generates a lockfile with pinned versions and triggers a browser download
  - After downloading, a modal shows: *"Place this file in your project root and run `skillsctl sync`"*
- Selections persist across search/filter/tag navigation via `localStorage`

**Item detail page (`/ui/items/{name}`)**
- Rendered markdown content
- For agents: labeled as "System Prompt"
- API panel with copy-ready:
  - REST endpoint URL
  - cURL command
  - Python snippet
  - `skillsctl install` command
- Metadata sidebar (version, author, model, tools, requires, changelog)
- Version history

---

## Configuration Reference

All settings are overridable via environment variables with the `CATALOG_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `CATALOG_CONTENT_DIR` | `content` | Local directory to scan for `.md` files |
| `CATALOG_CONTENT_REPO` | _(empty)_ | Git repo URL — overrides `CONTENT_DIR` when set |
| `CATALOG_CONTENT_BRANCH` | `main` | Git branch to track |
| `CATALOG_CONTENT_CACHE_DIR` | `.content-cache` | Where to clone the git repo locally |
| `CATALOG_SYNC_INTERVAL` | `300` | Seconds between git pulls (0 to disable) |
| `CATALOG_WEBHOOK_SECRET` | _(empty)_ | Secret for `X-Webhook-Secret` header validation |
| `CATALOG_HOST` | `0.0.0.0` | Server bind host |
| `CATALOG_PORT` | `8000` | Server bind port |
| `CATALOG_WATCHER_DEBOUNCE` | `0.5` | Seconds to wait after a file change before re-indexing |

---

## Deployment

### Docker

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY catalog/ catalog/
COPY templates/ templates/
COPY static/ static/

ENV CATALOG_CONTENT_REPO=""
ENV CATALOG_CONTENT_BRANCH="main"

EXPOSE 8000
CMD ["uvicorn", "catalog.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t skills-catalog .
docker run -p 8000:8000 \
  -e CATALOG_CONTENT_REPO=https://github.com/acme-corp/playbooks.git \
  skills-catalog
```

### Docker Compose

```yaml
services:
  catalog:
    build: .
    ports:
      - "8000:8000"
    environment:
      CATALOG_CONTENT_REPO: https://github.com/acme-corp/playbooks.git
      CATALOG_CONTENT_BRANCH: main
      CATALOG_SYNC_INTERVAL: 60
      CATALOG_WEBHOOK_SECRET: ${WEBHOOK_SECRET}
    volumes:
      - cache:/app/.content-cache
volumes:
  cache:
```

---

## Use Cases

### As an AI Skills Library
Store reusable prompts, agent system prompts, and tool definitions as versioned markdown. Teams install specific skills into their AI projects:

```bash
skillsctl install code-reviewer incident-responder --with-deps
```

### As a Runbook / Playbook Catalog
Centralize operational runbooks, incident response playbooks, and deployment workflows. Searchable and always up-to-date from your git repo.

### As a Policy / Rules Registry
Maintain compliance rules, security policies, and governance guidelines. Version them, tag them, and make them discoverable.

### As a Prompt Library
Store and version prompt templates for LLM applications. Engineers install the prompts they need via CLI, and the lockfile ensures everyone uses the same versions.

---

## Project Structure

```
enterprise-skills-catalog/
├── catalog/                     # FastAPI server package
│   ├── main.py                  # App + lifespan + UI routes
│   ├── config.py                # Settings (pydantic-settings)
│   ├── models.py                # Pydantic models
│   ├── store.py                 # In-memory index (dict + RLock)
│   ├── indexer.py               # Parse .md files, scan directories
│   ├── search.py                # Filter + text search functions
│   ├── watcher.py               # watchdog filesystem observer
│   ├── git_source.py            # Git clone/pull for remote content
│   └── routers/                 # API endpoints
│       ├── items.py
│       ├── tags.py
│       ├── health.py
│       └── webhook.py
├── cli/                         # skillsctl CLI package (PyPI-ready)
│   ├── pyproject.toml
│   └── src/skillsctl/
│       ├── main.py              # Click CLI group
│       ├── client.py            # HTTP client for catalog API
│       ├── lockfile.py          # skills.yaml management
│       └── commands/            # install, remove, list, search, sync, update
├── templates/                   # Jinja2 templates (dark theme UI)
├── static/                      # CSS
├── content/                     # Example .md files
│   ├── skills/
│   ├── agents/
│   ├── workflows/
│   └── rules/
└── requirements.txt
```

---

## License

MIT
