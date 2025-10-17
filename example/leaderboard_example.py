import os
from agisdk import REAL

# Optional leaderboard configuration.
# Set REAL_API_KEY / REAL_RUN_ID / REAL_MODEL_NAME / REAL_RUN_NAME in your environment
# (or replace the placeholders below) to submit results to the REAL portal.
API_KEY = os.environ.get("REAL_API_KEY") or "a5e94ced11c46ca1c211a349a3df59e752e76d68157324f7c7f6697a8d12dc59"
RUN_ID = os.environ.get("REAL_RUN_ID") or "8acbb2cc-9316-4e3c-b845-957a8709f4f9"

submit_to_leaderboard = (
    API_KEY not in ("", "<YOUR_REAL_API_KEY>")
    and RUN_ID not in ("", "<YOUR_RUN_ID>")
)

harness = REAL.harness(
    model="gpt-5",
    task_version="v2",
    task_name="omnizon-2",
    headless=False,
    leaderboard=submit_to_leaderboard,
    run_id=RUN_ID if submit_to_leaderboard else None,
    api_key=API_KEY if submit_to_leaderboard else None,
    force_refresh=True,
    use_cache=False,
)

print(harness.run())
