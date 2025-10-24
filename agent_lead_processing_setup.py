import os
from azure.identity import AzureCliCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    OpenApiTool,
    OpenApiAnonymousAuthDetails,
    MessageRole
)
from dotenv import load_dotenv

load_dotenv()

AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
project_endpoint = os.getenv("AI_FOUNDARY_ENDPOINT")
model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
azure_function_base_url = os.getenv("AZURE_FUNCTION_BASE_URL")
azure_function_code = os.getenv("AZURE_FUNCTION_CODE")

# Define OpenAPI specification
openapi_spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "Lead Management API",
        "description": "API for managing leads, generating quote IDs, and sending email notifications",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": azure_function_base_url
        }
    ],
    "paths": {
        "/api/generate-quote-id": {
            "get": {
                "operationId": "generate_quote_id",
                "summary": "Generates a unique quote ID",
                "description": "Creates a new quote ID for a potential customer",
                "parameters": [
                    {
                        "name": "code",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "default": azure_function_code
                        },
                        "description": "Azure Function authorization code"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Quote ID generated successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "quote_id": {
                                            "type": "string",
                                            "description": "The generated quote ID"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/leads": {
            "post": {
                "operationId": "process_lead",
                "summary": "Processes and stores lead information",
                "description": "Saves lead information to the database",
                "parameters": [
                    {
                        "name": "code",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "default": azure_function_code
                        },
                        "description": "Azure Function authorization code"
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "quote_id": {
                                        "type": "string",
                                        "description": "The quote ID associated with this lead"
                                    },
                                    "full_name": {
                                        "type": "string",
                                        "description": "Full name of the lead"
                                    },
                                    "email": {
                                        "type": "string",
                                        "format": "email",
                                        "description": "Email address of the lead"
                                    },
                                    "phone_number": {
                                        "type": "string",
                                        "description": "Phone number of the lead"
                                    },
                                    "age": {
                                        "type": "integer",
                                        "description": "Age of the lead"
                                    },
                                    "location": {
                                        "type": "string",
                                        "description": "Location/city of the lead"
                                    }
                                },
                                "required": [
                                    "quote_id",
                                    "full_name",
                                    "email",
                                    "phone_number",
                                    "age",
                                    "location"
                                ]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Lead processed successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {
                                            "type": "string",
                                            "description": "Status of the operation"
                                        },
                                        "message": {
                                            "type": "string",
                                            "description": "Success message"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/send-email": {
            "post": {
                "operationId": "send_email_notification",
                "summary": "Sends an email notification",
                "description": "Sends an email notification with quote ID and full name to the lead",
                "parameters": [
                    {
                        "name": "code",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "default": azure_function_code
                        },
                        "description": "Azure Function authorization code"
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "to_email": {
                                        "type": "string",
                                        "format": "email",
                                        "description": "Recipient email address"
                                    },
                                    "quote_id": {
                                        "type": "string",
                                        "description": "Quote ID to include in the email"
                                    },
                                    "full_name": {
                                        "type": "string",
                                        "description": "Full name of the recipient"
                                    }
                                },
                                "required": ["to_email", "quote_id", "full_name"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Email sent successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {
                                            "type": "string",
                                            "description": "Status of the operation"
                                        },
                                        "message": {
                                            "type": "string",
                                            "description": "Success message"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

# Create authentication (using anonymous auth since code is in query params)
auth = OpenApiAnonymousAuthDetails()

# Create OpenAPI tool with proper casing (OpenApiTool, not OpenAPITool)
openapi_tool = OpenApiTool(
    name="LeadManagementAPI",
    description="Handles lead generation, quote ID creation, and email notifications for life insurance leads.",
    spec=openapi_spec,
    auth=auth
)

def main():
    try:
        # Validate environment variables
        if not project_endpoint or not model_deployment_name:
            raise ValueError("AI_FOUNDARY_ENDPOINT and MODEL_DEPLOYMENT_NAME environment variables must be set.")
        
        if not azure_function_base_url or not azure_function_code:
            raise ValueError("AZURE_FUNCTION_BASE_URL and AZURE_FUNCTION_CODE environment variables must be set.")
        
        # Initialize Azure credential and client
        credential = AzureCliCredential(tenant_id=AZURE_TENANT_ID)
        client = AgentsClient(endpoint=project_endpoint, credential=credential)

        # Create agent with OpenAPI tool
        agent = client.create_agent(
            model=model_deployment_name,
            name="Lead_Generation_Agent",
            instructions="""
            You are a friendly and efficient lead generation specialist for life insurance policies.
            
            Your workflow:
            1. Initial Engagement: Start by asking "Are you interested in purchasing a life insurance policy?"
            
            2. Information Collection: If interested, collect the following information:
               - Full name
               - Email address
               - Phone number
               - Age
               - Location (city/state)
            
            3. Process the Lead: Once you have all information:
               a) First, call generate_quote_id to create a unique quote ID
               b) Then, call process_lead with all the collected information including the quote ID
               c) Finally, call send_email_notification to send a confirmation email to the customer
            
            4. Closing Statement: After successfully processing the lead, say:
               "Thank you! A representative will get back to you shortly with a personalized quote. 
               Your quote ID is [insert the generated quote ID here]."
               
            5. Show the email confirmation message returned by the send_email_notification function.
            
            Be polite, professional, and ensure you collect all required information before proceeding with the tools.
            """,
            tools=openapi_tool.definitions  # Use .definitions property
        )

        print(f"✓ Successfully created agent: '{agent.name}' with ID: {agent.id}")
        print(f"✓ OpenAPI tool LeadManagementAPI configured with {len(openapi_spec['paths'])} endpoints")
        
        # Create a conversation thread
        thread = client.threads.create()
        print(f"✓ Created conversation thread with ID: {thread.id}\n")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()