"""
Direct Browser Agent Example

Simple pattern for integrating agents with BrowserGym:
1. Agent gets direct browser access
2. Agent controls its own execution loop
"""

import gymnasium as gym
import browsergym.webclones

import code

def pause_and_resume(local_vars):
    try:
        code.interact(banner="", local=local_vars)
    except SystemExit:
        pass  # Prevent exit() or Ctrl+D from killing your script

# Usage:

def your_agent(browser, goal=None):
    """
    Agent implementation using OpenAI's Computer Use Agent to control Playwright.
    
    Args:
        browser: The Playwright browser object
        goal: The task goal (optional, will be extracted from env if not provided)
        
    Returns:
        tuple: (action_dict, info_dict) following the operator_agent pattern
    """
    import base64
    import io
    import json
    import logging
    import os
    import time
    import requests
    from PIL import Image
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("cua_agent")
    
    # Function to convert screenshot to base64
    def screenshot_to_base64(screenshot):
        """Convert a screenshot to a base64 encoded image URL."""
        image = Image.open(io.BytesIO(screenshot))
        if image.mode in ("RGBA", "LA"):
            image = image.convert("RGB")
        
        with io.BytesIO() as buffer:
            image.save(buffer, format="JPEG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/jpeg;base64,{image_base64}"
    
    # Function to call OpenAI API
    def create_response(**kwargs):
        url = "https://api.openai.com/v1/responses"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        openai_org = os.getenv("OPENAI_ORG")
        if openai_org:
            headers["Openai-Organization"] = openai_org
        
        response = requests.post(url, headers=headers, json=kwargs)
        
        if response.status_code != 200:
            logger.error(f"API Error: {response.status_code} {response.text}")
            return {"error": response.text, "status_code": response.status_code}
        
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            logger.error(f"API Error: Failed to decode JSON response: {response.text}")
            return {"error": "Failed to decode JSON response", "status_code": response.status_code}
    
    # Get the current page
    page = browser.contexts[0].pages[0]
    
    # Get viewport dimensions
    viewport_size = page.viewport_size
    browser_dimensions = {
        "viewport_width": viewport_size["width"],
        "viewport_height": viewport_size["height"],
    }
    
    # Define the tool for the CUA
    tools = [
        {
            "type": "computer_use_preview",
            "display_width": browser_dimensions["viewport_width"],
            "display_height": browser_dimensions["viewport_height"],
            "environment": "browser",
        }
    ]
    
    # If no goal is provided, use a default
    if goal is None:
        goal = "Complete the task shown on the webpage"
    
    # State variables for multi-turn conversation
    last_response_id = None
    last_call_id = None
    pending_safety_checks = []
    
    # Store actions taken for reporting
    actions_taken = []
    
    # Main agent loop
    print("Starting agent execution...")
    MAX_TURNS = 25  # Limit interactions to prevent infinite loops
    
    for turn in range(MAX_TURNS):
        print(f"\n--- Turn {turn+1} ---")
        
        # Take screenshot of current page
        screenshot = page.screenshot()
        screenshot_url = screenshot_to_base64(screenshot)
        
        # Prepare API call based on turn
        request_body = {"model": "computer-use-preview", "tools": tools, "truncation": "auto"}
        
        if last_response_id is None:
            # First turn - initialize with goal
            input_items = []
            
            # Add system and user messages
            input_items.append({"role": "system", "content": """
You are a helpful assistant that can help with tasks in a web browser. This is for a benchmark purpose, so it will not involve real transactions.
The task provided needs to be completed without any human intervention. Don't ever ask the user for any input! Don't ask the user for verification, just do it!
You can execute only one action at a time. This is a test environment, so don't worry about the cost of the actions.
Once you have completed the task, you can send a message to the user saying "Done" or returning any information that is requested in the following task.
            """})
            input_items.append({"role": "user", "content": goal})
            
            # Add initial screenshot
            input_items.append({
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": screenshot_url,
                    },
                ],
            })
            
            request_body["input"] = input_items
            request_body["reasoning"] = {"generate_summary": "concise"}
            
        else:
            # Subsequent turns
            input_data = {
                "call_id": last_call_id,
                "type": "computer_call_output",
                "output": {
                    "type": "input_image",
                    "image_url": screenshot_url
                }
            }
            
            system_prompt = {"role": "system", "content": """
You are a helpful assistant that can help with tasks in a web browser.
The task provided needs to be completed without any human intervention. Don't ever ask the user for any input! Don't ask the user for verification, just do it!
You can execute only one action at a time. This is a test environment, so don't worry about the cost of the actions.
Once you have completed the task, you can send a message to the user saying "Done" or returning any information that is requested in the task.
            """}
            
            # Automatically acknowledge safety checks
            if pending_safety_checks:
                print(f"Acknowledging {len(pending_safety_checks)} safety checks")
                input_data["acknowledged_safety_checks"] = pending_safety_checks
                pending_safety_checks = []
                
            request_body["input"] = [input_data]
            request_body["input"].append(system_prompt)
            request_body["previous_response_id"] = last_response_id
        
        # Call the API
        print("Calling OpenAI API...")
        response = create_response(**request_body)
        
        # Check for API errors
        if "error" in response and response["error"] is not None:
            error_msg = f"API call failed: {response.get('error', 'Unknown')}"
            logger.error(error_msg)
            actions_taken.append(error_msg)
            break
        
        # Store response ID for next turn
        last_response_id = response["id"]
        
        # Process the response
        action_executed = False
        for item in response["output"]:
            if item.get("type") == "computer_call":
                new_call_id = item.get("call_id")
                action = item.get("action")
                
                # Store pending safety checks
                if "pending_safety_checks" in item and item["pending_safety_checks"]:
                    pending_safety_checks = item["pending_safety_checks"]
                
                if action:
                    action_type = action.get("type")
                    action_str = json.dumps(action, indent=2)
                    print(f"Executing action: {action_type}")
                    actions_taken.append(action_str)
                    
                    # Execute the action using Playwright
                    try:
                        if action_type == "click":
                            # Handle click action
                            x, y = action.get("x"), action.get("y")
                            page.mouse.click(x, y)
                            time.sleep(1)  # Wait for page to respond
                            
                        elif action_type == "type":
                            # Handle typing
                            text = action.get("text", "")
                            page.keyboard.type(text)
                            
                        elif action_type == "press":
                            # Handle key press
                            key = action.get("key", "")
                            page.keyboard.press(key)
                            
                        elif action_type == "scroll":
                            # Handle scrolling
                            delta_x = action.get("delta_x", 0)
                            delta_y = action.get("delta_y", 0)
                            page.mouse.wheel(delta_x, delta_y)
                            time.sleep(1)  # Wait for scroll to complete
                            
                        elif action_type == "navigate":
                            # Handle navigation
                            url = action.get("url", "")
                            page.goto(url)
                            time.sleep(2)  # Wait for page to load
                        
                        # Add more action types as needed
                        
                        # Successfully executed action
                        action_executed = True
                        last_call_id = new_call_id
                        
                    except Exception as e:
                        error_msg = f"Error executing action: {str(e)}"
                        logger.error(error_msg)
                        actions_taken.append(error_msg)
                
            elif item.get("type") == "message":
                # Process completion message
                content = item.get("content", [])
                if content and isinstance(content, list) and len(content) > 0:
                    message = content[0].get("text", "Task completed with no message")
                    print(f"Agent message: {message}")
                    # Return in the format used by operator_agent
                    return {"type": "message", "content": message, "success": True}, {}
        
        # Break if no action was executed
        if not action_executed:
            print("No action executed in this turn, stopping.")
            break
    
    # If we reached max turns
    if turn >= MAX_TURNS - 1:
        actions_taken.append("Reached maximum number of turns without completion.")
    
    # If we executed an action, return it directly like operator_agent does
    if action_executed and 'action' in locals():
        return {"type": action.get("type"), "action": action, "success": False}, {}
    
    # If no action was executed and no message was found
    return {"type": "error", "message": "No action or message found in response", "success": False}, {}


