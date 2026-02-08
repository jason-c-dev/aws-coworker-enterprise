# Conversation: CloudFront Extension & Design Integrity

**Date:** 2026-02-08
**Participants:** Jason Croucher, Claude (Cowork)
**Topic:** Adding CloudFront to AWS Coworker and the design integrity lesson that emerged

---

## Context

During development of the AWS Coworker lessons-learned blog, Jason noticed that CloudFront was missing from the skills/CLI playbooks. What started as a simple feature request became a critical lesson about maintaining design integrity when extending AI-assisted systems.

---

## The Discussion

### User Initial Observation

**User:**
> I notice there's no reference to CloudFront in the skills, CLI etc. The real way to publish a static HTML page is, of course on an S3 bucket but buckets shouldn't be public, they should be fronted by CloudFront. Provide a plan to add this functionality and test it out with AWS Coworker. Not sure we need to register a domain name, maybe there's a default? What are your thoughts on this?

### Claude's Initial (Wrong) Response

**Claude:**
> Great observation! You're right - S3 buckets should never be public. The proper pattern is:
>
> **S3 (private) → CloudFront (CDN) → Users**
>
> **No Domain Registration Needed**
> CloudFront provides a default domain: `d1234567890.cloudfront.net` — perfect for testing without custom domains or Route 53 setup.
>
> **Plan: Add CloudFront Static Hosting to AWS Coworker**
>
> Phase 1: Add Skills & Governance
> - `.claude/skills/aws-services/cloudfront-config.md`
> - `.claude/skills/patterns/static-site-hosting.md`
> - Update `guardrails-governance.md`

**Claude's Thinking (at this point):**
```
The user is asking about adding CloudFront functionality to AWS Coworker. This is a great
observation - the proper way to serve static content from S3 is indeed through CloudFront,
not by making the S3 bucket public.

Let me think about this:
1. Current state: AWS Coworker can deploy to EC2 (like the Space Invaders game), but
   there's no CloudFront + S3 static hosting pattern
2. The right architecture for static sites:
   - S3 bucket (private, not public)
   - CloudFront distribution in front of it
   - Origin Access Control (OAC) to allow CloudFront to access the private bucket
   - Default CloudFront domain (*.cloudfront.net) - no custom domain needed

What needs to be added to AWS Coworker:
- New skill for CloudFront + S3 static hosting pattern
- Updates to governance/guardrails for CloudFront
- Test case for deploying static content via CloudFront
```

*Note: At this point, Claude invented `.claude/skills/aws-services/` which doesn't exist in the design.*

---

### User's First Pushback (Consistency Question)

**User:**
> Question. Why is CloudFront added as an aws-service under skills but RDS, EKS, EC2 etc. are commands under CLI playbook. We need to be consistent here. Does that change your thoughts?

**Claude's Thinking:**
```
The user is making an excellent point about consistency. Let me look at the current structure:
- `.claude/skills/aws-services/` - where I proposed putting cloudfront-config.md
- `.claude/skills/cli-playbooks/` - where RDS, EKS, EC2 etc. are as commands

The user is right - I was being inconsistent. If RDS, EKS, EC2 patterns are in cli-playbooks,
then CloudFront should follow the same pattern.
```

**Claude's Response:**
> Good idea to commit them for consistency... [checked the actual structure]
>
> Looking at the actual structure:
> ```
> .claude/
> ├── agents/
> ├── commands/
> └── config/
> ```
>
> There's **no `skills/` or `cli-playbooks/` folder** currently. Service-specific knowledge isn't separated out yet.
>
> **Revised Plan: Consistent Structure First**
>
> **Option A: Create `config/service-patterns/`**
> **Option B: Create `.claude/skills/`** (separate from config)
>
> My recommendation: Option A (`config/service-patterns/`)

*Note: Claude still hadn't read the DESIGN.md to understand the intended structure.*

---

### User's Second Pushback (Read the Design)

**User:**
> Wait, you specifically added skills at the root as you earlier suggested that they're human readable and editable for extensibility. Read the design.md - does that change your thoughts?

**Claude's Thinking:**
```
The user is pointing me to a design.md file that I should read to understand the intended
structure. Let me find and read it.
```

**Claude then read DESIGN.md and found:**
```
skills/
├── aws/                             # AWS-focused skills
│   ├── aws-cli-playbook/
│   │   ├── SKILL.md
│   │   └── commands/                # Service-specific command references
│   │       ├── ec2.md
│   │       ├── s3.md
│   │       ├── rds.md
│   │       ├── eks.md
│   │       └── cloudfront.md   # <-- CloudFront goes here!
```

