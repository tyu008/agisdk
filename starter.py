import time
from datetime import timedelta
from agisdk import REAL

def run_agent(api_key=None, run_name=None, results_dir="./results"):
    """
    Run agent with custom results directory.
    
    Args:
        api_key: Optional API key for leaderboard submission
        run_name: Optional run name for leaderboard submission
        results_dir: Directory to save results (default: ./results)
    """
    # Start timing
    start_time = time.time()
    
    harness = REAL.harness(
        model="grok-4-fast-reasoning",       # any LLM tag
        task_type="omnizon",  # Amazon-like store
        headless=False,        # watch it click in real-time!
        results_dir=results_dir  # custom output directory
    )
    results = harness.run()
    
    # Calculate and print elapsed time
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    elapsed_time_formatted = str(timedelta(seconds=int(elapsed_seconds)))
    
    print("\n" + "="*60)
    print(f"⏱️  TOTAL RUNNING TIME: {elapsed_time_formatted}")
    print(f"⏱️  Total seconds: {elapsed_seconds:.2f}s")
    print("="*60 + "\n")
    
    return results

if __name__ == "__main__":
    # Change results_dir to a custom directory if needed
    run_agent(results_dir="./results")