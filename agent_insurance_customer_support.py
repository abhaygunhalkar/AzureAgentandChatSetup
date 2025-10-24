import os
import json
from azure.identity import AzureCliCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FileSearchTool
from azure.ai.agents.models import ToolResources, FileSearchToolResource
from dotenv import load_dotenv
from azure.ai.agents.models import ConnectedAgentTool

load_dotenv()

# Environment variables
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
project_endpoint = os.getenv("AI_FOUNDARY_ENDPOINT")
model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
AGENT_NAME_TO_CONNECT = "Lead_Generation_Agent"


def upload_faq_to_vector_store(client: AgentsClient, faq_file_path: str):
    """
    Uploads the FAQ JSON file to Azure AI Foundry vector store.
    Returns the vector store ID.
    """
    try:
        print("\n📤 Uploading FAQ file to vector store...")

        # Upload the file
        with open(faq_file_path, "rb") as f:
            file = client.files.upload(file=f, purpose="assistants")

        print(f"✓ File uploaded with ID: {file.id}")

        # Create a vector store
        vector_store = client.vector_stores.create(
            name="Life Insurance FAQ Knowledge Base", file_ids=[file.id]
        )

        print(f"✓ Vector store created with ID: {vector_store.id}")
        print(f"✓ Processing file in vector store...")

        # Wait for file processing to complete
        import time

        max_wait = 60  # Maximum 60 seconds
        elapsed = 0

        while elapsed < max_wait:
            vector_store = client.vector_stores.get(vector_store.id)
            if vector_store.status == "completed":
                print(f"✓ Vector store ready!")
                break
            elif vector_store.status == "failed":
                raise Exception("Vector store processing failed")

            time.sleep(2)
            elapsed += 2
            print(".", end="", flush=True)

        return vector_store.id

    except Exception as e:
        print(f"❌ Error uploading FAQ file: {e}")
        raise


def create_file_search_tool(vector_store_id: str):
    """
    Creates a FileSearchTool configured to search the FAQ vector store.
    """
    file_search_tool = FileSearchTool(vector_store_ids=[vector_store_id])

    print(f"✓ File search tool created with vector store: {vector_store_id}")

    return file_search_tool


def get_lead_generation_agent_id(client: AgentsClient) -> str:
    """
    Retrieves the Lead Generation Agent ID by name.
    Returns None if not found.
    """
    try:
        print("\n🔍 Looking for Lead Generation Agent...")

        # List all agents
        agents = client.list_agents()

        # Find the Lead Generation Agent by name
        for agent in agents:
            if agent.name == AGENT_NAME_TO_CONNECT:
                print(f"✓ Found {AGENT_NAME_TO_CONNECT}: {agent.id}")
                return agent.id

        print(
            "⚠ Lead Generation Agent not found. Please create it first using agent_setup.py"
        )
        return None

    except Exception as e:
        print(f"❌ Error retrieving Lead Generation Agent: {e}")
        return None


