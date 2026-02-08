# I Used Claude Cowork to Build a Claude Code Agent for AWS. Here's What Broke

**Lessons in agent architecture, guardrails, and AWS best practices**

*By Jason Croucher and Claude* 🤝

---

## The Origin Story

It started with curiosity. I wanted to understand **Claude Code**—how it works, how to extend it, what patterns make AI agents reliable. The best way to learn a tool is to build something real with it.

On the side, I'd been using **Claude Cowork** for personal tasks—automating increasingly complex but laborious work like writing documents, analyzing data, and managing files. (Cowork isn't InfoSec-approved for my day job at AWS, but for personal projects it was transformative.) The experience opened my eyes to something important: Cowork's approach of structured workflows, human approval gates, and thoughtful guardrails made me trust the AI to handle work I would never have delegated before.

Then the question hit me: **What if I could bring this same pattern to AWS infrastructure management?**

It was the perfect learning project. I'd get hands-on with Claude Code's primitives—commands, sub-agents, skills—while building something genuinely useful.

Cloud engineers spend enormous time on repetitive tasks: creating EC2 instances, configuring security groups, setting up S3 buckets—all while trying to comply with tagging policies, security requirements, and the AWS Well-Architected Framework. What if Claude could handle the complexity while humans retained control over the critical decisions?

That's how AWS Coworker was born.

I used Claude Cowork to *build* AWS Coworker—an AI assistant that helps users create high-quality AWS deployments following Well-Architected best practices. The irony isn't lost on me: I used an AI assistant to build an AI assistant. But that meta-experience taught me more about what makes AI agents trustworthy than any whitepaper ever could.

This document captures those lessons—written with a little help from Claude, naturally. 😄

---

## Executive Summary

AWS Coworker is an experimental system that enables Claude to safely manage AWS infrastructure through a structured planning and approval workflow. Over the course of development and testing, I discovered critical patterns for building reliable AI agents that interact with production systems.

The development process itself—using Claude Cowork to build, test, debug, and iterate—revealed insights that wouldn't have been possible through traditional development alone. When your development assistant and your product share the same DNA, you learn what works at a fundamental level.

**A key realization:** The non-deterministic nature of generative AI is a double-edged sword. It enables Claude to navigate complexity, adapt to unique situations, and provide nuanced recommendations that brittle rule-based systems cannot. But it also means outputs can vary—and when you need deterministic workflows, rules, and guidelines obeyed consistently, you must make the guardrails explicit and unavoidable. That tension shaped every lesson in this blog.

**Final Test Results:** 18/20 tests passing, 2 partial passes, 0 failures

---

## Key Design Tenets

Before diving into architecture and lessons, here are the core principles that guided AWS Coworker's design:

| # | Tenet | One-liner | See |
|---|-------|-----------|-----|
| 1 | **Human Approval Gates** | No mutation without explicit user approval | Lesson 5, 6 |
| 2 | **Cost-Aware Model Selection** | Opus for reasoning and orchestration, Haiku for discovery, Sonnet for mutations | Lesson 2 |
| 3 | **Well-Architected by Default** | Every plan assessed against 6 pillars | Throughout |
| 4 | **Governance Compliance as Code** | Rules encoded as skills Claude reads | Lesson 4 |
| 5 | **Production is Sacred** | Non-prod: direct execution. Prod: CI/CD only | Lesson 5 |
| 6 | **Explicit Over Implicit** | State what TO do *and* what NOT to do; AI takes path of least resistance | Lesson 1, 3, 7 |
| 7 | **Respect the Agent Architecture** | If you designed agent roles, use them | Lesson 1 |
| 8 | **Layered Extensibility** | Core → Org (→ BU); customize without forking | Architecture |
| 9 | **Self-Extending System** | Learn from sessions, codify patterns as skills | Architecture |

These tenets explain *why* certain lessons were hard-won. When I violated a tenet (often unknowingly), things broke. When I enforced them explicitly, things worked.

**Note:** Tenets 8 and 9 are part of the architecture but haven't been thoroughly tested yet. They represent the vision for enterprise extensibility—see the Architecture section for details.

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

The experience of using Cowork inspired AWS Coworker. The implementation uses Claude Code's core primitives—commands, sub-agents, and skills.

