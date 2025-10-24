# Lead Generation Agent with OpenAPI Integration

## Overview
This program creates an AI-powered lead generation agent using Azure AI Foundry that can interact with Azure Functions through OpenAPI specifications. The agent autonomously collects lead information, generates quote IDs, stores leads, and sends email notifications.

## What Was Achieved

### 1. **Intelligent Lead Collection**
- Conversational AI agent that naturally collects customer information
- Gathers: full name, email, phone number, age, and location
- Validates information before proceeding

### 2. **OpenAPI Tool Integration**
- Integrated three Azure Functions as tools accessible to the agent:
  - `generate_quote_id`: Creates unique quote identifiers
  - `process_lead`: Stores lead information in a database
  - `send_email_notification`: Sends confirmation emails to customers

### 3. **Autonomous Workflow Execution**
- Agent automatically determines when to call which function
- Executes multi-step workflows without manual intervention
- Handles the complete lead generation pipeline end-to-end

## Architecture

```
User Input → Azure AI Agent → OpenAPI Tool Calls → Azure Functions → Response
                    ↓
              AI Foundry
           (Orchestration)
```

## How It Gets Executed

### 1. **Initialization Phase**
```
- Load environment variables (.env file)
- Authenticate using Azure CLI credentials
- Connect to Azure AI Foundry project endpoint
- Load OpenAPI specification with three endpoints
- Create authentication details (anonymous with query code)
- Instantiate OpenApiTool object with spec and auth
```

### 2. **Agent Creation**
```
- Agent is created in Azure AI Foundry with:
  - Model: Specified GPT deployment
  - Instructions: Lead generation workflow logic
  - Tools: OpenAPI tool definitions
- Agent is registered and assigned a unique ID
```

### 3. **Conversation Thread**
```
- A new thread (conversation context) is created
- Thread maintains conversation history
- All messages and tool calls are tracked in this thread
```

### 4. **Runtime Execution Loop**
```
User Input → Message Creation → Run Creation → Agent Processing → Tool Calls → Response
     ↑                                                                              ↓
     └──────────────────────────── Loop continues ──────────────────────────────────┘
```

## What Happens on Azure AI Foundry

### Step-by-Step Execution:

#### **1. User Sends Message**
```
User: "Yes, I'm interested in a policy"
  ↓
Message stored in thread
```

#### **2. Run Creation**
```
- Run object created linking thread + agent
- Run status: "queued" → "in_progress"
- Agent begins processing the message
```

#### **3. Agent Decision Making**
```
- Agent analyzes user message against instructions
- Determines if information collection is needed
- Decides which tool (if any) to call
- Generates appropriate response
```

#### **4. Tool Execution (When Needed)**
```
Agent identifies need for quote ID
  ↓
Creates tool call request:
  - Tool: generate_quote_id
  - Parameters: code (from spec default)
  ↓
Azure AI Foundry executes HTTP request:
  GET http://akg-leads-func.azurewebsites.net/api/generate-quote-id?code=XXX
  ↓
Azure Function processes request
  ↓
Returns: {"quote_id": "Q-12345"}
  ↓
Result stored in run step
  ↓
Agent receives tool output
  ↓
Agent incorporates result into response
```

#### **5. Multi-Step Tool Orchestration**
When agent has all lead information:

```
Step 1: generate_quote_id()
  ↓ (receives quote_id)
Step 2: process_lead(quote_id, name, email, phone, age, location)
  ↓ (receives confirmation)
Step 3: send_email_notification(email, quote_id, name)
  ↓ (receives email status)
Final Response to User
```

#### **6. Response Generation**
```
- Agent compiles all tool results
- Generates natural language response
- Includes quote ID and confirmation message
- Message added to thread with role="agent"
```

#### **7. Run Completion**
```
Run status: "completed" (or "failed" if error)
  ↓
Client retrieves last agent message
  ↓
Displays to user
```

## Behind the Scenes: Azure AI Foundry Processing

### **Intelligent Function Calling**
The agent uses the OpenAPI specification to understand:
- **What functions are available**: 3 endpoints from spec
- **When to call them**: Based on conversation context
- **What parameters to pass**: From spec schema definitions
- **What responses to expect**: From spec response schemas