**Claude's Response:**
> Now I understand! The DESIGN.md clearly specifies:
>
> The `skills/` folder is at the **root level** (not under `.claude/`) because skills are "knowledge documents" meant to be visible, browsable, and human-maintainable.
>
> **Revised Plan (No New Concepts)**
>
> 1. Add `cloudfront.md` to `skills/aws/aws-cli-playbook/commands/`
> 2. Within that file, document the S3 + CloudFront pattern for static sites
>
> **No `patterns/` directory needed.**

---

### User's Third Pushback (Think It Through)

**User:**
> That's better and makes more sense - but I'm curious about the "skills/aws/patterns/" directory. This is a new concept. Remember we're looking at a multi-layered model here for core, org, BU. Are patterns in the core right? (Maybe I'm just encouraging you to think through thoroughly). If patterns are a new concept, how does it impact our design across all layers and are there things already encoded in the skills, agents, commands, that should now be patterns. Ultra think this through as you're proposing a change that breaks from our original design. I'm potentially ok with that but I need to be sure you're not doing what it says in the blog - taking the path of least resistance, and over engineering your way out of a corner.
>
> Also, as your conversation with me is compacted, we need to make sure that you don't try to do this in future. Hence my insistence on the design doc and course correcting holistically and not just trying to shoe horn static websites as a concept.
>
> Make sense?

**Claude's Thinking:**
```
The user is making an excellent point. They're pushing back on my suggestion of adding a
`skills/aws/patterns/` directory because:
1. It's a new concept not in the original DESIGN.md
2. They want me to think through the implications across all layers (core, org, BU)
3. They're concerned I'm "taking the path of least resistance" and over-engineering
4. They want holistic design decisions, not shoe-horning solutions

Let me think through this more carefully:

**What the DESIGN.md actually says:**
Looking at the directory structure in DESIGN.md (lines 632-692), the skills are organized as:
[structure shown]

There's NO `patterns/` directory in the original design. I invented that.

**What are "patterns" really?**
Looking at the existing structure:
- `aws-cli-playbook/commands/` = service-specific CLI commands
- `aws-well-architected/` = pillar-based guidance
- `aws-governance-guardrails/` = policies

Where would "static site hosting with S3 + CloudFront" fit?

Actually, looking at the existing files like `ec2.md`, `s3.md`, etc., they likely already
contain patterns within them - not just raw CLI commands.

**My original mistake:**
I was trying to create a new `patterns/` directory when:
1. CloudFront CLI commands should just go in `aws-cli-playbook/commands/cloudfront.md`
2. The "static site hosting pattern" is really just documentation within CloudFront (and S3)
   about how to use these services together
3. If there's org-specific guidance for static site hosting, it would go in org-layer skills

**The right approach:**
1. Add `skills/aws/aws-cli-playbook/commands/cloudfront.md` - consistent with existing structure
2. Within that file, document the S3 + CloudFront pattern for static sites
3. Reference the existing `s3.md` for S3-specific commands
4. NO new `patterns/` directory needed

**Why I was over-engineering:**
I was treating "static site hosting" as a first-class concept when really it's just a use
case documented within service-specific skills.
```

**Claude's Response:**
> You're absolutely right. Let me think this through properly.
>
> ## My Mistake: I Invented a New Concept
>
> The `skills/aws/patterns/` directory **doesn't exist in DESIGN.md**. I was shoe-horning a solution.
>
> **Patterns already exist** — they're just organized by purpose/domain, not in a separate `patterns/` folder.

---

### User's Fourth Pushback (Verify, Don't Assume)

**User:**
> Looking at your thinking, you're right to see I'm pushing back. But I'm not disagreeing necessarily. That said, I think what you're saying makes sense now but you said something that worried me. "Just like `ec2.md` probably documents 'launch instance + security group + key pair' as a workflow, `cloudfront.md` would document 'create distribution + S3 origin + OAC' as a workflow." The word PROBABLY implies doubt vs certainty. Check it and make sure your suggestion of codifying static websites concept into CloudFront is, in fact, the right way.

**Claude's Thinking:**
```
The user is right to push back on my use of "probably". I should actually read the existing
files to understand their structure before making recommendations. Let me read ec2.md and
s3.md to see how they're structured, and then I can make an informed decision about where
static site hosting should go.
```

**Claude then read `ec2.md` and `s3.md` and found:**

