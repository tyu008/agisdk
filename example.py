from agisdk import EvalHarness

def my_agent(prompt, playwright_object):
    """
    Example agent implementation.
    
    Args:
        prompt: Task description
        playwright_object: Playwright browser instance or URL, depending on harness type
        
    Returns:
        String containing the agent's response
    """
    print(f"Agent received prompt: {prompt}")
    input("Press Enter to continue...")
    # In a real implementation, this would use the playwright_object to interact with a browser
    return "Task completed successfully"

# Initialize the evaluation harness
harness = EvalHarness(
    agent_fn=my_agent,
    type="playwright",
    max_steps=25
)

# Run the evaluation
results = harness.run(
    local=True,
    use_cache=True,
    dir="./results",
    tasks="all",
    paralel=True,
    num_workers=4
)

# Show the results
# results.show()

# You can also save the results to a file
# results.save("./results/summary.json")