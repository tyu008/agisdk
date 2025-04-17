import os
import glob
import random
import json
import time
import dataclasses
import logging
import tempfile
import shutil
from typing import List, Dict, Optional, Any, Union, Literal, Tuple, Type
from pathlib import Path
from statistics import mean, median, stdev
import multiprocessing as mp
from functools import partial

# Ensure tempfile is accessible in all scopes, including those that use
# multiprocessing which might not properly inherit imported modules
import tempfile as tempfile_module
tempfile = tempfile_module

from agisdk.real.browsergym.experiments import Agent, AbstractAgentArgs, EnvArgs, ExpArgs, get_exp_result


class Harness:
    def __init__(
        self,
        agentargs: None,
        leaderboard: bool = False,
        ):
        print("Harness initialized.")


# Worker initialization function for multiprocessing
def init_worker():
    global tempfile
    import tempfile

logger = logging.getLogger(__name__)

def run_tasks(
    tasks: List[str],
    agent_args: AbstractAgentArgs,
    env_args_dict: Dict[str, Any],
    results_dir: str = "./results",
    parallel: bool = False,
    num_workers: int = 5,
    continue_previous: bool = False,
) -> Dict[str, Any]:
    """
    Run tasks with the provided agent and environment configuration.
    
    Args:
        tasks: List of task names to run
        agent_args: Arguments for the agent
        env_args_dict: Dictionary of arguments for the environment
        results_dir: Directory to store results
        parallel: Whether to run tasks in parallel
        num_workers: Number of workers to use for parallel execution
        continue_previous: Whether to try to continue from previous runs
        
    Returns:
        Dictionary of results indexed by task name
    """
    # Generate a unique run ID for this batch
    import uuid
    from datetime import datetime
    run_uuid = str(uuid.uuid4())
    run_timestamp = datetime.now().isoformat()
    print(f"Running multiple tasks with ID: {run_uuid}")
    # Store run metadata for tracking
    run_metadata = {
        "run_uuid": run_uuid,
        "run_timestamp": run_timestamp,
        "agent_type": agent_args.agent_name if hasattr(agent_args, "agent_name") else type(agent_args).__name__,
        "model_name": getattr(agent_args, "model_name", "unknown"),
        "total_tasks": len(tasks)
    }
    
    print(f"Starting run with ID: {run_uuid}")
    
    # Initialize results dictionary
    results = {}
    
    # Determine which tasks need to be run
    tasks_to_run = []
    
    for task_name in tasks:
        # Try to find a cached result
        cached_result = find_cached_result(task_name, agent_args, env_args_dict, results_dir)
        
        if cached_result:
            # Use cached result
            print(f"Using cached result for {task_name} from {cached_result.get('exp_dir', 'unknown')}")
            results[task_name] = cached_result
            # Need to run this task
        else:
            tasks_to_run.append(task_name)
    
    # Run tasks if needed
    if tasks_to_run:
        print(f"Running {len(tasks_to_run)} tasks...")
        
        if parallel:
            # Create a partial function with the fixed arguments
            run_task_partial = partial(
                run_single_task,
                agent_args=agent_args,
                env_args_dict=env_args_dict,
                results_dir=results_dir,
                continue_previous=continue_previous,
                run_uuid=run_uuid
            )
            
            # Run tasks in parallel using multiprocessing
            with mp.Pool(processes=num_workers, initializer=init_worker) as pool:
                new_results = dict(pool.map(run_task_partial, tasks_to_run))
                
                # Merge with cached results
                results.update(new_results)
        else:
            # Run tasks sequentially
            for task_name in tasks_to_run:
                task_name, exp_record = run_single_task(
                    task_name=task_name,
                    agent_args=agent_args,
                    env_args_dict=env_args_dict,
                    results_dir=results_dir,
                    continue_previous=continue_previous,
                    run_uuid=run_uuid
                )
                results[task_name] = exp_record
    
    # Gather statistics for this run using the run_uuid
    cache_hits = len(tasks) - len(tasks_to_run)
    
    # Find all experiments with this run_uuid to count errors
    exps_with_errors = 0
    total_exps = 0
    
    for exp_dir in find_experiment_dirs(results_dir):
        # Extract experiment info
        info = get_experiment_info(exp_dir)
        
        # If we can't extract info, skip this directory
        if info is None:
            continue
            
        # Count only experiments from this run
        if info.get("run_uuid") == run_uuid:
            total_exps += 1
            
            # Check for errors
            if info.get("err_msg") is not None or info.get("stack_trace") is not None:
                exps_with_errors += 1
    
    # Print statistics
    print("\nRun Statistics:")
    print(f"  Run UUID: {run_uuid}")
    print(f"  Total tasks: {len(tasks)}")
    print(f"  From cache: {cache_hits}")
    print(f"  Newly executed: {len(tasks_to_run)}")
    print(f"  Tasks with errors: {exps_with_errors} of {total_exps} ({exps_with_errors/total_exps*100 if total_exps > 0 else 0:.1f}%)")
    
    return results