Each service file follows a consistent template:
1. **Overview** — Brief description
2. **Discovery Commands (Read-Only)** — Query commands
3. **Common Operations** — Create/configure commands
4. **Mutation Commands (Require Approval)** — Destructive operations with ⚠️
5. **Best Practices** — Guidelines
6. **Related Skills** — Cross-references

**Critical Finding from `s3.md` line 282:**
```markdown
## Related Skills

- CloudFront - Cache S3 objects at edge locations
```

**Claude's Response:**
> Now I can see the actual structure...
>
> **Critical Finding:** S3 already references CloudFront as a related skill!
>
> The existing structure handles cross-service patterns through:
> 1. **Related Skills** — explicit cross-references between service files
> 2. **Best Practices** — mention common patterns
>
> There are **no workflow documents** in these files. They're **CLI references** organized by operation type.
>
> **Correct Approach:**
> - Add `cloudfront.md` following the same template
> - Static site pattern mentioned in **Best Practices** section
> - Related Skills points to `s3.md`; `s3.md` already points to CloudFront
>
> This keeps the design consistent. No new concepts needed.

---

### User's Meta-Observation

**User:**
> Yes, that is the right solution. However, before you do anything, look at our conversation from when I said "I notice there's no reference to CloudFront in the skills, CLI etc......"
>
> This is an important lesson, you veered off to help solve my "problem"
>
> This, in itself, is a perfect example of implicit vs explicit commands and the other tenets I have for AWS Coworker. I not only need to ensure Claude Code follows guidelines and best practices, I need to also make sure Claude Cowork (YOU) follow the principals of the AWS Coworker design.
>
> So, I have 3 goals now:
>
> 1. Implement and test CloudFront CLI skill as you suggest for AWS Coworker (Claude Code) works as expected.
> 2. Make sure that you (Claude Coworker) stay on track with the fundamental design principals of AWS Coworker as this will be a key aspect of its extensibility without breaking it. Not just for me developing the core but others extending the org and BU above the core.
> 3. A new blog post detailing everything we (you and I) just discussed from "I notice there's no reference to CloudFront in the skills, CLI etc......" and how, had I not noticed would have allowed you to break the design.
>
> Does this make sense? Let's plan it, if so, let's continue talking if not.

---

## Where Claude Went Wrong

| Tenet Violated | What Claude Did | What Claude Should Have Done |
|----------------|-----------------|------------------------------|
| **Explicit Over Implicit** | Assumed patterns needed a new directory | Asked: "Where does the design say this goes?" |
| **Respect the Architecture** | Invented `skills/aws/patterns/` | Read DESIGN.md first, then proposed |
| **Path of Least Resistance** | Shoe-horned a solution | Validated against existing structure |
| **Verify, Don't Assume** | Said "probably documents..." | Actually read the files first |

---

## Key Lessons

1. **Read the design document FIRST** before proposing structural changes
2. **Actually verify assumptions** by reading existing files, not guessing
3. **New directories = design changes** — these require careful thought about layer implications
4. **Cross-service patterns belong in Related Skills** and Best Practices, not separate folders
5. **The builder needs the same guardrails as the built** — Claude Cowork extending AWS Coworker should follow AWS Coworker's own design principles

---

## The Meta-Lesson

If Claude (Cowork) can accidentally break the design while helping build it, then **anyone** extending at org/BU layer can make the same mistake. The guardrails need to protect against this — not just for Claude Code executing AWS commands, but for Claude Cowork extending the system itself.

**The principles are recursive:** they apply to the tool AND to the builder of the tool.

---

## Resulting Goals

### Goal 1: Implement CloudFront CLI Skill
- Create `skills/aws/aws-cli-playbook/commands/cloudfront.md`
- Follow exact template: Overview → Discovery → Common Ops → Mutations → Best Practices → Related Skills
- Test with AWS Coworker: deploy space-invaders style game via S3 + CloudFront

### Goal 2: Meta-Governance for Extensibility
- Document "extending AWS Coworker" guardrails
- Ensure anyone extending the system (including Claude Cowork) follows the design
- Protect against the failure mode demonstrated in this conversation

### Goal 3: Blog Post — "The Design Almost Broke"
- Document this conversation as a case study
- Show how AI assistants need the same guardrails as the systems they build
- Add as a new lesson or appendix to the existing blog

---

## References

- `docs/DESIGN.md` — The authoritative design document
- `skills/aws/aws-cli-playbook/commands/ec2.md` — Template for service CLI files
- `skills/aws/aws-cli-playbook/commands/s3.md` — Shows Related Skills cross-reference pattern