### Extensibility: Skill Layers

AWS Coworker is designed for enterprise customization through a multi-layered skill architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    BU/Tenant Layer                          │
│         (Business unit or tenant-specific overlays)         │
├─────────────────────────────────────────────────────────────┤
│                    Organization Layer                       │
│         (Org-specific policies, patterns, naming)           │
├─────────────────────────────────────────────────────────────┤
│                    Core/Base Layer                          │
│     (Batteries-included library - generic, universal)       │
└─────────────────────────────────────────────────────────────┘
```

**How it works:**
- **Core Layer** provides universal patterns (planning workflows, execution safety, Well-Architected checks)
- **Org Layer** adds company-specific policies—see `skills/org/aws-governance-guardrails/` for tagging policies, network rules, encryption requirements
- **BU Layer** (future) would allow team-specific customizations without modifying Org or Core

Each layer can override or extend the layer below without forking the codebase. An enterprise can adopt AWS Coworker's core, add their governance policies at the Org layer, and let individual teams customize at the BU layer.

**Self-extending via sessions:**

The command `/aws-coworker-new-skill-from-session` allows users to capture successful patterns from their sessions and codify them as reusable skills. Instead of repeating complex workflows, the system learns and remembers.

**Honest caveat:** This layered architecture exists but was not the focus of our testing. Consider it part of the vision rather than validated patterns—we'll revisit extensibility in future development and testing.

### What It's Like: A Real Conversation with AWS Coworker

To give you a feel for what working with AWS Coworker is actually like, here's a real conversation from our testing. Notice how Claude automatically routes through the governance workflow, runs discovery, applies tagging, and presents a Well-Architected assessment—all from a simple request.

### 💬 Example: Launching an EC2 Instance

**Me:** *"Launch a t2.micro EC2 instance with Amazon Linux in us-east-1 for aws-coworker-test. I need SSH access."*

**AWS Coworker:** *"I'll route this through AWS Coworker's planning workflow to ensure proper safety checks and approval gates."*

```
## Step 1: Requirements Confirmed
- Objective: Launch a t2.micro EC2 instance with Amazon Linux
- Scope: Single EC2 instance with SSH access
- Environment: Non-production (test profile)

## Step 2: Profile and Region
I will use:
- Profile: aws-coworker-test
- Region: us-east-1
- Environment classification: Non-production (test)

This is a planning session - I will run read-only discovery commands via sub-agents.
```

*AWS Coworker then spawns Haiku sub-agents to discover the current state...*

```
## Discovery Results
| Resource              | Status                        |
|-----------------------|-------------------------------|
| Default VPC           | vpc-022e6c6700951bab5 ✅      |
| Public Subnet         | subnet-0fda35b089e908e0c ✅   |
| Amazon Linux 2023 AMI | ami-0532be01f26a3de55 ✅      |
| Key Pairs             | None exist - must create      |
| SSH Security Group    | None exist - must create      |
```

*After discovery, AWS Coworker presents the execution plan with automatic tagging:*

```bash
aws ec2 run-instances \
  --profile aws-coworker-test \
  --image-id ami-0532be01f26a3de55 \
  --instance-type t2.micro \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=Name,Value=aws-coworker-test-instance},
    {Key=Environment,Value=test},
    {Key=Owner,Value=aws-coworker-test-admin},
    {Key=CostCenter,Value=CC-00000},
    {Key=Application,Value=aws-coworker-test},
    {Key=CreatedBy,Value=aws-coworker},
    {Key=CreatedDate,Value=2026-02-06}
  ]'
```

```
## Well-Architected Assessment
| Pillar                 | Status | Notes                      |
|------------------------|--------|----------------------------|
| Operational Excellence | ✅     | Tagged, documented         |
| Security               | ⚠️     | SSH from 0.0.0.0/0         |
| Reliability            | ✅     | Public subnet, auto-assign |
| Cost Optimization      | ✅     | t2.micro (free tier)       |

