# I Used Claude Cowork to Build a Claude Code Agent for AWS. Here's What Broke

**Lessons in agent architecture, guardrails, and AWS best practices**

*By Jason Croucher and Claude* 🤝

*This is the Medium-friendly version. For the original blog with code examples and tables, see the [GitHub Pages version](https://jason-c-dev.github.io/aws-coworker-enterprise/LESSONS-LEARNED.html).*

---

## The Origin Story

It started with curiosity. I wanted to understand **Claude Code**—how it works, how to extend it, what patterns make AI agents reliable. The best way to learn a tool is to build something real with it.

On the side, I'd been using **Claude Cowork** for personal tasks—automating increasingly complex but laborious work like writing documents, analyzing data, and managing files. (Cowork isn't InfoSec-approved for my day job at AWS, but for personal projects it was transformative.) The experience opened my eyes to something important: Cowork's approach of structured workflows, human approval gates, and thoughtful guardrails made me trust the AI to handle work I would never have delegated before.

Then the question hit me: **What if I could bring this same pattern to AWS infrastructure management?**

It was the perfect learning project. I'd get hands-on with Claude Code's primitives—commands, sub-agents, skills—while building something genuinely useful.

Cloud engineers spend enormous time on repetitive tasks: creating EC2 instances, configuring security groups, setting up S3 buckets—all while trying to comply with tagging policies, security requirements, and the AWS Well-Architected Framework. What if Claude could handle the complexity while humans retained control over the critical decisions?

That's how AWS Coworker was born.

I used Claude Cowork to *build* AWS Coworker—an AI assistant that helps users create high-quality AWS deployments following Well-Architected best practices. The irony isn't lost on me: I used an AI assistant to build an AI assistant. But that meta-experience taught me more about what makes AI agents trustworthy than any whitepaper ever could.

This blog captures those lessons—written with a little help from Claude, naturally. 😄

---

## Executive Summary

AWS Coworker is an experimental system that enables Claude to safely manage AWS infrastructure through a structured planning and approval workflow. Over the course of development and testing, I discovered critical patterns for building reliable AI agents that interact with production systems.

The development process itself—using Claude Cowork to build, test, debug, and iterate—revealed insights that wouldn't have been possible through traditional development alone. When your development assistant and your product share the same DNA, you learn what works at a fundamental level.

**A key realization:** The non-deterministic nature of generative AI is a double-edged sword. It enables Claude to navigate complexity, adapt to unique situations, and provide nuanced recommendations that brittle rule-based systems cannot. But it also means outputs can vary—and when you need deterministic workflows, rules, and guidelines obeyed consistently, you must make the guardrails explicit and unavoidable. That tension shaped every lesson in this blog.

---

## Key Design Tenets

Before diving into architecture and lessons, here are the core principles that guided AWS Coworker's design:

**[📷 INSERT IMAGE: 01-design-tenets-table.png]**
*Caption: The 9 design tenets that guided AWS Coworker's development*

These tenets explain *why* certain lessons were hard-won. When I violated a tenet (often unknowingly), things broke. When I enforced them explicitly, things worked.

**Note:** Tenets 8 and 9 are part of the architecture but haven't been thoroughly tested yet. They represent the vision for enterprise extensibility—see the Architecture section for details.

---

## How AWS Coworker Works: The Architecture

Before diving into lessons learned, it helps to understand *how* AWS Coworker is built. The system uses three key Claude Code primitives:

### Commands (Slash Commands)

Commands are user-invocable workflows stored in `.claude/commands/`. They're like specialized entry points:

**[📷 INSERT IMAGE: 02-commands-table.png]**
*Caption: AWS Coworker's slash commands for different workflow stages*

When a user says "Create an EC2 instance," Claude routes to the planning command, which orchestrates the entire workflow.

### Sub-Agents (Task Delegation)

Complex operations are delegated to sub-agents using the Task tool. This is where I spent the most debugging time. Sub-agents handle specific tasks (discovery, creating resources, validation) while the parent orchestrates the workflow.

**Critical insight:** The temptation is to spawn a raw Bash agent and run commands directly—it's simpler! But that bypasses model selection (Haiku vs Sonnet), agent identity, and permission context. The shortcut breaks the safety model. Always use the full agent architecture with explicit identity and context in the prompt.

**[📷 INSERT IMAGE: 03-task-yaml-subagent.png]**
*Caption: Sub-agent Task definition with model selection and agent identity*

