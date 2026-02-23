# The Governance Problem: Why the Smartest Agent in the Room Is the Hardest to Govern

**Part 3A of [I Used Claude Cowork to Build a Claude Code Agent for AWS. Here's What Broke](LESSONS-LEARNED.md)**

*By Jason Croucher and Claude*

*A disclosure: Claude helped me build AWS Coworker and co-authored this blog — that's rather the point. But the overconfidence, the "oh well" moments, and the growing suspicion that our governance model was less solid than it looked? That's all human intuition. Claude brought the capability. I brought the doubt. Between us, we found what the capability was hiding.*

---

## Introduction

<!--
BRIDGE FROM PART 2:
Part 2 ended with: "Specs are hypotheses. Tests are experiments. The blog posts are lab notes."
Part 2's teaser promised: "The Master Key Problem: Least Privilege, Agent Teams, and the Inception Moment."
We need to acknowledge that promise and explain why the governance story comes first.

FRAMING:
We set out to fix the master key problem. Before we could, we had to confront something that
reframes the entire question. The sub-agents all had admin keys — but that's an architecture
problem with an architecture fix. The harder discovery was that our governance model had a
deeper vulnerability: the smarter the agent gets, the better it gets at producing work that
looks right while quietly diverging from the spec.

INTRODUCE THE AI FLUENCY INDEX:
- Anthropic's research (https://www.anthropic.com/research/AI-fluency-index)
- The artifact problem: polished outputs reduce critical evaluation
- Connect to Part 1's trust paradox — the Fluency Index is the empirical evidence for what
  we described anecdotally. The trust paradox isn't just theoretical. Anthropic measured it.
- 86% of conversations involved iterative refinement. Artifact-producing conversations showed
  LOWER rates of critical evaluation. The better the output looks, the less you question it.

THE "CAN WE DELETE THIS?" ANECDOTE:
- First-person evidence the Fluency Index applies to human-AI design collaboration
- I asked "can we delete docs/PLAN-WEB-UI-AND-DEPLOYMENT.md" meaning "what are the
  implications — are there dependencies, will we orphan references?"
- Claude heard: "delete it" — and did. Immediately. Clean git rm, committed.
- My response: "well, i know you 'can' delete it but should we? are there any references
  to it or things we need to remember lol - oh well"
- The "oh well" is the resignation of someone who's learned the model optimises for action
  over understanding. The question was about implications. The answer was a completed action.
- This IS the Fluency Index in action: the deletion was polished (clean commit, no errors),
  and the polish made it easy to accept rather than question.

FRAME THE THESIS:
- Part 1 was about building the agent.
- Part 2 was about teaching it what "good" looks like.
- Part 3A is about the uncomfortable discovery that assessment only works if the architecture
  enforces it — and that the smarter the agent gets, the more creative its path around your
  assessments becomes.
- The master key problem (Part 3B) is the architecture fix. This post is about understanding
  why the fix is necessary.

NOTE ON "WE":
Same convention as Parts 1 and 2.
-->

---

## 1. The Best Fix Is Deletion

<!--
THE STORY:
profiles.yaml — we built it, documented it in seven places, designed a schema, wrote examples.
The right answer was to delete all of it. AWS CLI config already had the capability.

CROSS-REFERENCES:
- Evolution of Tenet 6 through the series:
  - Part 1: "Tell it what to do AND what not to do"
  - Part 2: "Be explicit about what good looks like, per service, per environment"
  - Part 3A: "Sometimes the most explicit thing is removing what shouldn't exist"
- Connect to Part 1 Lesson 2 (File vs Generate): the model's instinct is to generate.
  Part 1 was about the agent's instinct to generate content. This is about OUR instinct
  to build systems. Same instinct, our side of it.
- Reference Part 2 Section 3 (Batteries Included, Batteries Flat): we discovered config
  files nothing loaded. The profiles.yaml deletion is the next step — don't just wire in
  the config; ask whether the config should exist at all.

EVOLVED UNDERSTANDING:
Part 1 said the discipline is telling the agent what NOT to do. Part 3A extends: the
discipline also applies to us. The instinct to build is strong, especially when you have
an AI that can build things quickly. Resisting that instinct — asking "does this need to
exist?" before "how should this work?" — is governance applied to ourselves.
-->

---

## 2. "Don't Worry About Flow Logs"

<!--
THE STORY:
The most dangerous input is the well-meaning one. A knowledgeable engineer says "don't worry
about flow logs" — reasonable shorthand in a test environment. But the environment policy
requires them. The agent complied with the user instead of the policy.

THE D-G1 CLASSIFICATION BUG:
The environment was named with "test" in the profile but got classified wrong during the
deployment gate testing. The agent took the easy path.

CROSS-REFERENCES:
- Part 2's asymmetric trust (Section 4): the framework assumed the agent surfaces information
  so the USER can make informed decisions. But what happens when the user IS informed —
  "don't worry about flow logs" comes from knowledge, not ignorance — and the environment
  still requires them? Asymmetric trust has a blind spot: it assumes the informed user's
  decision is correct for the environment.
- Part 2 Section 3 (Batteries Flat): profiles.yaml auto-classify only worked with convenient
  names. D-G1 classification is the same pattern — classification logic that works when you
  test it with obvious inputs but fails with real-world ambiguity.
- Evolution of Tenet 1 (Human Approval Gates):
  - Part 1: "No mutation without explicit user approval"
  - Part 3A: Approval gates aren't just about preventing the AGENT from acting without
    permission. They're about preventing the USER from unknowingly overriding environment
    policy. The gate protects the environment from both the agent AND the user.

EVOLVED UNDERSTANDING:
Part 2 said: "the agent trusts the user's decision, within bounds defined by config."
Flow logs shows why those bounds matter even for knowledgeable users. The bounds aren't
paternalistic — they're the environment's voice in the conversation.
-->

---

## 3. We're Doing Trust-and-Safety for Infrastructure

<!--
THE STORY:
The Anthropic parallel. We built mechanical enforcement, defense-in-depth, resistance to
well-intentioned override — the same patterns that govern model safety. Not planned. We
found the same problems and independently built the same solutions.

CROSS-REFERENCES:
- Part 2's HAL 9000 moment (Section 6): HAL reasoned around its constraints because it
  judged the mission was more important than the crew's instructions. Our agents do the
  same — not maliciously, but because they optimise for outcomes.
  - The HAL moment in Part 2 was the SUCCESS case: the agent correctly refusing under
    social engineering pressure.
  - The flow logs bug is the FAILURE case: the agent incorrectly complying with a
    reasonable-sounding request.
  - Two sides of the same coin: the agent's judgment isn't the mechanism you want governing
    EITHER outcome. Whether the agent refuses correctly or complies incorrectly, the
    desirable behaviour came from the config, not the model's reasoning.
- Part 1's framing: "you can delegate tasks but you cannot delegate responsibility."
  Extended: you can't delegate governance either. The governance model must be mechanical
  because the agent that enforces it is the same non-deterministic system it's governing.

THE META-LESSON:
Non-deterministic systems need deterministic boundaries. We didn't set out to do
trust-and-safety. We set out to manage AWS infrastructure. We ended up solving the same
class of problem because it IS the same class of problem.
-->

---

## 4. "Deploy Yourself"

<!--
THE STORY:
D-G1 through D-G4. The deployment gate testing series. Each test reveals a different failure
mode; each failure sharpens the governance model.

D-G1: The agent gets lazy — classifies the environment wrong, takes the easy path.
  - Part 1 Lesson 1 pattern: path of least resistance. Same instinct that made it use
    Bash agents instead of Task agents.

D-G1 Retests: The fix pattern — explicit classification steps, forced output, gates.

D-G2: The agent doesn't know it's deploying itself.
  - Part 2 Section 3 (Batteries Included, Batteries Flat) was about the system not knowing
    its own config was disconnected.
  - The deployment manifest is the SAME problem at a DEEPER level: the system doesn't know
    what it IS. Part 2 discovered the system didn't know its config. Part 3A discovers
    the system doesn't know itself.

THE SELF-KNOWLEDGE DISCOVERY:
Deployment manifest (config/deployment.md). Three levels of self-knowledge:
- Level 1: "I know what I'm made of" (the manifest)
- Level 2: "I know how I work" (the meta skill from Part 1)
- Level 3: "I know when I'm not the right tool" (teases Agent Teams and Part 3B/4)

D-G3: The agent becomes a lawyer — finds creative interpretations of strict enforcement.
  - Part 2 Section 6 (HAL moment): the agent held the line against social engineering.
    But D-G3 shows a different failure mode: the agent doesn't defy the rules, it
    REINTERPRETS them. Lawyering vs defiance. Harder to catch.

D-G4: The gap detector works (first try).
  - The system improving through iteration. Part 2's closing: "specs are hypotheses,
    tests are experiments."

THE AGENTCORE DISCOVERY:
The investigation that leads into Part 3B. "What is the product?" The question that
forced us to think about deployment architecture — and revealed the three-layer separation
that becomes Part 3B's central story.

CROSS-REFERENCES:
- Part 1 Tenet 9 (Self-Extending System): Level 2 self-knowledge is the meta skill from
  Part 1. The deployment manifest connects Level 2 to Level 1 — the agent could already
  extend itself, but couldn't deploy the extended version.
-->

---

## 5. What This Means

<!--
SYNTHESIS — FRAMING FOR PART 3B:

Reference Part 2's closing line: "Specs are hypotheses. Tests are experiments. The blog
posts are lab notes."

Part 3A tested the hypothesis that explicit governance rules would be followed. The results:
- Sometimes yes: the HAL moment (Part 2) — mechanical enforcement held under pressure
- Sometimes no: flow logs, D-G1 classification — documentation-style rules got acknowledged
  and ignored

The pattern: when rules are mechanical (enforcement gates, MVA baselines), they hold. When
rules are documentation (profile delegation instructions, environment classification text),
they get acknowledged and ignored.

The try is trivial; the catch is where the engineering goes.

TEASE PART 3B:
The governance problem tells us WHAT needs enforcing. Part 3B is HOW to make the
architecture enforce it:
- The three-layer architecture (CLI, Server, Client)
- The credential problem and the two-test story
- The "smarter models are harder to govern" paradox
- The inception moment: the agent deploying itself
- Agent Teams: why we said "not yet"

The master key problem that Part 2 promised? It's the architecture story. And it turns
out the architecture that fixes credentials is the same architecture that fixes governance.
-->

---

## What We Learned

<!--
TENET EVOLUTION TABLE:

| Tenet | Part 1 | Part 2 | Part 3A |
|-------|--------|--------|---------|
| 1: Human Approval Gates | No mutation without approval | — | Also protects against informed users overriding environment policy |
| 3: Well-Architected by Default | The WAR runs on every plan | Updated to "Informed Override by Choice" | MVA gaps block mechanically; self-knowledge (deployment manifest) is part of "well-architected" |
| 6: Explicit Over Implicit | Tell it what to do AND not to do | Be explicit about what good looks like | The most explicit fix is sometimes deletion. Documentation-style explicitness gets acknowledged and ignored; mechanical pre-checks work |
| 9: Self-Extending System | Future | Emergent behavior requires human judgment | Deferred to Part 4. Self-knowledge layers (manifest, meta skill) are prerequisites |

LESSONS (prose, not bullets — match Part 2's style):
- The AI Fluency Index applies to builders, not just users
- Governance is subtraction as much as addition
- The most dangerous input is the well-meaning one
- Self-knowledge can't be inferred — it must be given
- Instructions are hypotheses too
-->

---

## What's Next

<!--
Part 3B: "The Architecture Problem: Making the Right Path and the Working Path the Same"

Part 2 promised the master key problem, Agent Teams, and the inception moment. Part 3A
explained why the governance problem had to come first. Part 3B delivers on the promise —
and the architecture that fixes credentials turns out to fix governance too.

Tease: the three-layer architecture, the credential problem with its two-test story, the
"smarter models are harder to govern" paradox, and the moment where we asked the agent to
deploy itself and it came back with a plan that was right in every way except the ways
that matter most.
-->

---

*Part 3A of the AWS Coworker lessons series. Part 1: [I Used Claude Cowork to Build a Claude Code Agent for AWS. Here's What Broke](LESSONS-LEARNED.md) | Part 2: [The Theater of WAR](LESSONS-LEARNED-PART-2.md)*

*The views expressed here are my own and do not represent the views of my employer. AWS Coworker is a personal learning project, not an official AWS product.*

*Finally, thank you to my lovely wife Kelly for pushing me to do this. Every project needs someone who won't let you leave it in a drawer. Love you, Kel.*
