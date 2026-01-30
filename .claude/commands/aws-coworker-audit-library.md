---
description: Audit AWS Coworker agents, skills, and commands for health and consistency
skills: [audit-library, skill-designer, command-designer]
agent: aws-coworker-meta-designer
tools: [Read, Glob, Grep]
arguments:
  - name: scope
    description: What to audit (all, agents, skills, commands)
    required: false
    default: all
  - name: output
    description: Output format (summary, detailed, report)
    required: false
    default: summary
---

# /aws-coworker-audit-library

## Overview

Run a comprehensive audit of AWS Coworker's library of agents, skills, and commands. Identifies issues, inconsistencies, and improvement opportunities.

## Prerequisites

- AWS Coworker repository with components to audit

---

## Workflow

### Step 1: Inventory Components

```
## AWS Coworker Library Audit

Starting audit at {timestamp}

### Inventory Scan
```

```bash
# Count components
echo "Agents: $(ls .claude/agents/*.md 2>/dev/null | wc -l)"
echo "Commands: $(ls .claude/commands/*.md 2>/dev/null | wc -l)"
echo "Skills: $(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
```

```
### Component Counts
| Type | Count |
|------|-------|
| Agents | {X} |
| Commands | {Y} |
| Skills | {Z} |
| **Total** | {X+Y+Z} |
```

### Step 2: Audit Agents

```
## Agent Audit

Checking .claude/agents/...
```

For each agent:

```
### {agent-name}

| Check | Status | Notes |
|-------|--------|-------|
| File exists | ✅/❌ | |
| Identity section | ✅/❌ | |
| Purpose section | ✅/❌ | |
| Scope section | ✅/❌ | |
| Allowed tools | ✅/❌ | |
| Behavior guidelines | ✅/❌ | |
| Naming convention | ✅/❌ | aws-coworker-* |
```

### Step 3: Audit Skills

```
## Skills Audit

Checking skills/...
```

For each skill:

```
### {category}/{skill-name}

| Check | Status | Notes |
|-------|--------|-------|
| SKILL.md exists | ✅/❌ | |
| Valid frontmatter | ✅/❌ | |
| Required fields | ✅/❌ | name, description, version, category, agents, tools |
| Purpose section | ✅/❌ | |
| When to Use | ✅/❌ | |
| When NOT to Use | ✅/❌ | |
| Main content | ✅/❌ | |
| Examples | ✅/⚠️/❌ | |
| Related skills valid | ✅/❌ | |
```

### Step 4: Audit Commands

```
## Commands Audit

Checking .claude/commands/...
```

For each command:

```
### {command-name}

| Check | Status | Notes |
|-------|--------|-------|
| File exists | ✅/❌ | |
| Valid frontmatter | ✅/❌ | |
| Required fields | ✅/❌ | description, skills, agent, tools |
| Skills exist | ✅/❌ | All referenced skills found |
| Agent exists | ✅/❌ | Referenced agent found |
| Workflow section | ✅/❌ | |
| Naming convention | ✅/❌ | aws-coworker-* |
```

### Step 5: Cross-Reference Validation

```
## Cross-Reference Validation

### Skills Referenced in Commands
| Command | Referenced Skills | Status |
|---------|------------------|--------|
| {command} | {skill1, skill2} | ✅/❌ |

### Agents Referenced in Skills
| Skill | Referenced Agents | Status |
|-------|------------------|--------|
| {skill} | {agent1, agent2} | ✅/❌ |

### Related Skills References
| Skill | Related Skills | Status |
|-------|---------------|--------|
| {skill} | {related1, related2} | ✅/❌ |
```

### Step 6: Consistency Checks

```
## Consistency Analysis

### Naming Conventions
| Component | Convention | Violations |
|-----------|------------|------------|
| Agents | aws-coworker-{role} | {list or none} |
| Commands | aws-coworker-{action} | {list or none} |
| Skills | {category}-{name} | {list or none} |

### Version Consistency
| Component | Version | Notes |
|-----------|---------|-------|
| {component} | {version} | {if inconsistent} |

### Tool Usage
| Tool | Agents Using | Appropriate |
|------|-------------|-------------|
| Bash | {list} | ✅/⚠️ |
| Write | {list} | ✅/⚠️ |
```

### Step 7: Gap Analysis

