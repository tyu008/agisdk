from agisdk import REAL

def run_agent(api_key=None, run_name=None):
    harness = REAL.harness(
        model="gpt-4o",
        headless=True,
        max_steps=25,
        use_screenshot=True,
        use_axtree=True,
        leaderboard=True,
        run_id="bb0362ac-f976-483c-9606-07b166dadb6e",
        num_workers=10
    )
    return harness.run()

if __name__ == "__main__":
    run_agent()