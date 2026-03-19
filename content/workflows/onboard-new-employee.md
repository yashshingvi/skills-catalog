---
name: onboard-new-employee
description: >
  End-to-end onboarding workflow for new hires. Provisions accounts, sends
  welcome messages, and schedules orientation meetings automatically.
version: 1.0.0
category: workflows
tags: [hr, onboarding, automation, accounts]
author: hr-automation
requires: [send-slack-notification, http-request]
---

# onboard-new-employee

Automated new-hire onboarding in three stages.

## Stages

1. **Account provisioning** — create SSO, email, and tool access
2. **Welcome comms** — Slack DM + email with first-day instructions
3. **Calendar setup** — schedule orientation with manager and team

## Trigger

Fires when HR system creates a new employee record.

## Configuration

```yaml
onboard_new_employee:
  slack_channel: "#new-hires"
  calendar_owner: hr@company.com
  tools:
    - github
    - jira
    - confluence
```
