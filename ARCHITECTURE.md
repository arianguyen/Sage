# Architecture Overview

## System Design

```
User Interface (PWA)
        ↓
    Flask API
        ↓
    AI Agent (agent.py)
        ↓
    ┌─────────┴─────────┐
    ↓                   ↓
OpenAI API          Tools
(GPT-4o-mini)    (tools.py)
    ↓                   ↓
Langfuse            SQLite DB
(Tracing)         (plants.db)
```

## Components

### 1. Agent (agent.py)
- Orchestrates conversation flow
- Manages tool calling
- Integrates Langfuse tracing
- Provides plant context to LLM

### 2. Tools (tools.py)
- `add_plant`: Adds plants to database
- `update_care_schedule`: Updates watering/fertilizing schedules
- `get_plants_context`: Retrieves current plant data
- Tool definitions for OpenAI function calling

### 3. Database (database.py)
- SQLite initialization
- Tables: plants, care_schedules
- Connection management

### 4. Evaluation (evaluation.py)
- DeepEval test cases
- Metrics: ToolCorrectnessMetric, ConversationCompletenessMetric
- Conversation simulation

### 5. Flask API (app.py)
- REST endpoints for CRUD operations
- Chat endpoint with agent integration
- Static file serving for PWA

## Agent Capabilities

### Plant Suggestions
The agent considers:
- Existing plants in collection
- Available locations (light, space)
- User's care capacity
- Climate compatibility
- Aesthetic preferences

### Tool Usage
Agent automatically:
- Adds plants when user requests
- Updates schedules based on conversation
- Retrieves context for informed responses

## LLMOps with Langfuse

Traces include:
- User messages
- Agent responses
- Tool calls and results
- Token usage
- Latency metrics

## Evaluation Metrics

### Tool Correctness
- Correct tool selection
- Argument accuracy
- Required vs optional parameters

### Conversation Completeness
- Response addresses user query
- Provides actionable information
- Natural conversation flow

## Data Flow

1. User sends message via chat interface
2. Flask receives request, generates trace_id
3. Agent retrieves plant context from database
4. Agent sends message + context + tools to OpenAI
5. LLM decides to use tools or respond directly
6. If tools used: execute → send results back to LLM
7. Final response returned to user
8. All steps traced in Langfuse (if configured)
