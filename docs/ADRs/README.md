# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the Boloo App project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences.

## Format

Each ADR follows this template:

```markdown
# ADR-NNN: Title

**Status**: Proposed | Accepted | Deprecated | Superseded
**Date**: YYYY-MM-DD
**Deciders**: Names
**Technical Story**: Issue/ticket reference

## Context

What is the issue we're addressing?

## Decision

What is the change we're proposing/making?

## Consequences

### Positive
- ...

### Negative
- ...

### Risks
- ...
```

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [001](./ADR-001-use-react-native-expo.md) | Use React Native with Expo for Mobile App | Accepted | 2025-10-25 |
| [002](./ADR-002-azure-openai-for-ai.md) | Use Azure OpenAI for Conversational AI | Accepted | 2025-10-27 |
| [003](./ADR-003-remove-training-mode.md) | Remove Training Mode in Favor of Conversational AI | Accepted | 2025-11-01 |
| [004](./ADR-004-feed-system-architecture.md) | Public Feed System with Social Features | Accepted | 2025-11-11 |
| [005](./ADR-005-offline-first-architecture.md) | Offline-First Architecture with Queue Sync | Accepted | 2025-11-11 |

## Creating a New ADR

1. Copy the template from `ADR-000-template.md`
2. Number it sequentially (e.g., ADR-006)
3. Fill in all sections
4. Submit for team review
5. Update this index when accepted

## Status Definitions

- **Proposed**: Under discussion
- **Accepted**: Decision made and being implemented
- **Deprecated**: No longer applicable but kept for history
- **Superseded**: Replaced by another ADR (link to it)

---

**Last Updated**: 2025-11-12 05:36 UTC
