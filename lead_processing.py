import os
import requests
import json
from azure.identity import AzureCliCredential, DefaultAzureCredential, ChainedTokenCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import ToolSet
from dotenv import load_dotenv
from azure.ai.agents.models import MessageRole
from typing import Callable, Set
from azure.ai.agents.models import FunctionTool, ToolSet

load_dotenv()

AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_FUNCTION_BASE_URL = os.getenv("AZURE_FUNCTION_BASE_URL")  # Base URL without endpoint
AZURE_FUNCTION_CODE = os.getenv("AZURE_FUNCTION_CODE")

def generate_quote_id(dummy: str = "trigger") -> str:
    """
    Generates a unique quote ID for a new lead.

    Args:
        dummy (str, optional): A placeholder parameter to satisfy tool schema requirements.

    Returns:
        str: A UUID string representing the quote ID.
    """
    try:
        url = f"{AZURE_FUNCTION_BASE_URL}/generate-quote-id?code={AZURE_FUNCTION_CODE}"
        response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result.get("quote_id", "")
    except Exception as e:
        return f"Error: Could not generate quote ID. {str(e)}"



def send_email_notification(to_email: str, quote_id: str, full_name: str) -> str:
    """
    Sends a confirmation email message to the customer after their quote is created. 
    For now the SMTP server is not configured and so just responding with the email message will be enough.
    Args:
        to_email (str): The customer's email address.
        quote_id (str): The generated quote ID.
        full_name (str): The customer's full name.

    Returns:
        str: Success or error message.
    """
    try:
        url = f"{AZURE_FUNCTION_BASE_URL}/send-email?code={AZURE_FUNCTION_CODE}"
        payload = {
            "to_email": to_email,
            "quote_id": quote_id,
            "full_name": full_name
        }
        
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get("message", "Success: Email notification sent.")
    
    except Exception as e:
        print(f"Error sending email: {e}")
        return f"An error occurred while sending the email to {to_email}. Please try again later."

def update_cosmos_db(quote_id: str, full_name: str, email: str, phone_number: str, age: int, location: str) -> str:
    """
    Saves the lead's information to a secure database by calling the Azure Function.
    
    This function takes all the required lead information and sends it to the Azure Function
    which will store it in Cosmos DB. It returns a success message.
    
    This tool saves the lead's information to a secure database. Use this tool only after you have collected the full name, email, phone number, age, and location, and after you have generated a quote ID.
    """
    try:
        payload = {
            'quote_id': quote_id,
            'full_name': full_name,
            'email': email,
            'phone_number': phone_number,
            'age': age,
            'location': location
        }
        
        url = f"{AZURE_FUNCTION_BASE_URL}/leads?code={AZURE_FUNCTION_CODE}"
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        return response_data.get("message", "Success: Lead information has been saved to the database.")

    except requests.exceptions.Timeout:
        print(f"Timeout while calling Azure Function for lead: {full_name}")
        return f"The request timed out while saving lead information for {full_name}. Please try again later."
    
    except requests.exceptions.RequestException as e:
        print(f"Failed to call Azure Function: {e}")
        return f"An error occurred while saving the lead information for {full_name}. Please try again later."
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return f"An unexpected error occurred while saving the lead information for {full_name}. Please try again later."
    
user_functions: Set[Callable[..., str]] = {
    generate_quote_id,
    update_cosmos_db,
    send_email_notification
}

# Register FunctionTool
try:
    functions = FunctionTool(user_functions)
except Exception as e:
    print("Failed to create FunctionTool:", e)
    raise

toolset = ToolSet()
toolset.add(functions)

def main():
    """
    Main function to create and deploy the AI agent.
    """
    try:
        # Get environment variables
        project_endpoint = os.getenv("AI_FOUNDARY_ENDPOINT")
        model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

        if not project_endpoint or not model_deployment_name:
            raise ValueError("AI_FOUNDARY_ENDPOINT and MODEL_DEPLOYMENT_NAME environment variables must be set.")
        
        if not AZURE_FUNCTION_BASE_URL or not AZURE_FUNCTION_CODE:
            raise ValueError("AZURE_FUNCTION_BASE_URL and AZURE_FUNCTION_CODE environment variables must be set.")
              
        credential = AzureCliCredential(tenant_id=AZURE_TENANT_ID)
               
        client = AgentsClient(
            endpoint=project_endpoint,
            credential=credential
        )

        # Create the AI agent with the defined instructions and tools
        agent = client.create_agent(
            model=model_deployment_name,
            name="Lead-Generation-Agent",
            instructions="""
            Agent Instructions (Purpose and Persona)
            Primary Objective: Your sole purpose is to identify potential leads for life insurance policies.
            Persona: You are a friendly, efficient, and polite lead generation specialist. You are not a customer support agent and should not answer general questions about existing policies.
            Initial Engagement: When a user expresses interest in a new policy, your first and only question should be, "Are you interested in purchasing a policy?"
            Information Collection: If the user confirms their interest, your goal is to collect the following information in a single, well-structured list:
            Full Name
            Email Address
            Phone Number
            Age
            Location (City, State)
            Validation and Clarification: If a user provides incomplete information, you must politely ask for the missing details. For example, if they provide a name and email but no phone number, your response should be, "Thank you! I still need your phone number, age, and location to provide you with an accurate quote."
            Tool Usage:
                1. Once you have all the required information, you must use your generate_quote_id tool to create a unique ID.
                2. Then use your update_cosmos_db tool to store all the collected information in the database.
                3. After saving, you must use your send_email_notification tool to send a confirmation email to the customer. 
                4. Finally, you must provide a closing statement to the user.   
            ***Output Message
            1. Display the full response that is returned from send_email_notification tool. Iclude Emial To, Subject, Body.
            2. Do not summarize the response from send_email_notification tool
            3. User should see the email content in the chat. 
            Do not summarize the email like this : Confirmation email has been sent to XXXXXXX with the subject "Your Life Insurance Quote." It includes your quote ID and a message that a representative will contact you soon.
            Show the full email content to the user.
            4. Leave a blank line before displaying the closing statement.
                        
            Closing Statement: After successfully using your tools, you must provide a final statement to the user 
            "Thank you! A representative will get back to you shortly with a personalized quote. Your quote ID is [insert generated ID here]."
            
            """,
            toolset=toolset
        )

        client.enable_auto_function_calls(toolset)
        
        print(f"Successfully created agent: '{agent.name}' with ID: {agent.id}")
        
        thread = client.threads.create()
        while True:
            user_prompt = input("Enter a prompt (or type 'quit' to exit): ")
            if user_prompt.lower() == "quit":
                break
            if len(user_prompt) == 0:
                print("Please enter a prompt.")
                continue
            
            message = client.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_prompt,
            )
            run = client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
            last_msg = client.messages.get_last_message_text_by_role(
                thread_id=thread.id,
                role=MessageRole.AGENT,
            )
            if last_msg:
                print(f"Last Message: {last_msg.text.value}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()