import os
import json


def show_results(dir: str = "./results"):
    """
    Compute and display statistics from task results in the specified directory.
    
    Args:
        dir: Directory containing the results (default: "./results")
    
    Returns:
        Dict with statistics about task results
    """
    if not os.path.exists(dir):
        print(f"Results directory {dir} does not exist")
        return {}
        
    # Collect all results
    all_results = []
    for task_dir in os.listdir(dir):
        results_file = os.path.join(dir, task_dir, "results.json")
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
                    all_results.append(results)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading results for {task_dir}: {e}")
    
    if not all_results:
        print("No results found")
        return {}
        
    # Compute statistics
    total_tasks = len(all_results)
    completed_tasks = sum(1 for r in all_results if r.get('completed', False))
    successful_tasks = sum(1 for r in all_results if r.get('success', False))
    error_tasks = sum(1 for r in all_results if r.get('error', False))
    
    # Group by task type
    task_types = {}
    for result in all_results:
        task_id = result.get('task_id', '')
        if task_id:
            # Extract task type from task_id (e.g., "dashdish-1" -> "dashdish")
            task_type = task_id.split('-')[0] if '-' in task_id else task_id
            if task_type not in task_types:
                task_types[task_type] = {
                    'total': 0,
                    'completed': 0,
                    'successful': 0,
                    'error': 0
                }
            
            task_types[task_type]['total'] += 1
            if result.get('completed', False):
                task_types[task_type]['completed'] += 1
            if result.get('success', False):
                task_types[task_type]['successful'] += 1
            if result.get('error', False):
                task_types[task_type]['error'] += 1
    
    # Calculate overall success rate
    success_rate = (successful_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    error_rate = (error_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    
    # Prepare and display statistics
    stats = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'successful_tasks': successful_tasks,
        'error_tasks': error_tasks,
        'success_rate': success_rate,
        'completion_rate': completion_rate,
        'error_rate': error_rate,
        'by_task_type': task_types
    }
    
    # Print summary
    print(f"\nResults Summary ({dir}):")
    print(f"Total Tasks: {total_tasks}")
    print(f"Completed: {completed_tasks} ({completion_rate:.1f}%)")
    print(f"Successful: {successful_tasks} ({success_rate:.1f}%)")
    print(f"Errors: {error_tasks} ({error_rate:.1f}%)")
    
    print("\nResults by Task Type:")
    for task_type, data in task_types.items():
        type_success_rate = (data['successful'] / data['total']) * 100 if data['total'] > 0 else 0
        print(f"  {task_type}: {data['successful']}/{data['total']} successful ({type_success_rate:.1f}%)")
    
    return stats