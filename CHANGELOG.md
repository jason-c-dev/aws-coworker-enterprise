# Changelog

All notable changes to AWS Coworker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Initial project structure and directory layout
- Design document (`docs/DESIGN.md`)
- Meta-designer agent (`aws-coworker-meta-designer`)
- Meta skills:
  - `skill-designer` - Patterns for creating skills
  - `command-designer` - Patterns for creating commands
  - `audit-library` - Health checks for AWS Coworker
- Core skills:
  - `git-workflow` - Git/GitHub best practices
  - `documentation-standards` - Documentation guidelines
- Documentation framework:
  - README.md
  - CONTRIBUTING.md
  - Getting Started guide structure
  - Customization guide structure
- Configuration templates
- .gitignore with comprehensive patterns

### Security
- Established secrets management patterns
- Read-only defaults for unknown AWS profiles
- Explicit approval requirements for mutations

---

## [0.1.0] - TBD

### Added
- Phase 1: Foundation complete
- Meta layer operational
- Documentation framework in place

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | TBD | Foundation release (Phase 1) |

---

## Upgrade Notes

### Upgrading to 0.1.0

This is the initial release. No upgrade path required.

---

## Deprecations

None yet.

---

## Breaking Changes Policy

AWS Coworker follows semantic versioning:

- **MAJOR** (x.0.0): Breaking changes to agents, skills, or commands
- **MINOR** (0.x.0): New features, backward compatible
- **PATCH** (0.0.x): Bug fixes, documentation updates

Breaking changes will be:
1. Announced in advance when possible
2. Documented in this changelog
3. Include migration guidance