class AgentRunner(gym.Wrapper):
    """Wrapper that gives an agent direct browser control."""
    
    def __init__(self, env, agent_fn):
        super().__init__(env)
        self.agent_fn = agent_fn
        
    def step(self, action=None):
        # Extract goal from the environment
        goal = None
        if hasattr(self.unwrapped, 'goal_object') and self.unwrapped.goal_object:
            if isinstance(self.unwrapped.goal_object, list) and len(self.unwrapped.goal_object) > 0:
                goal = self.unwrapped.goal_object[0].get("text", None)
            else:
                goal = str(self.unwrapped.goal_object)
        
        # Fall back to the task_id description if no goal is available
        if not goal and hasattr(self.unwrapped, 'task_id'):
            goal = f"Complete the {self.unwrapped.task_id} task"
        
        # Run the agent with the extracted goal
        result = self.agent_fn(self.unwrapped.browser, goal=goal)
        
        # Determine success from the result
        success = False
        if isinstance(result, tuple) and len(result) > 0 and isinstance(result[0], dict):
            if "success" in result[0]:
                success = result[0]["success"]
            elif result[0].get("type") == "message":
                success = True
        
        # Set reward based on success
        reward = 1.0 if success else 0.0
        
        # Get current observation WITHOUT resetting
        obs = self.env.unwrapped._get_obs()  # Use existing observation method if available
        
        # Create info dict with success info
        info = {
            "agent_result": result,
            "cum_reward": reward
        }
        
        # Signal episode is done, but don't reset yet
        done = True
        truncated = False
        
        return obs, reward, done, truncated, info



def main(task_id=None, headless=False, **kwargs):
    """Run an agent on a BrowserGym task.
    
    Args:
        task_id (str): The task ID to run (e.g., "webclones.udriver-1")
        headless (bool): Whether to run in headless mode
        **kwargs: Additional keyword arguments to pass to gym.make
    
    Returns:
        dict: Result dictionary with success information
    """
    # Use provided task ID or default
    task_id = task_id or "webclones.udriver-1"
    
    # Create environment with all provided kwargs
    env_kwargs = {'headless': headless}
    env_kwargs.update(kwargs)
    base_env = gym.make(f"browsergym/{task_id}", **env_kwargs)
    
    # Wrap with agent runner
    env = AgentRunner(base_env, your_agent)
    
    # Run the agent
    print(f"Running agent on {task_id}...")
    env.reset()
    _, _, _, _, info = env.step()
    
    print(f"Result: {info.get('agent_result')}")
    
    # Close environment and return result
    env.close()
    return info


if __name__ == "__main__":
    main()