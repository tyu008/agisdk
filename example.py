import gymnasium as gym
from agisdk.real.browsergym import webclones


# Choose a specific webclones task
env = gym.make(
    "browsergym/webclones.omnizon-1",  # Or any other available webclones task
    headless=False,  # Show browser for visualization
    wait_for_user_message=False,  # Set to True if you want interactive mode
)

obs, info = env.reset()
done = False; step_count = 0; max_steps = 4 

while not done:
    # Choose appropriate action based on current state
    if step_count < max_steps - 1:
        action = 'click("0")'  # Click on element with ID 0
    else:
        action = 'send_msg_to_user("I have completed the task successfully!")'    
    step_count += 1
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Observations: {obs.keys()}") # dict_keys(['chat_messages', 'goal', 'goal_object', 'open_pages_urls', 'active_page_index', 'url', 'screenshot', 'dom_object', 'axtree_object', 'extra_element_properties', 'focused_element_bid', 'last_action', 'last_action_error', 'elapsed_time', 'browser'])    
    done = terminated or truncated

env.close()
print("Environment closed")