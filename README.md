# Sage - Plant Care AI Agent

An AI-powered conversational agent for plant care suggestions, scheduling, and recommendations.

## Features

- **Conversational AI Agent**: Natural language interaction with GPT-4o-mini
- **Tool Calling**: Agent can add plants and update care schedules automatically
- **Plant Suggestions**: AI recommends plants based on location, existing collection, and preferences
- **OpenAI Tracing**: Request tracing for monitoring and debugging
- **Simple Web Interface**: Simple chat interface with Sage and side bar for plant care schedule and wishlist 

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=your_openai_api_key
```

3. Run the application:
```bash
python app.py
```

4. Open browser to `http://localhost:5001`

## Agent Tools

1. **add_plant**: Add plants to personal database
   - Parameters: name, location, notes

2. **update_care_schedule**: Update watering and fertilizing schedules
   - Parameters: plant_id, watering_days, fertilizing_days

3. **get_care_schedule**: Check current care schedules and due dates
   - Returns: Plants needing care with days until due

4. **add_to_wishlist**: Add plants to wishlist for future consideration
   - Parameters: name, notes

5. **remove_from_wishlist**: Remove plants from wishlist
   - Parameters: name

6. **mark_plant_dead**: Mark plants as deceased
   - Parameters: plant_id

## Architecture

- **Backend**: Flask + OpenAI API
- **Database**: SQLite (plants, care_schedules, wishlist tables)
- **Agent**: GPT-4o-mini with function calling and conversation context
- **Frontend**: Embedded HTML with sidebar showing care schedule and wishlist
- **Tracing**: OpenAI request headers
- **Evaluation**: DeepEval framework with CSV export

## Usage Examples

- "Add a Snake Plant to my living room"
- "What plants should I get for my sunny balcony?"
- "Set watering schedule for my Snake Plant to every 7 days"
- "What needs watering today?"
- "Add lavender to my wishlist"
- "Remove basil from my wishlist"

## Evaluation

Run DeepEval tests to measure agent performance:

```bash
python evaluation.py
```

Metrics evaluated:
- **Goal Accuracy**: Whether the agent achieves user goals
- **Conversation Completeness**: Whether responses fully address user intentions
- **Turn Relevancy**: Whether responses stay relevant to user messages
- **Tool Correctness**: Whether the agent calls the right tools

Results are automatically exported to `deepeval_results.csv` for analysis.