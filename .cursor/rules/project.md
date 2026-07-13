---
description: WorkspaceGPT project context and conventions
alwaysApply: true
---

# WorkspaceGPT

## Overview

WorkspaceGPT is an early-stage project for building an AI-powered workspace assistant.

## Structure

```
WorkspaceGPT/
  workspace-gpt/
    backend/
      main.py    # Python backend entry point
```

## Conventions

- Keep changes focused and minimal; avoid unrelated edits.
- Match existing naming, types, and patterns in the surrounding code.
- Prefer extending existing functions and components over reimplementing similar logic.
- Add comments only for non-obvious business logic or deep technical details.
- Only add tests when requested or when they provide meaningful coverage.

## Backend

- Python backend lives under `workspace-gpt/backend/`.
- Use clear, self-explanatory code; keep modules small and purposeful as the project grows.
