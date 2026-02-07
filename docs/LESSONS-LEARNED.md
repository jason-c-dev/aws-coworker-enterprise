# AWS Coworker: Lessons Learned

**Building a Safe, Autonomous AWS Agent with Claude**

---

## The Origin Story

It started with a simple observation: I was using **Claude Cowork** to help me with complex tasks—writing documents, analyzing code, creating presentations—and the experience was transformative. Cowork's approach of structured workflows, human approval gates, and thoughtful guardrails made me trust the AI to handle increasingly complex work.

Then the question hit me: **What if we could bring this same pattern to AWS infrastructure management?**

Cloud engineers spend enormous time on repetitive tasks: creating EC2 instances, configuring security groups, setting up S3 buckets—all while trying to comply with tagging policies, security requirements, and the AWS Well-Architected Framework. What if Claude could handle the complexity while humans retained control over the critical decisions?

That's how AWS Coworker was born.

I used Claude Cowork to *build* AWS Coworker—an AI assistant that helps users create high-quality AWS deployments following Well-Architected best practices. The irony isn't lost on me: I used an AI assistant to build an AI assistant. But that meta-experience taught me more about what makes AI agents trustworthy than any whitepaper ever could.

This document captures those lessons.

---

## Executive Summary

AWS Coworker is an experimental system that enables Claude to safely manage AWS infrastructure through a structured planning and approval workflow. Over the course of development and testing, we discovered critical patterns for building reliable AI agents that interact with production systems.

The development process itself—using Claude Cowork to build, test, debug, and iterate—revealed insights that wouldn't have been possible through traditional development alone. When your development assistant and your product share the same DNA, you learn what works at a fundamental level.

**Final Test Results:** 18/20 tests passing, 2 partial passes, 0 failures

---

## 1. The Sub-Agent Architecture Problem

### What We Tried
Initially, AWS Coworker used `subagent_type: "Bash"` to spawn sub-agents for AWS CLI operations. This seemed logical—the sub-agents were running bash commands, so use the Bash agent type.

### What Went Wrong
The output showed `"3 Bash agents finished"` instead of `"Task(Discover VPC state) Haiku 4.5"`. This was a red flag. The Bash agent type completely bypassed:
- Agent identity injection ("You are acting as aws-coworker-executor")
- Model selection (Haiku vs Sonnet)
- Permission context passing
- The entire agent definition architecture we had built

### The Fix
Changed from `subagent_type: "Bash"` to `subagent_type: "general-purpose"` with explicit agent identity in the prompt:

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
**"Commands invoke commands"** was the original design principle. The agent definitions in `.claude/agents/` existed for a reason—bypassing them with raw Bash/Task calls defeats the entire safety architecture.

---

## 2. Model Selection: Cost vs. Capability

### What We Tried
Use Haiku (fast, cheap) for read-only discovery operations. Use Sonnet (capable, more expensive) for mutations that modify infrastructure.

### What Went Wrong
Without explicit model parameters in Task invocations, sub-agents defaulted to whatever model was available—often Sonnet for everything, increasing costs unnecessarily.

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

### What We Tried
Spawn sub-agents with just the technical task: "Run these AWS CLI commands and report results."

### What Went Wrong
Newer Claude versions (Opus 4.5, Sonnet 4.5) have stronger safety behaviors. Sub-agents would refuse to execute mutations because they had no context that the user had approved the operation. From the sub-agent's perspective, it was being asked to modify AWS infrastructure with no authorization.

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

### What We Tried
Tag the primary resource (EC2 instance) and assume supporting resources would inherit tags or be handled separately.

### What Went Wrong
After an M4 test (EC2 lifecycle), we discovered:
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

### What We Tried
Create a clear separation between non-production (direct execution allowed) and production (CI/CD only) environments.

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

### What We Tried
Build a test framework that doesn't require complex automation—just structured conversations with clear pass/fail criteria.

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

### What We Tried (M8 Test)
Deploy a Space Invaders game to EC2. The prompt said: "The game is located at: tests/assets/space-invaders/space-invaders.html"

### What Went Wrong
AWS Coworker generated its own Space Invaders game instead of reading and embedding the user's actual file. The deployed game looked different because it was a different game.

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

There's something profound about using an AI assistant to build an AI assistant. Every time Claude Cowork helped me debug a problem, refine a prompt, or test a workflow, I was simultaneously learning what makes AI assistance trustworthy.

The patterns that made Cowork effective became the patterns I built into AWS Coworker:
- **Structured workflows** that guide users through complex tasks
- **Approval gates** that keep humans in control of critical decisions
- **Explicit context passing** so the AI understands what's been authorized
- **Graceful handling of edge cases** instead of failing silently

When Claude Cowork and I debugged the sub-agent architecture together, we weren't just fixing a bug—we were discovering a fundamental principle about AI agent design. When we iterated on the test framework, we were learning that human judgment is irreplaceable for evaluating conversational behavior.

### What We Built
AWS Coworker is a working foundation for safe, autonomous AWS infrastructure management:
- **Planning workflow** with governance guardrails and Well-Architected assessment
- **Approval gates** that prevent unauthorized changes
- **Production protection** that routes changes through CI/CD
- **Comprehensive tagging** for enterprise compliance
- **Model-appropriate delegation** for cost optimization
- **Human-in-the-loop testing** for quality assurance

### What We Learned
1. **Agent architecture matters.** Bypassing it with raw tool calls defeats safety mechanisms.
2. **Explicit is better than implicit.** Model selection, permission context, and file handling all require explicit instructions.
3. **Modern AI models are safety-conscious.** Orchestration systems must pass authorization context, not just tasks.
4. **Test with humans first.** Structured conversations reveal issues that automated tests miss.
5. **Production is sacred.** The friction of CI/CD is a feature that protects against AI-induced incidents.
6. **Use AI to build AI.** The experience of using Claude Cowork to build AWS Coworker taught me more about trustworthy AI design than any documentation.

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

That's the lesson Claude Cowork taught me. And that's the experience AWS Coworker aims to deliver.

---

*AWS Coworker v2.1.25 | Test Suite: 18/20 passing | February 2026*

*Built with Claude Cowork. Powered by Claude.*
