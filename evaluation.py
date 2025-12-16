from typing import List
from dotenv import load_dotenv
from deepeval import evaluate
from deepeval.test_case import Turn, ConversationalTestCase
from deepeval.metrics import ConversationCompletenessMetric, GoalAccuracyMetric
from deepeval.simulator import ConversationSimulator
from deepeval.dataset import ConversationalGolden
from agent import run_agent_conversation
from database import init_db
import pytest

load_dotenv()
init_db()

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
    # This is where your Sage agent gets called
    response = run_agent_conversation(input)
    return Turn(role="assistant", content=response)

def run_evaluation():
    """Run DeepEval evaluation on Sage agent"""
    # Create simulator
    simulator = ConversationSimulator(model_callback=model_callback, max_concurrent=1)
    
    # Generate test cases
    conversational_test_cases = simulator.simulate(
        conversational_goldens=[conversation_golden1, conversation_golden2, conversation_golden3]
    )
    
    # Define metrics for conversational evaluation
    metrics = [
        GoalAccuracyMetric(threshold=0.5, model="gpt-4o-mini"),
        ConversationCompletenessMetric(threshold=0.8, model="gpt-4o-mini")
    ]
    
    # Run evaluation
    results = evaluate(test_cases=conversational_test_cases, metrics=metrics)
    return results

if __name__ == "__main__":
    print("Running Sage agent evaluation...")
    results = run_evaluation()
    print("\nEvaluation completed!")