---
name: send-slack-notification
description: >
  Sends a formatted message to a Slack channel using the Slack Web API.
  Supports Block Kit layouts, attachments, and thread replies.
version: 2.1.0
category: skills
tags: [slack, notifications, api, messaging]
author: platform-team
requires: [http-request]
changelog: "v2.1: Added thread_ts support for replies"
---

# send-slack-notification

Post a message to any Slack channel via the Web API.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel` | string | ✓ | Channel ID or name (e.g. `#alerts`) |
| `text` | string | ✓ | Message text (fallback for Block Kit) |
| `blocks` | array | — | Block Kit layout blocks |
| `thread_ts` | string | — | Reply to a thread |

## Example

```python
import httpx

httpx.post("https://slack.com/api/chat.postMessage", headers={
    "Authorization": f"Bearer {SLACK_TOKEN}"
}, json={
    "channel": "#engineering",
    "text": "Deployment complete ✅",
    "blocks": [
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Deployment complete* ✅"}}
    ]
})
```

## Notes

- Token requires `chat:write` scope
- Use `channel` ID (not name) for reliability