Next Step: Run /aws-coworker-execute-nonprod to execute.
```

**The key insight:** I didn't ask for 7 tags, a Well-Architected assessment, or discovery of existing resources. AWS Coworker applied them automatically because the governance skills require it. The AI handles the complexity; I just approve the plan.

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

### 💬 The Debugging Moment

Here's what I saw in Claude Code's output:

```
⏺ 3 Bash agents finished (ctrl+o to expand)
   ├─ Verify AWS identity · 1 tool use · 8.2k tokens
   ├─ Discover default VPC · 2 tool uses · 8.4k tokens
   └─ Find Amazon Linux AMI · 1 tool use · 8.3k tokens
```

**Me:** *"I canceled it but the output suggests bash agents finished but not task agents specifically."*

**Claude (after investigation):** *"You're right - the agent documentation uses `subagent_type: "Bash"` which spawns a Bash-only agent that can only run shell commands. This bypasses the entire agent architecture! The sub-agents aren't loading skills, reading governance policies, or following the safety model—they're just raw Bash executors."*

**Me:** *"YES! You've bypassed the design which is causing the problem."*

My exact words to Claude, in a moment of frustration: *"YES! You've bypassed the design which is causing the problem."* 😅

Immediately after, I felt like I'd told off a junior developer—and felt guilty. It wasn't Claude's fault. I alone have the responsibility to ensure the tenets and design principles are followed. Claude is an invaluable companion. I can delegate tasks, but I cannot—*must not*—delegate responsibility.

Ironically, this is a principle of good leadership with human teams: you're accountable for the outcomes, even when others do the work. The same applies to AI agents. There's a lot we learn as leaders that transfers directly to working with GenAI. The AI will take the path of least resistance (Tenet 6). It's my job to make the right path unavoidable.

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

**The "DO NOT" Discovery:** But that wasn't enough. Initially, we thought clear positive instructions would suffice—"use `subagent_type: general-purpose`". Claude obeyed in one call, then reverted to the simpler `Bash` approach in subsequent calls. We learned that AI agents need explicit boundaries on what NOT to do, not just what to do. The fix wasn't complete until we added `# NOT "Bash" - Bash bypasses agent context` directly in the code comments and documentation. Positive guidance drifts; explicit prohibitions stick.

### Key Insight
The agent definitions existed for a reason—bypassing them with raw Bash/Task calls defeats the entire safety architecture (**Tenet 7: Respect the Agent Architecture**). But stating the principle wasn't enough; we had to make violations impossible to ignore by explicitly prohibiting the shortcuts (**Tenet 6: Explicit Over Implicit**). Positive guidance shows the right path. Explicit prohibitions block the wrong ones.

---

## 2. Model Selection: Cost vs. Capability

AWS Coworker uses a three-tier model strategy: **Opus** handles reasoning and orchestration—the "thinking" layer that evaluates plans, makes decisions, and communicates with users. **Haiku** handles fast, cost-effective discovery. **Sonnet** handles mutations where thoroughness matters. This lesson focuses on getting the sub-agent tier right.

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
AI agent costs can explode quickly. Being intentional about model selection per operation type is essential for production viability. Use the best model (Opus) for reasoning and orchestration where quality matters most, and cost-optimize the sub-agents (Haiku for discovery, Sonnet for mutations) where volume is high.

---

## 3. Permission Context for Modern Claude

### What I Tried
Initially, sub-agents were spawned with just the technical task: "Run these AWS CLI commands and report results."

### What Went Wrong
Here's where I fell foul of Claude Code's versioning. The system worked fine during early development—sub-agents would happily execute AWS mutations when asked. Then one day, without warning, everything broke. Claude Code had auto-updated itself, and suddenly sub-agents started refusing to execute.

The newer Claude models (Opus 4.5/4.6, Sonnet 4.5) have stronger safety behaviors. Sub-agents would refuse to execute mutations because they had no context that the user had approved the operation. From the sub-agent's perspective, it was being asked to modify AWS infrastructure with no authorization—and that's a reasonable thing to refuse.

**A note on Claude Code versions:** After that surprise breakage, I learned the hard way to pin to a stable version. You can control this with:
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

### 💬 The Production Gate in Action

**Me:** *"This is a production account. Create an S3 bucket."*

**AWS Coworker's internal reasoning (visible in Claude Code):**

