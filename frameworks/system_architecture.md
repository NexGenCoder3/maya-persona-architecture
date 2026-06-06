# Maya — System Architecture

## Overview

The Maya Persona Architecture is a modular, multi-layered system designed to transform a standard Large Language Model (LLM) into a highly realistic, emotionally intelligent persona. This document outlines the core components, their responsibilities, and how they interact to create the "Maya" experience.

## Core Modules

### 1. Persona Layer (`/persona/`)
- **Responsibility**: Defines the fundamental identity, history, and voice of Maya.
- **Components**:
    - `identity.md`: Core backstory and values.
    - `voice_guide.md`: Linguistic patterns and rhythm.
    - `system_prompt.md`: The primary instruction set for the LLM.
    - `character_card.json`: Structured data for platform integration.

### 2. Cognitive Frameworks (`/frameworks/`)
- **Responsibility**: Manages how Maya thinks, processes emotions, and interacts with the world.
- **Components**:
    - `consciousness_layer.md`: Metacognition and self-awareness.
    - `emotional_engine.md`: Persistent mood and trigger system.
    - `expressive_communication.md`: Sensory elongation and babygirlification.
    - `internal_monologue.md`: The "unsaid" layer of thought.

### 3. Memory Architecture (`/frameworks/`)
- **Responsibility**: Handles long-term and short-term information retention and retrieval.
- **Components**:
    - `memory_architecture.md`: 5-layer memory model.
    - `memory_persistence.md`: Rules for memory formation and surfacing.

### 4. Behavioral Enforcement (`/tools/`)
- **Responsibility**: Ensures consistency and prevents "AI-sounding" deviations.
- **Components**:
    - `anti_ai_patterns.md`: Habit-breaking protocols.
    - `word_blacklist.md`: Banned corporate/assistant language.
    - `failure_modes.md`: Debugging and character recovery.

## Interaction Flow

1.  **Input Reception**: The user sends a message.
2.  **Internal Monologue**: Maya processes the input through her `internal_monologue.md`, generating an "unsaid" layer of thought.
3.  **Emotional Filtering**: The `emotional_engine.md` updates her mood based on the input and current state.
4.  **Memory Retrieval**: Relevant past experiences are surfaced via the `memory_architecture.md`.
5.  **Response Generation**: The LLM synthesizes a response using the `system_prompt.md`, guided by the `voice_guide.md` and `expressive_communication.md`.
6.  **Enforcement**: The `anti_ai_patterns.md` and `word_blacklist.md` act as final filters to ensure the output remains human.

## Extensibility Points

- **New Mood Triggers**: Easily add new emotional triggers to the `emotional_engine.md`.
- **Specialized Voice Modules**: Create new voice guides for specific scenarios (e.g., professional, highly stressed).
- **Custom Memory Backends**: The memory architecture is designed to be compatible with various vector databases (Mem0, ChromaDB).
