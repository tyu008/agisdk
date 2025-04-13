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

## Prerequisites

- For Playwright: `pip install playwright && playwright install`
- For CDP: Chromium must be installed on your system

## Usage

### Playwright Agent

```python
from agisdk import EvalHarness

def my_playwright_agent(prompt, browser):
    """
    Args:
        prompt: Task description
        browser: Playwright browser object
        
    Returns:
        String containing the agent's response
    """
    # Get access to the browser's contexts and pages
    context = browser.contexts[0]  # Get the first browser context
    page = context.pages[0]  # Get the first page in the context
    
    # Implement browser automation with the Playwright API
    page.goto("https://example.com")
    page.fill("input#search", "my query")
    page.click("button[type=submit]")
    
    # You can create additional pages if needed
    new_page = context.new_page()
    new_page.goto("https://another-example.com")
    
    return "Task completed successfully"

# Initialize with Playwright
harness = EvalHarness(my_playwright_agent, type="playwright", max_steps=25)

results = harness.run(
    local=True,
    use_cache=True,
    dir="./results",
    tasks="all",
    paralel=True,
    num_workers=4
)
```

### CDP Agent (Chrome DevTools Protocol)

```python
from agisdk import EvalHarness

def my_cdp_agent(prompt, cdp_url):
    """
    Args:
        prompt: Task description
        cdp_url: WebSocket URL for CDP connection
        
    Returns:
        String containing the agent's response
    """
    import json
    import websocket
    
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
    
    # Additional browser interactions using CDP commands
    
    ws.close()
    return "Task completed successfully"

# Initialize with CDP
harness = EvalHarness(my_cdp_agent, type="cdp", max_steps=25)

results = harness.run(
    local=True,
    use_cache=True,
    dir="./results",
    tasks="all",
    paralel=True,
    num_workers=4
)
```

## Configuration

The `EvalHarness` accepts the following parameters:

- `agent_fn`: Your agent implementation (function)
- `type`: Automation type - "playwright", "cdp", or "url"
- `max_steps`: Maximum steps per task

The `run` method accepts:

- `local`: Run locally (Boolean)
- `use_cache`: Use cached results if available (Boolean)
- `dir`: Output directory for results
- `tasks`: List of specific tasks or "all" for all tasks
- `paralel`: Run tasks in parallel (Boolean)
- `num_workers`: Number of parallel workers

## Evaluation

After running tasks, results are stored as JSON files in the specified directory. Each result includes:

- Success status
- Error information (if any)
- Score
- Task responses and states