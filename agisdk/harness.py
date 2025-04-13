from typing import Callable, Literal, Optional, Union, List, Dict, Any
import os
import importlib.resources
import json
from .eval import check_evals
from cdp_utils import launch_chromium

# Import optional Playwright utilities
try:
    from .playwright_utils import (
        setup_playwright, cleanup_playwright, get_finish_json, PLAYWRIGHT_AVAILABLE
    )
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class EvalHarness:
    def __init__(self, 
                 agent_fn: Callable[[str, Any], str],
                 type: Literal["url", "playwright", "cdp"] = "playwright",
                 max_steps: int = 25):
        """
        Initialize the evaluation harness.
        
        Args:
            agent_fn: Function that implements the agent logic
            type: Type of harness to use (url, playwright, cdp)
            max_steps: Maximum number of steps allowed per task
        """
        self.agent_fn = agent_fn
        self.type = type
        self.max_steps = max_steps
        
    def run(self,
            local: bool = True,
            use_cache: bool = True,
            dir: str = "./results",
            tasks: Union[Literal["all"], List[str]] = "all",
            paralel: bool = True,
            num_workers: int = 4):
        """Run evaluation harness on tasks."""
        self.results_dir = dir
        self.use_cache = use_cache
        os.makedirs(dir, exist_ok=True)
        
        # Load all tasks
        all_tasks = []
        tasks_dir = importlib.resources.files("agisdk.tasks")
        for task_json in tasks_dir.iterdir():
            if task_json.name.endswith('.json'):
                obj = json.loads(task_json.read_text())
                all_tasks.append(obj)            
        
        # Run tasks
        for task in all_tasks:
            self.run_task(task)
        print("done")
                        
    def run_task(self, task_obj):
        """Run a single task and return success status and details."""
        task_id = task_obj['id']
        print(f"Running task {task_id}")
        
        # Create task directory
        task_dir = os.path.join(self.results_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)
        
        # Path to results file
        results_file = os.path.join(task_dir, "results.json")
        
        # Check if we can use cached results
        if self.use_cache and os.path.exists(results_file):
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                # Check if task completed successfully with no errors
                if results.get('completed', False) and not results.get('error'):
                    print(f"Using cached results for task {task_id}")
                    return [results.get('success', False), results]
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading cache for {task_id}: {e}")
                # Continue with execution if cache read fails
        task_result = {
            "completed": False,
            "success": False,
            "error": None,
            "score": 0.0,
            "task_id": task_id
        }

        if self.type == "playwright":
            if not PLAYWRIGHT_AVAILABLE:
                raise ImportError("Playwright is not available. Please install it.")
            
            
            # Get task website details
            base_url = task_obj['website']['url']
            
            try:
                # Setup Playwright
                browser, context, main_page, background_page = setup_playwright(
                    task_id=task_id,
                    base_url=base_url,
                    run_id="local",
                    headless=False,
                )
            except Exception as e:
                print(f"Error setting up Playwright: {e}")
                task_result["env_setup_error"] = str(e)
                task_result["error"] = True
                with open(results_file, 'w') as f:
                    json.dump(task_result, f, indent=2)
                return
            
            try:
                # Run the agent function
                agent_response = self.agent_fn(task_obj['goal'], main_page)
                task_result["agent_response"] = agent_response
            except Exception as e:
                print(f"Error running agent function: {e}")
                task_result["agent_error"] = str(e)
                task_result["error"] = True
                with open(results_file, 'w') as f:
                    json.dump(task_result, f, indent=2)
                cleanup_playwright(browser, context, main_page, background_page)
                return
            try:
                finish_state, error = get_finish_json(base_url, main_page)
            except Exception as e:
                print(f"Error getting finish state: {e}")
                task_result["finish_state_error"] = str(e)
                task_result["error"] = True
                with open(results_file, 'w') as f:
                    json.dump(task_result, f, indent=2)
                cleanup_playwright(browser, context, main_page, background_page)
                return
            task_result["finish_state"] = finish_state
            eval_results = check_evals(
                task_obj['evals'],
                finish_state,
                model_response=agent_response,
            )
            task_result["eval_results"] = eval_results
            if eval_results[0]:
                task_result["success"] = True
                task_result["score"] = 1.0
            else:
                task_result["success"] = False
                task_result["score"] = 0.0
            
            task_result["completed"] = True
            task_result["error"] = False
            task_result["env_setup_error"] = None
            task_result["agent_error"] = None
            task_result["finish_state_error"] = None
            cleanup_playwright(browser, context, main_page, background_page)
        
        elif self.type == "cdp":
            # Start CDP with cdp_utils
            cdp_port, kill_cdp = launch_chromium(headless=False)
            # connect to the target with websocket
            
            # go to urls
            # start the task (pass in cdp port too)
            pass
            
        else:
            raise ValueError(f"Unsupported harness type: {self.type}")
        # For other harness types (URL, CDP)
        # For now, create a dummy result
        task_result = {
            "completed": False,
            "success": False,
            "error": True,
            "score": 1.0,
            "task_id": task_id
        }
        
        # Save results
        with open(results_file, 'w') as f:
            json.dump(task_result, f, indent=2)
        
        return [True, task_result]