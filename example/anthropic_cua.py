#!/usr/bin/env python
"""
runner.py  – Benchmark Anthropic computer-use agents on REAL web-clone tasks.

Requirements
------------
pip install "scrapybara[anthropic]" agisdk requests
export SCRAPYBARA_API_KEY=<your_key>
export ANTHROPIC_API_KEY=<your_key>   # or omit → credits billed in agent-steps
"""
from __future__ import annotations
import os, json, time, argparse, urllib.parse, logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from scrapybara import Scrapybara
from scrapybara.anthropic import Anthropic
from scrapybara.tools import ComputerTool
from scrapybara.prompts import BROWSER_SYSTEM_PROMPT       

from agisdk.REAL.tasks import all_tasks as tasks          
from agisdk.REAL.browsergym.webclones.task_config import TaskConfig
from agisdk.REAL.browsergym.webclones.evaluate     import WebCloneEvaluator




# ───────────────────────────── core per-task worker ────────────────────────
def run_task(task: dict, run_id: str, model: Anthropic, 
             timeout_ms: int = 20000) -> dict:
    """
    Execute a single REAL task with Claude+Scrapybara and return result dict.
    """
    t0 = time.time()
    tid   = task["id"]
    base  = task["website"]["url"]
    goal  = task["goal"]
    cfg   = f"{base}/config?run_id={run_id}&task_id={tid}&removePopup=true"

    # Print detailed task information
    print(f"\n🚀 STARTING TASK: {tid}")
    print(f"   Website: {base}")
    print(f"   Goal: {goal}")
    print(f"   Config URL: {cfg}")
    print(f"   Model: {model.name}")
    print(f"   Run ID: {run_id}")
    print(f"   Started at: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 60)

    result = {
        "task_id": tid,
        "ok": False,
        "error": None,
        "elapsed": 0,
        "reward": None,
        "message": "",
        "env_state": None,
        "website": base,
        "goal": goal,
        "started_at": datetime.now().isoformat(),
    }

    inst = None
    try:
        # 1️⃣ spin up browser
        print(f"🌐 [{tid}] Starting browser instance...")
        client = Scrapybara()
        inst   = client.start_browser()
        print(f"✅ [{tid}] Browser started successfully")

        # Navigate to config page and let Claude complete the task
        resp = client.act(
            model  = model,
            tools  = [ComputerTool(inst)],
            system = BROWSER_SYSTEM_PROMPT,
            prompt = f"First navigate to {cfg} to configure the task, then complete this goal: {goal}. After completing the task, navigate to {base}/finish and extract the JSON from the <pre> element on that page.",
        )

        finish_resp = client.act(
            model  = model,
            tools  = [ComputerTool(inst)],
            system = BROWSER_SYSTEM_PROMPT,
            prompt = f"Navigate to {base}/finish and extract the JSON text from the <pre> element on the page. Return only the JSON content.",
        )
        
        # Try to extract JSON from the response
        try:
            env_state = json.loads(finish_resp.text)
        except (json.JSONDecodeError, TypeError):
            # If direct parsing fails, try to extract from response text
            import re
            json_match = re.search(r'\{.*\}', finish_resp.text, re.DOTALL)
            if json_match:
                env_state = json.loads(json_match.group())
            else:
                env_state = {"error": "Could not extract JSON", "response": finish_resp.text}
        result["env_state"] = env_state             # store for logs
        print(f"\n=== ENV STATE for {tid} ===")
        print(json.dumps(env_state, indent=2))

        # 5️⃣ evaluate
        evaluator = WebCloneEvaluator(TaskConfig(tid))
        reward, done, msg, _ = evaluator.evaluate(
            env_state=env_state,
            model_response=resp.text or "")
        result.update(ok=True, reward=reward, message=msg)
        print(f"=== EVAL RESULT for {tid} → {msg} (reward {reward}) ===")

    except Exception as e:
        result["error"] = str(e)
        print(f"❌ {tid}: {e}")

    finally:
        result["elapsed"] = time.time() - t0
        if inst:
            inst.stop()

    return result

# ───────────────────────────── CLI entrypoint ──────────────────────────────
def main() -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    p = argparse.ArgumentParser("Scrapybara-Claude REAL benchmark")
    p.add_argument("--filter",   default="omnizon-1",
                   help="Task id (or prefix) to run, e.g. `omnizon` for all matching")
    p.add_argument("--workers",  type=int, default=1,
                   help="Thread pool size (one browser per worker)")
    p.add_argument("--no-headless", action="store_false", dest="headless",
                   help="Disable headless mode for debugging")
    p.add_argument("--eval-api-key", default="",
                   help="REAL-Evals API key (optional)")
    p.add_argument("--run-name", default=f"Claude_run_{ts}")
    args = p.parse_args()

    model = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  # brings own key

    run_id = ""

    selected = [t for t in tasks if t["id"].startswith(args.filter)]
    print(f"{len(selected)} task(s) → {args.workers} worker(s)   run_id={run_id}")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(run_task, t, run_id, model)
                for t in selected]
        for f in as_completed(futs):
            results.append(f.result())

    # summary
    successes = [r for r in results if r["ok"]]
    avg = (sum(r["elapsed"] for r in results) / len(results)) if results else 0
    print(f"\n✓ {len(successes)}/{len(results)} succeeded   avg time {avg:.2f}s")


if __name__ == "__main__":
    main()