# AI Configuration — standalone bundle (redacted)

This repo publishes a standalone, redacted snapshot of the rules, skills, hooks,
context, settings, and instructions that configure Claude Code's behavior.

## Document

The full write-up lives in
[`AI/README-standalone-redacted.md`](AI/README-standalone-redacted.md), which
renders natively on GitHub.

## Overview

The bundle documents a Claude Code setup where everything is **conditional** —
each piece costs zero tokens until its trigger fires.

| Piece | What |
| --- | --- |
| `instructions/CLAUDE.md` | Global system prompt loaded into every session |
| `rules/` | Coding & git conventions, injected by hooks only when relevant |
| `skills/` | Reusable multi-step task workflows, invoked on demand |
| `hooks/` | Event-driven scripts that inject context or gate tool use |
| `context/` | Context fragments injected only when a hook's trigger fires |
| `settings.json` | Hook definitions plus model, theme, and permission preferences |

### Contents of the full doc

- Overview & directory structure
- Phrase commands
- Hooks
- Ansible integration
- Manual setup on a foreign (non-Ansible) machine
- Backing up Claude
- Appendix: bundled resource files
