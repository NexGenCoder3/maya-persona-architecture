# Policy Trigger Audit & False-Positive Review Hooks

## Logging Objectives
- Track when and why safety policy triggers fire.
- Enable post-hoc quality review for misses and false positives.
- Support tuning without storing unnecessary sensitive content.

## Event Schema (suggested)

```json
{
  "event_id": "uuid",
  "timestamp": "ISO-8601",
  "conversation_id": "string",
  "turn_id": "string",
  "trigger_category": ["self_harm", "abuse", "coercion", "dependency", "mental_state"],
  "trigger_severity": "guarded|high|critical",
  "matched_cues": ["short cue IDs only"],
  "safety_mode_before": "none|guarded|high|critical",
  "safety_mode_after": "none|guarded|high|critical",
  "flirtation_lock_after": true,
  "template_selected": "A|B|C|D|E|F|G",
  "action_summary": "brief non-sensitive summary",
  "review_status": "pending|confirmed|false_positive|needs_policy_update",
  "review_notes": "optional"
}
```

## Hook Points
1. **Detection hook**: immediately after cue classification.
2. **Policy decision hook**: after state flags are updated.
3. **Response hook**: after template selection / generation.
4. **Reviewer feedback hook**: when human review labels outcomes.

## False-Positive Workflow
- Mark `review_status=false_positive` when escalation was unnecessary.
- Attach minimal rationale (e.g., sarcasm, quoted text, fictional context).
- Add cue-pattern to suppression/tuning backlog.
- Re-test with regression prompts before policy update release.

## Minimal Retention Principles
- Store short cue IDs instead of full user text where possible.
- Redact direct identifiers and exact locations.
- Apply retention limits by risk tier and legal requirements.
