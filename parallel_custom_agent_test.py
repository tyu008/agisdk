from agisdk import EvalHarness
from agisdk.custom_agent import your_agent
import os
from multiprocessing import freeze_support

def harness_agent(prompt, browser, max_steps, task_dir):
    """
    Wrapper function that adapts your_agent to work with the EvalHarness.
    
    Args:
        prompt: Task description
        browser: Playwright browser instance
        max_steps: Maximum number of steps allowed
        task_dir: Directory for task-specific artifacts
    """
    # Create task directory if it doesn't exist
    if task_dir:
        os.makedirs(task_dir, exist_ok=True)
    
    # Run custom_agent with the browser instance
    result, _ = your_agent(browser, goal=prompt)
    
    # Extract the response based on result type
    if result.get("type") == "message":
        return result.get("content", "No message content")
    elif result.get("type") == "error":
        return f"Error: {result.get('message', 'Unknown error')}"
    else:
        return f"Action executed: {result.get('type', 'Unknown action')}"

# Move all execution code inside the if __name__ block
if __name__ == '__main__':
    # Add freeze_support for Windows compatibility
    freeze_support()
    
    # Initialize the harness
    harness = EvalHarness(
        agent_fn=harness_agent,
        type="playwright",
        max_steps=25,
        headless=False
    )

    # Run multiple tasks in parallel
    harness.run(
        local=True,
        use_cache=True,
        dir="./custom_agent_results",
        tasks=["udriver-1", "udriver-2", "udriver-3"],
        parallel=True,
        num_workers=3
    )

    # Show the results
    results = harness.show_results()
    print("\nResults summary:")
    print(f"Total tasks: {len(results.get('tasks', []))}")
    print(f"Successful tasks: {results.get('successful_tasks', 0)}")
    print(f"Failed tasks: {results.get('failed_tasks', 0)}") 