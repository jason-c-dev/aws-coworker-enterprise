---
name: command-designer
description: Best practices for creating AWS Coworker slash commands as workflows
version: 1.0.0
category: meta
agents: [aws-coworker-meta-designer]
tools: [Read, Write, Edit, Glob, Grep]
---

# Command Designer

## Purpose

This meta-skill provides patterns, templates, and best practices for creating slash commands in AWS Coworker. Slash commands are workflow orchestrators that combine agents and skills to accomplish specific tasks.

## When to Use

- Creating a new slash command for AWS Coworker
- Reviewing or improving an existing command
- Converting repeated multi-step interactions into reusable workflows
- Standardizing operational procedures

## When NOT to Use

- Creating reference material (use skills instead)
- One-off tasks that don't warrant automation
- Simple queries that don't need orchestration

---

## Command Design Process

### Step 1: Identify the Workflow

Before creating a command, answer:

1. **What outcome does this achieve?**
   - What is the end state after running this command?
   - Is it planning, execution, validation, or meta-operation?

2. **Who will use it?**
   - Platform engineers? Developers? Security team?
   - What level of AWS expertise is assumed?

3. **What safeguards are needed?**
   - Does it mutate infrastructure?
   - What approvals should be required?

### Step 2: Determine Dependencies

| Dependency | When Needed |
|------------|-------------|
| **Agent** | Primary orchestrator for the workflow |
| **Skills** | Reference material and patterns to follow |
| **Tools** | Capabilities required (Read, Bash, etc.) |

### Step 3: Choose a Name

**Naming Convention**: `aws-coworker-{action}-{scope}`

Good names:
- `aws-coworker-plan-interaction` — Clear action and scope
- `aws-coworker-execute-nonprod` — Indicates environment constraint
- `aws-coworker-audit-library` — Self-referential for meta-commands

Avoid:
- `run-aws` — Too vague
- `do-stuff` — Not descriptive
- `my-command` — Not meaningful

### Step 4: Write the Command

Follow this template:

```markdown
---
description: One-line description of what this command accomplishes
skills: [skill-1, skill-2]
agent: primary-agent-name
tools: [Read, Write, Bash, etc]
arguments:
  - name: argument-name
    description: What this argument specifies
    required: true|false
    default: optional-default-value
---

# Command Name

## Overview

[Brief description of what this command does and when to use it]

## Prerequisites

- [Prerequisite 1]
- [Prerequisite 2]

## Workflow

### Step 1: [First Phase]

[Instructions for the agent to follow]

### Step 2: [Second Phase]

[Instructions for the agent to follow]

### Step 3: [Approval/Checkpoint]

[Where human approval is required]

### Step 4: [Final Phase]

[Instructions for completion]

## Output

[What the user should expect as output]

## Error Handling

[How to handle common failures]
```

---

## Frontmatter Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Brief description, max 100 characters |
| `skills` | array | Skills this command uses |
| `agent` | string | Primary agent for orchestration |
| `tools` | array | Tools this command may use |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `arguments` | array | Input parameters |
| `arguments[].name` | string | Argument identifier |
| `arguments[].description` | string | What the argument does |
| `arguments[].required` | boolean | Whether it's mandatory |
| `arguments[].default` | any | Default value if not provided |

---

## Command Categories

### Planning Commands

For commands that analyze and propose without executing:

```markdown
---
description: Plan [what] for [context]
skills: [aws-cli-playbook, aws-well-architected, aws-governance-guardrails]
agent: aws-coworker-planner
tools: [Read, Grep, Glob]
---
```

Key characteristics:
- No Bash execution of AWS commands
- Output is a plan document
- May propose commands but doesn't run them

### Execution Commands

For commands that make changes:

```markdown
---
description: Execute [what] in [environment]
skills: [aws-cli-playbook, aws-governance-guardrails]
agent: aws-coworker-executor
tools: [Read, Write, Bash]
---
```

Key characteristics:
- Environment-scoped (nonprod vs prod)
- Explicit approval checkpoints
- Includes rollback information

### Validation Commands

For commands that check compliance:

```markdown
---
description: Validate [what] against [criteria]
skills: [aws-governance-guardrails]
agent: aws-coworker-guardrail
tools: [Read, Grep, Glob]
---
```

Key characteristics:
- Read-only operations
- Produces findings report
- No infrastructure changes

### Meta Commands

For commands that evolve AWS Coworker itself:

```markdown
---
description: [Meta-operation] for AWS Coworker
skills: [skill-designer, command-designer, audit-library]
agent: aws-coworker-meta-designer
tools: [Read, Write, Edit, Bash]
---
```

