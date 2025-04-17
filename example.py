# from agisdk import hello_agi
# from agisdk.real.browsergym import hello

# # Basic usage with default parameter
# hello_agi()

# # Custom greeting
# hello_agi("Developer")

# # Using the real submodule
# hello()
# hello("AGI Developer")

# =====

import gymnasium as gym
import agisdk.real.browsergym.core  # register the openended task as a gym environment

env = gym.make(
    "browsergym/webclones",
    task_kwargs={},  # starting URL
    wait_for_user_message=True,  # wait for a user message after each agent message sent to the chat
)
obs, info = env.reset()
done = False
while not done:
    action = ...  # implement your agent here
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated