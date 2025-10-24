import os
from azure.identity import AzureCliCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole
from dotenv import load_dotenv
from openAI_cost_calculator import OpenAICostCalculator, track_llm_call

load_dotenv()

AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
PROJECT_ENDPOINT = os.getenv("AI_FOUNDARY_ENDPOINT")
AGENT_ID = "asst_xS4WzzjvAasllgAnOYPiWFe2"

cost_tracker = OpenAICostCalculator()

def run_chat_interface(agent_id: str):
    """Run the chat interface with an existing agent"""
    try:
        credential = AzureCliCredential(tenant_id=AZURE_TENANT_ID)
        client = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=credential)
        
        agent = client.get_agent(agent_id)
        print(f"✓ Connected to agent: '{agent.name}' (ID: {agent.id})")
        
        # Create a conversation thread
        thread = client.threads.create()
        print(f"✓ Created conversation thread with ID: {thread.id}\n")
        print("="*60)
        print("Insurance Customer Service - Chat Interface")
        print("="*60)
        print("Type 'quit' to exit\n")

        # Main conversation loop
        while True:
            user_prompt = input("Your Input: ")
            
            if user_prompt.lower() == "quit":
                print("\nThank you for using the Lead Generation Agent!")
                break
            
            if len(user_prompt.strip()) == 0:
                print("Please enter a message.\n")
                continue
            
            # Add user message to thread
            client.messages.create( thread_id=thread.id, role="user", content=user_prompt )
            
            # Create and process the run
            print("\nAgent: ", end="", flush=True)
            run = client.runs.create_and_process( thread_id=thread.id, agent_id=agent_id )
            
            # Get the agent's response
            last_msg = client.messages.get_last_message_text_by_role( thread_id=thread.id, role=MessageRole.AGENT)
            
            if last_msg:
                print(f"{last_msg.text.value}\n")
            else:
                print("No response from agent.\n")
                
            # Check run status
            if run.status == "failed":
                print(f"⚠ Run failed: {run.last_error}\n")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Get agent ID from environment variable or command line
    agent_id = os.getenv("AGENT_ID")
    

    agent_id = AGENT_ID
        
    run_chat_interface(agent_id)