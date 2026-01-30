---
description: Review existing skills and propose refactoring improvements
skills: [skill-designer, audit-library, git-workflow]
agent: aws-coworker-meta-designer
tools: [Read, Write, Edit, Glob, Grep, Bash]
arguments:
  - name: scope
    description: Scope of refactoring (all, category, specific skill)
    required: false
    default: all
---

# /aws-coworker-refactor-skills

## Overview

Review existing skills, identify improvement opportunities, and propose refactoring changes. Creates changes as a Git branch for review.

## Prerequisites

- AWS Coworker skills directory populated
- Git repository initialized

---

## Workflow

### Step 1: Inventory Skills

```
## Skills Inventory

Scanning skills directory...
```

```bash
find skills/ -name "SKILL.md" -type f | sort
```

```
## Current Skills

| Category | Skill | Version | Last Updated |
|----------|-------|---------|--------------|
| aws | aws-cli-playbook | 1.0.0 | {date} |
| aws | aws-well-architected | 1.0.0 | {date} |
| ... | ... | ... | ... |

Total: {count} skills
```

### Step 2: Analyze Each Skill

For each skill, check:

```
## Skill Analysis

### {skill-name}

| Check | Status | Notes |
|-------|--------|-------|
| Valid frontmatter | ✅/❌ | |
| Required sections | ✅/❌ | |
| Naming convention | ✅/❌ | |
| Cross-references valid | ✅/❌ | |
| Examples present | ✅/❌ | |
| Content current | ✅/❓ | |
```

### Step 3: Identify Issues

```
## Issues Identified

### Critical (Must Fix)
{Issues that break functionality}

### High (Should Fix)
{Significant quality issues}

### Medium (Consider Fixing)
{Moderate improvements}

### Low (Nice to Have)
{Minor enhancements}
```

#### Common Issue Types

```
### Duplication
- {skill A} and {skill B} both cover {topic}
- Recommendation: {merge/split/clarify boundaries}

### Missing Content
- {skill} lacks {section/examples/guidance}
- Recommendation: {add content}

### Outdated Information
- {skill} references {outdated info}
- Recommendation: {update}

### Inconsistent Structure
- {skill} doesn't follow standard structure
- Recommendation: {restructure}

### Broken References
- {skill} references non-existent {skill/file}
- Recommendation: {fix reference or remove}
```

### Step 4: Propose Refactoring Plan

```
## Refactoring Plan

### Priority 1: Critical Fixes
| Skill | Issue | Proposed Fix | Effort |
|-------|-------|--------------|--------|
| {skill} | {issue} | {fix} | {low/med/high} |

### Priority 2: High-Value Improvements
| Skill | Issue | Proposed Fix | Effort |
|-------|-------|--------------|--------|
| {skill} | {issue} | {fix} | {low/med/high} |

### Priority 3: Optional Enhancements
| Skill | Issue | Proposed Fix | Effort |
|-------|-------|--------------|--------|
| {skill} | {issue} | {fix} | {low/med/high} |

### Estimated Total Effort
- Critical: {X} changes
- High: {Y} changes
- Optional: {Z} changes

Which items would you like me to implement?
```

### Step 5: Create Refactoring Branch

```bash
git checkout -b refactor/skills-{date-or-description}
```

### Step 6: Implement Changes

For each approved change:

```
## Implementing Change: {description}

### Before
{relevant portion of current content}

### After
{proposed new content}

### Diff
{show the diff}
```

Apply changes:

```bash
# Stage changes
git add skills/{category}/{skill}/SKILL.md

# Commit individual changes
git commit -m "refactor({skill}): {description}

{Details of change}

Co-Authored-By: AWS Coworker <aws-coworker@example.com>"
```

### Step 7: Validate Changes

Run validation after changes:

```
## Post-Refactoring Validation

| Skill | Valid Frontmatter | Sections | References |
|-------|------------------|----------|------------|
| {skill} | ✅ | ✅ | ✅ |
| ... | ... | ... | ... |

All validations: {PASSED/FAILED}
```

### Step 8: Update Documentation

```markdown
# CHANGELOG.md update

## [Unreleased]

### Changed
- Refactored `{skill-1}`: {change description}
- Refactored `{skill-2}`: {change description}

### Fixed
- Fixed {issue} in `{skill}`
```

### Step 9: Present Results

```
## Refactoring Complete

### Summary
- Skills analyzed: {count}
- Issues identified: {count}
- Changes implemented: {count}
- Commits: {count}

### Changes Made
| Skill | Change | Commit |
|-------|--------|--------|
| {skill} | {change} | {hash} |
| ... | ... | ... |

### Branch
`refactor/skills-{description}`

### Review Changes
```bash
git log main..refactor/skills-{description} --oneline
git diff main..refactor/skills-{description} --stat
```

### Create PR
```bash
gh pr create \
  --title "refactor: Improve skills quality" \
  --body "## Summary
Refactoring pass on AWS Coworker skills.

## Changes
{list of changes}

## Validation
All skills pass validation checks.

## Review
- [ ] Changes reviewed
- [ ] No regressions
- [ ] Documentation updated"
```
```

---

## Refactoring Patterns

### Merge Overlapping Skills

When two skills cover similar ground:

```
Before:
- skills/aws/ec2-basics/SKILL.md
- skills/aws/ec2-advanced/SKILL.md

After:
- skills/aws/ec2-patterns/SKILL.md (merged, with sections for basic/advanced)
```

### Split Overly Large Skills

When a skill is too broad:

```
Before:
- skills/aws/everything-aws/SKILL.md (5000 lines)

After:
- skills/aws/aws-compute/SKILL.md
- skills/aws/aws-storage/SKILL.md
- skills/aws/aws-networking/SKILL.md
```

### Standardize Structure

Apply consistent structure:

```markdown
---
{frontmatter}
---

# Title

## Purpose
## When to Use
## When NOT to Use

---

## Main Content

---

## Examples

## Related Skills
```

### Update Outdated Content

Replace outdated references:

```
Before: "Use AWS CLI version 1.x"
After: "Use AWS CLI version 2.x"

Before: "Python 2.7 supported"
After: "Python 3.9+ required"
```

---

## Output

The command produces:
1. **Inventory report** of all skills
2. **Analysis** of issues and improvements
3. **Refactored skill files** in a branch
4. **Validation results** confirming changes
5. **PR-ready branch** for review
