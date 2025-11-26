# 📐 Documentation Standards & Best Practices

**Version**: 1.0.0
**Last Updated**: 2025-11-12 05:45 UTC
**Status**: Current
**Maintainer**: Development Team

---

## 🎯 Purpose

This document defines documentation standards for the Boloo App project, following industry best practices from:
- [Docs as Code](https://www.writethedocs.org/guide/docs-as-code/)
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/welcome/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Architecture Decision Records](https://adr.github.io/)

---

## ✅ Industry Best Practices We Follow

### 1. **Docs as Code**
- ✅ Documentation stored in Git with code
- ✅ Markdown format for easy editing
- ✅ Version controlled alongside features
- ✅ Reviewed in pull requests
- ✅ Automated updates via scripts

### 2. **CHANGELOG**
- ✅ Following [Keep a Changelog](https://keepachangelog.com/) format
- ✅ Semantic versioning (MAJOR.MINOR.PATCH)
- ✅ Organized by release version
- ✅ Categories: Added, Changed, Deprecated, Removed, Fixed, Security

### 3. **Architecture Decision Records (ADRs)**
- ✅ Important decisions documented
- ✅ Standard template (Context, Decision, Consequences)
- ✅ Immutable record (new ADRs supersede old ones)
- ✅ Numbered sequentially (ADR-001, ADR-002, etc.)

### 4. **Documentation Index**
- ✅ Central catalog of all docs
- ✅ Status indicators (Current, Archive, Deprecated)
- ✅ Last updated timestamps
- ✅ Quick navigation links

### 5. **Automated Timestamps**
- ✅ Scripts to update timestamps
- ✅ Pre-commit hooks (optional)
- ✅ Consistent UTC format
- ✅ Prevents stale documentation

---

## 📝 Document Types & Templates

### 1. README Files
**Purpose**: Project/module overview
**Location**: Root or module directory
**Template**:
```markdown
# Project/Module Name

Brief one-liner description.

## Overview
What is this?

## Quick Start
How to get started quickly.

## Features
- Feature 1
- Feature 2

## Installation
Step-by-step setup.

## Usage
Basic examples.

## Configuration
Key settings.

## Contributing
How to contribute.

## License
License info.
```

### 2. CHANGELOG
**Purpose**: Version history
**Location**: Root directory
**Template**: See [CHANGELOG.md](../CHANGELOG.md)
**Update Frequency**: After every release

### 3. Architecture Decision Records (ADRs)
**Purpose**: Document major technical decisions
**Location**: `/docs/ADRs/`
**Template**: See [ADR-000-template.md](./ADRs/ADR-000-template.md)
**Update Frequency**: When decisions are made

### 4. API Documentation
**Purpose**: Document REST APIs
**Location**: `/backend/docs/` or `/mobile/docs/`
**Template**:
```markdown
# API Name

## Endpoint: POST /v1/resource

### Description
What does this endpoint do?

### Authentication
Required: Yes (JWT Bearer token)

### Request
\`\`\`json
{
  "field": "value"
}
\`\`\`

### Response
**Success (200)**:
\`\`\`json
{
  "success": true,
  "data": {}
}
\`\`\`

**Error (400)**:
\`\`\`json
{
  "error": "Error message"
}
\`\`\`

### Example
\`\`\`bash
curl -X POST http://localhost:8000/v1/resource \
  -H "Authorization: Bearer TOKEN" \
  -d '{"field":"value"}'
\`\`\`
```

### 5. Feature Documentation
**Purpose**: Document specific features
**Location**: `/docs/` or feature-specific directory
**Template**:
```markdown
---
title: "Feature Name"
status: "Current"
last_updated: "YYYY-MM-DD HH:MM UTC"
version: "X.Y.Z"
---

# Feature Name

## Overview
What is this feature?

## User Story
As a [user type], I want to [goal], so that [benefit].

## Requirements
- Functional requirement 1
- Non-functional requirement 1

## Architecture
How it works.

## Implementation
Code locations, key files.

## Testing
How to test.

## Known Issues
Current limitations.

## Future Enhancements
Planned improvements.
```

### 6. Testing Documentation
**Purpose**: Testing procedures
**Location**: `/docs/`
**Template**:
```markdown
# Testing Guide for [Component]

## Test Environment Setup
Pre-requisites.

## Test Cases
| ID | Scenario | Expected | Actual | Status |
|----|----------|----------|--------|--------|
| TC-001 | ... | ... | ... | ✅ Pass |

## Manual Testing
Step-by-step instructions.

## Automated Testing
How to run automated tests.

## Known Issues
Test failures and workarounds.
```

---

## 📋 Required Metadata

**All documentation files MUST include this metadata at the top:**

```markdown
---
title: "Document Title"
status: "Current | Archive | Deprecated"
last_updated: "YYYY-MM-DD HH:MM UTC"
version: "X.Y.Z"
maintainer: "Team or Person Name"
---
```

**Example**:
```markdown
---
title: "Feed System API Documentation"
status: "Current"
last_updated: "2025-11-11 23:11 UTC"
version: "2.0.0"
maintainer: "Backend Team"
---

# Feed System API
...
```

---

## 🏷️ Status Indicators

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| **Current** | Up-to-date and accurate | None |
| **Needs Update** | Outdated but still referenced | Update within 1 week |
| **Archive** | Historical reference only | Move to `/docs/archive/` |
| **Deprecated** | No longer applicable | Mark as deprecated, link to replacement |

---

## 📅 Timestamp Format

**Standard**: `YYYY-MM-DD HH:MM UTC`

**Examples**:
- ✅ `2025-11-12 05:45 UTC`
- ❌ `Nov 12, 2025` (inconsistent)
- ❌ `2025-11-12` (missing time)
- ❌ `2025-11-12 05:45 EST` (use UTC only)

**Why UTC?**
- Team members in different timezones
- Server logs use UTC
- Consistent across systems
- No daylight saving time confusion

---

## 🔄 Update Workflow

### Daily/Ongoing
```bash
# When you make a change:
1. Update the relevant documentation
2. Update the "Last Updated" timestamp
3. Update CHANGELOG.md if it's a feature/fix
4. Commit docs with code changes
```

### Weekly
```bash
# Run automated timestamp update:
./scripts/update-docs-timestamps.sh

# Review documentation health:
cat docs/DOCUMENTATION_INDEX.md | grep "Needs Update"
```

### Monthly
```bash
# Full documentation audit:
1. Review all "Current" docs for accuracy
2. Archive outdated docs
3. Update DOCUMENTATION_INDEX.md
4. Create missing ADRs
```

### On Release
```bash
# Before releasing version X.Y.Z:
1. Update CHANGELOG.md with release notes
2. Update VERSION file
3. Tag release in git: git tag vX.Y.Z
4. Update all "version: X.Y.Z" in doc metadata
```

---

## 🤖 Automation Tools

### 1. Update All Timestamps
```bash
./scripts/update-docs-timestamps.sh
```

**What it does**:
- Scans all .md files
- Updates "Last Updated" timestamps
- Updates CHANGELOG metadata
- Updates documentation index

### 2. Pre-Commit Hook (Optional)
```bash
# Install:
cp scripts/pre-commit.sample .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**What it does**:
- Checks for outdated timestamps
- Warns if CHANGELOG not updated
- Prevents commits with stale docs

### 3. Documentation Linter (Future)
```bash
# Coming soon:
npm run docs:lint
```

**What it will do**:
- Check for missing metadata
- Validate markdown formatting
- Check for broken links
- Verify timestamp format

---

## 📊 Documentation Quality Metrics

We track these metrics to ensure documentation health:

| Metric | Target | Current |
|--------|--------|---------|
| **Coverage** | >90% features documented | 92% |
| **Freshness** | <7 days since last update (active docs) | 5 days |
| **Metadata** | 100% docs have metadata | 15% |
| **Broken Links** | 0 broken links | Unknown |
| **ADR Coverage** | All major decisions have ADRs | 20% |

**Action Items**:
- [ ] Add metadata to 64 docs (85% remaining)
- [ ] Create missing ADRs (001, 002, 004, 005)
- [ ] Implement broken link checker
- [ ] Archive 36 outdated docs

---

## ✍️ Writing Style Guide

### General Principles
1. **Be concise** - Readers are busy
2. **Be specific** - Avoid ambiguity
3. **Be actionable** - Tell them what to do
4. **Be consistent** - Follow these standards
5. **Be empathetic** - Consider the reader's perspective

### Voice & Tone
- ✅ Use active voice: "Run the command" (not "The command should be run")
- ✅ Use second person: "You can configure..." (not "One can configure...")
- ✅ Be conversational but professional
- ✅ Use present tense
- ❌ Avoid jargon without explanation

### Code Examples
- Always test code examples before documenting
- Include full context (imports, setup, etc.)
- Show both success and error cases
- Use realistic, not abstract examples

### Screenshots
- Keep images in `/docs/images/`
- Use descriptive filenames: `feed-screen-like-button.png`
- Compress images (use tools like TinyPNG)
- Add alt text for accessibility

---

## 📂 Directory Structure

```
boloo-app/
├── README.md                          # Project overview
├── CHANGELOG.md                       # Version history
├── VERSION                            # Current version number
├── docs/
│   ├── DOCUMENTATION_INDEX.md         # Central catalog
│   ├── DOCUMENTATION_STANDARDS.md     # This file
│   ├── ADRs/                          # Architecture decisions
│   │   ├── README.md
│   │   ├── ADR-000-template.md
│   │   └── ADR-NNN-title.md
│   ├── archive/                       # Old docs (historical)
│   │   └── YYYY-MM-DD-old-doc.md
│   ├── images/                        # Screenshots, diagrams
│   └── [feature-specific-docs].md
├── backend/docs/
│   ├── API_REFERENCE.md
│   ├── MIGRATION_GUIDE.md
│   └── [backend-specific-docs].md
├── mobile/docs/
│   ├── API_INTEGRATION.md
│   ├── TESTING_GUIDE.md
│   └── [mobile-specific-docs].md
└── scripts/
    ├── update-docs-timestamps.sh
    └── check-docs-up-to-date.sh
```

---

## 🚀 Getting Started with Documentation

### For New Team Members
1. Read [README.md](../README.md)
2. Review [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)
3. Read [CHANGELOG.md](../CHANGELOG.md) for recent changes
4. Check [docs/ADRs/](./ADRs/) for architecture decisions

### For Contributors
1. Always update docs with code changes
2. Use the appropriate template for new docs
3. Add metadata header to all new docs
4. Run `./scripts/update-docs-timestamps.sh` before committing
5. Update CHANGELOG.md for significant changes

### For Maintainers
1. Review documentation in pull requests
2. Ensure metadata is present
3. Archive outdated docs monthly
4. Keep DOCUMENTATION_INDEX.md up-to-date
5. Create ADRs for major decisions

---

## 🎓 Resources & Learning

### Industry Standards
- [Google Technical Writing Courses](https://developers.google.com/tech-writing) - Free courses
- [Write the Docs](https://www.writethedocs.org/) - Community and best practices
- [The Documentation System](https://documentation.divio.com/) - Framework for documentation

### Tools
- [Markdown Guide](https://www.markdownguide.org/)
- [Mermaid](https://mermaid.js.org/) - Diagrams in Markdown
- [markdownlint](https://github.com/DavidAnson/markdownlint) - Linter
- [Grammarly](https://grammarly.com/) - Grammar checking

### Examples of Great Documentation
- [Stripe API Docs](https://stripe.com/docs/api)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [React Native Docs](https://reactnative.dev/docs/getting-started)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

## 🤝 Contributing to Documentation

### Small Changes
1. Edit the file directly
2. Update "Last Updated" timestamp
3. Commit with message: `docs: update [file]`

### New Documents
1. Copy appropriate template
2. Fill in all sections
3. Add to DOCUMENTATION_INDEX.md
4. Update CHANGELOG.md
5. Get review before merging

### Major Restructuring
1. Propose changes in an ADR
2. Get team consensus
3. Update in phases
4. Communicate changes to team

---

## 📞 Questions?

- **Documentation issues**: Create GitHub issue with `[docs]` tag
- **Standards questions**: Ask in team chat
- **Suggestions**: Submit PR with proposed changes

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-12 | Initial standards document |

---

**Next Review**: 2025-12-12 (Monthly review schedule)
**Feedback**: All team members encouraged to suggest improvements
