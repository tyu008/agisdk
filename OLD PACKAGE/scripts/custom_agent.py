"""
Direct Browser Agent Example

Simple pattern for integrating agents with BrowserGym:
1. Agent gets direct browser access
2. Agent controls its own execution loop
"""

import gymnasium as gym

import code

def pause_and_resume(local_vars):
    try:
        code.interact(banner="", local=local_vars)
    except SystemExit:
        pass  # Prevent exit() or Ctrl+D from killing your script

# Usage:

def your_agent(browser):
    """
    Example agent implementation.
    
    Args:
        browser: The Playwright browser object
        
    Returns:
        str: Result message
    """
    # 1. Get the page from the environment
    page = browser.contexts[0].pages[0]
    
    # 2. YOUR AGENT LOOP GOES HERE
    #    Example: Autonomous navigation
    #    title = page.title()
    #    page.click("button#submit")
    
    # For demo: Interactive mode for humans
    print("\n===== Browser Agent Demo =====")
    print("Access the page with: page = browser.contexts[0].pages[0]")
    print("Example commands:")
    print("  page.title()")
    print("  page.content()")
    print("  page.get_by_role('link', name='Navigate to Ride').click()")
    print("\nType exit() when done")
    
    # from code import interact
    # interact(banner="", local={"browser": browser, "page": page})
    pause_and_resume({"browser": browser, "page": page})

    
    # 3. Return some response text when done (some tasks may require this)
    return "Task completed successfully"


class AgentRunner(gym.Wrapper):
    """Wrapper that gives an agent direct browser control."""
    
    def __init__(self, env, agent_fn):
        super().__init__(env)
        self.agent_fn = agent_fn
        
    def step(self, action=None):
        # Run the agent (ignores action parameter)
        result = self.agent_fn(self.unwrapped.browser)
        
        # Get final observation and mark episode complete
        obs, info = self.env.reset()
        info["agent_result"] = result
        
        return obs, 0.0, True, False, info



def main():
    """Run an agent on a BrowserGym task."""
    # Create environment
    task_id = "webclones.udriver-1"
    base_env = gym.make(f"browsergym/{task_id}", headless=False)
    
    # Wrap with agent runner
    env = AgentRunner(base_env, your_agent)
    
    # Run the agent
    print(f"Running agent on {task_id}...")
    env.reset()
    _, _, _, _, info = env.step()
    
    print(f"Result: {info.get('agent_result')}")
    env.close()


if __name__ == "__main__":
    main()