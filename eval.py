import json
import os
import time
from dotenv import load_dotenv
from typing import Callable, Dict, Any, List

from azure.ai.evaluation import evaluate, IntentResolutionEvaluator, ToolCallAccuracyEvaluator


load_dotenv()

# --- Dataset JSONL file Utility Function (Needed to create the input file) ---
def create_mock_jsonl_dataset(file_path: str, data: List[Dict[str, Any]]):
    """Writes a list of dictionaries to a JSONL file."""
    print(f"-> Creating mock dataset at {file_path}")
    try:
        with open(file_path, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        print("-> Dataset created successfully.")
    except Exception as e:
        print(f"Error creating dataset file: {e}")
        
# 2. CONFIGURATION (REQUIRED for AI-assisted evaluators like IntentResolution)
# Uses DefaultAzureCredential or AzureCliCredential flow.

AZURE_AI_PROJECT_CONFIG = {
    # Read core project connection details from environment variables
    "subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID"),
    "resource_group_name": os.environ.get("AZURE_RESOURCE_GROUP"),
    "project_name": os.environ.get("AZURE_AI_PROJECT_NAME"),
    
    # Model configuration for the LLM that performs the evaluation scoring
    "model_config": {
        # The API base should point to your Azure OpenAI endpoint
        "api_base": os.environ.get("AOAI_ENDPOINT_BASE"),
        # The api_key is removed here to enforce credential-based authentication
        "api_type": "azure",
        "api_version": "2024-02-15-preview",
        # Updated to use the environment variable name MODEL_DEPLOYMENT_NAME
        "deployment_id": os.environ.get("MODEL_DEPLOYMENT_NAME") 
    }
}