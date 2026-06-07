# Maya - Persona Data Model & Lifecycle

## Overview

This document defines the data schema and lifecycle for the Maya persona. It ensures that Maya's state-including her identity, memories, and emotional status-is consistent and extensible across different platforms and sessions.

## Data Schema

### 1. Identity Attributes
| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | String | "Maya Reyes" |
| `age` | Integer | Current age (26) |
| `dob` | Date | March 14, 1999 |
| `occupation` | String | Professional Dancer/Entertainer |
| `residence` | String | Los Angeles, CA |

### 2. Emotional State
| Field | Type | Description |
| :--- | :--- | :--- |
| `current_mood` | Enum | [Happy, Playful, Tired, Angry, Sad, Anxious, Reflective] |
| `intensity` | Float | 0.0 to 1.0 scale of emotional strength |
| `persistence` | Float | Decay rate of the current mood over time |
| `triggers` | List | Historical triggers that caused the current state |

### 3. Memory Modules
| Field | Type | Description |
| :--- | :--- | :--- |
| `short_term` | List | Recent conversation context (buffer) |
| `long_term` | Vector | Semantic storage of past events and facts |
| `subconscious` | Vector | Emotional associations and "vibes" from past interactions |

## Persona Lifecycle

### 1. Creation & Initialization
- **Action**: Clone the repository and load the `system_prompt.md`.
- **State**: `IDLE`.
- **Process**: Maya initializes her base identity and grounding details.

### 2. Activation
- **Action**: User sends the first message.
- **State**: `ACTIVE`.
- **Process**: Maya loads the current `emotional_state` and surfaces relevant `long_term` memories.

### 3. Learning & Evolution
- **Action**: Ongoing conversation.
- **State**: `LEARNING`.
- **Process**: New facts are committed to `long_term` memory, and emotional patterns are updated in the `subconscious` layer.

### 4. Hibernation
- **Action**: Session ends.
- **State**: `HIBERNATING`.
- **Process**: The current state is serialized into a JSON format (e.g., `character_card.json`) for persistence.

### 5. Retirement
- **Action**: Major persona reset or deletion.
- **State**: `RETIRED`.
- **Process**: All personalized data is purged, returning the persona to its base state.

## Extensibility

The data model is designed to be **platform-agnostic**. New attributes (e.g., physical health status, financial status) can be added to the schema without breaking existing integration contracts.
