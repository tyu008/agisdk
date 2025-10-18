#!/usr/bin/env python3

# A minimal agent that you can modify to suit your needs. 
# Custom agent classes are in custom_agent.py to avoid Ray pickling issues
import argparse
import logging

from agisdk import REAL
from agisdk.REAL.demo_agent.run_demo import str2bool
from custom_agent import DemoAgentArgs  # Import from separate module to allow Ray pickling

logger = logging.getLogger(__name__)


def run_demo_agent(model_name="gpt-4o", task_type="omnizon", headless=False, leaderboard=False, run_id=None, workers=1):
    """Run a test with the DemoAgent on a browsergym task."""
    logger.info(f"Starting DemoAgent test with model: {model_name} on task: {task_type}")
    
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
        task_type=task_type,
        headless=headless,
        max_steps=25,
        use_axtree=agent_args.use_axtree,
        use_screenshot=agent_args.use_screenshot,
        leaderboard=leaderboard,
        run_id=run_id,
        num_workers=workers,
    )
    
    logger.info("Running task...")
    results = harness.run()
    
    logger.info("Task completed")
    logger.info(f"Results: {results}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run DemoAgent on browsergym tasks")
    parser.add_argument("--model", type=str, default="gpt-4o",
                        help="Model to use with the agent (default: gpt-4o)")
    parser.add_argument("--task_type", type=str, default="omnizon",
                        help="Task to run (default: omnizon)")
    parser.add_argument("--headless", type=str2bool, default=False,
                        help="Run headless (default: False)")
    parser.add_argument("--run_id", type=str, default=None,
                        help="Run ID for leaderboard submission (required for leaderboard)")
    parser.add_argument("--leaderboard", type=str2bool, default=False,
                        help="Submit results to leaderboard (default: False)")

    parser.add_argument("--workers", type=int, default=1,
                        help="Number of workers to use (default: 1)")
    
    args = parser.parse_args()
    
    results = run_demo_agent(
        model_name=args.model, 
        task_type=args.task_type, 
        headless=args.headless,
        leaderboard=args.leaderboard,
        run_id=args.run_id,
        workers=args.workers
    )
