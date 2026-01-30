# Contributing to AWS Coworker

Thank you for your interest in contributing to AWS Coworker! This document provides guidelines for contributing to the project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
3. [Development Workflow](#development-workflow)
4. [Contribution Types](#contribution-types)
5. [Style Guidelines](#style-guidelines)
6. [Pull Request Process](#pull-request-process)

---

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Assume good intentions
- Prioritize safety and security in all contributions

---

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use issue templates when available
3. Provide clear reproduction steps
4. Include relevant context (AWS services, environment, etc.)

### Suggesting Enhancements

1. Open a discussion or issue describing the enhancement
2. Explain the use case and benefits
3. Consider how it fits with existing architecture
4. Be open to feedback and iteration

### Contributing Code

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## Development Workflow

### Context Files

AWS Coworker uses two context files:

| File | Purpose |
|------|---------|
| `CLAUDE.md` | **Usage context** — Intercepts all AWS requests and routes through commands. **Do not modify** unless changing the safety model. |
| `CLAUDE-DEVELOPMENT.md` | **Development context** — Provides directory conventions and development guidance when working on AWS Coworker itself. |

When contributing, be aware that `CLAUDE.md` is critical for safety enforcement. Changes to this file require careful review.

### Branch Naming

```
feature/add-eks-skill          # New features
fix/guardrail-validation-bug   # Bug fixes
docs/improve-getting-started   # Documentation
refactor/simplify-planner      # Refactoring
```

### Commit Messages

Use clear, descriptive commit messages:

```
Add EKS cluster discovery commands to aws-cli-playbook

- Add describe-cluster and list-clusters patterns
- Include node group discovery
- Add Fargate profile patterns
```

### Testing Your Changes

Before submitting:

1. Verify skill/command syntax is valid
2. Test with actual AWS interactions (in sandbox/dev)
3. Run `/aws-coworker-audit-library` to check for issues
4. Update documentation as needed

---

## Contribution Types

### Adding a New Skill

1. Determine the appropriate category (`aws/`, `org/`, `meta/`, `core/`)
2. Create the skill directory: `skills/{category}/{skill-name}/`
3. Create `SKILL.md` with required frontmatter:

```markdown
---
name: skill-name
description: Brief description of the skill
version: 1.0.0
category: aws|org|meta|core
agents: [list, of, compatible, agents]
tools: [Read, Bash, etc]
---

# Skill Name

## Purpose

[What this skill does and when to use it]

## When to Use

- [Scenario 1]
- [Scenario 2]

## When NOT to Use

- [Anti-pattern 1]
- [Anti-pattern 2]

## Guidance

[Detailed instructions, patterns, examples]
```

4. Add supporting files as needed (templates, examples)
5. Update relevant documentation

### Adding a New Command

1. Create command file: `.claude/commands/aws-coworker-{action}.md`
2. Include required frontmatter:

```markdown
---
description: Brief description of what this command does
skills: [skill1, skill2]
agent: aws-coworker-core
tools: [Read, Write, Bash]
arguments:
  - name: target
    description: Description of this argument
    required: true
---

# Command Name

[Command implementation instructions]
```

3. Document the command in README and relevant guides

### Adding a New Agent

> **Note**: New agents require careful consideration. Most functionality should be added via skills or commands.

1. Justify why existing agents cannot cover the use case
2. Define clear boundaries and responsibilities
3. Create agent definition: `.claude/agents/aws-coworker-{role}.md`
4. Update command/skill references as needed
5. Document thoroughly

### Modifying Existing Components

1. Understand the current behavior and dependencies
2. Make minimal, focused changes
3. Maintain backward compatibility when possible
4. Update all affected documentation

---

## Style Guidelines

### Markdown

- Use ATX-style headers (`#`, `##`, etc.)
- Include blank lines before and after headers
- Use fenced code blocks with language identifiers
- Keep lines under 100 characters when practical

### YAML Frontmatter

- Use lowercase keys
- Use hyphens for multi-word keys (`allowed-tools`)
- Quote strings containing special characters
- Maintain consistent ordering

### Naming

- Lowercase with hyphens for files and directories
- Prefix all AWS Coworker components with `aws-coworker-`
- Use descriptive, action-oriented names for commands
- Use noun-based names for skills

### Documentation

- Write for the reader, not the author
- Include examples for complex concepts
- Keep sentences concise
- Use active voice

---

## Pull Request Process

### Before Submitting

- [ ] Changes follow style guidelines
- [ ] All new files have appropriate frontmatter
- [ ] Documentation is updated
- [ ] No secrets or credentials in commits
- [ ] Tested with actual AWS interactions

### PR Description

Include:
- **What**: Brief description of changes
- **Why**: Motivation and context
- **How**: Technical approach (if non-obvious)
- **Testing**: How changes were validated

### Review Process

1. Automated checks must pass
2. At least one maintainer approval required
3. Address all review feedback
4. Squash commits if requested

### After Merge

- Delete your feature branch
- Verify changes in main branch
- Monitor for any issues

---

## Questions?

- Open a [Discussion](https://github.com/your-org/aws-coworker-enterprise/discussions)
- Check existing [Issues](https://github.com/your-org/aws-coworker-enterprise/issues)

Thank you for contributing to AWS Coworker!
