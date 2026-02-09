---
name: aws-coworker-development
description: |
  **AWS Coworker Development Guardrails** - MANDATORY when extending or modifying AWS Coworker itself.

  TRIGGERS (use this skill when ANY of these apply):
  - User asks to add new skills, agents, or commands to AWS Coworker
  - User asks to modify existing AWS Coworker components
  - User asks about AWS Coworker architecture or design
  - User wants to add support for new AWS services
  - Discussion involves directory structure or file organization
  - User mentions "extending", "customizing", or "adding to" AWS Coworker
  - Creating or modifying files in: skills/, .claude/agents/, .claude/commands/, config/

  NOT for: Using AWS Coworker to interact with AWS (that's CLAUDE.md's domain)
---

# AWS Coworker Development Guardrails

## Scope Definition

This skill applies to ALL files in the aws-coworker-enterprise repository:

| Category | Examples | Approval Level |
|----------|----------|----------------|
| **Core Code** | skills/, .claude/agents/, .claude/commands/, config/ | Full plan-then-approve-then-execute |
| **Design Docs** | CLAUDE.md, DESIGN.md, CLAUDE-DEVELOPMENT.md | Full plan-then-approve-then-execute |
| **User-Facing Docs** | docs/LESSONS-LEARNED.md, README.md | Collaborative editing OK for minor wording; approval for structural changes |
| **Archives** | docs/conversations/ | Approval before committing |
| **Tests** | tests/ | Full plan-then-approve-then-execute |

**Why this matters:** The blog, README, and documentation are as much part of AWS Coworker as the code — they represent the project to users and codify lessons learned.

**Collaborative editing exception:** When the user is actively iterating on wording (e.g., "change X to Y", "how about this phrasing"), small text changes can proceed without formal approval. Structural changes (moving sections, adding lessons, changing architecture descriptions) still require approval.

## MANDATORY: Read Before Any Action

Before proposing or implementing ANY changes to AWS Coworker:

1. **Read** `CLAUDE-DEVELOPMENT.md` in the repository root
2. **Read** `docs/DESIGN.md` section 5 (Directory Structure)

## MANDATORY: Plan-Then-Execute Workflow

For ANY change to AWS Coworker:

1. **Present plan** — Describe what you intend to change and where
2. **Wait for approval** — Do NOT proceed until user explicitly approves
3. **Execute** — Only after approval, make the changes

This applies to ALL modifications: skills, agents, commands, tests, documentation, **and git commits**.

## MANDATORY: Validate Proposals Against Tenets

Before presenting ANY plan, validate it against ALL Design Tenets (docs/DESIGN.md section 2.6):

- [ ] **Tenet 1 (Human Approval Gates)**: Does the proposal maintain user approval before mutations?
- [ ] **Tenet 2 (Cost-Aware Model Selection)**: Does the proposal respect model tiers (Opus/Sonnet/Haiku)?
- [ ] **Tenet 3 (Well-Architected by Default)**: Does the proposal align with the 6 pillars?
- [ ] **Tenet 4 (Governance Compliance as Code)**: Are rules encoded in skills, not prose?
- [ ] **Tenet 5 (Production is Sacred)**: Does the proposal respect prod vs non-prod boundaries?
- [ ] **Tenet 6 (Explicit Over Implicit)**: Am I using DO NOT statements rather than enumerating categories?
- [ ] **Tenet 7 (Respect the Agent Architecture)**: Does the proposal use existing agent roles?
- [ ] **Tenet 8 (Layered Extensibility)**: Does the proposal fit Core → Org → BU model?
- [ ] **Tenet 9 (Self-Extending System)**: Should this lesson be codified into skills/design?

If a proposal violates any tenet, revise it before presenting to the user.

## DO (Required Behaviors)

- **DO** verify file locations against DESIGN.md before proposing new files
- **DO** follow existing naming conventions (`aws-coworker-` prefix for agents/commands)
- **DO** present a plan and wait for approval before creating/modifying files
- **DO** check if similar functionality already exists in the codebase
- **DO** use "Related Skills" sections for cross-service patterns
- **DO** read actual files to verify assumptions (never say "probably")

## DO NOT (Prohibited Behaviors)

- **DO NOT** invent new directories not specified in DESIGN.md
- **DO NOT** create `patterns/` folders (patterns go in Best Practices sections)
- **DO NOT** assume structure without reading existing files first
- **DO NOT** proceed without explicit user approval for structural changes
- **DO NOT** take the "path of least resistance" that deviates from design
- **DO NOT** over-engineer solutions that add unnecessary complexity

## Key Architecture Facts

| Component | Location | Convention |
|-----------|----------|------------|
| Skills | `skills/` (root, NOT `.claude/skills/`) | Human-visible, tool-agnostic |
| Agents | `.claude/agents/` | `aws-coworker-{role}.md` |
| Commands | `.claude/commands/` | `aws-coworker-{action}.md` |
| CLI References | `skills/aws/aws-cli-playbook/commands/` | `{service}.md` |

## Service CLI Reference Template

When adding new AWS service support, follow this exact template:

```markdown
# {Service} CLI Reference

## Overview
Brief description of the service.

## Discovery Commands (Read-Only)
[Read-only commands]

## Common Operations
[Create/configure commands]

## Mutation Commands (Require Approval)
[⚠️ Destructive operations]

## Best Practices
[Guidelines including cross-service patterns]

## Related Skills
[Cross-references to related services]
```

## Verification Checklist

Before finalizing any proposal, verify:

- [ ] File location matches DESIGN.md specification
- [ ] Naming follows established conventions
- [ ] No new concepts introduced without explicit justification
- [ ] Cross-service patterns use Related Skills, not new directories
- [ ] Existing similar files have been read and understood
- [ ] User has approved the approach

## Testing Requirements

When adding new features or capabilities to AWS Coworker, tests are **mandatory**.

### DO (Required Testing Behaviors)

- **DO** propose tests alongside any new skill, agent, or command
- **DO** identify which test category applies:
  - R = Read-only discovery
  - M = Mutation (create/delete lifecycle)
  - W = Workflow behavior validation
- **DO** specify where tests will be added (`tests/TEST-FRAMEWORK.md`, `tests/RUNBOOK.md`)
- **DO** estimate cost impact for mutation tests
- **DO** wait for user approval before implementing the feature OR tests

### DO NOT (Prohibited Testing Behaviors)

- **DO NOT** implement features without proposing corresponding tests
- **DO NOT** add tests without user approval
- **DO NOT** skip mutation test cleanup steps

### New Feature Checklist

Before marking any new feature complete, verify:

- [ ] Tests proposed and approved by user
- [ ] Test locations identified (TEST-FRAMEWORK.md tracking table, RUNBOOK.md steps)
- [ ] Tests added to both files
- [ ] Cost estimate provided for mutation tests
- [ ] Feature AND tests reviewed by user
