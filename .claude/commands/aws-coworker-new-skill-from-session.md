---
description: Analyze conversation and propose a new skill as a branch/PR
skills: [skill-designer, git-workflow, documentation-standards]
agent: aws-coworker-meta-designer
tools: [Read, Write, Edit, Glob, Grep, Bash]
arguments:
  - name: skill-name
    description: Proposed name for the new skill
    required: false
  - name: category
    description: Skill category (aws, org, meta, core)
    required: false
---

# /aws-coworker-new-skill-from-session

## Overview

Analyze the current conversation or session patterns to identify reusable knowledge and propose a new skill for AWS Coworker. Creates the skill as a Git branch for review.

## Prerequisites

- Recent conversation with AWS-related patterns worth capturing
- Git repository for AWS Coworker

---

## Workflow

### Step 1: Analyze Session

```
## Session Analysis

Reviewing conversation for skill-worthy patterns...

Looking for:
- Repeated questions or patterns
- AWS service interactions not well covered
- Organizational patterns that could be generalized
- Workflows that could benefit others
```

### Step 2: Identify Skill Gap

```
## Gap Identification

### Patterns Found
1. {pattern 1 - description}
2. {pattern 2 - description}
3. {pattern 3 - description}

### Existing Skill Coverage
| Pattern | Existing Skill | Gap |
|---------|----------------|-----|
| {pattern 1} | {skill or none} | {gap description} |
| {pattern 2} | {skill or none} | {gap description} |

### Proposed Skill Scope
{What the new skill would cover}
```

### Step 3: Determine Category

```
## Skill Categorization

Based on the patterns, this skill belongs in:

| Category | Fit | Reason |
|----------|-----|--------|
| aws/ | {✅/❌} | {reason} |
| org/ | {✅/❌} | {reason} |
| meta/ | {✅/❌} | {reason} |
| core/ | {✅/❌} | {reason} |

**Selected category:** {category}
```

### Step 4: Propose Skill Structure

```
## Proposed Skill: {skill-name}

### Purpose
{Why this skill should exist}

### When to Use
- {scenario 1}
- {scenario 2}

### When NOT to Use
- {anti-pattern 1}
- {anti-pattern 2}

### Proposed Content Sections
1. {section 1}
2. {section 2}
3. {section 3}

### Supporting Files (if needed)
- templates/{file}.md
- examples/{file}.md

Does this structure look right? Would you like to proceed?
```

### Step 5: Create Git Branch

```bash
# Create feature branch
git checkout -b feature/add-{skill-name}-skill

# Verify branch
git branch --show-current
```

```
Branch created: feature/add-{skill-name}-skill
```

### Step 6: Generate Skill Content

Create the skill following `skill-designer` patterns:

```markdown
---
name: {skill-name}
description: {description}
version: 1.0.0
category: {category}
agents: [{relevant agents}]
tools: [{required tools}]
---

# {Skill Name}

## Purpose

{Expanded purpose from session analysis}

## When to Use

{Scenarios derived from session patterns}

## When NOT to Use

{Anti-patterns and exclusions}

---

## Guidance

{Main content extracted and generalized from session}

---

## Examples

### Example 1: {Scenario from Session}

{Concrete example}

---

## Related Skills

- {related skill 1}
- {related skill 2}
```

### Step 7: Write Files

```
## Writing Skill Files

Creating:
- skills/{category}/{skill-name}/SKILL.md

{If supporting files needed:}
- skills/{category}/{skill-name}/templates/...
- skills/{category}/{skill-name}/examples/...
```

### Step 8: Update CHANGELOG

Add entry to CHANGELOG.md:

```markdown
## [Unreleased]

### Added
- New skill: `{skill-name}` - {brief description}
```

### Step 9: Commit and Report

```bash
# Stage new skill
git add skills/{category}/{skill-name}/
git add CHANGELOG.md

# Commit
git commit -m "feat: add {skill-name} skill

{Description of what the skill covers}

Derived from session patterns:
- {pattern 1}
- {pattern 2}

Co-Authored-By: AWS Coworker <aws-coworker@example.com>"
```

### Step 10: Present for Review

```
## Skill Created

### Summary
New skill `{skill-name}` created in category `{category}`.

### Files Created
| File | Purpose |
|------|---------|
| skills/{category}/{skill-name}/SKILL.md | Main skill definition |
| {additional files} | {purpose} |

### Branch
`feature/add-{skill-name}-skill`

### Review the Changes
```bash
git diff main..feature/add-{skill-name}-skill
```

### Create PR
```bash
gh pr create \
  --title "feat: Add {skill-name} skill" \
  --body "## Summary
Adds new skill for {purpose}.

## Derived From
Session patterns around {topic}.

## Content
- {section 1}
- {section 2}

## Testing
- [ ] Skill syntax valid
- [ ] Frontmatter complete
- [ ] Examples tested"
```

### Next Steps
1. Review the generated skill content
2. Adjust if needed (edit directly or request changes)
3. Create PR for team review
4. Merge after approval
```

---

## Output

The command produces:
1. **Session analysis** identifying skill-worthy patterns
2. **New skill file(s)** in appropriate category
3. **Git branch** ready for PR
4. **CHANGELOG update** documenting the addition

---

## Quality Checks

Before finalizing, the skill is checked against:

- [ ] Valid YAML frontmatter
- [ ] Required sections present (Purpose, When to Use, When NOT to Use)
- [ ] Follows naming conventions
- [ ] No duplication with existing skills
- [ ] Examples are concrete and useful
- [ ] Related skills cross-referenced

---

## Customization Options

```
## Skill Customization

If you'd like to adjust the proposed skill:

1. **Change name:** "Use {new-name} instead"
2. **Change category:** "Put this in {category}/"
3. **Add content:** "Also include {topic}"
4. **Remove content:** "Don't include {section}"
5. **Add examples:** "Add an example for {scenario}"

What would you like to adjust?
```
