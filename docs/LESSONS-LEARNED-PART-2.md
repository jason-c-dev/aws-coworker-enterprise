# The Well-Architected Review Was Theater: Lessons in Trust, Defaults, and Minimum Viable Architecture

**Part 2 of our lessons building AWS Coworker with Claude**

*By Jason Croucher and Claude*

---

## Introduction

In [Part 1](LESSONS-LEARNED.md), we covered the foundational lessons of building AWS Coworker: sub-agent architecture, model selection, permission context, and production gates. Those were about making the agent *work correctly*.

This post is about making the agent *think correctly*.

We discovered that our Well-Architected Review (WAR) — the mechanism designed to ensure every deployment meets AWS best practices — was theater. It produced green checkmarks without evaluating anything. Worse, the config files that were supposed to make AWS Coworker "batteries-included" didn't actually work out of the box. And the trust model we'd designed had a subtle asymmetry we hadn't articulated.

These lessons run deeper than the Part 1 bugs. They're about the difference between *appearing* to follow best practices and *actually* following them — a distinction that matters enormously when your agent is making infrastructure decisions.

---

## Topics to Cover

### 1. The WAR Was Theater

**The discovery:** A CloudFront distribution created by AWS Coworker shipped without access logging — a basic Well-Architected requirement (SEC04-BP01). The WAR had passed it with green checkmarks.

**Root cause analysis across 5 files:**
- The WAR in `aws-coworker-plan-interaction.md` was a fill-in template, not an evaluation
- The planner self-certified its own work (no separation of assessment and execution)
- The guardrail agent validated governance (tagging, IAM, encryption) but not architectural fitness
- The Well-Architected skill had `- [ ] Logging enabled?` as a checklist item — never enforced
- The governance guardrails had "ALWAYS: Logging" — never consulted by the WAR process

**The EC2 absurdity:** A t2.micro instance deployed to host a static HTML space invaders game received ✅ for Cost Optimization. The "correct" architecture would have been S3 + CloudFront — the EC2 approach was fundamentally wrong, not just suboptimal. But the WAR couldn't flag this because it was evaluating the *configuration* of the chosen service, not whether the *choice of service* was appropriate.

**The lesson:** A WAR that the planner self-certifies is not a review — it's a rubber stamp. Real assessment requires evaluating the architecture against a defined baseline, not asking the implementor to grade their own work.

---

### 2. MVA vs MNA: What Should a WAR Actually Assess?

**The concept:**
- **MNA (Minimum Needed Architecture):** What's technically required for the thing to function. A CloudFront distribution needs an origin and a domain — that's MNA.
- **MVA (Minimum Viable Architecture):** What the Well-Architected Framework says you should have at a given environment tier. For CloudFront in production, that includes access logging, TLS 1.2 minimum, custom error pages, WAF integration, and OAC for S3 origins.

**The gap between MNA and MVA is where informed decisions live.** For a test deployment, you might accept the gap. For production, you shouldn't. The current WAR didn't distinguish between these.

**Environment-aware enforcement:**
- **sandbox/test:** Present MVA gaps as informational — "here's what you're skipping"
- **development:** Warn — "proceeding without logging; here's what that means"
- **staging:** Enforce required items — block on critical gaps
- **production:** Full MVA compliance required — no exceptions, output Terraform

---

### 3. Trust Directionality: Who Trusts Whom?

**The tension we identified:**
- Tenet 8 says the system is layered and extensible
- The WAR findings showed the agent was making decisions the user should be making
- But we also don't want to burden the user with every detail

**The resolution — asymmetric trust:**

> "The user never needs to trust the agent's judgment. The agent can trust the user's decision — but only after ensuring the user has full knowledge of what they're deciding."

This doesn't break Tenet 8 because:
- The agent's trust in the user is conditional (requires informed consent)
- The agent's trust is scoped (production has no override path)
- The user's agency is bounded by architectural constraints, not the agent's judgment

**What this means in practice:** AWS Coworker must present MVA gaps, explain the trade-offs, and let the user decide. It should never silently accept gaps, and it should never refuse a user's informed decision for non-production environments.

**Revised Tenet 3:** "Well-Architected by Default, Informed Override by Choice"

---

### 4. Batteries-Included Was a Lie

**The discovery:** The config files were all prefixed with `example-`. No actual config files existed. No agent or command referenced any config file. After `git clone`, AWS Coworker had zero working configuration.

**The "batteries-included" promise was broken on clone.**

**The fix — config file ownership:**

| File | Layer | Committed? |
|------|-------|------------|
| `environments.yaml` | Core | Yes — universal environment tiers |
| `profiles.yaml` | Core | Yes — schema + auto-classify patterns |
| `example-profiles.yaml` | Reference | Yes — org-specific mapping examples |
| `example-org-config.yaml` | Reference | Yes — no sensible core default exists |

**The override pattern:** Organization customizations use `*.local.yaml` files, which are already gitignored. This means core defaults are always present after clone, and org-specific configuration never pollutes the shared repo.

**The deeper lesson:** "Batteries-included" is a design commitment, not a marketing phrase. If your system claims to work out of the box, verify that it actually does after `git clone` with zero manual steps. Every example file that requires copying and renaming is a broken promise.

---

### 5. The Model Hierarchy for WAR Assessment

