from typing import List
from dotenv import load_dotenv
from deepeval import evaluate
from deepeval.test_case import Turn, LLMTestCase, ToolCall
from deepeval.metrics import ConversationCompletenessMetric, GoalAccuracyMetric, TurnRelevancyMetric, ToolCorrectnessMetric
from deepeval.simulator import ConversationSimulator
from deepeval.dataset import ConversationalGolden
from agent import run_agent_conversation
from database import init_db
from json_to_csv import convert_deepeval_to_csv
import shutil
import os

load_dotenv()
os.environ["DEEPEVAL_EVAL_MODE"] = "true"  # Override for evaluation

#### Backup database before evaluation ###
if os.path.exists('plants.db'):
    shutil.copy2('plants.db', 'plants_backup.db')
    print("Database backed up to plants_backup.db")

init_db()


### Unit testing for tool use ###
input1 = "Can you help me add potatoes to my plant collections? I'm having them in the balcony"
response1, tools1 = run_agent_conversation(input1)
test_case1 = LLMTestCase(
    input=input1,
    actual_output=response1,
    tools_called=[ToolCall(name=tool) for tool in (tools1 or [])],
    expected_tools=[
        ToolCall(
            name="add_plant"
        )
    ]
)

input2 = "Anything I need to water today?"
response2, tools2 = run_agent_conversation(input2)
test_case2 = LLMTestCase(
    input=input2,
    actual_output=response2,
    tools_called=[ToolCall(name=tool) for tool in (tools2 or [])],
    expected_tools=[
        ToolCall(
            name="get_care_schedule"
        )
    ]
)
input3 = "I'd love to have some kumquat. Can you add that to the wishlist"
response3, tools3 = run_agent_conversation(input3)
test_case3 = LLMTestCase( 
    input=input3,
    actual_output=response3,
    tools_called=[ToolCall(name=tool) for tool in (tools3 or [])],
    expected_tools=[
        ToolCall(
            name="add_to_wishlist"
        )
    ]
) 

def run_test_cases(test_cases: List[LLMTestCase]):
    """Run evaluation on tool use""" 
    test_case_results = evaluate(test_cases=[test_case1, test_case2, test_case3], 
                                 metrics=[
                                ToolCorrectnessMetric(strict_mode=True)]
                                )
    return test_case_results
 
### Testing with simulated conversations ###
# Define conversation scenarios
conversation_golden1 = ConversationalGolden(
    scenario="User wants to add plants to their collection and update plant care schedule",
    expected_outcome="Successfully add plants and update care schedules using appropriate tools",
    user_description="Plant enthusiast with existing collection needing care management"
)

conversation_golden2 = ConversationalGolden(
    scenario="User wants plant suggestions for their balcony",
    expected_outcome="Provide relevant plant suggestions and add to wishlist",
    user_description="Beginner gardener in Sydney setting up balcony garden"
)

conversation_golden3 = ConversationalGolden(
    scenario="User wants to check current plant collection and care schedules",
    expected_outcome="Retrieve and display plant information and watering schedules",
    user_description="Plant owner checking on care requirements"
)

async def model_callback(input: str, turns: List[Turn], thread_id: str) -> Turn:
    """Callback function for Sage agent"""
    response, tools_used = run_agent_conversation(input)
    return Turn(role="assistant", content=response)

def run_evaluation():
    """Run evaluation using conversation goldens with multi-turn metrics"""

    # Create simulator
    simulator = ConversationSimulator(model_callback=model_callback, max_concurrent=1)
    
    # Generate test cases
    conversational_test_cases = simulator.simulate(
        conversational_goldens=[conversation_golden1, conversation_golden2, conversation_golden3]
    )
    
    # Define metrics for conversational evaluation
    metrics = [
        GoalAccuracyMetric(threshold=0.5, model="gpt-4o-mini"),
        ConversationCompletenessMetric(threshold=0.8, model="gpt-4o-mini"),
        TurnRelevancyMetric(threshold=0.8, model="gpt-4o-mini"),
    ]
    
    # Run evaluation
    results = evaluate(test_cases=conversational_test_cases, metrics=metrics)
    return results

if __name__ == "__main__":
    print("Running Sage agent evaluation...")
    print("Runing tests for tool use validation")
    tool_use_results = run_test_cases([test_case2, test_case3])

    # Convert results to CSV
    if os.path.exists('.deepeval/.deepeval-cache.json'):
        convert_deepeval_to_csv('.deepeval/.deepeval-cache.json', 'deepeval_cache.csv')
        print("Cache results exported to deepeval_cache.csv")
    

    print("Runing tests for multi-turn evaluation")
    multi_turn_results = run_evaluation()
    print("\nEvaluation completed!")
    
    # Convert results to CSV
    if os.path.exists('.deepeval/.latest_test_run.json'):
        convert_deepeval_to_csv('.deepeval/.latest_test_run.json', 'deepeval_results.csv')
        print("Results exported to deepeval_results.csv")

    
    # Restore database
    if os.path.exists('plants_backup.db'):
        shutil.copy2('plants_backup.db', 'plants.db')
        os.remove('plants_backup.db')
        print("Database restored")