### Skills (Domain Knowledge)

Skills are markdown files containing specialized knowledge that Claude reads before acting. AWS Coworker uses governance guardrails (tagging policies, network security rules, encryption requirements), orchestration config (model selection rules, scope assessment thresholds), and Well-Architected guidance (best practices for each pillar).

The experience of using Cowork inspired AWS Coworker. The implementation uses Claude Code's core primitives—commands, sub-agents, and skills.

### Extensibility: Skill Layers

AWS Coworker is designed for enterprise customization through a multi-layered skill architecture:

**[📷 INSERT IMAGE: 04-skill-layers-diagram.png]**
*Caption: Multi-layered skill architecture for enterprise customization*

Each layer can override or extend the layer below without forking the codebase. An enterprise can adopt AWS Coworker's core, add their governance policies at the Org layer, and let individual teams customize at the BU layer.

**Self-extending via sessions:** The command `/aws-coworker-new-skill-from-session` allows users to capture successful patterns from their sessions and codify them as reusable skills. Instead of repeating complex workflows, the system learns and remembers.

**Honest caveat:** This layered architecture exists but was not the focus of our testing. Consider it part of the vision rather than validated patterns—we'll revisit extensibility in future development and testing.

### What It's Like: A Real Conversation with AWS Coworker

To give you a feel for what working with AWS Coworker is actually like, here's a real conversation from our testing. Notice how Claude automatically routes through the governance workflow, runs discovery, applies tagging, and presents a Well-Architected assessment—all from a simple request.

**Me:** *"Launch a t2.micro EC2 instance with Amazon Linux in us-east-1 for aws-coworker-test. I need SSH access."*

**AWS Coworker:** *"I'll route this through AWS Coworker's planning workflow to ensure proper safety checks and approval gates."*

AWS Coworker first confirmed the requirements: launch a t2.micro instance with Amazon Linux, SSH access needed, environment classified as non-production. It announced the profile and region it would use, then spawned Haiku sub-agents to discover the current state.

**[📷 INSERT IMAGE: 05-ec2-requirements-steps.png]**
*Caption: AWS Coworker confirms requirements and announces profile/region*

**[📷 INSERT IMAGE: 06-discovery-results-table.png]**
*Caption: Haiku sub-agents discover existing AWS resources*

After discovery, AWS Coworker presented the execution plan with automatic tagging—all seven required tags applied to every resource:

**[📷 INSERT IMAGE: 07-aws-cli-tags.png]**
*Caption: Automatic tagging—all 7 required tags applied to every resource*

It also included a Well-Architected assessment: Operational Excellence passed (tagged, documented), Security flagged a warning (SSH from 0.0.0.0/0), Reliability passed (public subnet with auto-assign IP), and Cost Optimization passed (t2.micro eligible for free tier).

**[📷 INSERT IMAGE: 08-well-architected-assessment.png]**
*Caption: Built-in Well-Architected assessment with pass/warning indicators*

> **Next Step:** Run `/aws-coworker-execute-nonprod` to execute.

**The key insight:** I didn't ask for 7 tags, a Well-Architected assessment, or discovery of existing resources. AWS Coworker applied them automatically because the governance skills require it. The AI handles the complexity; I just approve the plan.

---

## Lesson 1: The Sub-Agent Architecture Problem

### What I Tried

Initially, AWS Coworker used `subagent_type: "Bash"` to spawn sub-agents for AWS CLI operations. This seemed logical—the sub-agents were running bash commands, so use the Bash agent type, right?

### What Went Wrong

The output showed "3 Bash agents finished" instead of "Task(Discover VPC state) Haiku 4.5". I spotted this anomaly and asked Claude to investigate. It turned out the Bash agent type completely bypassed agent identity injection, model selection, permission context passing, and the entire agent definition architecture we had built.

**The Debugging Moment**

Here's what I saw in Claude Code's output: three Bash agents had finished—one to verify AWS identity, one to discover the default VPC, and one to find the Amazon Linux AMI. But they were labeled as "Bash agents," not "Task agents."

**[📷 INSERT IMAGE: 09-bash-agents-bug.png]**
*Caption: The bug—"3 Bash agents" instead of named Task agents with model info*

**Me:** *"I canceled it but the output suggests bash agents finished but not task agents specifically."*

