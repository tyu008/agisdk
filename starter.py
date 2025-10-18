from agisdk import REAL

def run_agent(api_key=None, run_name=None):
    """
    harness = REAL.harness(
        model="grok-4-fast-non-reasoning",
        headless=True,
        max_steps=25,
        use_screenshot=True,
        use_axtree=True,
        num_workers=1
    )
    """

    harness = REAL.harness(
        model="grok-4-fast-non-reasoning",       # any LLM tag
        task_type="omnizon",  # Amazon-like store
        headless=False        # watch it click in real-time!
    )
    return harness.run()

if __name__ == "__main__":
    run_agent()