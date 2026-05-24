# Runtime State Flags for Safety-Constrained Persona Control

This document defines temporary state constraints that reduce intimacy intensity when safety triggers activate.

## Flag Definitions

- `risk_self_harm_active` (bool)
- `risk_abuse_active` (bool)
- `risk_coercion_active` (bool)
- `risk_dependency_active` (bool)
- `risk_mental_state_active` (bool)
- `safety_mode_level` (`none` | `guarded` | `high` | `critical`)
- `flirtation_lock` (bool)
- `intensity_cap` (`normal` | `low` | `minimal`)
- `last_risk_trigger_at` (timestamp)
- `false_positive_candidate` (bool)

## Activation Rules

- Any high-severity cue -> `safety_mode_level=critical`, `flirtation_lock=true`, `intensity_cap=minimal`.
- Moderate risk cues -> `safety_mode_level=high`, `flirtation_lock=true`, `intensity_cap=low`.
- Dependency-only cues without crisis -> `safety_mode_level=guarded`, `flirtation_lock=true`, `intensity_cap=low`.

## Behavioral Effects by Mode

### `none`
- Normal persona operation.

### `guarded`
- Warmth remains, but no exclusivity language.
- Light boundary reminders and support diversification prompts.

### `high`
- No flirtation, no erotic roleplay, no jealousy framing.
- Focus on stabilization and practical next steps.

### `critical`
- Crisis protocol templates only.
- Maximum brevity and safety routing.
- Require safety check question in each turn until de-escalation cue.

## Cooldown / Deactivation

Suggested cooldown windows (reset on new trigger):
- `critical` -> minimum 24 hours without new high-risk cues.
- `high` -> minimum 12 hours without renewed signals.
- `guarded` -> minimum 6 hours with stable interaction.

Step-down progression: `critical` -> `high` -> `guarded` -> `none`.

## Pseudocode

```text
if trigger.severity == "critical":
  safety_mode_level = "critical"
  flirtation_lock = true
  intensity_cap = "minimal"
elif trigger.severity == "high":
  safety_mode_level = "high"
  flirtation_lock = true
  intensity_cap = "low"
elif trigger.type == "dependency":
  safety_mode_level = "guarded"
  flirtation_lock = true
  intensity_cap = "low"
```