def run_single_task(
    task_name: str,
    agent_args: AbstractAgentArgs,
    env_args_dict: Dict[str, Any],
    results_dir: str,
    continue_previous: bool = False,
    use_cache: bool = True,
    run_uuid: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Run a single task with the provided agent and environment configuration.
    
    Args:
        task_name: Name of the task to run
        agent_args: Arguments for the agent
        env_args_dict: Dictionary of arguments for the environment
        results_dir: Directory to store results
        continue_previous: Whether to try to continue from a previous run
        use_cache: Whether to update the cache with results
        run_uuid: Optional UUID for tracking this run batch
        
    Returns:
        Tuple of (task_name, results_dict)
    """
    print(f"Running task: {task_name}")
    
    # Set task name in env args
    env_args_dict["task_name"] = task_name
    
    # Create EnvArgs from dictionary
    env_args = EnvArgs(**env_args_dict)
    
    # Set up experiment
    exp_args = ExpArgs(
        env_args=env_args,
        agent_args=agent_args
    )
    
    # Start timing
    start_time = time.time()
    
    # Run experiment
    exp_args.prepare(results_dir)
    
    # Add essential metadata to summary_info.json before running the experiment
    # This ensures the cache has what it needs even if there's a crash
    summary_info_path = Path(exp_args.exp_dir) / "summary_info.json"
    
    # Extract metadata for cache key
    agent_type = agent_args.agent_name if hasattr(agent_args, "agent_name") else type(agent_args).__name__
    model_name = getattr(agent_args, "model_name", "unknown")
    max_steps = env_args.max_steps
    
    # Create initial summary info with metadata
    initial_summary = {
        "task_name": task_name,
        "agent_type": agent_type,
        "model_name": model_name,
        "max_steps": max_steps,
        "cache_key": f"{task_name}_{agent_type}_{model_name}_{max_steps}",
        "experiment_status": "started",
        "run_uuid": run_uuid,  # Add the run UUID for tracking
    }
    
    # Write initial summary info
    with open(summary_info_path, "w") as f:
        json.dump(initial_summary, f, indent=4)
    
    # Run the experiment
    exp_args.run()
    
    # End timing
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Get results
    exp_result = get_exp_result(exp_args.exp_dir)
    exp_record = exp_result.get_exp_record()
    
    # Add timing information to the record
    exp_record['elapsed_time'] = elapsed_time
    
    # Add experiment directory to the record
    exp_record['exp_dir'] = str(exp_args.exp_dir)
    
    # Print current task result
    print(f"Task: {task_name}")
    print(f"  Reward: {exp_record.get('cum_reward', 0)}")
    success = exp_record.get('cum_reward', 0) == 1
    print(f"  Success: {success}")
    print(f"  Time: {elapsed_time:.2f} seconds")
    
    return task_name, exp_record

def find_cached_result(task_name: str, agent_args: AbstractAgentArgs, env_args_dict: Dict[str, Any], 
                      results_dir: str) -> Optional[Dict[str, Any]]:
    """
    Find a cached result for the given task and agent configuration.
    
    Args:
        task_name: Name of the task
        agent_args: Arguments for the agent
        env_args_dict: Dictionary of arguments for the environment
        results_dir: Directory containing experiment results
        
    Returns:
        The cached result or None if not found or if the result contains errors
    """
    # Create cache key
    cache_key = create_cache_key(task_name, agent_args, env_args_dict)
    
    # Find all experiment directories
    exp_dirs = find_experiment_dirs(results_dir)
    
    # Filter by cache key
    matching_exps = []
    
    for exp_dir in exp_dirs:
        # Extract experiment info
        info = get_experiment_info(exp_dir)
        
        # If we can't extract info, skip this directory
        if info is None:
            continue
        
        # Check if this experiment matches our cache key
        if info.get("cache_key") == cache_key:
            matching_exps.append(info)
    
    # If no matching experiments, return None
    if not matching_exps:
        return None
    
    # Sort by timestamp (newest first)
    matching_exps.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    # Get the most recent experiment
    result = matching_exps[0]
    
    # Check if the result has errors
    has_error = (result.get("err_msg") is not None or 
                result.get("stack_trace") is not None)
    
    # Always skip results with errors
    if has_error:
        print(f"Skipping cached result for {task_name} due to errors, will rerun")
        return None
        
    return result


def create_cache_key(task_name: str, agent_args: AbstractAgentArgs, env_args_dict: Dict[str, Any]) -> str:
    """
    Create a unique cache key for a task-agent-env combination.
    
    Args:
        task_name: Name of the task
        agent_args: Arguments for the agent
        env_args_dict: Dictionary of arguments for the environment
        
    Returns:
        A string key for the cache
    """
    # Extract core agent info for the cache key
    agent_model = getattr(agent_args, "model_name", "unknown")
    agent_type = agent_args.agent_name if hasattr(agent_args, "agent_name") else type(agent_args).__name__
    
    # Extract core environment settings
    max_steps = env_args_dict.get("max_steps", "default")
    
    # Create a reproducible cache key
    cache_key = f"{task_name}_{agent_type}_{agent_model}_{max_steps}"
    
    return cache_key

def find_experiment_dirs(results_dir: str) -> List[Path]:
    """
    Find all experiment directories in the results directory.
    
    Args:
        results_dir: Directory containing experiment results
        
    Returns:
        List of experiment directory paths
    """
    results_path = Path(results_dir)
    
    # Experiment directories are identified by the presence of summary_info.json
    exp_dirs = []
    
    # Walk through all directories in results_dir
    for root, dirs, files in os.walk(results_dir):
        root_path = Path(root)
        
        # Check if this directory has the required files to be an experiment directory
        if "summary_info.json" in files:
            exp_dirs.append(root_path)
    
    return exp_dirs

def get_experiment_info(exp_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Extract information about an experiment from its directory.
    
    Args:
        exp_dir: Path to experiment directory
        
    Returns:
        Dictionary with experiment information, or None if info can't be extracted
    """
    try:
        # Get modification time as timestamp
        timestamp = os.path.getmtime(exp_dir / "summary_info.json")
        
        # Load summary info
        with open(exp_dir / "summary_info.json", "r") as f:
            summary_info = json.load(f)
        
        # Extract relevant information directly from summary_info.json
        task_name = summary_info.get("task_name")
        agent_type = summary_info.get("agent_type")
        model_name = summary_info.get("model_name", "unknown")
        max_steps = summary_info.get("max_steps")
        
        # Create complete info dict
        info = {
            "task_name": task_name,
            "agent_type": agent_type,
            "model_name": model_name,
            "max_steps": max_steps,
            "timestamp": timestamp,
            "exp_dir": str(exp_dir),
            "cache_key": f"{task_name}_{agent_type}_{model_name}_{max_steps}",
        }
        
        # Add any other summary information
        info.update(summary_info)
        
        return info
    except Exception as e:
        print(f"Warning: Failed to extract info from {exp_dir}: {e}")
        return None
