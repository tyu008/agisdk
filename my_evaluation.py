from agisdk import EvalHarness
import os
from multiprocessing import freeze_support
from agisdk.custom_agent import your_agent

# Custom run ID to use for all tasks
CUSTOM_RUN_ID = "4259f911-99e9-4012-a2c0-d5f37b53db80"

def my_agent(prompt, browser, max_steps, task_dir):
    """
    Agent function that implements BrowserGym agent logic and works with the EvalHarness.
    
    Args:
        prompt: Task description/goal
        browser: Playwright browser instance or CDP URL
        max_steps: Maximum steps allowed
        task_dir: Directory for saving task artifacts
    """
    # Create task directory
    if task_dir:
        os.makedirs(task_dir, exist_ok=True)
    
    # Extract task_id from task_dir (it's the last part of the path)
    current_task_id = os.path.basename(task_dir) if task_dir else ""
    
    # Determine if we're using Playwright or CDP
    is_playwright = not isinstance(browser, str)
    
    try:
        if is_playwright:
            # Get the main page
            page = browser.contexts[0].pages[0]
            
            # Get the current URL and extract base URL
            current_url = page.url
            base_url = current_url.split('/config')[0] if '/config' in current_url else current_url
            
            # Configure with our specific run_id and the current task_id
            config_url = f"{base_url}/config?run_id={CUSTOM_RUN_ID}&task_id={current_task_id}"
            print(f"Configuring with URL: {config_url}")
            
            page.goto(config_url)
            import time
            time.sleep(3)  # Wait for config to apply
            
            # Navigate back to main page
            page.goto(base_url)
            time.sleep(3)  # Wait for page to load
            
            # Use the your_agent function from custom_agent.py
            print(f"Running your_agent for task: {current_task_id}")
            agent_result, agent_info = your_agent(browser, goal=prompt)
            
            # Extract the response message from agent_result
            if isinstance(agent_result, dict):
                if agent_result.get("type") == "message":
                    response = agent_result.get("content", "")
                else:
                    # For other result types, convert the result to a string
                    response = str(agent_result)
            else:
                response = str(agent_result)
                
        else:  # CDP Mode
            # Similar CDP setup as in the original code
            cdp_url = browser
            cdp_port = cdp_url.split(':')[-1]
            
            # Get list of targets
            import requests
            import websocket
            import json
            import time
            
            debug_url = f"http://localhost:{cdp_port}/json"
            targets = requests.get(debug_url).json()
            
            # Find target with WebSocket debugger URL
            target = next((t for t in targets if "webSocketDebuggerUrl" in t), None)
            if not target:
                raise Exception("No target with WebSocket debugger URL found")
            
            # Connect to the target
            ws = websocket.create_connection(target["webSocketDebuggerUrl"])
            
            # Get the current URL to determine base URL
            get_url_cmd = {
                "id": 1,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "window.location.href",
                    "returnByValue": True
                }
            }
            ws.send(json.dumps(get_url_cmd))
            url_response = json.loads(ws.recv())
            current_url = url_response.get("result", {}).get("result", {}).get("value", "")
            
            # Extract base URL
            base_url = current_url.split('/config')[0] if '/config' in current_url else current_url
            
            # Configure with our specific run_id and the current task_id
            config_url = f"{base_url}/config?run_id={CUSTOM_RUN_ID}&task_id={current_task_id}"
            print(f"Configuring with URL: {config_url}")
            
            config_cmd = {
                "id": 2,
                "method": "Page.navigate",
                "params": {
                    "url": config_url
                }
            }
            ws.send(json.dumps(config_cmd))
            ws.recv()  # Get navigation response
            time.sleep(3)  # Wait for config to apply
            
            # Navigate to main URL
            main_cmd = {
                "id": 3,
                "method": "Page.navigate",
                "params": {
                    "url": base_url
                }
            }
            ws.send(json.dumps(main_cmd))
            ws.recv()  # Get navigation response
            time.sleep(3)  # Wait for page to load
            
            # We need to close the WebSocket before the agent runs
            ws.close()
            
            # For CDP mode, since your_agent expects Playwright browser,
            # we'll use a simpler response for now
            response = f"CDP mode not fully supported for your_agent - use Playwright mode instead"
            
    except Exception as e:
        import traceback
        error_msg = f"Error in my_agent: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        response = f"Error occurred: {str(e)}"
    
    # Save the response for debugging
    with open(os.path.join(task_dir, "agent_response.txt"), "w", encoding="utf-8") as f:
        f.write(response if response is not None else "None")
    
    # Return the response - harness.py will handle submission
    return response

if __name__ == '__main__':
    freeze_support()  # For Windows compatibility
    
    # Initialize harness
    harness = EvalHarness(
        agent_fn=my_agent,
        type="playwright",  # Using Playwright mode for better custom_agent compatibility
        max_steps=25,
        headless=False  # Set True for production
    )

    # Run the evaluation on all tasks
    harness.run(
        local=True,
        use_cache=True,
        dir="./my_results",
        tasks="all",  # Run all available tasks
        parallel=False,  # Set to False initially for easier debugging
        num_workers=1
    )

    # Display results
    results = harness.show_results()
    print("\nResults summary:")
    print(f"Total tasks: {len(results.get('tasks', []))}")
    print(f"Successful tasks: {results.get('successful_tasks', 0)}")
    print(f"Failed tasks: {results.get('failed_tasks', 0)}")


#BROWSER USE WITH SONNET -> BROWER USER.PY