#!/usr/bin/env python3
"""
Comprehensive failure analysis script for all_results_time_2 directory
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any

def load_summary_info(result_dir: Path) -> Dict[str, Any]:
    """Load summary_info.json from a result directory"""
    summary_path = result_dir / "summary_info.json"
    if summary_path.exists():
        try:
            with open(summary_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {summary_path}: {e}")
            return None
    return None

def extract_task_domain(task_name: str) -> str:
    """Extract domain from task name (e.g., 'v2.omnizon-10' -> 'omnizon')"""
    if '.' in task_name:
        parts = task_name.split('.')
        if len(parts) > 1:
            domain_parts = parts[1].split('-')
            if domain_parts:
                return domain_parts[0]
    return "unknown"

def analyze_failure_patterns(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze specific failure patterns from summary"""
    patterns = {
        'truncated': summary.get('truncated', False),
        'terminated': summary.get('terminated', False),
        'error': summary.get('error', False),
        'success': summary.get('success', False),
        'n_steps': summary.get('n_steps', 0),
        'max_steps': summary.get('max_steps', 0),
        'cum_reward': summary.get('cum_reward', 0.0),
        'err_msg': summary.get('err_msg'),
        'stack_trace': summary.get('stack_trace'),
        'env_setup_error': summary.get('env_setup_error'),
    }
    
    return patterns