Key characteristics:
- Only Git operations via Bash (no AWS CLI)
- Creates branches/PRs
- Self-referential to AWS Coworker

---

## Safety Patterns

### Approval Checkpoints

Include explicit approval points for mutations:

```markdown
### Step 3: Approval Checkpoint

**Before proceeding, confirm:**

1. Review the proposed changes above
2. Verify the target environment: `{profile}` / `{region}`
3. Confirm blast radius is acceptable

**Awaiting explicit user confirmation to proceed.**
```

### Environment Guards

Enforce environment constraints:

```markdown
### Environment Validation

This command is restricted to **non-production** environments.

Before any execution:
1. Confirm profile is classified as non-production
2. Verify region is in the allowed list
3. If production detected, abort and suggest `/aws-coworker-prepare-prod-change`
```

### Blast Radius Disclosure

Always disclose impact:

```markdown
### Impact Assessment

**Resources affected:**
- [Resource type]: [count] in [scope]
- [Resource type]: [count] in [scope]

**Estimated blast radius:** [Low/Medium/High]

**Rollback complexity:** [Simple/Moderate/Complex]
```

---

## Quality Checklist

Before finalizing a command, verify:

### Structure
- [ ] Valid YAML frontmatter
- [ ] All required fields present
- [ ] Clear workflow steps
- [ ] Proper markdown formatting

### Safety
- [ ] Appropriate agent assigned
- [ ] Environment constraints clear
- [ ] Approval checkpoints included (for mutations)
- [ ] Rollback guidance provided

### Usability
- [ ] Clear prerequisites listed
- [ ] Expected output described
- [ ] Error handling documented
- [ ] Arguments well-documented

### Integration
- [ ] Skills correctly referenced
- [ ] Tools accurately specified
- [ ] Works with specified agent

### Documentation
- [ ] README updated
- [ ] CHANGELOG entry added
- [ ] Examples tested

---

## Common Patterns

### Pattern 1: Discover → Plan → Approve → Execute

```markdown
## Workflow

### Step 1: Discovery

Use `aws-cli-playbook` to discover current state:
- [Discovery command 1]
- [Discovery command 2]

### Step 2: Planning

Based on discovery, create execution plan:
- Proposed changes
- Sequence of operations
- Rollback steps

### Step 3: Validation

Run guardrail checks against the plan:
- Policy compliance
- Tagging requirements
- Security constraints

### Step 4: Approval

Present plan for human approval:
- Summary of changes
- Blast radius
- Risk assessment

### Step 5: Execution (upon approval)

Execute the approved plan:
- Run commands in sequence
- Validate each step
- Report completion
```

### Pattern 2: Audit → Report → Recommend

```markdown
## Workflow

### Step 1: Inventory

Collect current state:
- List resources
- Gather configurations
- Note relationships

### Step 2: Analysis

Evaluate against criteria:
- Policy compliance
- Best practices
- Cost efficiency

### Step 3: Findings

Generate findings report:
- Issues identified
- Severity levels
- Affected resources

### Step 4: Recommendations

Propose remediation:
- Prioritized actions
- Implementation guidance
- Estimated effort
```

### Pattern 3: Generate → Review → Commit

```markdown
## Workflow

### Step 1: Generation

Create artifacts based on requirements:
- IaC templates
- Configuration files
- Documentation

### Step 2: Validation

Verify generated content:
- Syntax validation
- Policy compliance
- Completeness check

### Step 3: Review

Present for human review:
- Show generated files
- Highlight key decisions
- Note assumptions

### Step 4: Commit (upon approval)

Persist changes via Git:
- Create branch
- Stage files
- Commit with message
- Report PR-ready
```

---

## Anti-Patterns

Avoid these common mistakes:

### Too Many Steps

❌ 20-step workflow with no clear phases

✅ Grouped into 4-6 logical phases with clear transitions

### Hidden Mutations

❌ Commands that modify without explicit acknowledgment

✅ Clear "this will modify..." statements before any mutation

### Missing Rollback

❌ Execute without rollback guidance

✅ Every mutation includes "to undo this..." instructions

### Vague Prerequisites

❌ "Make sure everything is set up"

✅ "Requires: AWS CLI configured, profile X with Y permissions"

### No Error Handling

❌ Assume everything succeeds

✅ Include "If X fails, do Y" guidance

---

## Testing Commands

Before publishing a command:

1. **Dry run**: Walk through steps mentally or in sandbox
2. **Edge cases**: What if prerequisites aren't met?
3. **Failure modes**: What if a step fails?
4. **Approval flow**: Are checkpoints clear?
5. **Documentation**: Is output format clear?

Use `/aws-coworker-audit-library` to check command quality.
