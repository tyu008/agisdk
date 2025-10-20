#!/usr/bin/env python3

# A minimal agent that you can modify to suit your needs. 
# Custom agent classes are in custom_agent.py to avoid Ray pickling issues
import argparse
import logging
import time
from datetime import timedelta

from agisdk import REAL
from agisdk.REAL.demo_agent.run_demo import str2bool
from custom_agent import DemoAgentArgs  # Import from separate module to allow Ray pickling

logger = logging.getLogger(__name__)


def run_demo_agent(model_name="gpt-4o", task_type=None, task_name=None, headless=False, leaderboard=False, run_id=None, workers=1, results_dir="./results"):
    """Run a test with the DemoAgent on a browsergym task."""
    logger.info(f"Starting DemoAgent test with model: {model_name} on task: {task_type}")
    logger.info(f"Results will be saved to: {results_dir}")
    
    # Start timing
    start_time = time.time()
    
    agent_args = DemoAgentArgs(
        model_name=model_name,
        chat_mode=False,
        demo_mode="off",
        use_html=False,
        use_axtree=True,
        use_screenshot=True,
        system_message_handling="separate"
    )
    
    harness = REAL.harness(
        agentargs=agent_args,
        task_type=task_type,  # Uncommented - now respects task_type parameter
        task_name=task_name,
        headless=headless,
        max_steps=25,
        use_axtree=agent_args.use_axtree,
        use_screenshot=agent_args.use_screenshot,
        leaderboard=leaderboard,
        run_id=run_id,
        num_workers=workers,
        results_dir=results_dir,  # Specify custom results directory
    )
    
    logger.info("Running task...")
    results = harness.run()
    
    # Calculate elapsed time
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    elapsed_time_formatted = str(timedelta(seconds=int(elapsed_seconds)))
    
    logger.info("Task completed")
    logger.info(f"Results: {results}")
    print("\n" + "="*60)
    print(f"⏱️  TOTAL RUNNING TIME: {elapsed_time_formatted}")
    print(f"⏱️  Total seconds: {elapsed_seconds:.2f}s")
    print("="*60 + "\n")
    
    return results


if __name__ == "__main__":
    #logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Run DemoAgent on browsergym tasks")
    parser.add_argument("--model", type=str, default="gpt-4o",
                        help="Model to use with the agent (default: gpt-4o)")
    parser.add_argument("--task_type", type=str, default=None, help="Task to run (default: None, run all tasks)")
    
    parser.add_argument("--task_name", type=str, default=None, help="Task name to run (default: None, run all tasks)")
    parser.add_argument("--headless", type=str2bool, default=False,
                        help="Run headless (default: False - browser visible)")
    parser.add_argument("--run_id", type=str, default=None,
                        help="Run ID for leaderboard submission (required for leaderboard)")
    parser.add_argument("--leaderboard", type=str2bool, default=False,
                        help="Submit results to leaderboard (default: False)")
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of workers to use (default: 1)")
    parser.add_argument("--results_dir", type=str, default="./results",
                        help="Directory to save results (default: ./results)")
    
    args = parser.parse_args()
    
    results = run_demo_agent(
        model_name=args.model, 
        task_type=args.task_type, 
        task_name=args.task_name,
        headless=args.headless,
        leaderboard=args.leaderboard,
        run_id=args.run_id,
        workers=args.workers,
        results_dir=args.results_dir
    )