```
## Gap Analysis

### AWS Service Coverage
| Service | Skill Coverage | Gap |
|---------|---------------|-----|
| EC2 | aws-cli-playbook | ✅ |
| S3 | aws-cli-playbook | ✅ |
| Lambda | aws-cli-playbook | ⚠️ Basic |
| EKS | None | ❌ Missing |

### Workflow Coverage
| Workflow | Command | Status |
|----------|---------|--------|
| Planning | aws-coworker-plan-interaction | ✅ |
| Execution | aws-coworker-execute-nonprod | ✅ |
| Rollback | aws-coworker-rollback-change | ✅ |
| {missing} | None | ❌ |

### Documentation Coverage
| Doc | Status |
|-----|--------|
| README | ✅/❌ |
| Getting Started | ✅/❌ |
| Customization | ✅/❌ |
| CONTRIBUTING | ✅/❌ |
```

### Step 8: Generate Report

```
## Audit Report Summary

### Overall Health
| Category | Score | Status |
|----------|-------|--------|
| Agents | {X}/100 | {Good/Fair/Poor} |
| Skills | {Y}/100 | {Good/Fair/Poor} |
| Commands | {Z}/100 | {Good/Fair/Poor} |
| **Overall** | {avg}/100 | {status} |

### Findings by Severity

#### Critical ({count})
{Issues that must be addressed}

#### High ({count})
{Issues that should be addressed}

#### Medium ({count})
{Issues to consider addressing}

#### Low ({count})
{Minor improvements}

### Top Recommendations
1. {recommendation 1}
2. {recommendation 2}
3. {recommendation 3}

### Action Items
| Priority | Item | Effort |
|----------|------|--------|
| Critical | {item} | {effort} |
| High | {item} | {effort} |
```

---

## Detailed Report (if requested)

```
## Detailed Audit Report

### Agents Detail
{Full details for each agent}

### Skills Detail
{Full details for each skill}

### Commands Detail
{Full details for each command}

### All Findings
{Complete list of all findings}

### Cross-Reference Matrix
{Full matrix of component relationships}
```

---

## Output Formats

### Summary (default)

Quick overview with key metrics and top issues.

### Detailed

Full analysis of every component with all checks.

### Report

Formal audit report suitable for documentation or review:

```markdown
# AWS Coworker Library Audit Report

**Date:** {date}
**Auditor:** aws-coworker-meta-designer
**Scope:** {scope}

## Executive Summary
{summary}

## Findings
{detailed findings}

## Recommendations
{prioritized recommendations}

## Appendix
{supporting details}
```

---

## Audit Checklist Reference

### Agent Checklist
- [ ] File exists with .md extension
- [ ] Identity section clearly defines role
- [ ] Purpose section explains what agent does
- [ ] Scope section defines in/out of scope
- [ ] Allowed tools section with restrictions
- [ ] Behavior guidelines documented
- [ ] Collaboration patterns defined
- [ ] Examples provided

### Skill Checklist
- [ ] SKILL.md exists in skill directory
- [ ] Valid YAML frontmatter
- [ ] All required fields present
- [ ] Purpose section clear
- [ ] When to Use scenarios listed
- [ ] When NOT to Use exclusions listed
- [ ] Substantive guidance content
- [ ] At least one example
- [ ] Related skills valid references

### Command Checklist
- [ ] File exists with .md extension
- [ ] Valid YAML frontmatter
- [ ] Description field present
- [ ] Skills field references existing skills
- [ ] Agent field references existing agent
- [ ] Tools field appropriate for workflow
- [ ] Arguments documented
- [ ] Workflow section with steps
- [ ] Output section describes results

---

## Example Output

```
## AWS Coworker Audit Summary

Date: 2026-01-29
Scope: All components

### Inventory
- Agents: 6
- Commands: 8
- Skills: 11
- Total: 25 components

### Health Score: 87/100 (Good)

### Issues Found
- Critical: 0
- High: 2
- Medium: 5
- Low: 8

### Top Issues
1. [HIGH] Skill 'aws-cli-playbook' missing EKS examples
2. [HIGH] Command 'aws-coworker-bootstrap-account' references non-existent template
3. [MEDIUM] Inconsistent version numbers across skills

### Recommendations
1. Add EKS patterns to aws-cli-playbook
2. Create missing template file or update reference
3. Standardize version to 1.0.0 for initial release

### Next Audit
Recommended: After next significant update or in 30 days
```