**Current (broken) model usage:**
- Planner (whatever model) self-certifies its own WAR
- No separation between "assess" and "implement"

**Proposed model hierarchy:**
- **Haiku sub-agents:** Discovery phase (fast, cheap) — "what exists today?"
- **Opus orchestrator (primary):** WAR assessment inline during planning — "does this architecture meet MVA for the environment tier?"
- **Sonnet sub-agents:** Execution (thorough) — "implement the approved plan"

The key insight is that WAR assessment is a *reasoning task*, not a discovery task. It requires judgment about trade-offs, service appropriateness, and the gap between what's proposed and what's needed. That's Opus territory — and crucially, it's the *orchestrator's* Opus, not a separate Opus sub-agent. The orchestrator already has the user's request, the discovery results from Haiku, and the skill context. Spinning up a dedicated Opus sub-agent for WAR would pay for Opus twice for no benefit. The orchestrator IS the reasoning layer — WAR assessment belongs there.

For batch assessment at scale (e.g., auditing hundreds of existing resources against MVA), the cost equation changes and a tiered approach using Sonnet or even Opus 4.5/4.6 for batch sub-agents may be justified. But for the standard single-resource planning flow, the orchestrator handles WAR directly.

---

### 6. Extensibility of MVA Baselines

**The layered model:**
```
Core MVA (per service)    ← skills/aws/ defines baseline
        ↓
Org MVA overrides         ← skills/org/ can ADD requirements
        ↓
BU MVA overrides          ← skills/bu/ can ADD further
```

**Key constraint:** Higher layers can raise the bar but cannot lower it. Only the user can accept gaps below core MVA, and only for non-production environments.

**Why this matters for the future:** AWS services evolve. New best practices emerge. Organization requirements change. The MVA baseline must be updatable without breaking existing deployments or requiring changes to the core evaluation logic.

---

### 7. Emergent Behavior: When Agents Improve Your Spec

**The discovery:** The WAR Findings Format spec defined two MVA statuses — PASS (compliant) and GAP (non-compliant). Binary. During the first real test (M1: create an S3 bucket), the orchestrator invented a third: **PLAN**.

**Why it improvised:** The orchestrator was evaluating a *plan*, not existing infrastructure. The bucket didn't exist yet, so nothing could "pass." But marking "Block all public access" as GAP was misleading — the plan already included `put-public-access-block`. The binary model didn't fit the situation, so the agent created a middle ground.

**What PLAN means:** The item is a gap in the *current state*, but the plan remediates it. This lets you distinguish at a glance between three things: items the plan addresses (PLAN), items that already comply (PASS), and items the plan leaves unresolved (GAP). Critically, the execution gate only evaluates GAPs — PLAN items are considered addressed because the user approves the full plan including those remediations.

**The pattern:** When agents encounter specs that don't cover their situation, they improvise. Sometimes the improvisation is wrong. Sometimes it's better than what you wrote. The right response isn't to prevent improvisation — it's to evaluate whether it's good, then codify it so it's consistent across sessions rather than leaving it to chance.

**What we codified:** The three-state model (PASS / PLAN / GAP) is now part of the WAR Findings Format spec, with guidance on when each status applies depending on context — planning new resources, reviewing existing infrastructure, or modifying existing resources.

**The deeper lesson:** Specs are hypotheses. Real usage generates data. If your agent invents something useful that your spec didn't anticipate, that's not a bug — it's a signal that the spec was incomplete. Codify the good emergent behavior; suppress the bad. This is Tenet 9 (Self-Extending System) in action, except the extension came from the agent at runtime, not from a meta-designer at design time.

---

## Implementation Roadmap

The documentation and config file changes have been completed. The following items require separate implementation work:

1. **Define MVA baselines per service** — Starting with CloudFront, EC2, S3, RDS in the CLI playbook commands
2. **Rewrite WAR evaluation in the plan command** — Replace fill-in template with actual evaluation logic
3. **Add `well_architected:` sections to environments.yaml** — Per-environment enforcement levels
4. **Update the planner agent** — WAR evaluation logic with model hierarchy (Haiku → Opus → Sonnet)
5. **Add the informed override flow** — Present gaps, explain trade-offs, record user's decision
6. **Consider a new `skills/aws/aws-mva-baselines/` skill** — Extensible per-service MVA definitions
7. **Test framework updates** — New W-category tests for WAR evaluation behavior

---

## Connection to Part 1

These lessons build directly on the foundations from Part 1:

| Part 1 Lesson | Part 2 Extension |
|---------------|-----------------|
| Sub-agent architecture matters | WAR assessment needs its own model tier (Opus) |
| Explicit over implicit | MVA baselines must be explicitly defined, not inferred |
| Permission context | Trust directionality — the user decides, the agent informs |
| Production gates | Environment-aware WAR enforcement adds graduated gates |
| Model selection | WAR assessment is a reasoning task that deserves Opus |

The pattern is consistent: every time we assumed the agent would "figure it out," things broke. Explicit baselines, explicit evaluation, explicit user decisions — that's the path forward.

---

*Part 2 of the AWS Coworker lessons series. Part 1: [I Used Claude Cowork to Build a Claude Code Agent for AWS. Here's What Broke](LESSONS-LEARNED.md)*

*The views expressed here are my own and do not represent the views of my employer. AWS Coworker is a personal learning project, not an official AWS product.*
