"""
Quick smolagents test with Langfuse tracing
"""

from smolagents import CodeAgent, Tool, LiteLLMModel
from backend.config import config
from backend.observability import observability  # Initialize instrumentation


class CalculatorTool(Tool):
    name = "calculator"
    description = "Performs basic arithmetic calculations. Can add, subtract, multiply, or divide two numbers."
    inputs = {
        "operation": {
            "type": "string",
            "description": "The operation to perform: add, subtract, multiply, or divide"
        },
        "a": {
            "type": "number",
            "description": "First number"
        },
        "b": {
            "type": "number",
            "description": "Second number"
        }
    }
    output_type = "number"

    def forward(self, operation: str, a: float, b: float) -> float:
        """Perform the calculation"""
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")


def main():
    print("\n🧪 Testing smolagents with Langfuse tracing...\n")

    # Initialize model
    model = LiteLLMModel(
        model_id=config.get_llm_model_id(),
        api_key=config.get_llm_api_key(),
        temperature=0.5
    )

    # Create agent with calculator tool
    agent = CodeAgent(
        tools=[CalculatorTool()],
        model=model,
        max_steps=5,
        verbosity_level=2
    )

    # Run a simple task
    task = "What is 15 multiplied by 8, then add 42 to the result?"

    print(f"Task: {task}\n")
    result = agent.run(task)

    print("\n" + "="*60)
    print("Result:", result)
    print("="*60)

    print("\n✅ Test complete!")
    print("📊 Check Langfuse UI at localhost:3069 for traces\n")


if __name__ == "__main__":
    main()