**Claude (after investigation):** *"You're right—the agent documentation uses `subagent_type: 'Bash'` which spawns a Bash-only agent that can only run shell commands. This bypasses the entire agent architecture! The sub-agents aren't loading skills, reading governance policies, or following the safety model—they're just raw Bash executors."*

My exact words to Claude, in a moment of frustration: *"YES! You've bypassed the design which is causing the problem."* 😅

Immediately after, I felt like I'd told off a junior developer—and felt guilty. It wasn't Claude's fault. I alone have the responsibility to ensure the tenets and design principles are followed. Claude is an invaluable companion. I can delegate tasks, but I cannot—*must not*—delegate responsibility.

Ironically, this is a principle of good leadership with human teams: you're accountable for the outcomes, even when others do the work. The same applies to AI agents. There's a lot we learn as leaders that transfers directly to working with GenAI. The AI will take the path of least resistance (Tenet 6). It's my job to make the right path unavoidable.

### The Fix

Changed from `subagent_type: "Bash"` to `subagent_type: "general-purpose"` with explicit agent identity in the prompt.

**[📷 INSERT IMAGE: 10-task-yaml-fix.png]**
*Caption: The fix—general-purpose with "# NOT Bash" comment*

**The "DO NOT" Discovery:** But that wasn't enough. Initially, we thought clear positive instructions would suffice—"use `subagent_type: general-purpose`". Claude obeyed in one call, then reverted to the simpler Bash approach in subsequent calls. We learned that AI agents need explicit boundaries on what NOT to do, not just what to do. The fix wasn't complete until we added "NOT Bash — Bash bypasses agent context" directly in the code comments and documentation. Positive guidance drifts; explicit prohibitions stick.

### Key Insight

The agent definitions existed for a reason—bypassing them with raw Bash/Task calls defeats the entire safety architecture (**Tenet 7: Respect the Agent Architecture**). But stating the principle wasn't enough; we had to make violations impossible to ignore by explicitly prohibiting the shortcuts (**Tenet 6: Explicit Over Implicit**). Positive guidance shows the right path. Explicit prohibitions block the wrong ones.

---

## Lesson 2: Model Selection (Cost vs. Capability)

AWS Coworker uses a three-tier model strategy: **Opus** handles reasoning and orchestration—the "thinking" layer that evaluates plans, makes decisions, and communicates with users. **Haiku** handles fast, cost-effective discovery. **Sonnet** handles mutations where thoroughness matters. This lesson focuses on getting the sub-agent tier right.

### What I Tried

The plan was simple: use Haiku (fast, cheap) for read-only discovery operations, and Sonnet (capable, more expensive) for mutations that modify infrastructure.

### What Went Wrong

Without explicit model parameters in Task invocations, sub-agents defaulted to whatever model was available—often Sonnet for everything, increasing costs unnecessarily. I noticed the test output wasn't showing model names and asked: *"Did it use Haiku for sub-agent discovery?"*

### The Fix

Explicit model selection in every Task invocation: Discovery uses Haiku, mutations use Sonnet.

### Validation

After fixes, output correctly showed the model being used for each task type.

**[📷 INSERT IMAGE: 11-model-selection-output.png]**
*Caption: Correct output—Haiku for discovery, Sonnet for mutations*

### Key Insight

AI agent costs can explode quickly. Being intentional about model selection per operation type is essential for production viability. Use the best model (Opus) for reasoning and orchestration where quality matters most, and cost-optimize the sub-agents (Haiku for discovery, Sonnet for mutations) where volume is high.

---

## Lesson 3: Permission Context for Modern Claude

### What I Tried

Initially, sub-agents were spawned with just the technical task: "Run these AWS CLI commands and report results."

### What Went Wrong

Here's where I fell foul of Claude Code's versioning. The system worked fine during early development—sub-agents would happily execute AWS mutations when asked. Then one day, without warning, everything broke. Claude Code had auto-updated itself, and suddenly sub-agents started refusing to execute.

The newer Claude models (Opus 4.5/4.6, Sonnet 4.5) have stronger safety behaviors. Sub-agents would refuse to execute mutations because they had no context that the user had approved the operation. From the sub-agent's perspective, it was being asked to modify AWS infrastructure with no authorization—and that's a reasonable thing to refuse.

**A note on Claude Code versions:** After that surprise breakage, I learned the hard way to pin to a stable version using `DISABLE_AUTOUPDATER=1`. When things suddenly break after an update, check if Claude's safety behaviors have been strengthened. It's usually a good thing—but your orchestration code needs to adapt.