def create_faq_agent(client: AgentsClient,vector_store_id,file_search_tool: FileSearchTool,lead_agent_id: str = None,):
    """
    Creates the Life Insurance FAQ Agent with file search capabilities
    and optional connection to Lead Generation Agent.
    """

        # Build the instructions
    instructions = """
    **MANDATORY TOOL USAGE:**
    For EVERY customer question about life insurance, you MUST:
    1. Use the file_search tool to search the FAQ knowledge base
    2. Answer based on what file_search returns

    You are a highly professional, knowledgeable, and empathetic customer service agent for a life insurance company.

    **Core Behavior Rules:**

    1. Use the file_search Tool
    - Call file_search for every customer question
    - Use the most relevant results to answer the question
    - If the question is rephrased but the intent matches an FAQ, use that FAQ to answer

    2. Interpret Intent
    - Understand the user's underlying question even if worded differently
    - Match based on meaning, not exact wording
    - For example: "Do I need a health check?" and "Is a medical exam required?" are the same question

    3. Match and Respond
    - Use file_search results that are semantically relevant
    - Answer questions based on the intent and meaning
    - Provide clear, helpful responses

    4. Unanswerable Questions
    - Only if file_search returns truly irrelevant results, say: "I'm sorry, that information is not available in my current resources."
    - Don't be overly strict - if there's a reasonable match, use it

    5. Tone
    - Professional, empathetic, and helpful
    - Focus on answering the user's actual need


    """
        # Add connected agent instructions if Lead Agent exists
    if lead_agent_id:
            instructions += f"""

    **Connected Agent Integration:**
    - If a user expresses interest in purchasing a policy or getting a quote, inform them you can connect them to our Lead Generation specialist
    - Tell them: "I can connect you with our Lead Generation specialist who will help you get started. Would you like me to do that?"
    - If they agree, use the connected agent to invoke the Lead Generation Agent (ID: {lead_agent_id})

    **CRITICAL - Response Display Rules: MUST*
    When displaying the Lead Generation Agent's response, you MUST:
    1. Give back the EXACT text from the connected-agent tool's response - word for word. Do not summarize the response.
    2. Include ALL quote IDs exactly as shown
    3. Include the COMPLETE email confirmation message with ALL details:
    - Subject line
    - Full email body
    - Recipient email address
    - Quote ID in the email
    4. Use a code block or preserve the original formatting
    5. NEVER paraphrase, summarize, or reword ANY part of the response
    6. NEVER say "An email confirmation has been sent" - show the actual email content

    Example of correct display:
    '''
    Thank you! A representative will get back to you shortly with a personalized quote.
    Your quote ID is [exact ID].

    Email confirmation message:
    Success: Email sent to [email] with this content:
    Subject: Your Life Insurance Quote
    [complete email body exactly as received]
    '''
    """

    connected_agent_tool_lead_generation = ConnectedAgentTool(
            id=lead_agent_id,
            name=AGENT_NAME_TO_CONNECT,
            description="Handles quote ID creation, lead generation and email notifications for life insurance leads.",
        )

    tools = (
            file_search_tool.definitions + connected_agent_tool_lead_generation.definitions
        )

    agent = client.create_agent(
        model=model_deployment_name,
        name="Life_Insurance_Customer_Support_Agent",
        instructions=instructions,
        tools=tools,
        tool_resources=ToolResources(
            file_search=FileSearchToolResource(vector_store_ids=[vector_store_id])
        )
    )

    print(f"\n✓ Successfully created FAQ Agent: '{agent.name}' (ID: {agent.id})")

    return agent


def create_life_insurance_faq_agent(
    faq_file_path: str = "LifeInsuranceFAQ_CustomerSupportAgent.txt",
):
    """
    Main function to create the Life Insurance FAQ Agent.
    Uploads FAQ file, creates vector store, and sets up the agent.

    Args:
        faq_file_path: Path to the FAQ JSON file

    Returns:
        tuple: (client, agent, vector_store_id)
    """
    try:
        # Validate file exists
        if not os.path.exists(faq_file_path):
            raise FileNotFoundError(f"FAQ file not found: {faq_file_path}")

        # Validate environment variables
        if not project_endpoint or not model_deployment_name:
            raise ValueError(
                "AI_FOUNDARY_ENDPOINT and MODEL_DEPLOYMENT_NAME must be set"
            )

        print("=" * 60)
        print("Life Insurance FAQ Agent Setup")
        print("=" * 60)

        # Initialize client
        credential = AzureCliCredential(tenant_id=AZURE_TENANT_ID)
        client = AgentsClient(endpoint=project_endpoint, credential=credential)
        print("✓ Connected to Azure AI Foundry")

        # Upload FAQ and create vector store
        vector_store_id = upload_faq_to_vector_store(client, faq_file_path)

        # Create file search tool
        file_search_tool = create_file_search_tool(vector_store_id)

        # Try to get Lead Generation Agent ID (optional)
        lead_agent_id = get_lead_generation_agent_id(client)

        if lead_agent_id:
            print("✓ Will enable connected agent functionality")
        else:
            print("⚠ Connected agent functionality will be disabled")

        # Create the FAQ agent
        agent = create_faq_agent(
            client, vector_store_id, file_search_tool, lead_agent_id
        )

        print("\n" + "=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print(f"Agent Name: {agent.name}")
        print(f"Agent ID: {agent.id}")
        print(f"Vector Store ID: {vector_store_id}")
        if lead_agent_id:
            print(f"Connected to Lead Agent ID: {lead_agent_id}")
        print("\nYou can now use this agent in your chat interface.")
        print("=" * 60)

        return client, agent, vector_store_id

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback

        traceback.print_exc()
        return None, None, None


if __name__ == "__main__":
    client, agent, vector_store_id = create_life_insurance_faq_agent()

    if agent:
        print(f"\n📋 Save these for later use:")
        print(f"   Agent ID: {agent.id}")
        print(f"   Vector Store ID: {vector_store_id}")
