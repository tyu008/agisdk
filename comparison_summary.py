#!/usr/bin/env python3
"""
Generate a quick comparison summary between the two test runs
"""

import json
from pathlib import Path

def main():
    # Load both analyses
    full_results = json.load(open("/Users/tayu/agisdk/full_results_analysis.json"))
    time2_results = json.load(open("/Users/tayu/agisdk/time2_results_analysis.json"))
    
    print("=" * 80)
    print("COMPARISON SUMMARY: full_results vs all_results_time_2")
    print("=" * 80)
    print()
    
    # Overall comparison
    print("OVERALL PERFORMANCE:")
    print("-" * 80)
    print(f"{'Metric':<30} {'Full Results':>15} {'Time 2':>15} {'Change':>15}")
    print("-" * 80)
    
    fr_success = full_results['summary']['success_rate']
    t2_success = time2_results['summary']['success_rate']
    
    print(f"{'Success Rate':<30} {fr_success:>14.2f}% {t2_success:>14.2f}% {t2_success-fr_success:>+14.2f}pp")
    print(f"{'Total Tasks':<30} {full_results['summary']['total_tasks']:>15} {time2_results['summary']['total_tasks']:>15} {time2_results['summary']['total_tasks']-full_results['summary']['total_tasks']:>+15}")
    print(f"{'Truncation Rate':<30} {full_results['summary']['truncation_rate']:>14.2f}% {time2_results['summary']['truncation_rate']:>14.2f}% {time2_results['summary']['truncation_rate']-full_results['summary']['truncation_rate']:>+14.2f}pp")
    print(f"{'Error Rate':<30} {full_results['summary']['error_rate']:>14.2f}% {time2_results['summary']['error_rate']:>14.2f}% {time2_results['summary']['error_rate']-full_results['summary']['error_rate']:>+14.2f}pp")
    print()
    
    # Domain comparison
    print("DOMAIN PERFORMANCE COMPARISON:")
    print("-" * 80)
    print(f"{'Domain':<15} {'Full Results':>15} {'Time 2':>15} {'Change':>15} {'Status':<15}")
    print("-" * 80)
    
    # Create domain lookup
    fr_domains = {d['domain']: d for d in full_results['domain_stats']}
    t2_domains = {d['domain']: d for d in time2_results['domain_stats']}
    
    all_domains = set(fr_domains.keys()) | set(t2_domains.keys())
    
    changes = []
    for domain in sorted(all_domains):
        fr = fr_domains.get(domain, {'success_rate': 0})
        t2 = t2_domains.get(domain, {'success_rate': 0})
        
        fr_rate = fr['success_rate']
        t2_rate = t2['success_rate']
        change = t2_rate - fr_rate
        
        changes.append((domain, fr_rate, t2_rate, change))
    
    # Sort by change magnitude
    changes.sort(key=lambda x: x[3], reverse=True)
    
    for domain, fr_rate, t2_rate, change in changes:
        if change > 10:
            status = "⬆️ IMPROVED"
        elif change < -10:
            status = "⬇️ REGRESSED"
        elif abs(change) < 0.1:
            status = "➡️ STABLE"
        else:
            status = "~ MINOR"
        
        print(f"{domain.upper():<15} {fr_rate:>14.1f}% {t2_rate:>14.1f}% {change:>+14.1f}pp {status:<15}")
    
    print()
    print("KEY HIGHLIGHTS:")
    print("-" * 80)
    
    # Find biggest improvements
    improvements = [(d, c) for d, _, _, c in changes if c > 0]
    if improvements:
        improvements.sort(key=lambda x: x[1], reverse=True)
        print("✅ Biggest Improvements:")
        for domain, change in improvements[:3]:
            print(f"   - {domain.upper()}: +{change:.1f}pp")
    
    # Find regressions
    regressions = [(d, c) for d, _, _, c in changes if c < 0]
    if regressions:
        regressions.sort(key=lambda x: x[1])
        print("\n⚠️ Regressions:")
        for domain, change in regressions:
            print(f"   - {domain.upper()}: {change:.1f}pp")
    
    # Find breakthroughs
    breakthroughs = [(d, fr_rate, t2_rate) for d, fr_rate, t2_rate, _ in changes if fr_rate == 0 and t2_rate > 0]
    if breakthroughs:
        print("\n🎯 Breakthroughs (0% → Success):")
        for domain, _, t2_rate in breakthroughs:
            print(f"   - {domain.upper()}: 0% → {t2_rate:.1f}%")
    
    # Still zero
    still_zero = [(d, fr_rate, t2_rate) for d, fr_rate, t2_rate, _ in changes if fr_rate == 0 and t2_rate == 0]
    if still_zero:
        print("\n❌ Still 0% Success:")
        for domain, _, _ in still_zero:
            print(f"   - {domain.upper()}")
    
    print()
    print("=" * 80)
    print("Full reports:")
    print("  - COMPREHENSIVE_FAILURE_ANALYSIS_REPORT.md (full_results)")
    print("  - TIME2_FAILURE_ANALYSIS.md (all_results_time_2)")
    print("  - COMPARISON_REPORT.md (detailed comparison)")
    print("=" * 80)

if __name__ == "__main__":
    main()

