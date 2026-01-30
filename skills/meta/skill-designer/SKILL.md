---
name: skill-designer
description: Patterns and checklists for designing high-quality AWS Coworker skills
version: 1.0.0
category: meta
agents: [aws-coworker-meta-designer]
tools: [Read, Write, Edit, Glob, Grep]
---

# Skill Designer

## Purpose

This meta-skill provides patterns, templates, and checklists for creating high-quality skills within AWS Coworker. Use this skill when designing new skills from conversations, requirements, or identified gaps.

## When to Use

- Creating a new skill for AWS Coworker
- Reviewing or improving an existing skill
- Converting repeated conversation patterns into reusable skills
- Extending AWS Coworker's capabilities

## When NOT to Use

- Creating slash commands (use `command-designer` instead)
- Modifying agent definitions (follow agent patterns directly)
- One-off tasks that don't warrant a reusable skill

---

## Skill Design Process

### Step 1: Identify the Need

Before creating a skill, answer:

1. **What gap does this fill?**
   - What task or pattern is not covered by existing skills?
   - Has this come up multiple times in conversations?

2. **Who will use it?**
   - Which agents should have access to this skill?
   - What level of AWS expertise is assumed?

3. **What's the scope?**
   - Is it focused enough to be useful?
   - Is it broad enough to justify a separate skill?

### Step 2: Determine Category

| Category | Use When | Example |
|----------|----------|---------|
| `aws` | AWS service-specific patterns | `aws-cli-playbook` |
| `org` | Organization-specific policies | `aws-governance-guardrails` |
| `meta` | AWS Coworker self-management | `skill-designer` |
| `core` | Non-AWS foundational patterns | `git-workflow` |

### Step 3: Choose a Name

**Naming Convention**: `{category-prefix}-{descriptive-name}`

Good names:
- `aws-cli-playbook` — Clear, describes content
- `aws-governance-guardrails` — Indicates purpose
- `skill-designer` — Action-oriented

Avoid:
- `misc-utils` — Too vague
- `my-aws-skill` — Not descriptive
- `skill1` — Not meaningful

### Step 4: Write the Skill

Follow this template:

```markdown
---
name: skill-name
description: One-line description (max 100 chars)
version: 1.0.0
category: aws|org|meta|core
agents: [list, of, compatible, agents]
tools: [Read, Write, Bash, etc]
---

# Skill Name

## Purpose

[2-3 sentences explaining why this skill exists and what problem it solves]

## When to Use

- [Specific scenario 1]
- [Specific scenario 2]
- [Specific scenario 3]

## When NOT to Use

- [Anti-pattern or exclusion 1]
- [Anti-pattern or exclusion 2]

---

## Guidance

### [Section 1: Primary Content]

[Main instructions, patterns, or reference material]

### [Section 2: Additional Content]

[Supporting information, examples, edge cases]

---

## Examples

### Example 1: [Scenario]

[Concrete example with inputs and expected outputs]

### Example 2: [Scenario]

[Another example showing different usage]

---

## Related Skills

- `skill-name-1` — [How it relates]
- `skill-name-2` — [How it relates]
```

---

## Frontmatter Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier, lowercase with hyphens |
| `description` | string | Brief description, max 100 characters |
| `version` | string | Semantic version (major.minor.patch) |
| `category` | string | One of: `aws`, `org`, `meta`, `core` |
| `agents` | array | List of compatible agent names |
| `tools` | array | Tools this skill may require |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `requires` | array | Other skills this depends on |
| `tags` | array | Searchable tags |
| `author` | string | Creator or maintainer |
| `updated` | date | Last modification date |

---

## Quality Checklist

Before finalizing a skill, verify:

### Structure
- [ ] Valid YAML frontmatter
- [ ] All required fields present
- [ ] Consistent heading hierarchy
- [ ] Proper markdown formatting

### Content
- [ ] Clear, specific purpose statement
- [ ] Actionable "When to Use" scenarios
- [ ] Helpful "When NOT to Use" exclusions
- [ ] Substantive guidance section
- [ ] At least one concrete example

### Naming
- [ ] Follows naming convention
- [ ] Unique (no conflicts with existing skills)
- [ ] Descriptive and memorable

### Integration
- [ ] Compatible agents listed correctly
- [ ] Required tools accurately specified
- [ ] Related skills cross-referenced

### Documentation
- [ ] README updated if user-facing
- [ ] CHANGELOG entry added
- [ ] Examples tested and working

---

## Supporting Files

Skills may include supporting files:

```
skills/aws/my-skill/
├── SKILL.md           # Required: main skill definition
├── templates/         # Optional: reusable templates
│   └── resource.yaml
├── examples/          # Optional: detailed examples
│   ├── basic.md
│   └── advanced.md
└── commands/          # Optional: sub-command references
    └── service1.md
```

### When to Add Supporting Files

- **Templates**: Reusable configuration or code snippets
- **Examples**: Complex scenarios needing detailed walkthroughs
- **Commands**: Service-specific command references (for large skills)

---

## Common Patterns

### Pattern 1: Service-Specific AWS Skill

For skills covering a specific AWS service:

```markdown
## Discovery Commands

[Read-only commands to explore current state]

## Common Operations

[Frequently used patterns with examples]

## Safety Considerations

[What to watch out for, common mistakes]

## IaC Patterns

[CDK/Terraform/CloudFormation approaches]
```

### Pattern 2: Governance/Policy Skill

For skills encoding rules and constraints:

```markdown
## Always Do

[Mandatory practices]

## Never Do

[Prohibited actions]

## Validation Checks

[How to verify compliance]

## Exceptions Process

[How to handle legitimate exceptions]
```

### Pattern 3: Workflow Skill

For skills describing multi-step processes:

```markdown
## Prerequisites

[What must be in place before starting]

## Step-by-Step Process

[Numbered steps with checkpoints]

## Validation

[How to verify success]

## Rollback

[How to undo if needed]
```

---

## Anti-Patterns

Avoid these common mistakes:

### Too Broad

❌ "AWS Best Practices" — covers everything, helps nothing

✅ "AWS S3 Security Patterns" — focused, actionable

### Too Narrow

❌ "How to Create One Specific Lambda" — too specific

✅ "AWS Lambda Deployment Patterns" — reusable across scenarios

### Missing Context

❌ Just commands without explanation

✅ Commands with rationale, prerequisites, and expected outcomes

### Copy-Paste Documentation

❌ Verbatim AWS docs (adds no value)

✅ Curated, opinionated guidance based on AWS docs

---

## Iteration and Improvement

Skills should evolve:

1. **Initial version**: Cover core use cases
2. **Refinement**: Add examples based on real usage
3. **Expansion**: Include edge cases and advanced patterns
4. **Consolidation**: Merge or split as scope clarifies

Use `/aws-coworker-audit-library` to identify skills needing improvement.
