from agisdk import EvalHarness
import os

def my_cdp_agent(prompt, cdp_url, max_steps, task_dir):
    """
    Example agent implementation using CDP.
    
    Args:
        prompt: Task description
        cdp_url: Chrome DevTools Protocol URL
        max_steps: Maximum number of steps allowed
        task_dir: Directory for task-specific artifacts
        
    Returns:
        String containing the agent's response with extracted information
    """
    
    print(f"Agent received prompt: {prompt}")
    print(f"Connecting to CDP URL: {cdp_url}")
    print(f"Max steps: {max_steps}")
    print(f"Task directory: {task_dir}")
    
    # Save task information if task_dir is provided
    if task_dir:
        os.makedirs(task_dir, exist_ok=True)
        with open(f"{task_dir}/agent_log.txt", "w") as f:
            f.write(f"Agent started with prompt: {prompt}\n")
            f.write(f"CDP URL: {cdp_url}\n")
            f.write(f"Max steps: {max_steps}\n")
    
    # In a real implementation, this would use CDP to interact with a browser
    # Here we would extract information from the web page
    extracted_info = "Example.com page title"
    
    return f"Extracted information: {extracted_info}"

def my_playwright_agent(prompt, browser, max_steps, task_dir):
    """
    Example agent implementation with Playwright.
    
    Args:
        prompt: Task description
        browser: Playwright browser instance
        max_steps: Maximum number of steps allowed
        task_dir: Directory for task-specific artifacts
        
    Returns:
        String containing the agent's response with extracted information
    """
    
    print(f"Agent received prompt: {prompt}")
    print(f"Browser has {len(browser.contexts)} contexts")
    print(f"Max steps: {max_steps}")
    print(f"Task directory: {task_dir}")
    
    # Access the context and pages
    if browser.contexts:
        context = browser.contexts[0]
        print(f"Context has {len(context.pages)} pages")
        
        # Take a screenshot if task_dir is provided
        if task_dir and context.pages:
            os.makedirs(task_dir, exist_ok=True)
            page = context.pages[0]
            page.screenshot(path=f"{task_dir}/screenshot.png")
    
    # In a real implementation, extract information from the web page
    extracted_info = "First search result: Example information"
    
    return f"Extracted information: {extracted_info}"


# Initialize the evaluation harness with the CDP agent
harness_cdp = EvalHarness(
    agent_fn=my_cdp_agent,
    type="cdp",
    max_steps=25,
    headless=False  # Set to True to run in headless mode
)

# Initialize the evaluation harness with the Playwright agent
harness_pw = EvalHarness(
    agent_fn=my_playwright_agent,
    type="playwright",
    max_steps=25,
    headless=False  # Set to True to run in headless mode
)

# Choose which harness to run
use_cdp = True  # Set to False to use Playwright instead

if use_cdp:
    # Run the CDP evaluation
    harness_cdp.run(
        local=True,
        use_cache=True,
        dir="./results_cdp",
        tasks="all",
        parallel=True,
        num_workers=4
    )
    
    # Show the results
    results = harness_cdp.show_results()
else:
    # Run the Playwright evaluation
    harness_pw.run(
        local=True,
        use_cache=True,
        dir="./results_pw",
        tasks="all",
        parallel=True,
        num_workers=4
    )
    
    # Show the results
    results = harness_pw.show_results()