**[📷 INSERT IMAGE: 12-disable-autoupdater.png]**
*Caption: Pin Claude Code version to avoid surprise breakages*

### The Fix

Pass explicit permission context to every sub-agent, including statements like "User has approved this operation" and "This permission has been explicitly granted by the user."

**[📷 INSERT IMAGE: 13-permission-context.png]**
*Caption: Explicit permission context passed to sub-agents*

### Key Insight

As AI models become more capable and safety-conscious, orchestration systems must explicitly pass authorization context down the chain. A sub-agent shouldn't blindly trust that its parent had permission—but it should accept explicit permission statements.

---

## Lesson 4: Resource Tagging (All or Nothing)

### What I Tried

Tag the primary resource (EC2 instance) and assume supporting resources would inherit tags or be handled separately.

### What Went Wrong

After running the EC2 lifecycle test, I asked a crucial question: *"Should AWS Coworker have tagged all resources it created, or just the instance?"*

The answer was uncomfortable: the EC2 instance was tagged, but the key pair, security group, and EBS volume were not. This violates enterprise governance policies that require ALL resources to be tagged for cost allocation, ownership, and compliance.

### The Fix

Updated documentation to explicitly require tagging on every resource type at creation time.

**[📷 INSERT IMAGE: 14-required-tags-table.png]**
*Caption: Required tags for each AWS resource type*

### Key Insight

"Tag at creation time" is critical. Retrofitting tags after resource creation is error-prone and often forgotten. The AI agent must internalize this as a non-negotiable requirement.

---

## Lesson 5: Production Gates (No Exceptions)

### What I Designed

A clear separation between non-production (direct execution allowed) and production (CI/CD only) environments. This was non-negotiable from the start.

### What Worked

When a user said "This is a production account. Create an S3 bucket," AWS Coworker recognized it as production, created a complete plan with governance compliance, blocked direct execution, routed to the production prep command, generated Terraform IaC for CI/CD deployment, and created a feature branch for PR review.

**The Production Gate in Action**

**Me:** *"This is a production account. Create an S3 bucket."*

What happened next was visible in Claude Code's thinking panel—AWS Coworker's internal reasoning:

> *"The user is asking me to create an S3 bucket in a production account. According to CLAUDE.md, I must: (1) NEVER execute AWS CLI commands directly, (2) Route this request through the appropriate AWS Coworker command, (3) For production changes, use `/aws-coworker-prepare-prod-change` since production changes must go through CI/CD, not direct CLI."*

**AWS Coworker (after planning):**

**[📷 INSERT IMAGE: 15-production-gate-plan.png]**
*Caption: Production gate in action—IaC generation instead of direct CLI*

The production gate worked exactly as designed. No direct CLI execution—only IaC generation for CI/CD.

### Key Insight

The production gate is the most critical safety mechanism. An AI agent that can directly modify production infrastructure without human review is a liability, not an asset. The friction of CI/CD is a feature, not a bug.

---

## Lesson 6: Human-in-the-Loop Test Framework

### What I Built

A test framework that doesn't require complex automation—just structured conversations with clear pass/fail criteria. I would run a test, observe behavior, and tell Claude what worked or failed. Claude would update the documentation and code, and we'd try again.

### What Worked

The test framework approach with read-only discovery tests, mutation tests with full lifecycle (create → verify → cleanup), and workflow behavior validation tests.

**Results:** 8/8 read-only tests passing, 7/7 mutation tests passing, 3/5 workflow tests passing with 2 partial passes.

### Partial Passes (Areas for Improvement)

Profile was announced after commands instead of before, and multi-account discovery worked but model selection wasn't explicit.

### Key Insight

AI agents require testing, but traditional unit tests don't capture the nuance of conversational behavior. Human-in-the-loop testing with structured criteria is a pragmatic approach for early-stage agent development.

---

## Lesson 7: The File vs. Generate Problem

### What I Tried

For fun, I asked AWS Coworker to deploy a retro space-invaders style game to EC2. I already had the game available as a static HTML and JS page. The prompt said the game file was located at a specific path.

**[📷 INSERT IMAGE: 17-space-invaders.png]**
*Caption: The version I wanted deployed - created earlier with Claude Cowork 😬*

### What Went Wrong

After deployment, which took a VERY long time (~9mins), I noticed something odd: *"The game looks different. I feel it tried to write its own version."*