def main():
    results_dir = Path("/Users/tayu/agisdk/all_results_assamble/all_results_time_2")
    
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return
    
    # Collect all result directories
    result_dirs = [d for d in results_dir.iterdir() if d.is_dir()]
    print(f"Found {len(result_dirs)} result directories")
    
    # Data structures for analysis
    all_results = []
    domain_stats = defaultdict(lambda: {
        'total': 0,
        'success': 0,
        'failure': 0,
        'truncated': 0,
        'error': 0,
        'avg_steps': [],
        'avg_reward': [],
    })
    
    failure_reasons = Counter()
    step_distribution = []
    reward_distribution = []
    
    # Process each result directory
    for result_dir in result_dirs:
        summary = load_summary_info(result_dir)
        if not summary:
            continue
        
        task_name = summary.get('task_name', 'unknown')
        domain = extract_task_domain(task_name)
        
        # Analyze failure patterns
        patterns = analyze_failure_patterns(summary)
        
        # Store result
        result_data = {
            'dir_name': result_dir.name,
            'task_name': task_name,
            'domain': domain,
            'summary': summary,
            'patterns': patterns,
        }
        all_results.append(result_data)
        
        # Update domain stats
        domain_stats[domain]['total'] += 1
        domain_stats[domain]['avg_steps'].append(summary.get('n_steps', 0))
        domain_stats[domain]['avg_reward'].append(summary.get('cum_reward', 0.0))
        
        if summary.get('success', False):
            domain_stats[domain]['success'] += 1
        else:
            domain_stats[domain]['failure'] += 1
        
        if summary.get('truncated', False):
            domain_stats[domain]['truncated'] += 1
            failure_reasons['Truncated (max steps reached)'] += 1
        
        if summary.get('error', False):
            domain_stats[domain]['error'] += 1
            err_msg = summary.get('err_msg', 'Unknown error')
            failure_reasons[f'Error: {err_msg[:50]}'] += 1
        
        if not summary.get('success', False) and not summary.get('truncated', False) and not summary.get('error', False):
            failure_reasons['Task incomplete (terminated early)'] += 1
        
        step_distribution.append(summary.get('n_steps', 0))
        reward_distribution.append(summary.get('cum_reward', 0.0))
    
    # Calculate statistics
    total_tasks = len(all_results)
    total_success = sum(1 for r in all_results if r['summary'].get('success', False))
    total_failure = total_tasks - total_success
    success_rate = (total_success / total_tasks * 100) if total_tasks > 0 else 0
    
    # Generate report
    report = []
    report.append("=" * 80)
    report.append("COMPREHENSIVE FAILURE ANALYSIS REPORT")
    report.append("all_results_time_2 Directory Analysis")
    report.append("=" * 80)
    report.append("")
    
    # Overall Statistics
    report.append("## OVERALL STATISTICS")
    report.append("-" * 80)
    report.append(f"Total Tasks Executed: {total_tasks}")
    report.append(f"Successful Tasks: {total_success} ({success_rate:.2f}%)")
    report.append(f"Failed Tasks: {total_failure} ({100-success_rate:.2f}%)")
    report.append("")
    
    # Step and Reward Statistics
    if step_distribution:
        avg_steps = sum(step_distribution) / len(step_distribution)
        max_steps = max(step_distribution)
        min_steps = min(step_distribution)
        report.append(f"Average Steps per Task: {avg_steps:.2f}")
        report.append(f"Max Steps: {max_steps}, Min Steps: {min_steps}")
    
    if reward_distribution:
        avg_reward = sum(reward_distribution) / len(reward_distribution)
        max_reward = max(reward_distribution)
        min_reward = min(reward_distribution)
        report.append(f"Average Reward: {avg_reward:.4f}")
        report.append(f"Max Reward: {max_reward:.4f}, Min Reward: {min_reward:.4f}")
    
    report.append("")
    report.append("")
    
    # Domain-wise Analysis
    report.append("## DOMAIN-WISE PERFORMANCE")
    report.append("-" * 80)
    
    # Sort domains by success rate
    domain_list = []
    for domain, stats in domain_stats.items():
        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        avg_steps = sum(stats['avg_steps']) / len(stats['avg_steps']) if stats['avg_steps'] else 0
        avg_reward = sum(stats['avg_reward']) / len(stats['avg_reward']) if stats['avg_reward'] else 0
        domain_list.append({
            'domain': domain,
            'total': stats['total'],
            'success': stats['success'],
            'failure': stats['failure'],
            'truncated': stats['truncated'],
            'error': stats['error'],
            'success_rate': success_rate,
            'avg_steps': avg_steps,
            'avg_reward': avg_reward,
        })
    
    domain_list.sort(key=lambda x: x['success_rate'], reverse=True)
    
    for d in domain_list:
        report.append(f"\n### {d['domain'].upper()}")
        report.append(f"  Total Tasks: {d['total']}")
        report.append(f"  Success: {d['success']} ({d['success_rate']:.2f}%)")
        report.append(f"  Failure: {d['failure']} ({100-d['success_rate']:.2f}%)")
        report.append(f"  Truncated: {d['truncated']}")
        report.append(f"  Errors: {d['error']}")
        report.append(f"  Avg Steps: {d['avg_steps']:.2f}")
        report.append(f"  Avg Reward: {d['avg_reward']:.4f}")
    
    report.append("")
    report.append("")
    
    # Failure Reasons
    report.append("## TOP FAILURE REASONS")
    report.append("-" * 80)
    for reason, count in failure_reasons.most_common(15):
        percentage = (count / total_failure * 100) if total_failure > 0 else 0
        report.append(f"{count:4d} ({percentage:5.2f}%) - {reason}")
    
    report.append("")
    report.append("")
    
    # Detailed Failure Analysis by Domain
    report.append("## DETAILED FAILURE ANALYSIS BY DOMAIN")
    report.append("-" * 80)
    
    for domain in sorted(domain_stats.keys()):
        domain_failures = [r for r in all_results if r['domain'] == domain and not r['summary'].get('success', False)]
        if not domain_failures:
            continue
        
        report.append(f"\n### {domain.upper()} - Failed Tasks")
        report.append(f"Total Failures: {len(domain_failures)}")
        
        # Categorize failures
        truncated = sum(1 for r in domain_failures if r['patterns']['truncated'])
        errors = sum(1 for r in domain_failures if r['patterns']['error'])
        early_term = len(domain_failures) - truncated - errors
        
        report.append(f"  - Truncated (max steps): {truncated}")
        report.append(f"  - Errors: {errors}")
        report.append(f"  - Early termination: {early_term}")
        
        # Sample failure details
        report.append(f"\n  Sample Failures:")
        for i, failure in enumerate(domain_failures[:3]):
            report.append(f"\n  Task {i+1}: {failure['task_name']}")
            report.append(f"    Steps: {failure['patterns']['n_steps']}/{failure['patterns']['max_steps']}")
            report.append(f"    Reward: {failure['patterns']['cum_reward']:.4f}")
            report.append(f"    Truncated: {failure['patterns']['truncated']}")
            report.append(f"    Error: {failure['patterns']['error']}")
            if failure['patterns']['err_msg']:
                report.append(f"    Error Message: {failure['patterns']['err_msg'][:100]}")
    
    report.append("")
    report.append("")
    
    # Success Analysis
    report.append("## SUCCESS ANALYSIS")
    report.append("-" * 80)
    
    successful_tasks = [r for r in all_results if r['summary'].get('success', False)]
    if successful_tasks:
        success_steps = [r['patterns']['n_steps'] for r in successful_tasks]
        success_rewards = [r['patterns']['cum_reward'] for r in successful_tasks]
        
        report.append(f"Total Successful Tasks: {len(successful_tasks)}")
        report.append(f"Average Steps to Success: {sum(success_steps)/len(success_steps):.2f}")
        report.append(f"Average Reward: {sum(success_rewards)/len(success_rewards):.4f}")
        
        # Success by domain
        success_by_domain = defaultdict(int)
        for r in successful_tasks:
            success_by_domain[r['domain']] += 1
        
        report.append(f"\nSuccesses by Domain:")
        for domain, count in sorted(success_by_domain.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {domain}: {count}")
    
    report.append("")
    report.append("")
    
    # Key Insights
    report.append("## KEY INSIGHTS AND RECOMMENDATIONS")
    report.append("-" * 80)
    
    # Calculate truncation rate
    truncation_rate = sum(1 for r in all_results if r['patterns']['truncated']) / total_tasks * 100
    error_rate = sum(1 for r in all_results if r['patterns']['error']) / total_tasks * 100
    
    report.append(f"\n1. TRUNCATION ISSUES:")
    report.append(f"   - {truncation_rate:.2f}% of tasks hit max step limit")
    report.append(f"   - Consider increasing max_steps or improving agent efficiency")
    
    report.append(f"\n2. ERROR RATE:")
    report.append(f"   - {error_rate:.2f}% of tasks encountered errors")
    report.append(f"   - Review error messages for common patterns")
    
    # Identify problematic domains
    low_performing_domains = [d for d in domain_list if d['success_rate'] < 30]
    if low_performing_domains:
        report.append(f"\n3. LOW-PERFORMING DOMAINS:")
        for d in low_performing_domains:
            report.append(f"   - {d['domain']}: {d['success_rate']:.2f}% success rate")
    
    # Identify high-performing domains
    high_performing_domains = [d for d in domain_list if d['success_rate'] > 70]
    if high_performing_domains:
        report.append(f"\n4. HIGH-PERFORMING DOMAINS:")
        for d in high_performing_domains:
            report.append(f"   - {d['domain']}: {d['success_rate']:.2f}% success rate")
    
    report.append("")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    # Write report
    report_text = "\n".join(report)
    output_path = Path("/Users/tayu/agisdk/TIME2_FAILURE_ANALYSIS.md")
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    print(f"\nReport generated: {output_path}")
    print(f"\nSummary:")
    print(f"  Total Tasks: {total_tasks}")
    print(f"  Success Rate: {success_rate:.2f}%")
    print(f"  Truncation Rate: {truncation_rate:.2f}%")
    print(f"  Error Rate: {error_rate:.2f}%")
    
    # Also save detailed JSON data
    json_output = {
        'summary': {
            'total_tasks': total_tasks,
            'success_rate': success_rate,
            'truncation_rate': truncation_rate,
            'error_rate': error_rate,
        },
        'domain_stats': domain_list,
        'all_results': all_results,
    }
    
    json_path = Path("/Users/tayu/agisdk/time2_results_analysis.json")
    with open(json_path, 'w') as f:
        json.dump(json_output, f, indent=2)
    
    print(f"Detailed JSON data: {json_path}")

if __name__ == "__main__":
    main()

