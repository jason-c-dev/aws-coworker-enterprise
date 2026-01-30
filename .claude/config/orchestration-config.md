# Orchestration Configuration

**This file defines thresholds and settings for AWS Coworker's multi-agent orchestration.**

All agents MUST reference this configuration when making decisions about task delegation and parallelization.

---

## Execution Mode

```yaml
mode: always-agent  # Options: always-agent | threshold-based

# always-agent (CURRENT):
#   - Every request spawns at least one agent via Task tool
#   - Thresholds determine parallelization strategy (single vs multiple agents)
#   - Provides consistent execution paths and audit trails
#   - Optimized for enterprise workloads where complex tasks are the norm
#
# threshold-based (LEGACY):
#   - Simple tasks execute directly without spawning agents
#   - Only complex tasks spawn sub-agents
#   - Lower overhead for trivial operations
```

---

## Why Always-Agent Mode?

AWS Coworker is designed for **enterprise environments** where:

1. **Complex tasks are the norm** — Multi-region, multi-account operations are common
2. **Consistency matters** — Same execution path regardless of task size
3. **Audit trails are critical** — Every operation tracked through agent invocation
4. **Efficiency at scale** — Parallelization benefits compound with complexity

Simple tasks like "list my S3 buckets" work perfectly fine in always-agent mode — they simply use a single agent rather than spawning parallel workers. The overhead is minimal, while the consistency and auditability benefits are significant.

---

## Parallelization Thresholds

These thresholds determine **how many agents** to spawn, not **whether** to spawn agents.

```yaml
thresholds:
  # Resource count thresholds
  resources:
    single_agent: 50       # < 50 resources: 1 agent handles sequentially
    parallel_start: 50     # >= 50 resources: consider parallelization
    parallel_required: 200 # >= 200 resources: mandatory parallelization

  # Region thresholds
  regions:
    single_agent: 3        # <= 3 regions: 1 agent can handle
    parallel_start: 4      # > 3 regions: consider parallel agents per region
    parallel_required: 8   # >= 8 regions: mandatory parallel agents

  # Account thresholds (for multi-account operations)
  accounts:
    single_agent: 3        # <= 3 accounts: 1 agent can handle
    parallel_start: 4      # > 3 accounts: consider parallel agents per account
    parallel_required: 10  # >= 10 accounts: mandatory parallel agents

  # Time estimation thresholds
  estimated_time:
    advise_user: 300       # > 5 minutes: advise user of expected duration
    require_approval: 600  # > 10 minutes: require explicit user approval
```

---

## Model Hierarchy

AWS Coworker uses a tiered model strategy for cost efficiency and performance:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PRIMARY AGENT (Orchestrator)                            │
│                                                                             │
│  Model: User's selected model (e.g., Opus 4.5, Sonnet, etc.)                │
│                                                                             │
│  Responsibilities:                                                          │
│  • Intercept and route requests                                             │
│  • Read orchestration config                                                │
│  • Perform discovery and scope assessment                                   │
│  • Evaluate thresholds                                                      │
│  • Communicate with user (advisement, approval)                             │
│  • Spawn and coordinate sub-agents                                          │
│  • Aggregate results into final response                                    │
│  • Handle complex decision-making                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│  SUB-AGENT (Read-Only)      │   │  SUB-AGENT (Mutations)      │
│                             │   │                             │
│  Model: haiku               │   │  Model: sonnet              │
│                             │   │                             │
│  Tasks:                     │   │  Tasks:                     │
│  • Discovery operations     │   │  • State-changing ops       │
│  • Audit scans              │   │  • Resource modifications   │
│  • Cost analysis            │   │  • Tag updates              │
│  • Compliance checks        │   │  • Configuration changes    │
└─────────────────────────────┘   └─────────────────────────────┘
```

**Why this hierarchy?**

| Aspect | Primary Agent | Sub-Agents |
|--------|---------------|------------|
| **Model** | User's choice (Opus, Sonnet, etc.) | Configured (haiku/sonnet) |
| **Cost** | Premium (user accepts this) | Optimized per task type |
| **Role** | Orchestration, synthesis, communication | Parallelized execution |
| **Complexity** | High (decision-making, aggregation) | Lower (focused tasks) |

This means if you run AWS Coworker with Opus 4.5, Opus handles the "thinking" while Haiku does the "doing" — getting you the best of both worlds.

---

## Sub-Agent Model Selection

```yaml
agents:
  # Model selection for sub-agents (NOT the primary orchestrator)
  models:
    read_only: haiku       # Fast, efficient for discovery/audit tasks
    mutations: sonnet      # More capable for state-changing operations
    planning: sonnet       # Thorough analysis for complex planning
    default: haiku         # Default for unspecified tasks

  # Parallelization limits
  limits:
    max_parallel_agents: 10      # Maximum concurrent sub-agents
    batch_size: 50               # Resources per batch when batching
    timeout_seconds: 600         # Maximum execution time per agent
