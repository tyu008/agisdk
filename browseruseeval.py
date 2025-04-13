import os, sys, asyncio
from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from agisdk import EvalHarness

async def browseruse_async_agent(prompt, cdp_url):
    print(f"Agent received prompt: {prompt}")
    print(f"Connecting to CDP URL: {cdp_url}")
    browser = Browser(config=BrowserConfig(headless=False, cdp_url=cdp_url))
    controller = Controller()
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=SecretStr(api_key))
    agent = Agent(task=prompt, llm=model, controller=controller, browser=browser)
    print("Agent initialized 🔥")
    
    # Run the agent and get the history
    history = await agent.run()
    print("Agent finished running 🏃🏼‍♂️")
    
    # Extract the final result from the agent's history
    final_result = history.final_result()
    
    # If no explicit final result, try to get the most relevant information
    if not final_result:
        # Get all extracted content from the history
        all_content = history.extracted_content()
        if all_content:
            # Join all extracted content with newlines
            final_result = "\n".join(all_content)
        else:
            final_result = "Done"
    
    # Clean up
    await browser.close()
    print("Browser closed 🧹")
    
    # Return the extracted information instead of just "agent finished"
    return final_result

def browseruse_agent(prompt, cdp_url):
    return asyncio.run(browseruse_async_agent(prompt, cdp_url))

harness = EvalHarness(agent_fn=browseruse_agent, type="cdp", max_steps=25)
harness.run(local=True, use_cache=True, dir="./browseruse", tasks="all", paralel=True, num_workers=4)