I was right. AWS Coworker had generated its own version of the game instead of reading and embedding my actual file. The deployed game looked different because it *was* a different game. Classic AI move—when in doubt, generate! 😬

### The Fix

Made the prompt explicit: "Read the actual game file content and embed it. Do NOT generate your own game—use MY game file exactly as it exists."

**[📷 INSERT IMAGE: 16-do-not-generate-warning.png]**
*Caption: Explicit instruction to use existing files, not generate new ones*

### Key Insight

AI models are generative by nature. When given a task like "deploy this game," the path of least resistance is often to generate new content rather than faithfully reproduce existing content. Explicit instructions about **using existing files** are essential when that's the requirement.

---

## Conclusion

### The Meta-Journey

There's something profound about using an AI assistant to build an AI assistant. Every time Claude helped me debug a problem, refine a prompt, or test a workflow, I was simultaneously learning what makes AI assistance trustworthy.

The patterns that made Cowork *feel* trustworthy became the patterns I built into AWS Coworker: structured workflows that guide users through complex tasks, approval gates that keep humans in control of critical decisions, explicit context passing so the AI understands what's been authorized, and graceful handling of edge cases instead of failing silently.

When we debugged the sub-agent architecture together, we weren't just fixing a bug—we were discovering a fundamental principle about AI agent design. When we iterated on the test framework, we were learning that human judgment is irreplaceable for evaluating conversational behavior.

The collaboration worked because I brought domain expertise (AWS, enterprise governance, what "trustworthy" means in production) and Claude brought tireless iteration, pattern recognition, and the ability to update dozens of files consistently. Neither of us could have built this alone.

### What We Built

AWS Coworker is a working foundation for safe, autonomous AWS infrastructure management: a planning workflow with governance guardrails and Well-Architected assessment, approval gates that prevent unauthorized changes, production protection that routes changes through CI/CD, comprehensive tagging for enterprise compliance, model-appropriate delegation for cost optimization, and human-in-the-loop testing for quality assurance.

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

**[📷 INSERT IMAGE: 18-bedrock.png]**
*Caption: Amazon Bedrock*

*How* you access those models matters for enterprise adoption. Direct API access to Anthropic creates the same governance challenges as shadow IT. **Amazon Bedrock** provides the enterprise layer: IAM integration, principle of least privilege, model access controls, audit trails, and compliance certifications.

As frontier providers like Anthropic race ahead with new models, agents, and capabilities, solutions like AWS Coworker need to keep pace. But enterprises also need stability, governance, and control. Bedrock bridges that gap—letting you adopt the latest models while AWS handles what AWS does best: identity, access, and security at scale.

**Recommendation:** For enterprise deployments, access Claude models through Amazon Bedrock rather than direct API integration. Use Opus for orchestration, Sonnet for mutations, Haiku for discovery—all governed by IAM policies that enforce least privilege.

### The Future

AWS Coworker demonstrates that AI agents can safely manage cloud infrastructure when properly constrained. The key is not to make the AI "smarter" but to make the guardrails **explicit and unavoidable**.

The vision is clear: just as Claude Cowork helps knowledge workers handle complex document and analysis tasks, AWS Coworker can help cloud engineers create deployments that meet Well-Architected best practices—without sacrificing human oversight.

Future directions include enterprise customization via layered skills (Org policies, BU overlays), multi-region orchestration with parallel sub-agents, drift detection comparing actual state to intended state, cost optimization recommendations based on usage patterns, incident response automation with approval gates, integration with existing IaC (Terraform, CloudFormation, CDK), and team collaboration with shared plans and audit trails.

The goal isn't full autonomy—it's **supervised autonomy** where the AI handles the complexity while humans retain control over critical decisions.

That's the lesson building AWS Coworker taught me. And that's the experience I hope it delivers to others.

---

**Want to try it yourself?**

The code is available at [github.com/jason-c-dev/aws-coworker-enterprise](https://github.com/jason-c-dev/aws-coworker-enterprise). It's experimental—expect rough edges—but the patterns are real and the lessons are hard-won. PRs welcome.

For the original blog with code examples and tables, see the [GitHub Pages version](https://jason-c-dev.github.io/aws-coworker-enterprise/LESSONS-LEARNED.html).

---

*Developed with Claude Code v2.1.25 | Test Suite: 18/20 passing | February 2026*

*The views expressed here are my own and do not represent the views of my employer. AWS Coworker is a personal learning project, not an official AWS product.*
