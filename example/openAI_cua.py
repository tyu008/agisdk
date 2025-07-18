from __future__ import annotations

import argparse
import base64
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

import requests  # pip install requests
from openai import OpenAI, OpenAIError
from playwright.sync_api import sync_playwright, Error as PlaywrightError

from agisdk.REAL.tasks import all_tasks as tasks  # noqa – provided by agisdk
from agisdk.REAL.browsergym.webclones.evaluate import WebCloneEvaluator
from agisdk.REAL.browsergym.webclones.task_config import TaskConfig
from agisdk.REAL.logging import logger as rich_logger



################################################################################
# Minimal Playwright “computer”
################################################################################


class PlaywrightComputer:
    def __init__(self, w: int = 1024, h: int = 768, headless: bool = True):
        self.w, self.h = w, h
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=headless, args=[f"--window-size={w},{h}"])
        self.ctx = self.browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
        self.page = self.ctx.new_page()

    # ---------------------------------------------------------------- Tools
    def screenshot_b64(self) -> str:
        return base64.b64encode(self.page.screenshot(full_page=False)).decode()

    def _clamp(self, x: float, y: float):
        return max(0, min(x, self.w - 1)), max(0, min(y, self.h - 1))

    def click(self, x: float, y: float, button: str = "left"):
        x, y = self._clamp(x, y)
        self.page.mouse.click(x, y, button=button)

    def double_click(self, x: float, y: float, button: str = "left"):
        x, y = self._clamp(x, y)
        self.page.dblclick(x, y, button=button)

    def scroll(self, start_x: float, start_y: float, dx: float, dy: float):
        start_x, start_y = self._clamp(start_x, start_y)
        self.page.mouse.move(start_x, start_y)
        self.page.mouse.wheel(dx, dy)

    def type(self, text: str, delay: int = 20):
        self.page.keyboard.type(text, delay=delay)

    def keypress(self, keys: List[str]):
        # Map common key names to Playwright format
        key_mapping = {
            "HOME": "Home",
            "END": "End",
            "PAGE_UP": "PageUp",
            "PAGE_DOWN": "PageDown",
            "ARROW_UP": "ArrowUp",
            "ARROW_DOWN": "ArrowDown",
            "ARROW_LEFT": "ArrowLeft",
            "ARROW_RIGHT": "ArrowRight",
            "ENTER": "Enter",
            "ESCAPE": "Escape",
            "TAB": "Tab",
            "SPACE": "Space",
            "BACKSPACE": "Backspace",
            "DELETE": "Delete",
            "CTRL": "Control",
            "ALT": "Alt",
            "SHIFT": "Shift",
            "META": "Meta"
        }
        
        mapped_keys = [key_mapping.get(key, key) for key in keys]
        self.page.keyboard.press("+".join(mapped_keys))

    def wait(self, ms: int):
        self.page.wait_for_timeout(ms)

    def move(self, x: float, y: float):
        x, y = self._clamp(x, y)
        self.page.mouse.move(x, y)

    def drag(self, start_x: float, start_y: float,
             end_x: float, end_y: float,
             button: str = "left"):
        start_x, start_y = self._clamp(start_x, start_y)
        end_x, end_y = self._clamp(end_x, end_y)
        self.page.mouse.move(start_x, start_y)
        self.page.mouse.down(button=button)
        self.page.mouse.move(end_x, end_y)
        self.page.mouse.up(button=button)

    # Convenience
    def goto(self, url: str):
        self.page.goto(url, wait_until="load", timeout=30000)

    # Clean-up
    def close(self):
        with suppress(Exception):
            self.ctx.close(); self.browser.close(); self._pw.stop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

################################################################################
# Runner
################################################################################

MODEL = "computer-use-preview"
WIDTH = 1024
HEIGHT = 768
ITER_LIMIT = 40
TIME_LIMIT = 300  # seconds per task

client = OpenAI()


