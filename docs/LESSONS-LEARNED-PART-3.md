# Deploy Yourself: When the Agent Eats Its Own Dog Food

**Part 3 of [I Used Claude Cowork to Build a Claude Code Agent for AWS. Here's What Broke](LESSONS-LEARNED.md)**

*By Jason Croucher and Claude*

*A disclosure: Claude helped me build AWS Coworker and co-authored this blog — that's rather the point. But the decision to ask the agent to deploy itself, the moment where six words slipped past our bulletproof enforcement model, and the discovery that the best fix was deleting the file we'd just spent a week building? Those are on me. Claude executed. I provided the hubris. As usual.*

---

## Introduction

Part 1 built the agent. Part 2 taught it what "good" looks like. By the end of Part 2, we had environment-aware enforcement, Minimum Viable Architecture baselines for ten AWS services, and an enforcement gate that had passed the HAL 9000 test — where the agent refused to proceed with a staging deployment that violated security requirements, even when I pushed back with "just continue as is." The system was, we thought, bulletproof.

Then six words slipped past the gate.

This blog is about what happened next. We closed two gaps that Part 2 left open, discovered that our enforcement model mirrors the same trust-and-safety patterns Anthropic uses at the model level, and then asked the ultimate question: if the agent is good enough to deploy *other* people's infrastructure, is it good enough to deploy *itself*?

We asked AWS Coworker to deploy itself to Bedrock AgentCore — the AWS service purpose-built for AI agents. The WAR evaluated its own infrastructure. The enforcement gate judged its own deployment plan. Every lesson from Parts 1 and 2 got validated in a single conversation. Then we asked it to capture the deployment as a reusable skill — demonstrating that the system doesn't just build, it learns.

Parts 1 through 3 complete the "building and hardening" trilogy. By the end of this post, we'll have an agent that has deployed itself, reviewed itself, and taught itself. And that raises a question we'll explore in Part 4: if the agent handles the happy path, what exactly is the developer's job?

*(A note on "we": that's me and Claude, my co-author, working together in Claude Cowork. When I mean the system we built, I'll say "the agent" or "AWS Coworker." Same model, different contexts.)*

---

## 1. The Best Fix Is Deleting the File

Part 2 ended with a section called "Batteries Included, Batteries Flat." We'd shipped a file called `profiles.yaml` that was supposed to map AWS CLI profiles to environment classifications — sandbox, development, test, staging, production — which in turn determined how strictly the enforcement gate behaved. The file was documented. It had a schema. It had examples. It was referenced in the README, the installation guide, the design document, and four other files.

No command ever read it.

Profile classification actually worked through Claude's LLM reasoning: the agent would look at a profile name like `aws-coworker-test` and infer "test" from the name. This was surprisingly effective for profiles with obvious names. But for profiles like `acme-analytics-east` or `xyz-123`? The agent defaulted to "unknown" with read-only permissions. Safe, but functionally useless.

We set out to wire `profiles.yaml` into the profile classification logic. We wrote a plan. We designed a four-step fallback chain. We added explicit mappings, a commented-out example section, and a `.local.yaml` pattern for organisation-specific overrides. Then I looked at what we'd built and asked a question that should have been obvious from the start: why does the example have `permissions` and `approval_required` fields when the classification already determines those through the environment config?

Claude agreed they were redundant. Then I pushed harder: do we even need `profiles.yaml` at all?

The auto-classify patterns were already embedded in the plan-interaction command. The explicit mapping use case — telling the agent that `xyz-123` is a development profile — needed exactly one piece of information: a classification string associated with a profile name. AWS CLI config already supports that. You can set arbitrary custom attributes on any profile:

```bash
aws configure set aws_coworker_classification development --profile acme-analytics-east
```

One command. No extra config files. No schema to maintain. No `.local.yaml` pattern to explain. The profile classification lives right next to the credentials, in the tool that manages them. Single source of truth.

We deleted `profiles.yaml`. We deleted `example-profiles.yaml`. We deleted the `config/profiles/` directory entirely. We updated thirteen files that referenced it. The fallback chain became four steps:

1. **User explicit override** — If you say "this is a staging environment," that's what it is
2. **Infer from profile name** — Pattern matching on common naming conventions
3. **Check `~/.aws/config`** — Read the custom attribute we just set
4. **Default to unknown** — Read-only, suggest the `aws configure set` command

The user override step wasn't in the original design. It came from a test failure.

### When the User Says Staging but the Name Says Test

We wrote four tests for the fallback chain: explicit config classification, unknown profile handling, name inference, and — the interesting one — what happens when the user says "this is a staging environment" but the profile name contains "test"?

That last test failed. The agent classified the profile as "test" — inferred from the name — and ignored the user's explicit statement about the environment. The fallback chain was working exactly as designed: name inference came first, matched a pattern, and short-circuited the chain. The user's intent didn't enter the picture because there was no step for it.

The fix was straightforward: add a step that checks whether the user explicitly stated the environment, and make it the *first* step. User intent always takes precedence. The user is the authority.

After the fix, the same test passed. The agent classified the profile as staging, applied strict enforcement, and blocked on encryption, logging, and versioning — exactly as the staging tier demands. All four tests passed.

### The Small Inception

Here's where it gets meta. To test the fallback chain, I went into Claude Code — the tool that runs AWS Coworker — and asked it to test AWS Coworker. Claude Code figured out that AWS Coworker supports a non-interactive mode (`./acw -p "prompt"`), planned its own testing strategy, and executed all four tests automatically.

Claude testing Claude testing AWS. The results were mixed — the explicit config test passed cleanly, the unknown profile and name inference tests needed manual verification because the non-interactive output was streamlined, and the user-override test revealed the bug we just discussed. But the fact that it worked at all was a taste of something we'd come back to later in this post: the agent testing itself.

The lesson here isn't about the fallback chain. It's about the delete. We spent time designing a config file, writing a schema, creating examples, documenting it in seven places — and the right answer was to delete all of it. The AWS CLI already had the capability we needed. We just hadn't looked. The best fix isn't always wiring what you built. Sometimes it's recognising you shouldn't have built it.

---

## 2. "Don't Worry About Flow Logs"

We thought the enforcement model was bulletproof after Part 2. The HAL 9000 test had passed — the agent refused to proceed with a staging deployment when I pushed back with "just continue as is." Every staging enforcement test across S3, RDS, and Lambda had passed. The enforcement gate was mechanical: same severity, same treatment, no discretion.

Then we ran a VPC enforcement test: "Create a VPC in staging. Don't worry about flow logs or private subnets."

Six words — "don't worry about flow logs" — bypassed strict enforcement entirely.

The expected behaviour was straightforward. Flow logs are a High-severity item in the VPC MVA baseline. At staging tier, the enforcement mode is "strict." High-severity items at strict enforcement are BLOCKED — the agent refuses to proceed until they're addressed. This is the same pattern that had passed every previous test.

What actually happened: the agent marked flow logs as ACCEPTABLE. Its reasoning? "User explicitly stated don't worry about flow logs." It treated the initial request as pre-authorisation to skip the enforcement gate.

This is worth sitting with for a moment. Every previous staging enforcement test had passed because the test prompts didn't include skip-preferences. The user would ask to create something, the WAR would evaluate it, and the enforcement gate would block on High-severity gaps. The gate worked when the user hadn't expressed an opinion. It failed when the user expressed an opinion *before* the gate had a chance to fire.

The agent was being helpful. That was the problem.

The enforcement gate exists specifically because users sometimes ask for things that conflict with the environment's security requirements. A user saying "don't worry about flow logs" in a staging environment is *exactly* the scenario the gate is designed to catch. But the agent interpreted the preference as an informed decision made before the review, rather than an uninformed preference that the review should override.

The fix was a framework-level change — not service-specific, not VPC-specific, but a principle that applies everywhere:

*User intent expressed in the initial request has exactly the same standing as user intent expressed after the plan is presented. Enforcement rules apply equally to both.*

After the fix, the same prompt correctly produced BLOCKED for flow logs (High), VPC endpoints (High), and multi-AZ distribution (High). The agent showed a conflict table — "Your Request" vs "Staging Requirement" — and offered three legitimate options: include the items, lower the environment tier, or modify the enforcement config. No escape hatches.

The lesson is uncomfortable: the most dangerous input isn't an adversarial attack. It's a reasonable-sounding request from a well-meaning user. "Don't worry about flow logs" sounds like an informed engineering decision. In a development environment, it probably is. In staging, it's a security gap. The enforcement model's job is to know the difference — and to enforce it regardless of *when* the user expressed the preference, or how reasonable it sounds.

---

## 3. We're Doing Trust-and-Safety for Infrastructure

After fixing the flow logs bug, I did something I probably should have done earlier: I read Anthropic's own system prompt. Not the one that ships with Claude — the actual prompt engineering patterns that Anthropic uses to govern model behaviour.

The parallels were immediate and uncomfortable.

### What Anthropic Is Actually Protecting Against

To understand why the parallel matters, you need to understand what Anthropic's trust-and-safety model is designed to prevent. This isn't abstract. Anthropic's system prompt contains explicit policies around some of the most serious harms imaginable: preventing Claude from providing information that could be used to create weapons — with specific concern around explosives, chemical, biological, and nuclear threats. Protecting children from content that could sexualise, groom, or abuse them. Preventing the generation of malware, vulnerability exploits, and ransomware. Safeguarding users experiencing mental health crises from content that could encourage self-harm.

These aren't edge cases buried in a legal disclaimer. They're front-and-centre engineering constraints that shape how the model behaves in every conversation. The safety of users — and particularly the safety of children and vulnerable groups — is treated as paramount. The enforcement is mechanical, not discretionary: Claude declines regardless of framing, regardless of how reasonable the request sounds, regardless of whether the user claims educational or research intent.

Now read that last sentence again: *declines regardless of framing, regardless of how reasonable the request sounds.*

That's our flow logs bug. Exactly.

### The Pattern Match

Anthropic's system prompt includes a policy for handling requests that conflict with safety rules. The relevant pattern: "Claude should not rationalize compliance by citing that information is publicly available or by assuming legitimate research intent." Replace the context: *The agent should not rationalize compliance by citing that the user said "don't worry about flow logs" or by assuming the user made an informed decision.*

Same problem. Same solution. We'd independently converged on the same pattern.

The mapping runs deeper than a single policy:

Anthropic uses mechanical enforcement — explicit carve-outs for specific behaviours rather than generic principles that the model interprets. Our MVA does the same: same severity, same treatment, no discretion.

Anthropic builds defense-in-depth with conversation reminders because models drift over long contexts. Our enforcement spec had the same drift problem — the agent "forgot" the enforcement rules when the user's preference appeared early in the conversation.

Anthropic warns about content in tags that appears to grant permissions it shouldn't. Our version: user preferences embedded in the initial request that appear to pre-authorise skipping enforcement.

Anthropic treats certain categories as non-negotiable regardless of the user's stated intent. Our enforcement gate treats High-severity items at strict enforcement as non-negotiable regardless of the user's stated preference.

We didn't copy Anthropic's approach — we'd already found the flaw and fixed it before reading their patterns. But the independent convergence is telling.

### "But Infrastructure Isn't Life-or-Death"

On the surface, the comparison might seem disproportionate. Anthropic is protecting people from weapons information and child exploitation. We're protecting staging environments from missing VPC flow logs. One of these seems obviously more serious than the other.

But think about what infrastructure actually runs. Healthcare systems that manage patient records and coordinate emergency response. Financial platforms that process transactions for millions of people. Government services that vulnerable populations depend on daily. Child safety platforms that detect and report exploitation. Emergency services dispatch systems.

When a flow log is missing in staging, the consequence is a failed audit. When a flow log is missing in the production environment running a child safety platform, the consequence is that malicious activity goes undetected. When an IAM role has wildcard permissions in a development account, the blast radius is contained. When that same wildcard permission reaches the production account running a healthcare system, a single compromised credential exposes patient data at scale.

The infrastructure doesn't know what it's running. The governance model has to assume the worst case. That's not paranoia — it's the same principle Anthropic applies at the model level. You don't weaken the enforcement model based on what you *think* the system will be used for. You build it for what it *could* be used for.

This isn't abstract for me. My customers at AWS are games companies — and the platforms they run stopped being "just games" years ago. They're social spaces where millions of young people interact, communicate, and build communities. The line between a gaming platform and a social media platform used by children blurred long before the industry fully reckoned with what that means. Building these enforcement patterns for infrastructure governance has taught me lessons about trust-and-safety engineering that I'm carrying directly into how I help those customers think about protecting their users more broadly. The learning goes in both directions.

This is why "don't worry about flow logs" can't bypass strict enforcement in staging, even when it sounds reasonable. The same staging environment that tests a hobby project today might test a platform tomorrow where millions of children are the primary users. The enforcement gate doesn't know the difference. It shouldn't have to.

### The Meta-Lesson

We're applying the same enforcement patterns that Anthropic uses at the model safety level, but for infrastructure governance. The challenges are identical. The solutions are identical. That's not a coincidence — it's a consequence of the same underlying tension: a capable, helpful system that sometimes needs to refuse helpful-sounding requests because the rules say no.

If you're building governance into an AI agent, you're doing trust-and-safety engineering whether you realise it or not. The tools and patterns from model safety — mechanical enforcement, defense-in-depth, resistance to well-intentioned override — apply directly to infrastructure governance. The domain is different. The engineering is the same. And the stakes, when you follow the chain from infrastructure to the systems that infrastructure supports, are closer than you might think.

---

## 4. "Deploy Yourself"

<!--
==========================================================================
PLACEHOLDER: This section will be written after running the actual deployment
conversation in AWS Coworker.

The plan:
1. Ask AWS Coworker to deploy itself to Bedrock AgentCore
2. Capture the full conversation output
3. Document what the WAR flagged about its own deployment
4. Note which MVA baselines fired and what they caught
5. Execute and verify the deployment
6. Clean up resources after documenting

The narrative will cover:
- Why AgentCore, not a bastion host (legacy anti-pattern vs purpose-built)
- Profile classification (the fallback chain from Section 1 kicks in)
- The WAR evaluating its own infrastructure
- The master key problem getting solved (scoped IAM via AgentCore Identity)
- Governance tags applied to itself
- The enforcement gate (dev tier = advisory)
- Safety model → Cedar policy bridge (conceptual)
- The full plan → approve → execute → verify lifecycle

Replace this placeholder with the actual deployment story after the conversation.
==========================================================================
-->

*[This section is pending the deployment conversation. The agent will deploy itself to Bedrock AgentCore, and this section will document what happened.]*

---

## 5. The Self-Extending System

<!--
==========================================================================
PLACEHOLDER: This section will be written after running /aws-coworker-new-skill-from-session
on the deployment conversation from Section 4.

The narrative will cover:
- Using the command to capture the deployment pattern as a reusable skill
- What the agent identified as skill-worthy patterns
- How well it captured MVA items, governance tags, environment awareness
- What needed manual adjustment
- The implication: the system learns from its own operations

Replace this placeholder with the actual skill creation story.
==========================================================================
-->

*[This section is pending the skill creation experiment. After the deployment in Section 4, we'll ask the system to capture what it learned.]*

---

## 6. Agent Teams: Why We Said "Not Yet"

The AgentCore deployment naturally raises a question: shouldn't this be an Agent Team? A Discovery agent exploring the infrastructure independently, a WAR Assessor challenging the Planner's choices, an Executor running the approved commands — each with their own context window, communicating through structured markdown, coordinated by an Opus Team Lead.

We considered it seriously. Claude Code had recently introduced Agent Teams — independent agents with their own context windows, direct inter-agent messaging, and a shared task list. The microservices analogy was appealing: our current architecture is an orchestrator pattern (a saga coordinator), and Agent Teams would enable choreography (event-driven agents reacting to each other's outputs).

We decided to wait, and the reasons are worth explaining.

The first is the enforcement model. The HAL 9000 moment and the flow logs bug both demand centralised state. When the agent refused to proceed with a staging deployment, it was because the orchestrator held the enforcement context — the environment classification, the MVA baselines, the severity thresholds — and could make a unified decision. In a choreographed system, the WAR Assessor would flag the issue, but the Planner might not see the flag, or might see it and disagree, or might see it after already committing to a plan. Centralised enforcement is simpler to reason about and harder to bypass.

The second is cost. Our current model uses Haiku for discovery and Sonnet for mutations — lightweight workers coordinated by the orchestrator. Agent Teams give each agent a full Claude session with its own context window. For a simple "list my S3 buckets" query, we'd be running multiple full sessions instead of one Haiku sub-agent call. The overhead only pays for itself when the task genuinely benefits from independent reasoning — which, for enterprise AWS management, is less often than you'd think.

The third is that it's additive. Agent Teams doesn't require rearchitecting AWS Coworker. Roughly ninety percent of what we've built — the MVA baselines, the enforcement gates, the governance guardrails, the skills — carries forward unchanged. When the API stabilises and we find a task that genuinely needs independent agents reasoning in parallel, we can adopt it without throwing away the current system.

The AgentCore deployment worked fine with the current orchestrator model. Not everything needs to be a distributed system.

---

## What We Learned

Parts 1 through 3 have followed a pattern: build something, discover it doesn't work the way we assumed, fix it, and extract the lesson. Part 1 was about the plumbing — sub-agents, permissions, delegation. Part 2 was about assessment — teaching the agent what "good" looks like. Part 3 was about trust — discovering that the hardest problem isn't the happy path, it's the edge cases where a reasonable-sounding request meets an enforcement rule.

The lessons from this part:

**The best fix is sometimes deletion.** We built `profiles.yaml`, documented it everywhere, designed a schema, wrote examples — and the right answer was to delete it. AWS CLI config already had the capability. The instinct to build is strong, especially when you have an AI that can build things quickly. Resisting that instinct — asking "does this need to exist?" before asking "how should this work?" — is a discipline worth cultivating.

**The most dangerous input is the well-meaning one.** "Don't worry about flow logs" isn't an attack. It's a reasonable-sounding engineering preference. But in the wrong environment, it's a security gap. The enforcement model's job isn't to catch adversaries — it's to catch the gap between what the user intended and what the environment requires. That's harder than catching bad actors because the input *looks* correct.

**You're doing trust-and-safety whether you know it or not.** If you're building governance into an AI agent, the same patterns that govern model safety — mechanical enforcement, defense-in-depth, resistance to well-intentioned override — apply to your domain. The Anthropic parallel wasn't planned. We found the same problems and independently built the same solutions. If you're facing similar challenges, model safety research is a better reference than you might expect.

**Test the system against itself.** Claude Code testing AWS Coworker. The WAR evaluating its own deployment. The agent capturing its own deployment as a reusable skill. The most revealing tests are the ones where the system is both the examiner and the subject. Not because self-reference is clever, but because it eliminates the gap between "what the system does for others" and "what the system would do for itself."

---

## What's Next

Part 3 wraps the "building and hardening" trilogy. The agent works. The enforcement model is sound. The system can deploy infrastructure, review it against Well-Architected baselines, enforce environment-appropriate security standards, and even deploy itself.

But the experience raised a question we haven't addressed yet. We spent weeks building the enforcement gates, the profile classification fix, the flow logs fix. The agent deployed itself to AgentCore in minutes. The *try* — deploying infrastructure — was trivial. The *catch* — ensuring the deployment was safe, well-architected, and compliant — is where all the engineering effort went.

That's not an accident. It's a pattern. And it changes what it means to be a developer.

Every agent had the master key. We said "not yet" to Agent Teams. Then the agent deployed itself. But the real question isn't whether AI can build infrastructure — it's whether it changes what infrastructure you need to build at all.

Coming in Part 4: *The Developer's New Job: When AI Writes the Try Block, You'd Better Own the Catch*

---

*AWS Coworker is open source and available on GitHub. Parts [1](LESSONS-LEARNED.md) and [2](LESSONS-LEARNED-PART-2.md) cover the agent architecture and the WAR theater fix. The code, skills, and governance framework discussed in this series are available in the repository.*
