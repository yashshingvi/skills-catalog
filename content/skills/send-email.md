---
name: send-email
description: >
  Sends transactional emails via SMTP or SendGrid. Supports HTML templates,
  attachments, and CC/BCC recipients.
version: 1.0.0
category: skills
tags: [email, notifications, smtp, sendgrid]
author: platform-team
requires: [http-request]
---

# send-email

Send transactional emails with HTML support.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `to` | string/list | ✓ | Recipient(s) |
| `subject` | string | ✓ | Email subject |
| `html_body` | string | — | HTML content |
| `text_body` | string | — | Plain text fallback |
| `attachments` | list | — | File paths to attach |
