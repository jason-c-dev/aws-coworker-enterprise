---
name: audit-library
description: Guidance for auditing AWS Coworker's agents, skills, and commands
version: 1.0.0
category: meta
agents: [aws-coworker-meta-designer]
tools: [Read, Glob, Grep]
---

# Audit Library

## Purpose

This meta-skill provides guidance for auditing AWS Coworker's library of agents, skills, and commands. Use it to identify issues, inconsistencies, and improvement opportunities within the framework itself.

## When to Use

- Scheduled periodic reviews of AWS Coworker
- After significant additions or changes
- When issues are reported with skills or commands
- Before major version releases
- When onboarding new team members (to verify library health)

## When NOT to Use

- Auditing AWS infrastructure (use AWS-specific tools)
- Creating new skills (use `skill-designer`)
- Creating new commands (use `command-designer`)

---

## Audit Process

### Phase 1: Inventory

Collect complete inventory of AWS Coworker components:

```bash
# List all agents
ls -la .claude/agents/

# List all commands
ls -la .claude/commands/

# List all skills
find skills/ -name "SKILL.md" -type f

# Count components
echo "Agents: $(ls .claude/agents/*.md 2>/dev/null | wc -l)"
echo "Commands: $(ls .claude/commands/*.md 2>/dev/null | wc -l)"
echo "Skills: $(find skills/ -name 'SKILL.md' | wc -l)"
```

### Phase 2: Structural Checks

Verify each component meets structural requirements.

#### Agent Checks

For each agent in `.claude/agents/`:

| Check | Criteria | Severity |
|-------|----------|----------|
| File exists | `.md` file present | Critical |
| Identity section | Clear role statement | High |
| Purpose section | Defined responsibilities | High |
| Scope section | In/out of scope defined | High |
| Tools section | Allowed tools listed | High |
| Behavior section | Guidelines documented | Medium |

#### Skill Checks

For each skill in `skills/`:

| Check | Criteria | Severity |
|-------|----------|----------|
| SKILL.md exists | Main file present | Critical |
| Valid frontmatter | YAML parses correctly | Critical |
| Required fields | name, description, version, category, agents, tools | High |
| Purpose section | Clear explanation | High |
| When to Use | Scenarios listed | High |
| When NOT to Use | Exclusions listed | Medium |
| Guidance section | Actionable content | High |

#### Command Checks

For each command in `.claude/commands/`:

| Check | Criteria | Severity |
|-------|----------|----------|
| File exists | `.md` file present | Critical |
| Valid frontmatter | YAML parses correctly | Critical |
| Required fields | description, skills, agent, tools | High |
| Workflow section | Steps defined | High |
| Prerequisites | Requirements listed | Medium |
| Output section | Expected results described | Medium |

### Phase 3: Content Quality

Evaluate content quality across components.

#### Naming Consistency

```
Pattern: aws-coworker-{role|action}

✅ aws-coworker-planner
✅ aws-coworker-plan-interaction
❌ planner (missing prefix)
❌ aws-coworker_planner (underscore)
❌ AWSCoworkerPlanner (wrong case)
```

#### Cross-Reference Integrity

Verify all references are valid:

1. **Skills referenced in commands** — Do they exist?
2. **Agents referenced in skills** — Are they valid?
3. **Related skills in skill docs** — Do they exist?
4. **Tools listed** — Are they appropriate for the component?

#### Documentation Quality

| Aspect | Good | Needs Improvement |
|--------|------|-------------------|
| Clarity | Specific, actionable | Vague, unclear |
| Completeness | All sections filled | Missing sections |
| Examples | Concrete, tested | Abstract or missing |
| Formatting | Consistent markdown | Inconsistent |

### Phase 4: Governance Alignment

Check alignment with AWS Coworker governance:

#### Safety Compliance

- [ ] Mutation commands have approval checkpoints
- [ ] Production commands enforce CI/CD patterns
- [ ] No direct AWS CLI in read-only agents
- [ ] Blast radius disclosure in execution commands

#### Layer Compliance

- [ ] Core skills don't contain org-specific content
- [ ] Org skills are in `skills/org/`
- [ ] Meta skills follow self-evolution patterns
- [ ] Clear separation between layers

#### AWS Well-Architected Alignment

