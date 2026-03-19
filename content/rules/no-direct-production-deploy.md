---
name: no-direct-production-deploy
description: >
  Enforces that all production deployments go through a pull-request review
  and CI pipeline. Direct pushes to the production branch are blocked.
version: 1.0.0
category: rules
tags: [security, deployment, ci-cd, governance]
author: security-team
---

# no-direct-production-deploy

## Rule

All changes to `main`/`production` branches **must** pass through:

1. A pull request with at least **1 approved review**
2. All CI checks passing (lint, test, security scan)
3. Deployment approval from a `release-manager` role

## Enforcement

- Branch protection rules on GitHub/GitLab
- Pre-receive hook rejects direct pushes
- PagerDuty alert if rule is bypassed

## Exceptions

Emergency hotfixes may bypass PR review with post-hoc review within **2 hours**,
documented in the incident ticket.
