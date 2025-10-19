#!/usr/bin/env python3
"""Generate visualizations for failure analysis."""

import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

def load_all_results(results_dir):
    """Load all experiment results."""
    results_dir = Path(results_dir)
    all_results = []
    
    for exp_dir in sorted(results_dir.iterdir()):
        if not exp_dir.is_dir():
            continue
            
        summary_file = exp_dir / "summary_info.json"
        if not summary_file.exists():
            continue
        
        try:
            with open(summary_file, 'r') as f:
                data = json.load(f)
                all_results.append(data)
        except Exception as e:
            print(f"Error reading {summary_file}: {e}")
    
    return all_results

def create_visualizations(results):
    """Create various visualizations."""
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (15, 10)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 12))
    
    # 1. Overall Success/Failure Distribution
    ax1 = plt.subplot(2, 3, 1)
    success_counts = Counter([r.get('success', False) for r in results])
    labels = ['Failed', 'Success']
    sizes = [success_counts[False], success_counts[True]]
    colors = ['#ff6b6b', '#51cf66']
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    ax1.set_title('Overall Success Rate', fontsize=14, fontweight='bold')
    
    # 2. Failure Type Distribution
    ax2 = plt.subplot(2, 3, 2)
    failure_types = []
    for r in results:
        if not r.get('success', False):
            if r.get('error', False):
                failure_types.append('Error')
            elif r.get('truncated', False):
                failure_types.append('Truncated')
            else:
                failure_types.append('Completed but Failed')
    
    failure_counter = Counter(failure_types)
    ax2.bar(failure_counter.keys(), failure_counter.values(), color=['#ff6b6b', '#ffd93d', '#ff8787'])
    ax2.set_title('Failure Types', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Count')
    plt.xticks(rotation=15, ha='right')
    
    # 3. Steps Distribution
    ax3 = plt.subplot(2, 3, 3)
    steps = [r.get('n_steps', 0) for r in results]
    ax3.hist(steps, bins=25, color='#4dabf7', edgecolor='black', alpha=0.7)
    ax3.axvline(np.mean(steps), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(steps):.1f}')
    ax3.set_title('Steps Distribution', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Number of Steps')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    
    # 4. Success Rate by Website
    ax4 = plt.subplot(2, 3, 4)
    website_stats = defaultdict(lambda: {'total': 0, 'success': 0})
    
    for r in results:
        task_name = r.get('task_name', 'unknown')
        website = task_name.split('-')[0] if '-' in task_name else task_name
        website_stats[website]['total'] += 1
        if r.get('success', False):
            website_stats[website]['success'] += 1
    
    # Sort by success rate
    website_data = [(w, stats['success']/stats['total']*100, stats['total']) 
                    for w, stats in website_stats.items() if stats['total'] > 0]
    website_data.sort(key=lambda x: x[1], reverse=True)
    
    websites = [w[0].replace('v2.', '') for w in website_data]
    success_rates = [w[1] for w in website_data]
    colors_bars = ['#51cf66' if sr >= 50 else '#ffd93d' if sr >= 25 else '#ff6b6b' for sr in success_rates]
    
    bars = ax4.barh(websites, success_rates, color=colors_bars, edgecolor='black')
    ax4.set_title('Success Rate by Website', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Success Rate (%)')
    ax4.axvline(50, color='red', linestyle='--', linewidth=1, alpha=0.5)
    
    # Add count labels
    for i, (bar, data) in enumerate(zip(bars, website_data)):
        ax4.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, 
                f'{data[2]} tasks', va='center', fontsize=8)
    
    # 5. Steps Used: Success vs Failure
    ax5 = plt.subplot(2, 3, 5)
    success_steps = [r.get('n_steps', 0) for r in results if r.get('success', False)]
    failure_steps = [r.get('n_steps', 0) for r in results if not r.get('success', False)]
    
    ax5.violinplot([success_steps, failure_steps], positions=[1, 2], 
                   showmeans=True, showmedians=True)
    ax5.set_xticks([1, 2])
    ax5.set_xticklabels(['Success', 'Failure'])
    ax5.set_ylabel('Number of Steps')
    ax5.set_title('Steps: Success vs Failure', fontsize=14, fontweight='bold')
    ax5.grid(axis='y', alpha=0.3)
    
    # 6. Truncation Rate by Website
    ax6 = plt.subplot(2, 3, 6)
    truncation_rates = []
    website_names = []
    
    for website, stats in website_stats.items():
        truncated_count = sum(1 for r in results 
                             if r.get('task_name', '').startswith(website) 
                             and r.get('truncated', False))
        if stats['total'] > 0:
            truncation_rate = truncated_count / stats['total'] * 100
            truncation_rates.append(truncation_rate)
            website_names.append(website.replace('v2.', ''))
    
    # Sort by truncation rate
    sorted_data = sorted(zip(website_names, truncation_rates), key=lambda x: x[1], reverse=True)
    website_names = [d[0] for d in sorted_data]
    truncation_rates = [d[1] for d in sorted_data]
    
    colors_trunc = ['#ff6b6b' if tr >= 40 else '#ffd93d' if tr >= 20 else '#51cf66' for tr in truncation_rates]
    ax6.barh(website_names, truncation_rates, color=colors_trunc, edgecolor='black')
    ax6.set_title('Truncation Rate by Website', fontsize=14, fontweight='bold')
    ax6.set_xlabel('Truncation Rate (%)')
    ax6.axvline(25, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Average')
    ax6.legend()
    
    plt.tight_layout()
    plt.savefig('/Users/tayu/agisdk/failure_analysis_charts.png', dpi=300, bbox_inches='tight')
    print("Saved visualization to failure_analysis_charts.png")
    
    # Create a second figure for detailed analysis
    fig2 = plt.figure(figsize=(20, 8))
    
    # 7. Steps timeline for failed vs successful
    ax7 = plt.subplot(1, 2, 1)
    for i, r in enumerate(results):
        color = '#51cf66' if r.get('success', False) else '#ff6b6b'
        marker = 'o' if r.get('success', False) else 'x'
        ax7.scatter(i, r.get('n_steps', 0), color=color, marker=marker, s=50, alpha=0.6)
    
    ax7.axhline(25, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Max Steps')
    ax7.axhline(np.mean(steps), color='blue', linestyle='--', linewidth=1, alpha=0.5, label=f'Mean: {np.mean(steps):.1f}')
    ax7.set_title('Steps Used Per Experiment', fontsize=14, fontweight='bold')
    ax7.set_xlabel('Experiment Index')
    ax7.set_ylabel('Steps Used')
    ax7.legend()
    ax7.grid(alpha=0.3)
    
    # 8. Task completion heatmap
    ax8 = plt.subplot(1, 2, 2)
    
    # Create matrix: website x outcome
    websites_list = sorted(list(set(r.get('task_name', '').split('-')[0] for r in results)))
    outcomes = ['Success', 'Completed-Failed', 'Truncated', 'Error']
    matrix = np.zeros((len(websites_list), len(outcomes)))
    
    for i, website in enumerate(websites_list):
        for r in results:
            if r.get('task_name', '').startswith(website):
                if r.get('success', False):
                    matrix[i, 0] += 1
                elif r.get('error', False):
                    matrix[i, 3] += 1
                elif r.get('truncated', False):
                    matrix[i, 2] += 1
                else:
                    matrix[i, 1] += 1
    
    sns.heatmap(matrix, annot=True, fmt='.0f', cmap='RdYlGn', 
                xticklabels=outcomes, 
                yticklabels=[w.replace('v2.', '') for w in websites_list],
                cbar_kws={'label': 'Count'},
                ax=ax8)
    ax8.set_title('Outcome Distribution by Website', fontsize=14, fontweight='bold')
    ax8.set_xlabel('Outcome Type')
    ax8.set_ylabel('Website')
    
    plt.tight_layout()
    plt.savefig('/Users/tayu/agisdk/failure_analysis_detailed.png', dpi=300, bbox_inches='tight')
    print("Saved detailed visualization to failure_analysis_detailed.png")
    
    plt.close('all')

def main():
    results_dir = "/Users/tayu/agisdk/full_results"
    print("Loading results...")
    results = load_all_results(results_dir)
    print(f"Loaded {len(results)} experiments")
    
    print("Creating visualizations...")
    create_visualizations(results)
    print("Done!")

if __name__ == "__main__":
    main()

