# {Service Name} — MVA Baseline

## Overview

Brief description of the service and what MVA means for it.

**MNA (Minimum Needed Architecture):** What's technically required for {service} to function.
**MVA (Minimum Viable Architecture):** What the Well-Architected Framework says you should have.

---

## Common (All Environments)

Items required regardless of environment tier. These are the absolute minimum for any deployment.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | {item} | {Critical/High/Medium/Low} | {reason} |
| ... | ... | ... | ... |

---

## Sandbox

Additional items beyond Common for sandbox environments. Typically empty — sandbox is intentionally loose.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| — | No additional items | — | Sandbox prioritizes experimentation |

---

## Development

Additional items beyond Common for development environments.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| {Pillar} | {item} | {severity} | {reason} |

---

## Staging

Additional items beyond Development for staging environments. These items are enforcement-gated: critical/high gaps BLOCK execution when enforcement is `strict`.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| {Pillar} | {item} | {severity} | {reason} |

---

## Production

Additional items beyond Staging for production environments. ALL items are mandatory when enforcement is `enforce` — no override path.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| {Pillar} | {item} | {severity} | {reason} |

---

## Full MVA Summary (Production = Superset)

This table shows ALL MVA items for production, which is the complete superset. Lower tiers inherit from Common upward.

| Pillar | MVA Item | Sandbox | Dev | Staging | Prod | Severity |
|--------|----------|---------|-----|---------|------|----------|
| {Pillar} | {item} | {-/R} | {-/R} | {R} | {R} | {severity} |

Legend: R = Required, - = Not required at this tier

---

## Gap Detection Guide

For each MVA item, how to detect a gap programmatically:

### {MVA Item Name}

- **Check command:** `aws {service} {describe/get command}`
- **Gap condition:** {what indicates a gap — e.g., "Logging.Enabled is false"}
- **Severity:** {Critical/High/Medium/Low}
- **Remediation:** `aws {service} {fix command}`
- **Remediation description:** {what the fix does}

---

## Notes

- Production MVA is the superset — all lower tiers are subsets
- Higher layers (org/BU) can ADD items but cannot remove core items
- Only the user can accept gaps below core MVA (non-production only)
- See `skills/aws/aws-well-architected/SKILL.md` for evaluation instructions
