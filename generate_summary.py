#!/usr/bin/env python3
"""
Generate a quick summary of the failure analysis
"""

import json
from pathlib import Path
from collections import defaultdict

def main():
    # Load analysis data
    json_path = Path("/Users/tayu/agisdk/full_results_analysis.json")
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("FAILURE ANALYSIS SUMMARY")
    print("=" * 80)
    print()
    
    # Overall stats
    summary = data['summary']
    print(f"Total Tasks: {summary['total_tasks']}")
    print(f"Success Rate: {summary['success_rate']:.2f}%")
    print(f"Truncation Rate: {summary['truncation_rate']:.2f}%")
    print(f"Error Rate: {summary['error_rate']:.2f}%")
    print()
    
    # Domain performance
    print("DOMAIN PERFORMANCE RANKING:")
    print("-" * 80)
    domain_stats = sorted(data['domain_stats'], key=lambda x: x['success_rate'], reverse=True)
    
    for i, domain in enumerate(domain_stats, 1):
        status = "✓" if domain['success_rate'] > 50 else "✗" if domain['success_rate'] == 0 else "~"
        print(f"{i:2d}. {status} {domain['domain'].upper():15s} - {domain['success_rate']:5.1f}% "
              f"({domain['success']}/{domain['total']}) - Avg Steps: {domain['avg_steps']:.1f}")
    
    print()
    print("CRITICAL ISSUES:")
    print("-" * 80)
    
    # Zero success domains
    zero_success = [d for d in domain_stats if d['success_rate'] == 0]
    if zero_success:
        print(f"❌ {len(zero_success)} domains with 0% success:")
        for d in zero_success:
            print(f"   - {d['domain'].upper()}: {d['total']} tasks, avg {d['avg_steps']:.1f} steps")
    
    # High truncation
    high_trunc = [d for d in domain_stats if d['truncated'] / d['total'] > 0.4]
    if high_trunc:
        print(f"\n⚠️  {len(high_trunc)} domains with high truncation (>40%):")
        for d in high_trunc:
            trunc_rate = d['truncated'] / d['total'] * 100
            print(f"   - {d['domain'].upper()}: {d['truncated']}/{d['total']} ({trunc_rate:.1f}%)")
    
    # Low performers
    low_perf = [d for d in domain_stats if 0 < d['success_rate'] < 30]
    if low_perf:
        print(f"\n⚠️  {len(low_perf)} domains with low success (<30%):")
        for d in low_perf:
            print(f"   - {d['domain'].upper()}: {d['success_rate']:.1f}%")
    
    print()
    print("TOP RECOMMENDATIONS:")
    print("-" * 80)
    print("1. Fix GOMAIL, STAYNB, GOCALENDAR (0% success) - CRITICAL")
    print("2. Increase max_steps to 35-40 for UDRIVER, MARRISUITE")
    print("3. Implement loop detection to prevent repeated actions")
    print("4. Add validation before early termination")
    print("5. Improve domain-specific prompts and examples")
    print()
    
    print("=" * 80)
    print("Full report: COMPREHENSIVE_FAILURE_ANALYSIS_REPORT.md")
    print("=" * 80)

if __name__ == "__main__":
    main()

