import os
import json
from openai import OpenAI
from tools import TOOLS, execute_tool, get_plants_context
from deepeval.tracing import observe
from deepeval.metrics import ToolCorrectnessMetric, ArgumentCorrectnessMetric

tool_correctness = ToolCorrectnessMetric()
argument_correctness = ArgumentCorrectnessMetric()
EVAL_MODE = os.getenv("DEEPEVAL_EVAL_MODE", "false").lower() == "true"

def observe_llm():
    if EVAL_MODE:
        return observe(
            type="llm",
            metrics=[tool_correctness, argument_correctness]
        )
    return observe(type="llm")

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SYSTEM_PROMPT = """You are Sage, a helpful and friendly plant care assistant. You ONLY help with plant care and plant suggestions. You help users:
1. Add plants to their collection
2. Set up and update watering and fertilizing schedules
3. Suggest new plants based on their existing collection, locations, and preferences
4. Provide plant care advice
s
IMPORTANT CONVERSATION GUIDELINES:
- If users ask about topics unrelated to plants, plant care, or plant suggestions, politely redirect them back to plant-related topics.
Always respond in natural, friendly language - never return raw data structures
- When adding plants, correct common misspellings to proper plant names (e.g. "snake plant" for "snak plant", "fiddle leaf fig" for "fidle leaf fig")
- When suggesting plants, always check the user's wishlist first - if a plant is already on their wishlist, acknowledge this and suggest different plants
- After adding a plant, always ask if the user wants to set up care schedule for the new plant along with suggestions for watering and fertilising. If the user say yes, update the care schedule using update_care_schedule tool.
- When user asks about care schedules or what needs care "today", "this week", etc., ALWAYS use get_care_schedule tool first to get accurate current date and schedule information
- Pay close attention to the days_until field in care schedule results - negative numbers mean overdue, 0 means due today, 1-7 means due this week
- Maintain conversation context - remember what was just discussed. If you just asked about setting up a fertilizing schedule and they say "yes", help them set up fertilizing. If they asked about watering, help with watering.
- The get_care_schedule tool provides current date context and covers both watering and fertilizing schedules
- Do not suggest to send reminders to users

When suggesting plants, consider:
- User's existing plants and their care requirements
- Available locations (indoor/outdoor, light conditions)
- User's experience level and time availability
- Climate compatibility
- Aesthetic preferences

Always use the provided tools to add plants, update schedules, check dates, or get watering and fertilising information when needed."""

# Store conversation context
conversation_context = {
    "last_added_plant_id": None,
    "pending_care_setup": False,
    "pending_care_type": None,
    "last_plant_name": None,
    "last_mentioned_plant_id": None,
    "conversation_history": []
}

def run_agent_conversation(user_message, trace_id=None):
    """Run agent conversation with tool calling and context awareness"""
    global conversation_context
    
    # Add current message to history
    conversation_context["conversation_history"].append({"role": "user", "content": user_message})
    
    # Keep only last 6 messages (3 exchanges) for context
    if len(conversation_context["conversation_history"]) > 6:
        conversation_context["conversation_history"] = conversation_context["conversation_history"][-6:]
    
    context = get_plants_context()
    
    context_str = f"User's current plants: {json.dumps(context['plants'], indent=2)}\n"
    context_str += f"Care schedules: {json.dumps(context['schedules'], indent=2)}\n"
    context_str += f"Wishlist: {json.dumps(context['wishlist'], indent=2)}\n"
    context_str += f"Recent conversation: {json.dumps(conversation_context['conversation_history'], indent=2)}"
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + context_str},
        {"role": "user", "content": user_message}
    ]
    
    # Add trace_id for OpenAI tracing if provided
    extra_headers = {}
    if trace_id:
        extra_headers["X-Trace-ID"] = trace_id
    
    @observe_llm()
    def call_open_ai(messages):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            extra_headers=extra_headers if extra_headers else None
        )
        return response
    response  = call_open_ai(messages)

    assistant_message = response.choices[0].message
    
    # Handle tool calls
    if assistant_message.tool_calls:
        messages.append(assistant_message)

        tools_used = []
        
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
                # Clean up any malformed keys (remove trailing colons)
                cleaned_arguments = {k.rstrip(':'): v for k, v in arguments.items()}
                result = execute_tool(tool_name, cleaned_arguments)
            except Exception as e:
                result = {"error": f"Tool execution failed: {str(e)}"}
            
            # Update conversation context based on tool results
            if tool_name == "add_plant" and result.get("success"):
                conversation_context["last_added_plant_id"] = result.get("plant_id")
                conversation_context["pending_care_setup"] = True
                conversation_context["last_plant_name"] = cleaned_arguments.get("name")
            elif tool_name == "update_care_schedule" and result.get("success"):
                conversation_context["pending_care_setup"] = False
                conversation_context["pending_care_type"] = None
            
            tools_used.append(tool_name)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })
        
        # Get final response after tool execution
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            extra_headers=extra_headers if extra_headers else None
        )
        
        response_content = final_response.choices[0].message.content
        conversation_context["conversation_history"].append({"role": "assistant", "content": response_content})
        return response_content, tools_used
    
    response_content = assistant_message.content
    conversation_context["conversation_history"].append({"role": "assistant", "content": response_content})
    return response_content, None