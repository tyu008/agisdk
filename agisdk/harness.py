from typing import Callable, Literal, Optional, Union, List, Dict, Any
import os
import importlib.resources
import json
from .eval import check_evals
from .cdp_utils import launch_chromium


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
            kill_cdp, cdp_port = launch_chromium(headless=False)
            
            import requests
            import websocket
            import time
            # setup the connection and navigate to the task URL + config
            try:
                # Wait for Chrome to start up
                time.sleep(2)
                
                # Get task website details
                base_url = task_obj['website']['url']
                
                # Get the list of available targets
                debug_url = f"http://localhost:{cdp_port}/json"
                response = requests.get(debug_url)
                targets = response.json()
                
                # Find a target with WebSocket debugger URL
                target = None
                for t in targets:
                    if "webSocketDebuggerUrl" in t:
                        target = t
                        break
                
                if target is None:
                    raise Exception("No target with a WebSocket debugger URL was found.")
                
                ws_url = target["webSocketDebuggerUrl"]
                
                # Connect to the target using WebSocket
                ws = websocket.create_connection(ws_url)
                
                # Configure the task
                config_url = f"{base_url}/config?run_id=local&task_id={task_id}"
                navigate_config_cmd = {
                    "id": 1,
                    "method": "Page.navigate",
                    "params": {
                        "url": config_url
                    }
                }
                ws.send(json.dumps(navigate_config_cmd))
                ws.recv()  # Get navigation response
                
                # Wait for page to load
                time.sleep(2)
                
                # Navigate to the main task URL
                navigate_cmd = {
                    "id": 2,
                    "method": "Page.navigate",
                    "params": {
                        "url": base_url
                    }
                }
                ws.send(json.dumps(navigate_cmd))
                ws.recv()  # Get navigation response
                
                # Wait for page to load
                time.sleep(2)
            except Exception as e:
                print(f"Error setting up CDP: {e}")
                task_result["env_setup_error"] = str(e)
                task_result["error"] = True
                with open(results_file, 'w') as f:
                    json.dump(task_result, f, indent=2)
                ws.close()
                kill_cdp()
                with open(results_file, 'w') as f:
                    json.dump(task_result, f, indent=2)
                return
            
            # Run the agent function
            try:
                # Run the agent function with CDP port instead of Playwright page
                agent_response = self.agent_fn(task_obj['goal'], cdp_port)
                task_result["agent_response"] = agent_response
            except Exception as e:
                print(f"Error running agent function: {e}")
                task_result["agent_error"] = str(e)
                task_result["error"] = True
                with open(results_file, 'w') as f:
                    json.dump(task_result, f, indent=2)
                ws.close()
                kill_cdp()
                return
            
            # extract state and evals
            try:
                # Navigate to the finish endpoint
                finish_url = f"{base_url}/finish"
                finish_cmd = {
                    "id": 3,
                    "method": "Page.navigate",
                    "params": {
                        "url": finish_url
                    }
                }
                
                ws.send(json.dumps(finish_cmd))
                ws.recv()  # Get navigation response
                
                # Wait for page to load
                time.sleep(5)
                
                # Extract JSON from the page using CDP
                cmd = {
                    "id": 4,  # unique ID for this command
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": "document.documentElement.outerHTML",
                        "returnByValue": True  # ensures the HTML is returned directly as a JSON value
                    }
                }
                
                # Send the command
                ws.send(json.dumps(cmd))
                
                # Receive and parse the response
                response = ws.recv()
                result = json.loads(response)
                page_text = result.get("result", {}).get("result", {}).get("value", "")
                # get the text in the <pre></pre> tag
                import re
                match = re.search(r'<pre.*?>(.*?)</pre>', page_text, re.DOTALL)
                if match:
                    json_text = match.group(1)
                    finish_state = json.loads(json_text)
                else:
                    raise Exception("No JSON found in the <pre> tag")
            except Exception as e:
                import traceback
                import sys
                exc_type, exc_value, exc_traceback = sys.exc_info()
                trace_details = traceback.format_exception(exc_type, exc_value, exc_traceback)
                error_trace = "".join(trace_details)
                
                print(f"Error getting finish state: {e}")
                print(f"Error type: {exc_type.__name__}")
                print(f"Full traceback:\n{error_trace}")
                
                task_result["finish_state_error"] = str(e)
                task_result["error_traceback"] = error_trace
                task_result["error"] = True
                with open(results_file, 'w') as f:
                    json.dump(task_result, f, indent=2)
                ws.close()
                kill_cdp()
                with open(results_file, 'w') as f:
                    json.dump(task_result, f, indent=2)
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
            
            ws.close()
            kill_cdp()
            with open(results_file, 'w') as f:
                json.dump(task_result, f, indent=2)
            return
        
        else:
            raise ValueError(f"Unsupported harness type: {self.type}")
        # Save results
        