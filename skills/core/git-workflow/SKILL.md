---
name: git-workflow
description: Git and GitHub best practices for AWS Coworker change management
version: 1.0.0
category: core
agents: [aws-coworker-meta-designer, aws-coworker-core]
tools: [Bash, Read, Write]
---

# Git Workflow

## Purpose

This skill provides Git and GitHub best practices for managing changes within AWS Coworker. It ensures consistent, reviewable, and reversible change management across all AWS Coworker components.

## When to Use

- Creating or modifying AWS Coworker components (agents, skills, commands)
- Proposing infrastructure changes via IaC
- Managing configuration changes
- Collaborating on AWS Coworker improvements

## When NOT to Use

- Direct AWS CLI operations (Git is for code/config, not runtime state)
- Emergency break-glass scenarios (follow incident procedures first)

---

## Branch Strategy

### Branch Types

| Type | Pattern | Purpose | Merge Target |
|------|---------|---------|--------------|
| Main | `main` | Production-ready baseline | N/A (protected) |
| Feature | `feature/{description}` | New capabilities | `main` |
| Fix | `fix/{description}` | Bug fixes | `main` |
| Refactor | `refactor/{description}` | Code improvements | `main` |
| Docs | `docs/{description}` | Documentation updates | `main` |
| Release | `release/v{version}` | Release preparation | `main` + tag |

### Naming Conventions

```bash
# Good branch names
feature/add-eks-skill
fix/guardrail-validation-error
refactor/simplify-planner-workflow
docs/improve-getting-started

# Avoid
feature/stuff          # Too vague
my-branch              # No type prefix
Feature/Add-EKS-Skill  # Wrong case
feature/add_eks_skill  # Underscores
```

---

## Commit Practices

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

#### Type Prefixes

| Type | Use For |
|------|---------|
| `feat` | New features |
| `fix` | Bug fixes |
| `docs` | Documentation |
| `refactor` | Code restructuring |
| `style` | Formatting (no logic change) |
| `test` | Adding tests |
| `chore` | Maintenance tasks |

#### Examples

```bash
# Simple commit
git commit -m "feat: add EKS discovery commands to aws-cli-playbook"

# Detailed commit
git commit -m "fix: correct region validation in executor agent

The executor was accepting invalid region codes due to
a regex pattern error. This fix:
- Updates the region validation regex
- Adds test cases for edge cases
- Documents valid region formats

Fixes #42"
```

### Commit Hygiene

**Do:**
- Make atomic commits (one logical change per commit)
- Write clear, descriptive messages
- Reference issues/PRs in footer when relevant

**Don't:**
- Commit secrets or credentials
- Make massive commits with unrelated changes
- Use vague messages like "fix stuff" or "updates"

---

## Pull Request Process

### Creating a PR

```bash
# 1. Create and switch to feature branch
git checkout -b feature/add-new-skill

# 2. Make changes
# ... edit files ...

# 3. Stage specific files
git add skills/aws/new-skill/SKILL.md

# 4. Commit with clear message
git commit -m "feat: add new-skill for [purpose]"

# 5. Push branch
git push -u origin feature/add-new-skill

# 6. Create PR via GitHub CLI or web
gh pr create --title "Add new-skill" --body "..."
```

### PR Description Template

```markdown
## Summary

[Brief description of changes]

## Changes

- [Change 1]
- [Change 2]
- [Change 3]

## Testing

- [ ] Tested in sandbox environment
- [ ] Ran audit-library checks
- [ ] Verified documentation accuracy

## Related

- Fixes #[issue]
- Related to #[PR]
```

### Review Checklist

For reviewers:

- [ ] Changes match PR description
- [ ] No secrets or credentials
- [ ] Follows naming conventions
- [ ] Documentation updated
- [ ] CHANGELOG entry added (if user-facing)

---

## Tagging and Releases

### Version Tags

Follow semantic versioning:

```bash
# Tag a release
git tag -a v1.2.0 -m "Release v1.2.0: Add EKS support"
git push origin v1.2.0

# List tags
git tag -l "v*"
```

### Baseline Tags

For rollback points:

```bash
# Create baseline before major changes
git tag -a baseline/pre-org-customization -m "Baseline before org customization"

# Create date-based baseline
git tag -a baseline/2026-01-29 -m "Baseline 2026-01-29"
```

---

## Common Operations

### Starting New Work

```bash
# Ensure main is current
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/descriptive-name
```

### Syncing with Main

```bash
# While on feature branch
git fetch origin
git rebase origin/main

# Or merge if preferred
git merge origin/main
```

### Undoing Changes

```bash
# Discard unstaged changes to a file
git checkout -- path/to/file

# Unstage a file (keep changes)
git reset HEAD path/to/file

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - CAREFUL
git reset --hard HEAD~1
```

### Viewing History

```bash
# Recent commits
git log --oneline -10

# Commits affecting a file
git log --oneline -- path/to/file

# Changes in a commit
git show <commit-hash>

# Diff between branches
git diff main..feature/my-branch
```

---

## Protected Branches

### Main Branch Protection

The `main` branch should have:

- [ ] Require pull request reviews
- [ ] Require status checks to pass
- [ ] Require branches to be up to date
- [ ] Include administrators in restrictions

### Bypass for Emergencies

In genuine emergencies:

1. Document the emergency
2. Use break-glass procedure if available
3. Create follow-up PR for review
4. Update CHANGELOG with emergency context

---

## .gitignore Maintenance

### When to Update

Add patterns when:
- New tool introduces local state files
- New secrets/credentials format appears
- Build artifacts change

### Pattern Guidelines

```gitignore
# Be specific
.terraform/          # Good: specific directory

# Avoid overly broad patterns
*                    # Bad: ignores everything

# Comment sections
# -----------------------
# Terraform
# -----------------------
.terraform/
*.tfstate
```

---

## Conflict Resolution

### Prevention

- Keep branches short-lived
- Sync with main frequently
- Communicate about overlapping work

### Resolution Process

```bash
# When merge/rebase conflicts occur

# 1. See conflicting files
git status

# 2. Open files and resolve conflicts
# Look for <<<<<<< HEAD ... ======= ... >>>>>>> markers

# 3. After resolving, stage files
git add path/to/resolved/file

# 4. Continue rebase or complete merge
git rebase --continue
# or
git commit
```

---

## GitHub CLI Quick Reference

```bash
# Create PR
gh pr create --title "Title" --body "Description"

# List PRs
gh pr list

# View PR
gh pr view 123

# Check out PR locally
gh pr checkout 123

# Merge PR
gh pr merge 123

# Create issue
gh issue create --title "Title" --body "Description"
```

---

## Related Skills

- `documentation-standards` — For documentation in commits/PRs
- `skill-designer` — For creating new skills via Git workflow
- `command-designer` — For creating new commands via Git workflow
