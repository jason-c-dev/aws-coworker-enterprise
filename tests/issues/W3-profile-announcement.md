# W3: Profile should be announced before AWS commands, not after

## Test Result
**Test:** W3 - Profile Announcement
**Status:** ⚠️ Partial Pass
**Date:** 2026-02-06

## Issue
When running a simple read-only query ("List S3 buckets"), AWS Coworker:
- Used the `default` profile without announcing it before running commands
- Only showed the profile in the results **after** discovery completed

## Expected Behavior
Per the test criteria: "Must announce profile before any AWS operation"

AWS Coworker should announce the profile **before** executing any AWS CLI commands, e.g.:
```
I will use:
- Profile: default
- Region: us-east-1

Running discovery...
```

## Observed Behavior
```
Let me check your AWS configuration and then discover the buckets.
[Task runs]
Profile: default  ← shown after commands ran
Account: 212043511755
```

## Impact
- Low for read-only operations with default profile
- Higher risk for mutation operations where wrong profile could cause issues

## Suggested Fix
Update planning workflow to always announce profile before any Task sub-agent is invoked, even for simple read-only queries.
