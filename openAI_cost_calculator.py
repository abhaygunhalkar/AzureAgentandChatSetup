from functools import wraps
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel

OPENAI_PRICING = {
    "gpt-4o": {"input_price_per_1m": 2.50, "output_price_per_1m": 10.00},
    "gpt-4o-mini": {"input_price_per_1m": 0.150, "output_price_per_1m": 0.600},
    "gpt-4-turbo": {"input_price_per_1m": 10.00, "output_price_per_1m": 30.00},
    "gpt-4": {"input_price_per_1m": 30.00, "output_price_per_1m": 60.00},
    "gpt-3.5-turbo": {"input_price_per_1m": 0.50, "output_price_per_1m": 1.50}
}

class CostRecord(BaseModel):
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    timestamp: str

class OpenAICostCalculator:
    def __init__(self):
        self.session_costs: List[CostRecord] = []

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> CostRecord:
        if model not in OPENAI_PRICING:
            raise ValueError(f"Model '{model}' not found in pricing table")

        pricing = OPENAI_PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input_price_per_1m"]
        output_cost = (output_tokens / 1_000_000) * pricing["output_price_per_1m"]
        total_cost = input_cost + output_cost

        cost_record = CostRecord(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=round(input_cost, 6),
            output_cost=round(output_cost, 6),
            total_cost=round(total_cost, 6),
            timestamp=datetime.now().isoformat()
        )

        self.session_costs.append(cost_record)
        
        # Automatic per-call logging
        print(f"[LLM] {model} | Input: {input_tokens} | Output: {output_tokens} | Cost: ${total_cost:.6f}")
        
        return cost_record

    def get_session_summary(self) -> Dict:
        if not self.session_costs:
            return {"message": "No cost records in this session"}

        total_input = sum(r.input_tokens for r in self.session_costs)
        total_output = sum(r.output_tokens for r in self.session_costs)
        total_cost = sum(r.total_cost for r in self.session_costs)

        return {
            "total_calls": len(self.session_costs),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost": round(total_cost, 6),
            "individual_calls": [r.dict() for r in self.session_costs]
        }
    
    def print_summary(self):
        """Print a formatted summary of all LLM usage in this session"""
        summary = self.get_session_summary()
        
        if "message" in summary:
            print(f"\n{summary['message']}")
            return
        
        print("\n" + "="*60)
        print("LLM Usage Summary")
        print("="*60)
        print(f"Total API Calls: {summary['total_calls']}")
        print(f"Total Input Tokens: {summary['total_input_tokens']:,}")
        print(f"Total Output Tokens: {summary['total_output_tokens']:,}")
        print(f"Total Cost: ${summary['total_cost']:.6f}")
        print("="*60 + "\n")

# Decorator to wrap LLM calls and track cost
def track_llm_call(tracker: OpenAICostCalculator, model: str = "gpt-4o-mini"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            
            # Debug: Print response type and attributes
            print(f"\n[DEBUG] Response type: {type(response)}")
            print(f"[DEBUG] Response attributes: {dir(response)}")
            print(f"[DEBUG] Response: {response}")
            
            usage = getattr(response, "response_metadata", {}).get("token_usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            if input_tokens == 0 and output_tokens == 0:
                print("[WARNING] No token usage found in response")

            tracker.calculate_cost(model, input_tokens, output_tokens)
            
            return response
        return wrapper
    return decorator