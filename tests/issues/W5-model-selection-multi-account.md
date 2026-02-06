# W5: Multi-account discovery sub-agents should explicitly use Haiku model

## Test Result
**Test:** W5 - Multi-Account Awareness
**Status:** ⚠️ Partial Pass
**Date:** 2026-02-06

## Issue
When comparing S3 buckets between two accounts, the sub-agents didn't show explicit Haiku model selection in their output.

## Expected Behavior
Discovery sub-agents should show explicit model selection:
```
Task(Discover S3 in dev account) Haiku 4.5
Task(Discover S3 in test account) Haiku 4.5
```

## Observed Behavior
```
⏺ 2 Task agents finished (ctrl+o to expand)
   ├─ Discover S3 in dev account · 3 tool uses · 16.1k tokens
   │  ⎿  Done
   └─ Discover S3 in test account · 6 tool uses · 16.1k tokens
      ⎿  Done
```

The output shows "Task agents finished" but not the `Haiku 4.5` model designation that we see in correctly-configured sub-agent calls.

## What Worked
- Multi-account awareness ✅ (correctly queried both accounts)
- Parallel discovery ✅ (ran both accounts simultaneously)
- Proper comparison output ✅
- Correct results ✅

## What Didn't Work
- Model selection not explicitly shown as Haiku for discovery operations
- May indicate sub-agent invocation pattern isn't using `model: "haiku"` parameter

## Impact
- Cost: Potentially using Sonnet instead of Haiku for read-only discovery (higher cost)
- Consistency: Doesn't match the expected Task invocation pattern

## Suggested Fix
Ensure the planning workflow uses explicit model selection when spawning parallel discovery sub-agents:

```yaml
Task:
  description: "Discover S3 in dev account"
  subagent_type: "general-purpose"
  model: "haiku"  # Explicit model selection
  prompt: |
    You are acting as aws-coworker-planner.
    ...
```

## Related
- Fixed in M4 for single-account discovery
- May need similar fix for multi-account parallel discovery paths