```

---

## Partitioning Strategies

When parallelizing, choose the appropriate partition strategy:

```yaml
partitioning:
  # By geography
  by_region:
    description: "Spawn one agent per AWS region"
    use_when: "Multi-region operations"
    example: "Audit S3 buckets across all regions"

  # By account
  by_account:
    description: "Spawn one agent per AWS account"
    use_when: "Multi-account operations in Organizations"
    example: "Compliance check across all member accounts"

  # By resource type
  by_service:
    description: "Spawn one agent per AWS service"
    use_when: "Broad inventory or audit operations"
    example: "Full account security audit"

  # By batch
  by_batch:
    description: "Split resources into fixed-size batches"
    use_when: "Large number of homogeneous resources"
    example: "Tag 500 EC2 instances"

  # Hybrid
  hybrid:
    description: "Combine multiple strategies"
    use_when: "Complex operations spanning regions and accounts"
    example: "Organization-wide compliance audit"
```

---

## Task Flow: Always-Agent Mode

```
User Request
     │
     ▼
CLAUDE.md Interception
     │
     ▼
Slash Command
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CORE AGENT (via Task tool)                            │
│                                                                             │
│  1. Receive request context                                                 │
│  2. Perform initial discovery                                               │
│  3. Assess scope against thresholds (from this config)                      │
│  4. Determine parallelization strategy                                      │
│  5. If complex: advise user, get approval                                   │
│  6. Delegate to sub-agents OR execute as single agent                       │
│  7. Aggregate results                                                       │
│  8. Return unified response                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ├── Simple task (below thresholds)
     │   └── Single sub-agent executes sequentially
     │
     └── Complex task (above thresholds)
         └── Multiple sub-agents execute in parallel
              ├── Sub-Agent A (region-1 or batch-1)
              ├── Sub-Agent B (region-2 or batch-2)
              └── Sub-Agent N (region-N or batch-N)
```

---

## Configuration Reference for Agents

When making orchestration decisions, agents should:

1. **Read this file** at the start of any operation
2. **Assess scope** against the thresholds defined above
3. **Select model** based on operation type (read-only vs mutation)
4. **Choose partitioning strategy** appropriate to the task
5. **Respect limits** on parallel agents and timeouts
6. **Advise user** when estimated time exceeds thresholds

### Example Decision Flow

```python
# Pseudocode for agent decision-making

scope = assess_scope(discovery_results)

if scope.resources < thresholds.resources.single_agent \
   and scope.regions <= thresholds.regions.single_agent \
   and scope.accounts <= thresholds.accounts.single_agent:
    # Single agent, sequential execution
    strategy = "single_agent"
    num_agents = 1
else:
    # Determine parallelization
    if scope.accounts > 1:
        strategy = "by_account"
        num_agents = min(scope.accounts, limits.max_parallel_agents)
    elif scope.regions > thresholds.regions.single_agent:
        strategy = "by_region"
        num_agents = min(scope.regions, limits.max_parallel_agents)
    else:
        strategy = "by_batch"
        num_agents = min(
            ceil(scope.resources / limits.batch_size),
            limits.max_parallel_agents
        )

# Check if user advisement needed
if scope.estimated_time > thresholds.estimated_time.advise_user:
    advise_user(scope, strategy, num_agents)
    await_approval()
```

---

## Updating Thresholds

To modify these thresholds:

1. Edit the values in this file
2. All agents will use the new values on next invocation
3. No code changes required — agents read this configuration dynamically

**Recommended approach for tuning:**

- Start with defaults (above)
- Monitor execution times and user experience
- Adjust thresholds based on your specific AWS estate size
- Lower `single_agent` thresholds for faster parallelization
- Raise `parallel_required` thresholds to reduce agent overhead

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-30 | Initial configuration with always-agent mode |