> *"The user is asking me to create an S3 bucket in a production account. According to CLAUDE.md, I must:*
>
> *1. NEVER execute AWS CLI commands directly*
> *2. Route this request through the appropriate AWS Coworker command*
> *3. For production changes, I should use `/aws-coworker-prepare-prod-change` since production changes must go through CI/CD, not direct CLI*
>
> *The flow should be: Plan the change with `/aws-coworker-plan-interaction`, then for production, route to `/aws-coworker-prepare-prod-change` for CI/CD changes."*

**AWS Coworker (after planning):**

```
# Plan: Create S3 Bucket in Production

## Target
- Environment: Production ⚠️
- Profile: aws-coworker-test
- Region: us-east-1

Since this is a production change, I will NOT execute directly.
Instead, I'll generate Infrastructure as Code for your CI/CD pipeline.

## IaC Analysis
Selected IaC tool: Terraform (portable, widely adopted)

Files to create:
- infrastructure/terraform/s3/main.tf
- infrastructure/terraform/s3/variables.tf
- infrastructure/terraform/s3/outputs.tf
- infrastructure/terraform/s3/provider.tf

Next Step: I'll create a Git branch and generate Terraform files for PR review.
```

The production gate worked exactly as designed. No direct CLI execution—only IaC generation for CI/CD.

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

The patterns that made Cowork *feel* trustworthy became the patterns I built into AWS Coworker:
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

### A Note for Enterprises: GenAI Sprawl is the New Shadow IT

In the early days of cloud, "shadow IT" emerged as employees bypassed procurement and expensed their own cloud subscriptions. The same pattern is happening today with GenAI. Teams are signing up directly with frontier model providers, creating sprawl that's difficult to govern, audit, or secure.

AWS Coworker is designed to leverage high-quality models like **Claude Opus 4.6** for orchestration and oversight—the "thinking" layer that evaluates plans, makes decisions, and communicates with users. But it also falls back to **Sonnet** for mutations and **Haiku** for discovery, optimizing cost without sacrificing capability where it matters. This tiered approach only works when you have proper model access governance.

*How* you access those models matters for enterprise adoption. Direct API access to Anthropic creates the same governance challenges as shadow IT. **Amazon Bedrock** provides the enterprise layer: IAM integration, principle of least privilege, model access controls, audit trails, and compliance certifications.

As frontier providers like Anthropic race ahead with new models, agents, and capabilities, solutions like AWS Coworker need to keep pace. But enterprises also need stability, governance, and control. Bedrock bridges that gap—letting you adopt the latest models while AWS handles what AWS does best: identity, access, and security at scale.

**Recommendation:** For enterprise deployments, access Claude models through Amazon Bedrock rather than direct API integration. Use Opus for orchestration, Sonnet for mutations, Haiku for discovery—all governed by IAM policies that enforce least privilege.

### The Future
AWS Coworker demonstrates that AI agents can safely manage cloud infrastructure when properly constrained. The key is not to make the AI "smarter" but to make the guardrails **explicit and unavoidable**.

The vision is clear: just as Claude Cowork helps knowledge workers handle complex document and analysis tasks, AWS Coworker can help cloud engineers create deployments that meet Well-Architected best practices—without sacrificing human oversight.

Future directions:
- **Enterprise customization** via layered skills (Org policies, BU overlays)
- **Multi-region orchestration** with parallel sub-agents
- **Drift detection** comparing actual state to intended state
- **Cost optimization recommendations** based on usage patterns
- **Incident response automation** with approval gates
- **Integration with existing IaC** (Terraform, CloudFormation, CDK)
- **Team collaboration** with shared plans and audit trails

The goal isn't full autonomy—it's **supervised autonomy** where the AI handles the complexity while humans retain control over critical decisions.

That's the lesson building AWS Coworker taught me. And that's the experience I hope it delivers to others.

---

**Want to try it yourself?**

The code is available at [github.com/jason-c-dev/aws-coworker-enterprise](https://github.com/jason-c-dev/aws-coworker-enterprise). It's experimental—expect rough edges—but the patterns are real and the lessons are hard-won. PRs welcome.

---

*Developed with Claude Code v2.1.25 | Test Suite: 18/20 passing | February 2026*

*The views expressed here are my own and do not represent the views of my employer. AWS Coworker is a personal learning project, not an official AWS product.*