- [ ] Security: Least-privilege, encryption defaults
- [ ] Reliability: Error handling, rollback guidance
- [ ] Operational Excellence: Automation, documentation
- [ ] Cost: Cost-aware recommendations where applicable

### Phase 5: Duplication Detection

Identify overlapping or duplicated functionality:

#### Skill Overlap

Look for skills that cover similar ground:

```
Questions to ask:
- Do multiple skills address the same AWS service?
- Are there redundant patterns across skills?
- Could skills be merged or split?
```

#### Command Overlap

Look for commands with similar workflows:

```
Questions to ask:
- Do multiple commands achieve similar outcomes?
- Are there redundant approval patterns?
- Could commands share more common steps?
```

### Phase 6: Gap Analysis

Identify missing coverage:

#### AWS Service Coverage

Compare against major AWS services:

```
Core Services:
- [ ] IAM
- [ ] Organizations
- [ ] VPC / Networking
- [ ] EC2
- [ ] ECS / EKS
- [ ] Lambda
- [ ] S3
- [ ] RDS / DynamoDB
- [ ] CloudFormation / CDK
- [ ] CloudWatch / CloudTrail
```

#### Workflow Coverage

Compare against common operations:

```
Standard Workflows:
- [ ] Discovery / inventory
- [ ] Planning
- [ ] Non-prod execution
- [ ] Prod change preparation
- [ ] Rollback
- [ ] Account bootstrap
- [ ] Security audit
- [ ] Cost review
```

---

## Audit Report Template

```markdown
# AWS Coworker Audit Report

**Date:** YYYY-MM-DD
**Auditor:** [Name/Agent]
**Scope:** [Full/Partial - specify]

## Executive Summary

[2-3 sentence overview of findings]

## Inventory

| Component | Count | Status |
|-----------|-------|--------|
| Agents | X | ✅/⚠️/❌ |
| Skills | X | ✅/⚠️/❌ |
| Commands | X | ✅/⚠️/❌ |

## Critical Findings

[Issues that must be addressed]

### Finding 1: [Title]
- **Severity:** Critical
- **Component:** [Name]
- **Issue:** [Description]
- **Recommendation:** [Action]

## High Priority Findings

[Issues that should be addressed soon]

## Medium Priority Findings

[Issues to address when convenient]

## Low Priority Findings

[Minor improvements]

## Gap Analysis

### Missing Coverage
- [Gap 1]
- [Gap 2]

### Recommendations
- [Recommendation 1]
- [Recommendation 2]

## Action Items

| Priority | Item | Owner | Due |
|----------|------|-------|-----|
| Critical | [Action] | [Who] | [When] |
| High | [Action] | [Who] | [When] |

## Next Audit

Recommended: [Date or trigger]
```

---

## Severity Definitions

| Severity | Definition | Response Time |
|----------|------------|---------------|
| **Critical** | Broken functionality, security issue | Immediate |
| **High** | Missing required content, significant gaps | Within 1 week |
| **Medium** | Quality issues, minor gaps | Within 1 month |
| **Low** | Improvements, nice-to-haves | Backlog |

---

## Automation Opportunities

### Automated Checks

These checks can be automated:

```bash
# Check all skills have valid frontmatter
for skill in $(find skills/ -name "SKILL.md"); do
  # Validate YAML frontmatter
  head -50 "$skill" | grep -A 20 "^---" | head -n -1 | tail -n +2
done

# Check all commands reference existing skills
for cmd in .claude/commands/*.md; do
  # Extract skills from frontmatter
  # Verify each exists in skills/
done

# Check naming conventions
ls .claude/agents/ | grep -v "^aws-coworker-"
ls .claude/commands/ | grep -v "^aws-coworker-"
```

### Manual Checks

These require human judgment:

- Content quality and clarity
- Appropriateness of scope
- Governance alignment
- Strategic gaps

---

## Audit Frequency

| Trigger | Scope |
|---------|-------|
| Weekly | Quick inventory check |
| Monthly | Full structural audit |
| After major changes | Affected components |
| Before releases | Full audit |
| On-demand | As issues arise |

---

## Related Skills

- `skill-designer` — For creating skills identified as gaps
- `command-designer` — For creating commands identified as gaps
- `git-workflow` — For managing audit-driven changes