def run_task(task: Dict[str, Any], run_id: str, headless: bool) -> Dict[str, Any]:
    tid = task["id"]
    goal = task["goal"]
    base = task["website"]["url"]
    cfg_url = f"{base}/config?run_id={run_id}&task_id={tid}&removePopup=true"

    # Start task logging
    rich_logger.task_start(f"{tid}: {goal[:50]}{'...' if len(goal) > 50 else ''}", "OpenAI-CUA")

    res: Dict[str, Any] = {
        "task_id": tid,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "ok": False,
        "success": False,
        "error": None,
        "response": None,
        "elapsed_time": 0.0,
        "actions_taken": [],
        "iterations": 0,
    }
    wall0 = time.time()

    try:
        with PlaywrightComputer(WIDTH, HEIGHT, headless=headless) as comp:
            comp.goto(cfg_url)
            comp.goto(base)

            pending_safety: List[str] = []
            last_call_id: Optional[str] = None

            # ------------------ loop
            for it in range(ITER_LIMIT):
                res["iterations"] = it + 1
                if time.time() - wall0 > TIME_LIMIT:
                    rich_logger.warning(f"Task {tid} hit time limit ({TIME_LIMIT}s)")
                    raise TimeoutError("time budget exceeded")

                if it == 0:
                    input_payload = [
                        {"role": "user", "content": goal},
                    ]
                    prev_id = None
                else:
                    # send screenshot as computer_call_output
                    try:
                        screenshot_b64 = comp.screenshot_b64()
                        input_payload = [
                            {
                                "call_id": last_call_id,
                                "type": "computer_call_output",
                                "output": {
                                    "type": "input_image",
                                    "image_url": f"data:image/png;base64,{screenshot_b64}",
                                },
                                **({"acknowledged_safety_checks": pending_safety} if pending_safety else {}),
                            }
                        ]
                    except PlaywrightError as pe:
                        rich_logger.error(f"Failed to take screenshot: {pe}")
                        raise RuntimeError("Browser context closed during screenshot") from pe
                    prev_id = resp.id  # defined below

                try:
                    resp = client.responses.create(
                        model=MODEL,
                        previous_response_id=prev_id,
                        tools=[
                            {
                                "type": "computer_use_preview",
                                "display_width": WIDTH,
                                "display_height": HEIGHT,
                                "environment": "browser",
                            }
                        ],
                        input=input_payload,
                        truncation="auto",
                    )
                except OpenAIError as e:
                    raise RuntimeError(f"OpenAI error: {e}") from e

                # Handle outputs
                comp_calls = [o for o in resp.output if o.type == "computer_call"]
                if comp_calls:
                    for call in comp_calls:
                        act = call.action
                        last_call_id = call.call_id
                        
                        # Log the action being taken
                        action_summary = f"{act.type}"
                        if act.type == "click":
                            action_summary += f"({act.x}, {act.y})"
                        elif act.type == "type":
                            action_summary += f"({act.text[:30]}{'...' if len(act.text) > 30 else ''})"
                        elif act.type == "scroll":
                            action_summary += f"(scroll)"
                        elif act.type == "move":
                            action_summary += f"({act.x}, {act.y})"
                        elif act.type == "drag":
                            if hasattr(act, 'path') and act.path:
                                try:
                                    # Try to access path as list first
                                    if hasattr(act.path, '__getitem__'):
                                        start_point = act.path[0]
                                        end_point = act.path[-1]
                                        action_summary += f"({start_point['x']}, {start_point['y']}) -> ({end_point['x']}, {end_point['y']})"
                                    else:
                                        # Handle ActionDragPath object
                                        action_summary += f"(drag path)"
                                except (TypeError, IndexError, KeyError):
                                    action_summary += "(drag - invalid path)"
                            else:
                                action_summary += "(drag - no path)"
                        
                        rich_logger.task_step(it + 1, action_summary)
                        res["actions_taken"].append({"step": it + 1, "action": action_summary})
                        
                        # Execute tool call
                        try:
                            if act.type == "click":
                                comp.click(act.x, act.y, getattr(act, "button", "left"))
                            elif act.type == "double_click":
                                comp.double_click(act.x, act.y, getattr(act, "button", "left"))
                            elif act.type == "scroll":
                                # Handle different scroll parameter formats
                                start_x = getattr(act, 'start_x', getattr(act, 'x', WIDTH // 2) if hasattr(act, 'x') else WIDTH // 2)
                                start_y = getattr(act, 'start_y', getattr(act, 'y', HEIGHT // 2) if hasattr(act, 'y') else HEIGHT // 2)
                                dx = getattr(act, 'dx', getattr(act, 'delta_x', 0))
                                dy = getattr(act, 'dy', getattr(act, 'delta_y', 0))
                                comp.scroll(start_x, start_y, dx, dy)
                            elif act.type == "type":
                                comp.type(act.text)
                            elif act.type == "keypress":
                                comp.keypress(act.keys)
                            elif act.type == "move":
                                comp.move(act.x, act.y)
                            elif act.type == "drag":
                                if hasattr(act, 'path') and act.path:
                                    try:
                                        # Try to access path as list first
                                        if hasattr(act.path, '__getitem__'):
                                            start_point = act.path[0]
                                            end_point = act.path[-1]
                                            button = getattr(act, 'button', 'left')
                                            comp.drag(start_point['x'], start_point['y'], end_point['x'], end_point['y'], button)
                                        else:
                                            # Handle ActionDragPath object - check for start_x, start_y, end_x, end_y attributes
                                            start_x = getattr(act.path, 'start_x', getattr(act, 'start_x', 0))
                                            start_y = getattr(act.path, 'start_y', getattr(act, 'start_y', 0))
                                            end_x = getattr(act.path, 'end_x', getattr(act, 'end_x', 0))
                                            end_y = getattr(act.path, 'end_y', getattr(act, 'end_y', 0))
                                            button = getattr(act, 'button', 'left')
                                            comp.drag(start_x, start_y, end_x, end_y, button)
                                    except (TypeError, IndexError, KeyError, AttributeError) as e:
                                        rich_logger.warning(f"Drag action failed: {e}")
                                else:
                                    rich_logger.warning("Drag action missing path data")
                            elif act.type == "wait":
                                # Handle different wait parameter formats
                                wait_time = getattr(act, 'ms', getattr(act, 'duration', getattr(act, 'seconds', 1000)))
                                comp.wait(wait_time)
                            elif act.type == "screenshot":
                                pass  # handled by next iteration’s screenshot
                        except PlaywrightError as pe:
                            rich_logger.error(f"Playwright error: {pe}")
                            continue

                        pending_safety = [sc.id for sc in call.pending_safety_checks]
                    continue  # next iteration

                # No computer_call → look for text answer
                texts = [o for o in resp.output if o.type == "text"]
                model_ans = texts[0].text if texts else ""
                res["response"] = model_ans
                break
            else:
                raise TimeoutError("iteration limit reached without final answer")

            # ------------------ evaluate
            env_state = {}
            with suppress(PlaywrightError, json.JSONDecodeError):
                pre = comp.page.query_selector("pre")
                if pre:
                    env_state = json.loads(pre.inner_text())

            ev = WebCloneEvaluator(TaskConfig(tid))
            reward, done, msg, _ = ev.evaluate(env_state=env_state, model_response=model_ans)
            rich_logger.info(f"🌍 Environment State: {json.dumps(env_state, indent=2)[:200]}...")
            rich_logger.info(f"🤖 Model Response: {model_ans[:100]}{'...' if len(model_ans) > 100 else ''}")
            
            success = bool(done and reward > 0)
            res["success"] = success
            res["ok"] = True
            res["reward"] = reward
            res["eval_message"] = msg
            
            # Log task completion
            elapsed = time.time() - wall0
            rich_logger.task_complete(success, reward, elapsed)
            
            # Save final state to base_url/final
            final_url = f"{base}/final"
            final_state = {
                "task_id": tid,
                "env_state": env_state,
                "model_response": model_ans,
                "success": success,
                "reward": reward,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            comp.goto(final_url)
            comp.page.evaluate(f"window.finalState = {json.dumps(final_state)}")

    except Exception as exc:
        res["error"] = str(exc)
        elapsed = time.time() - wall0
        rich_logger.error(f"Task {tid} failed: {exc}")
        rich_logger.task_complete(False, 0, elapsed)

    res["elapsed_time"] = time.time() - wall0
    res["end_time"] = datetime.now(timezone.utc).isoformat()
    return res

################################################################################
# CLI
################################################################################

def create_results_directory() -> Path:
    """Create results directory structure similar to agisdk."""
    results_dir = Path("/Users/pran-ker/Developer/agisdk/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped subdirectory
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = results_dir / f"openai_cua_{timestamp}"
    run_dir.mkdir(exist_ok=True)
    
    return run_dir

def save_results_to_file(results: List[Dict[str, Any]], run_dir: Path, run_name: str) -> None:
    """Save detailed results to JSON file."""
    
    # Calculate summary statistics
    successful_tasks = [r for r in results if r.get("success", False)]
    failed_tasks = [r for r in results if not r.get("ok", False)]
    
    summary = {
        "run_name": run_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": "OpenAI-CUA",
        "total_tasks": len(results),
        "successful_tasks": len(successful_tasks),
        "failed_tasks": len(failed_tasks),
        "success_rate": len(successful_tasks) / len(results) * 100 if results else 0,
        "avg_time": sum(r["elapsed_time"] for r in results) / len(results) if results else 0,
        "total_time": sum(r["elapsed_time"] for r in results),
        "tasks": results
    }
    
    # Save to JSON file
    results_file = run_dir / "results.json"
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    rich_logger.info(f"📁 Results saved to: {results_file}")
    
    # Save summary to separate file
    summary_file = run_dir / "summary.json"
    summary_only = {k: v for k, v in summary.items() if k != "tasks"}
    with open(summary_file, 'w') as f:
        json.dump(summary_only, f, indent=2)

def main() -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    default_name = f"CUA_{ts}"

    argp = argparse.ArgumentParser("Computer-Use runner")
    argp.add_argument("--filter", default="omnizon-1", help="task id to run")
    argp.add_argument("--workers", type=int, default=1)
    argp.add_argument("--no-headless", action="store_false")
    argp.add_argument("--api-key", default=os.getenv("REALEVALS_API_KEY", ""))
    argp.add_argument("--run-name", default=default_name)
    argp.add_argument("--run-id", default="aba700cf-447a-4dc7-84eb-c50ca5df78b8")
    args = argp.parse_args()

    run_id = args.run_id
    
    # Create results directory
    run_dir = create_results_directory()
    rich_logger.info(f"📁 Results directory: {run_dir}")

    if args.filter == "all":
        selected = tasks
    else:
        selected = [t for t in tasks if t["id"] == args.filter]
    rich_logger.info(f"🚀 Running {len(selected)} task(s) with {args.workers} worker(s)")

    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(run_task, t, run_id, not args.no_headless) for t in selected]
        for f in as_completed(futs):
            results.append(f.result())

    # Calculate and display summary
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("ok", False)]
    success_rate = len(successful) / len(results) * 100 if results else 0
    avg_time = sum(r["elapsed_time"] for r in results) / len(results) if results else 0
    
    # Rich logging for summary
    rich_logger.success("🎉 BENCHMARK RESULTS")
    rich_logger.info(f"Tasks completed successfully: {len(successful)}/{len(results)}")
    rich_logger.info(f"Success rate: {success_rate:.2f}%")
    rich_logger.info(f"Average time: {avg_time:.2f} seconds")
    rich_logger.info(f"Total time: {sum(r['elapsed_time'] for r in results):.2f} seconds")
    
    if failed:
        rich_logger.warning(f"Failed tasks: {len(failed)}")
        for task in failed:
            rich_logger.error(f"  - {task['task_id']}: {task.get('error', 'Unknown error')}")
    
    # Save results to file
    save_results_to_file(results, run_dir, args.run_name)


if __name__ == "__main__":
    main()
