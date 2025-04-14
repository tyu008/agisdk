#!/usr/bin/env python3
"""
Statistics script for AGI SDK evaluation results.
Displays summary statistics for a given results directory.

Usage:
    python stats.py [results_directory]

Arguments:
    results_directory: Path to the results directory (default: "./results")
"""

import os
import sys
import json
import argparse
from tabulate import tabulate
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init()

def print_colored(text, color=Fore.WHITE, bold=False):
    """Print text with color and optional bold formatting."""
    bold_style = Style.BRIGHT if bold else ""
    print(f"{bold_style}{color}{text}{Style.RESET_ALL}")

def show_results(dir_path: str = "./results", verbose: bool = False):
    """
    Compute and display statistics from task results in the specified directory.
    
    Args:
        dir_path: Directory containing the results (default: "./results")
        verbose: Whether to show detailed information per task
        
    Returns:
        Dict with statistics about task results
    """
    if not os.path.exists(dir_path):
        print_colored(f"Results directory {dir_path} does not exist", Fore.RED, bold=True)
        return {}
        
    # Collect all results
    all_results = []
    task_details = []
    
    for task_dir in sorted(os.listdir(dir_path)):
        results_file = os.path.join(dir_path, task_dir, "results.json")
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
                    all_results.append(results)
                    
                    # Collect details for verbose output
                    task_details.append({
                        'task_id': results.get('task_id', task_dir),
                        'completed': results.get('completed', False),
                        'success': results.get('success', False),
                        'error': results.get('error', False),
                        'score': results.get('score', 0.0),
                    })
            except (json.JSONDecodeError, IOError) as e:
                print_colored(f"Error reading results for {task_dir}: {e}", Fore.YELLOW)
    
    if not all_results:
        print_colored("No results found", Fore.RED)
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
                    'error': 0,
                    'avg_score': 0.0,
                }
            
            task_types[task_type]['total'] += 1
            if result.get('completed', False):
                task_types[task_type]['completed'] += 1
            if result.get('success', False):
                task_types[task_type]['successful'] += 1
            if result.get('error', False):
                task_types[task_type]['error'] += 1
            
            # Add score to calculate average later
            task_types[task_type]['avg_score'] += result.get('score', 0.0)
    
    # Calculate averages
    for task_type, data in task_types.items():
        if data['total'] > 0:
            data['avg_score'] = data['avg_score'] / data['total']
    
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
    print_colored("\n📊 RESULTS SUMMARY", Fore.CYAN, bold=True)
    print_colored(f"📁 Directory: {os.path.abspath(dir_path)}", Fore.CYAN)
    print()
    
    # Overall statistics table
    overall_table = [
        ["Total Tasks", total_tasks],
        ["Completed", f"{completed_tasks} ({completion_rate:.1f}%)"],
        ["Successful", f"{successful_tasks} ({success_rate:.1f}%)"],
        ["Errors", f"{error_tasks} ({error_rate:.1f}%)"],
    ]
    print(tabulate(overall_table, tablefmt="simple"))
    
    # Task type statistics table
    print_colored("\n📊 RESULTS BY TASK TYPE", Fore.CYAN, bold=True)
    
    task_type_table = []
    headers = ["Task Type", "Success Rate", "Completed", "Errors", "Avg Score"]
    
    # Sort task types by success rate (highest first)
    sorted_types = sorted(
        task_types.items(), 
        key=lambda x: (x[1]['successful'] / x[1]['total'] if x[1]['total'] > 0 else 0), 
        reverse=True
    )
    
    for task_type, data in sorted_types:
        type_success_rate = (data['successful'] / data['total']) * 100 if data['total'] > 0 else 0
        
        # Color-code the success rate
        if type_success_rate >= 80:
            success_color = Fore.GREEN
        elif type_success_rate >= 50:
            success_color = Fore.YELLOW
        else:
            success_color = Fore.RED
            
        success_text = f"{data['successful']}/{data['total']} ({type_success_rate:.1f}%)"
        
        task_type_table.append([
            task_type,
            f"{success_color}{success_text}{Style.RESET_ALL}",
            f"{data['completed']}/{data['total']}",
            f"{data['error']}/{data['total']}",
            f"{data['avg_score']:.2f}",
        ])
    
    print(tabulate(task_type_table, headers=headers, tablefmt="simple"))
    
    # If verbose, show details for each task
    if verbose:
        print_colored("\n📝 TASK DETAILS", Fore.CYAN, bold=True)
        
        task_details_table = []
        headers = ["Task ID", "Status", "Success", "Error", "Score"]
        
        # Sort by task ID
        sorted_details = sorted(task_details, key=lambda x: x['task_id'])
        
        for task in sorted_details:
            # Determine status color
            if task['error']:
                status_color = Fore.RED
                status = "ERROR"
            elif task['completed']:
                status_color = Fore.GREEN
                status = "COMPLETED"
            else:
                status_color = Fore.YELLOW
                status = "INCOMPLETE"
                
            # Determine success color
            success_color = Fore.GREEN if task['success'] else Fore.RED
            success = "✓" if task['success'] else "✗"
            
            task_details_table.append([
                task['task_id'],
                f"{status_color}{status}{Style.RESET_ALL}",
                f"{success_color}{success}{Style.RESET_ALL}",
                "✓" if task['error'] else "",
                f"{task['score']:.2f}",
            ])
        
        print(tabulate(task_details_table, headers=headers, tablefmt="simple"))
    
    return stats

def main():
    parser = argparse.ArgumentParser(description="Show statistics for AGI SDK evaluation results.")
    parser.add_argument("directory", nargs="?", default="./results", help="Directory containing results (default: ./results)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed information for each task")
    
    args = parser.parse_args()
    show_results(args.directory, args.verbose)

if __name__ == "__main__":
    main()