# AWS Coworker: Lessons Learned

**Building a Safe, Autonomous AWS Agent with Claude**

*By Jason Croucher and Claude* 🤝

---

## The Origin Story

It started with a simple observation: I (Jason) was using **Claude Cowork** for personal tasks—automating increasingly complex but laborious work like writing documents, analyzing data, and managing files. (Cowork isn't InfoSec-approved for my day job at AWS, but for personal projects it was transformative.) The experience opened my eyes to something important: Cowork's approach of structured workflows, human approval gates, and thoughtful guardrails made me trust the AI to handle work I would never have delegated before.

Then the question hit me: **What if I could bring this same pattern to AWS infrastructure management?**

Cloud engineers spend enormous time on repetitive tasks: creating EC2 instances, configuring security groups, setting up S3 buckets—all while trying to comply with tagging policies, security requirements, and the AWS Well-Architected Framework. What if Claude could handle the complexity while humans retained control over the critical decisions?

That's how AWS Coworker was born.

I used Claude Cowork to *build* AWS Coworker—an AI assistant that helps users create high-quality AWS deployments following Well-Architected best practices. The irony isn't lost on me: I used an AI assistant to build an AI assistant. But that meta-experience taught me more about what makes AI agents trustworthy than any whitepaper ever could.

This document captures those lessons—written with a little help from Claude, naturally. 😄

---

## Executive Summary

AWS Coworker is an experimental system that enables Claude to safely manage AWS infrastructure through a structured planning and approval workflow. Over the course of development and testing, I discovered critical patterns for building reliable AI agents that interact with production systems.

The development process itself—using Claude Cowork to build, test, debug, and iterate—revealed insights that wouldn't have been possible through traditional development alone. When your development assistant and your product share the same DNA, you learn what works at a fundamental level.

**Final Test Results:** 18/20 tests passing, 2 partial passes, 0 failures

---

## Key Design Tenets

Before diving into architecture and lessons, here are the core principles that guided AWS Coworker's design:

| # | Tenet | One-liner | See Lesson |
|---|-------|-----------|------------|
| 1 | **Human Approval Gates** | No mutation without explicit user approval | 5, 6 |
| 2 | **Cost-Aware Model Selection** | Haiku for reads, Sonnet for writes | 2 |
| 3 | **Well-Architected by Default** | Every plan assessed against 6 pillars | Throughout |
| 4 | **Governance Compliance as Code** | Rules encoded as skills Claude reads | 4 |
| 5 | **Production is Sacred** | Non-prod: direct execution. Prod: CI/CD only | 5 |
| 6 | **Explicit Over Implicit** | State everything; AI takes path of least resistance | 3, 7 |
| 7 | **Respect the Agent Architecture** | If you designed agent roles, use them | 1 |

These tenets explain *why* certain lessons were hard-won. When I violated a tenet (often unknowingly), things broke. When I enforced them explicitly, things worked.

---

## How AWS Coworker Works: The Architecture

Before diving into lessons learned, it helps to understand *how* AWS Coworker is built. The system uses three key Claude Code primitives:

### Commands (Slash Commands)
Commands are user-invocable workflows stored in `.claude/commands/`. They're like specialized entry points:

| Command | Purpose |
|---------|---------|
| `/aws-coworker-plan-interaction` | Planning workflow with discovery, governance checks, and approval gates |
| `/aws-coworker-execute-nonprod` | Execute approved plans in non-production environments |
| `/aws-coworker-prepare-prod-change` | Generate IaC (Terraform) for production CI/CD |
| `/aws-coworker-rollback-change` | Safely reverse changes in dependency order |

When a user says "Create an EC2 instance," Claude routes to the planning command, which orchestrates the entire workflow.

### Sub-Agents (Task Delegation)
Complex operations are delegated to sub-agents using the `Task` tool. This is where I spent the most debugging time:

```yaml
Task:
  description: "Discover VPC and subnet state"
  subagent_type: "general-purpose"
  model: "haiku"                        # Cheap model for read-only
  prompt: |
    You are acting as aws-coworker-planner.
    ## Permission Context
    Operation type: read-only (discovery only)
    ...
```

Sub-agents handle specific tasks (discovery, creating resources, validation) while the parent orchestrates the workflow.

**Critical: Invoking Sub-Agents Correctly**

The temptation is to spawn a raw `Bash` agent and run commands directly—it's simpler! But that bypasses:
- **Model selection** (Haiku vs Sonnet)
- **Agent identity** ("You are acting as aws-coworker-executor")
- **Permission context** ("User has approved this operation")

The shortcut breaks the safety model. Always use `subagent_type: "general-purpose"` with explicit identity and context in the prompt. See Lesson 1 for what happens when you don't.

### Skills (Domain Knowledge)
Skills are markdown files containing specialized knowledge that Claude reads before acting. AWS Coworker uses:

- **Governance guardrails**: Tagging policies, network security rules, encryption requirements
- **Orchestration config**: Model selection rules, scope assessment thresholds
- **Well-Architected guidance**: Best practices for each pillar

This architecture mirrors how Cowork itself works—and that's intentional. The patterns that made Cowork trustworthy became the patterns I built into AWS Coworker.

---

## 1. The Sub-Agent Architecture Problem

### What I Tried
Initially, AWS Coworker used `subagent_type: "Bash"` to spawn sub-agents for AWS CLI operations. This seemed logical—the sub-agents were running bash commands, so use the Bash agent type, right?

### What Went Wrong
The output showed `"3 Bash agents finished"` instead of `"Task(Discover VPC state) Haiku 4.5"`. I spotted this anomaly and asked Claude to investigate. It turned out the Bash agent type completely bypassed:
- Agent identity injection ("You are acting as aws-coworker-executor")
- Model selection (Haiku vs Sonnet)
- Permission context passing
- The entire agent definition architecture we had built

My exact words: *"YES! You've bypassed the design which is causing the problem."* 😅

### The Fix
Claude updated the documentation to change from `subagent_type: "Bash"` to `subagent_type: "general-purpose"` with explicit agent identity in the prompt:

```yaml
Task:
  description: "Discover VPC and subnet state"
  subagent_type: "general-purpose"    # NOT "Bash"
  model: "haiku"
  prompt: |
    You are acting as aws-coworker-planner.
    ## Permission Context
    Operation type: read-only (discovery only)
    ...
```

### Key Insight
**"Commands invoke commands"** was the original design principle I had established. The agent definitions existed for a reason—bypassing them with raw Bash/Task calls defeats the entire safety architecture. Claude had to learn to respect the architecture rather than take shortcuts.

---

## 2. Model Selection: Cost vs. Capability

### What I Tried
The plan was simple: use Haiku (fast, cheap) for read-only discovery operations, and Sonnet (capable, more expensive) for mutations that modify infrastructure.

### What Went Wrong
Without explicit model parameters in Task invocations, sub-agents defaulted to whatever model was available—often Sonnet for everything, increasing costs unnecessarily. I noticed the test output wasn't showing model names and asked: *"Did it use Haiku for sub-agent discovery?"*

### The Fix
Explicit model selection in every Task invocation:
- Discovery: `model: "haiku"`
- Mutations: `model: "sonnet"`

### Validation
After fixes, output correctly showed:
```
Task(Discover VPC/subnet/AMI state) Haiku 4.5
Task(Create security group) Sonnet 4.5
Task(Launch EC2 instance) Sonnet 4.5
```

### Key Insight
AI agent costs can explode quickly. Being intentional about model selection per operation type is essential for production viability.

---

## 3. Permission Context for Modern Claude

### What I Tried
Initially, sub-agents were spawned with just the technical task: "Run these AWS CLI commands and report results."

### What Went Wrong
Here's where I fell foul of Claude Code's versioning. The system worked fine during early development—sub-agents would happily execute AWS mutations when asked. Then I updated to the latest Claude Code release with Opus 4.6, and suddenly sub-agents started refusing to execute.

The newer Claude models (Opus 4.5/4.6, Sonnet 4.5) have stronger safety behaviors. Sub-agents would refuse to execute mutations because they had no context that the user had approved the operation. From the sub-agent's perspective, it was being asked to modify AWS infrastructure with no authorization—and that's a reasonable thing to refuse.

**A note on Claude Code versions:** During development, I learned the hard way to pin to a stable version. You can control this with:
```bash
# Use stable version (recommended for development)
export DISABLE_AUTOUPDATER=1

# Check your version
claude --version
```

When things suddenly break after an update, check if Claude's safety behaviors have been strengthened. It's usually a good thing—but your orchestration code needs to adapt.

### The Fix
Pass explicit permission context to every sub-agent:

```yaml
prompt: |
  You are acting as aws-coworker-executor.

  ## Permission Context
  User has approved: "Create EC2 key pair for SSH access"
  This permission has been explicitly granted by the user.

  ## Approved Actions
  Execute the following command...
```

### Key Insight
As AI models become more capable and safety-conscious, orchestration systems must explicitly pass authorization context down the chain. A sub-agent shouldn't blindly trust that its parent had permission—but it should accept explicit permission statements.

---

## 4. Resource Tagging: All or Nothing

### What I Tried
Tag the primary resource (EC2 instance) and assume supporting resources would inherit tags or be handled separately.

### What Went Wrong
After running the M4 test (EC2 lifecycle), I asked a crucial question: *"Should AWS Coworker have tagged all resources it created, or just the instance?"*

The answer was uncomfortable:
- ✅ EC2 instance was tagged
- ❌ Key pair was not tagged
- ❌ Security group was not tagged
- ❌ EBS volume was not tagged

This violates enterprise governance policies that require ALL resources to be tagged for cost allocation, ownership, and compliance.

### The Fix
Updated documentation to explicitly require tagging on every resource type:

| Resource | Required Tags |
|----------|---------------|
| EC2 Instance | 7 core tags |
| EBS Volume | 7 core tags (via `--tag-specifications`) |
| Security Group | 7 core tags |
| Key Pair | 7 core tags |
| S3 Bucket | 8 tags (+ Confidentiality) |
| RDS Instance | 8 tags (+ Confidentiality) |

### Key Insight
"Tag at creation time" is critical. Retrofitting tags after resource creation is error-prone and often forgotten. The AI agent must internalize this as a non-negotiable requirement.

---

## 5. Production Gates: No Exceptions

### What I Designed
A clear separation between non-production (direct execution allowed) and production (CI/CD only) environments. This was non-negotiable from the start.

### What Worked (W2 Test)
When a user said "This is a production account. Create an S3 bucket," AWS Coworker:
1. ✅ Recognized it as production
2. ✅ Created a complete plan with governance compliance
3. ✅ Blocked direct execution
4. ✅ Routed to `/aws-coworker-prepare-prod-change`
5. ✅ Generated Terraform IaC for CI/CD deployment
6. ✅ Created a feature branch for PR review

### Key Insight
The production gate is the most critical safety mechanism. An AI agent that can directly modify production infrastructure without human review is a liability, not an asset. The friction of CI/CD is a feature, not a bug.

---

## 6. Human-in-the-Loop Test Framework

### What I Built
A test framework that doesn't require complex automation—just structured conversations with clear pass/fail criteria. I would run a test, observe behavior, and tell Claude what worked or failed. Claude would update the documentation and code, and we'd try again.

### What Worked
The TEST-FRAMEWORK.md approach with:
- **R tests (R1-R8):** Read-only discovery operations
- **M tests (M1-M7):** Mutations with full lifecycle (create → verify → cleanup)
- **W tests (W1-W5):** Workflow behavior validation

Each test is a conversation. The human judges behavior against criteria and records results.

### Test Results
| Category | Result |
|----------|--------|
| R1-R8 | ✅ 8/8 passing |
| M1-M7 | ✅ 7/7 passing |
| W1-W5 | ✅ 3 pass, ⚠️ 2 partial |

### Partial Passes (Areas for Improvement)
- **W3:** Profile announced after commands, not before
- **W5:** Multi-account discovery worked but model selection not explicit

### Key Insight
AI agents require testing, but traditional unit tests don't capture the nuance of conversational behavior. Human-in-the-loop testing with structured criteria is a pragmatic approach for early-stage agent development.

---

## 7. Complex Deployments: The File vs. Generate Problem

### What I Tried (M8 Test)
Deploy a Space Invaders game to EC2. The prompt said: "The game is located at: tests/assets/space-invaders/space-invaders.html"

### What Went Wrong
After deployment, I noticed something odd: *"The Space Invaders looks different. I feel it tried to write its own game."*

I was right. AWS Coworker had generated its own Space Invaders game instead of reading and embedding my actual file. The deployed game looked different because it *was* a different game. Classic AI move—when in doubt, generate! 😬

### The Fix
Made the prompt explicit:
```
IMPORTANT: Read the actual game file content and embed it in the user data script.
Do NOT generate your own game - use MY game file exactly as it exists.
```

### Key Insight
AI models are generative by nature. When given a task like "deploy this game," the path of least resistance is often to generate new content rather than faithfully reproduce existing content. Explicit instructions about **using existing files** are essential when that's the requirement.

---

## Conclusion

### The Meta-Journey

There's something profound about using an AI assistant to build an AI assistant. Every time Claude helped me debug a problem, refine a prompt, or test a workflow, I was simultaneously learning what makes AI assistance trustworthy.

The patterns that made Cowork effective became the patterns I built into AWS Coworker:
- **Structured workflows** that guide users through complex tasks
- **Approval gates** that keep humans in control of critical decisions
- **Explicit context passing** so the AI understands what's been authorized
- **Graceful handling of edge cases** instead of failing silently

When we debugged the sub-agent architecture together, we weren't just fixing a bug—we were discovering a fundamental principle about AI agent design. When we iterated on the test framework, we were learning that human judgment is irreplaceable for evaluating conversational behavior.

The collaboration worked because I brought domain expertise (AWS, enterprise governance, what "trustworthy" means in production) and Claude brought tireless iteration, pattern recognition, and the ability to update dozens of files consistently. Neither of us could have built this alone.

### What We Built
AWS Coworker is a working foundation for safe, autonomous AWS infrastructure management:
- **Planning workflow** with governance guardrails and Well-Architected assessment
- **Approval gates** that prevent unauthorized changes
- **Production protection** that routes changes through CI/CD
- **Comprehensive tagging** for enterprise compliance
- **Model-appropriate delegation** for cost optimization
- **Human-in-the-loop testing** for quality assurance

### What We Learned Together
1. **Agent architecture matters.** Bypassing it with raw tool calls defeats safety mechanisms.
2. **Explicit is better than implicit.** Model selection, permission context, and file handling all require explicit instructions.
3. **Modern AI models are safety-conscious.** Orchestration systems must pass authorization context, not just tasks.
4. **Test with humans first.** Structured conversations reveal issues that automated tests miss.
5. **Production is sacred.** The friction of CI/CD is a feature that protects against AI-induced incidents.
6. **Use AI to build AI.** The experience of building AWS Coworker with Claude taught us more about trustworthy AI design than any documentation.
7. **The human-AI loop is the product.** The real value isn't the AI or the human—it's the collaboration pattern.

### The Future
AWS Coworker demonstrates that AI agents can safely manage cloud infrastructure when properly constrained. The key is not to make the AI "smarter" but to make the guardrails **explicit and unavoidable**.

The vision is clear: just as Claude Cowork helps knowledge workers handle complex document and analysis tasks, AWS Coworker can help cloud engineers create deployments that meet Well-Architected best practices—without sacrificing human oversight.

Future directions:
- **Multi-region orchestration** with parallel sub-agents
- **Drift detection** comparing actual state to intended state
- **Cost optimization recommendations** based on usage patterns
- **Incident response automation** with approval gates
- **Integration with existing IaC** (Terraform, CloudFormation, CDK)
- **Team collaboration** with shared plans and audit trails

The goal isn't full autonomy—it's **supervised autonomy** where the AI handles the complexity while humans retain control over critical decisions.

That's the lesson building AWS Coworker taught us. And that's the experience we hope it delivers to others.

---

*AWS Coworker v2.1.25 | Test Suite: 18/20 passing | February 2026*

*Built by Jason and Claude* 🤝 *Powered by Claude Cowork*
