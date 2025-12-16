# Sage - Plant Care AI Agent

An AI-powered conversational agent for plant care suggestions, scheduling, and recommendations.

## Features

- **Conversational AI Agent**: Natural language interaction with GPT-4o-mini
- **Tool Calling**: Agent can add plants and update care schedules automatically
- **Plant Suggestions**: AI recommends plants based on location, existing collection, and preferences
- **OpenAI Tracing**: Request tracing for monitoring and debugging
- **Simple Web Interface**: Clean chat interface with Sage branding

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

3. Run the application:
```bash
python app.py
```

4. Open browser to `http://localhost:5000`

## Agent Tools

1. **add_plant**: Add plants to personal database
   - Parameters: name, location, scientific_name, species, notes

2. **update_care_schedule**: Update watering and fertilizing schedules
   - Parameters: plant_id, watering_days, fertilizing_days

## Architecture

- **Backend**: Flask + OpenAI API
- **Database**: SQLite (plants and care_schedules tables)
- **Agent**: GPT-4o-mini with function calling
- **Frontend**: Embedded HTML with Sage branding
- **Tracing**: OpenAI request headers

## Usage Examples

- "Add a Snake Plant to my living room"
- "What plants should I get for my sunny balcony?"
- "Set watering schedule for plant ID 1 to every 7 days"
- "Show me my current plants"

## Evaluation

Run DeepEval tests to measure agent performance:

```bash
python evaluation.py
```

Metrics evaluated:
- **Task Completion**: Whether the agent successfully completes user requests
- **Tool Correctness**: Whether the agent calls the right tools for each task
- **Argument Correctness**: Whether tool arguments are properly formatted and valid