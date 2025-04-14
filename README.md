# AGI SDK

A simple SDK for benchmarking AI agents across different browser automation methods.

## Installation

```bash
pip install agisdk
```

## Features

- Multiple browser automation options:
  - **Playwright**: High-level browser automation with the Playwright API
  - **CDP (Chrome DevTools Protocol)**: Low-level browser automation using WebSockets
- Task-based evaluation system
- Caching to avoid redundant runs
- Parallel execution of tasks
- Automated task result collection and evaluation

## Prerequisites

- For Playwright: `pip install playwright && playwright install`
- For CDP: Chromium must be installed on your system

## Usage

### Playwright Agent

```python
from agisdk import EvalHarness

def my_playwright_agent(prompt, browser, max_steps, task_dir):
    """
    Args:
        prompt: Task description
        browser: Playwright browser object
        max_steps: Maximum number of steps allowed
        task_dir: Directory for task-specific artifacts

    Returns:
        String containing the agent's response
    """
    # Get access to the browser's contexts and pages
    context = browser.contexts[0]  # Get the first browser context
    page = context.pages[0]  # Get the first page in the context

    # Save screenshots if task_dir is provided
    if task_dir:
        import os
        os.makedirs(task_dir, exist_ok=True)
        page.screenshot(path=f"{task_dir}/screenshot.png")

    # Implement browser automation with the Playwright API
    page.goto("https://example.com")
    page.fill("input#search", "my query")
    page.click("button[type=submit]")

    # You can create additional pages if needed
    new_page = context.new_page()
    new_page.goto("https://another-example.com")

    # Return information extracted from the page
    return "Extracted information: Page title is Example Domain"

# Initialize with Playwright
harness = EvalHarness(
    agent_fn=my_playwright_agent,
    type="playwright",
    max_steps=25,
    headless=False  # Set to True to run in headless mode
)

harness.run(
    local=True,
    use_cache=True,
    dir="./results",
    tasks="all",
    parallel=True,
    num_workers=4
)
```

### CDP Agent (Chrome DevTools Protocol)

```python
from agisdk import EvalHarness

def my_cdp_agent(prompt, cdp_url, max_steps, task_dir):
    """
    Args:
        prompt: Task description
        cdp_url: WebSocket URL for CDP connection
        max_steps: Maximum number of steps allowed
        task_dir: Directory for task-specific artifacts

    Returns:
        String containing the agent's response with extracted information
    """
    import json
    import websocket

    # Log artifacts if task_dir is provided
    if task_dir:
        import os
        os.makedirs(task_dir, exist_ok=True)
        with open(f"{task_dir}/task_info.txt", "w") as f:
            f.write(f"Prompt: {prompt}\nCDP URL: {cdp_url}\nMax Steps: {max_steps}")

    # Connect to Chrome via CDP WebSocket
    ws = websocket.create_connection(cdp_url)

    # Navigate to a URL
    navigate_cmd = {
        "id": 1,
        "method": "Page.navigate",
        "params": {
            "url": "https://example.com"
        }
    }
    ws.send(json.dumps(navigate_cmd))
    response = ws.recv()

    # Extract information from the page
    cmd = {
        "id": 2,
        "method": "Runtime.evaluate",
        "params": {
            "expression": "document.title",
            "returnByValue": True
        }
    }
    ws.send(json.dumps(cmd))
    result = json.loads(ws.recv())
    page_title = result.get("result", {}).get("result", {}).get("value", "")

    ws.close()
    return f"Extracted page title: {page_title}"

# Initialize with CDP
harness = EvalHarness(
    agent_fn=my_cdp_agent,
    type="cdp",
    max_steps=25,
    headless=False  # Set to True to run in headless mode
)

harness.run(
    local=True,
    use_cache=True,
    dir="./results",
    tasks="all",
    parallel=True,
    num_workers=4
)
```

## Configuration

The `EvalHarness` accepts the following parameters:

- `agent_fn`: Your agent implementation (function)
- `type`: Automation type - "playwright", "cdp", or "url"
- `max_steps`: Maximum steps per task
- `headless`: Whether to run browsers in headless mode (default: False)

The `run` method accepts:

- `local`: Run locally (Boolean)
- `use_cache`: Use cached results if available (Boolean)
- `dir`: Output directory for results
- `tasks`: List of specific tasks or "all" for all tasks
- `parallel`: Run tasks in parallel (Boolean)
- `num_workers`: Number of parallel workers

## Agent Function Parameters

Your agent function will receive the following parameters:

- `prompt`: The task description to be completed
- `browser` or `cdp_url`: Depending on the harness type:
  - For "playwright": A Playwright browser instance
  - For "cdp": A CDP URL for connecting to Chrome
- `max_steps`: Maximum number of steps allowed
- `task_dir`: Directory for saving task-specific artifacts

The CDP mode allows connecting any automation library that can interface with Chrome DevTools Protocol. For example, libraries like browser-use, pyppeteer, or custom implementations can be integrated for advanced automation and evaluation.

## Evaluation

After running tasks, results are stored as JSON files in the specified directory. Each result includes:

- Success status
- Error information (if any)
- Score
- Agent response with task-specific information
- Task state information