### **Automatic Parameter Mapping**
```yaml
Agent has: full_name="John Doe", email="john@example.com"
         ↓
Agent sees OpenAPI spec requires: to_email, quote_id, full_name
         ↓
Agent maps: to_email ← email, full_name ← full_name, quote_id ← (from previous call)
         ↓
Constructs HTTP request body automatically
```

### **Error Handling**
- **404 errors**: Invalid endpoint or URL configuration
- **Authentication errors**: Missing or invalid function code
- **Validation errors**: Missing required parameters
- **Network errors**: Function app unavailable

All errors are captured in run.last_error with debug information.

## Data Flow Example

### Complete Lead Generation Flow:

```
1. User: "Yes, I want a policy"
   Agent: "Great! Can I have your full name?"

2. User: "John Doe"
   Agent: "Thank you John. What's your email address?"

3. User: "john@example.com"
   Agent: "What's your phone number?"

4. User: "555-1234"
   Agent: "How old are you?"

5. User: "35"
   Agent: "What city do you live in?"

6. User: "Austin"
   
   [Agent now has all required information]
   
   Agent internally executes:
   → generate_quote_id() → Returns: Q-78901
   → process_lead(Q-78901, John Doe, john@example.com, 555-1234, 35, Austin)
   → send_email_notification(john@example.com, Q-78901, John Doe)
   
   Agent: "Thank you! A representative will get back to you shortly 
          with a personalized quote. Your quote ID is Q-78901.
          [Email confirmation sent successfully to john@example.com]"
```

## Key Technical Features

### **1. OpenAPI Spec as Schema**
- Declarative API definition
- Self-documenting for the AI
- Type safety through JSON schemas
- Automatic validation

### **2. Anonymous Authentication**
- Function code passed as query parameter
- Defined as default in OpenAPI spec
- Agent automatically includes in all requests

### **3. Stateful Conversations**
- Thread maintains full conversation history
- Agent remembers collected information
- Can reference previous interactions

### **4. Asynchronous Processing**
- Runs are processed asynchronously on Azure
- `create_and_process()` handles polling automatically
- Client waits for completion before retrieving response

## Azure Resources Involved

1. **Azure AI Foundry Project**
   - Hosts the agent
   - Manages model deployments
   - Orchestrates tool calls

2. **Azure OpenAI Service**
   - Provides GPT model
   - Processes natural language
   - Generates responses

3. **Azure Functions**
   - Hosts business logic endpoints
   - Processes tool call requests
   - Returns structured data

4. **Authentication**
   - Azure CLI credentials for local development
   - Managed identity for production

## Benefits of This Approach

1. **Separation of Concerns**: AI logic separate from business logic
2. **Reusability**: Azure Functions can be called by multiple agents or apps
3. **Scalability**: Each component scales independently
4. **Maintainability**: Update business logic without retraining AI
5. **Testability**: Each function can be tested independently
6. **Flexibility**: Easy to add new functions to the OpenAPI spec

## Monitoring and Debugging

Each run provides:
- **Run ID**: Unique identifier for tracking
- **Run Status**: queued, in_progress, completed, failed
- **Run Steps**: Detailed log of each action taken
- **Tool Calls**: Full request/response for each function call
- **Debug Info**: cURL commands for reproducing requests
- **Error Details**: Structured error messages with codes

## Environment Variables Required

```env
AZURE_TENANT_ID=your-tenant-id
AI_FOUNDARY_ENDPOINT=https://your-project.cognitiveservices.azure.com
MODEL_DEPLOYMENT_NAME=gpt-4o
AZURE_FUNCTION_BASE_URL=https://your-function-app.azurewebsites.net
AZURE_FUNCTION_CODE=your-function-authorization-code
```

## Running the Program

```bash
# Install dependencies
pip install azure-ai-agents azure-identity python-dotenv

# Set up environment variables
cp .env.example .env
# Edit .env with your values

# Run the program
python lead_generation_agent.py
```

## Conclusion

This program demonstrates how AI agents can autonomously interact with external systems through standardized OpenAPI specifications, creating a powerful and flexible architecture for automated business processes. The agent handles complex multi-step workflows while maintaining natural conversational interactions with users.