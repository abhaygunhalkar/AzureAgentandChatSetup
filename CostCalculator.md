**OpenAI Cost Calculator - High-Level Description**

**Purpose and Use Case:**
This module is designed to track and calculate the monetary cost of using OpenAI's API services. When working with Large Language Models (LLMs) like GPT-4 or GPT-3.5, every API call incurs costs based on the number of tokens processed. Since token usage can accumulate quickly across multiple calls, especially in production applications, this calculator helps developers monitor spending in real-time and maintain budget control.

**Why It's Used:**
Without cost tracking, developers can easily lose visibility into their API expenses, leading to unexpected bills. This is particularly important during development, testing, or when running conversational agents that make numerous API calls. The calculator provides transparency by showing exactly how much each call costs and maintaining a running total for the entire session. This enables informed decision-making about model selection, prompt optimization, and overall API usage patterns.

**Design Patterns:**
The module implements several design patterns. First, it uses the **Decorator Pattern** through the `track_llm_call` decorator, which wraps existing LLM functions to automatically intercept and log their token usage without modifying the original function code. This promotes clean separation of concerns - your business logic remains unchanged while cost tracking is added as a cross-cutting concern. Second, it employs the **Data Transfer Object (DTO) pattern** through the `CostRecord` Pydantic model, which encapsulates all cost-related data in a validated, immutable structure. Third, there's an element of the **Observer Pattern** where the calculator acts as a collector that observes and records each API interaction.

**How Cost Determination Works:**
The calculator maintains a pricing table with per-million-token rates for different OpenAI models. When you make an API call, it extracts two key metrics: the number of input tokens (your prompt) and output tokens (the model's response). It then applies simple arithmetic - dividing the token counts by one million and multiplying by the respective rates - to calculate the cost in dollars. Input and output tokens have different prices because generating text is computationally more expensive than processing it. The calculator rounds costs to six decimal places for precision and stores each calculation with a timestamp for audit purposes.

**Session Tracking and Reporting:**
Beyond individual call costs, the calculator accumulates all cost records throughout a session, allowing you to generate summary reports. These summaries show total API calls made, aggregate token usage, and cumulative costs, giving you a complete financial picture of your application's LLM usage over time. This is invaluable for analyzing usage patterns, identifying expensive operations, and optimizing your application to reduce costs.

**Practical Usage:**
In practice, you instantiate the calculator once at the start of your application session, then either manually log costs after each API call or use the decorator to automate tracking. The decorator approach is preferred because it's non-invasive - you simply annotate your LLM-calling functions and the tracking happens automatically. At any point, you can request a session summary to see your spending, making it easy to set budgets, create alerts, or generate reports for stakeholders.

**How to Use **
@track_llm_call(cost_tracker, model="gpt-4o")
def ask_gpt(question: str):
    response = llm.invoke(question)
    return response