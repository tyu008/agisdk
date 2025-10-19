"""
IMPROVED Evaluation Script: gocalendar-11 (with Partial Credit)
Task: "I have math camp July 21st to 27th all day. Create a reminder and the camp is in Sunnyvale btw."

This version breaks down the task into 5 weighted criteria:
1. Event created (30%)
2. Correct title (20%)
3. Correct dates (25%)
4. All-day event (10%)
5. Correct location (15%)

Usage:
    python eval_gocalendar_11_v2.py <path_to_final_state_diff.json>
"""

import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from eval_framework_partial_credit import PartialCreditEvaluator, load_json, normalize_text


def check_title(title):
    """Check if title indicates Math Camp."""
    title_norm = normalize_text(title)
    
    if not title_norm:
        return 0.0, "Title is empty"
    
    has_math = 'math' in title_norm
    has_camp = 'camp' in title_norm
    
    if has_math and has_camp:
        return 1.0, f"Perfect match: '{title}'"
    elif has_math or has_camp:
        return 0.5, f"Partial match: '{title}' (has {'math' if has_math else 'camp'})"
    else:
        return 0.0, f"No match: '{title}'"


def check_dates(start_str, end_str, target_start="2024-07-21", target_end="2024-07-27"):
    """Check if dates match the required range."""
    if not start_str or not end_str:
        return 0.0, "Start or end date missing"
    
    start_date = start_str[:10] if len(start_str) >= 10 else start_str
    end_date = end_str[:10] if len(end_str) >= 10 else end_str
    
    start_match = (start_date == target_start)
    end_match = (end_date == target_end)
    
    if start_match and end_match:
        return 1.0, f"Perfect match: {start_date} to {end_date}"
    elif start_match:
        return 0.5, f"Start date correct ({start_date}), end date wrong ({end_date}, expected {target_end})"
    elif end_match:
        return 0.5, f"End date correct ({end_date}), start date wrong ({start_date}, expected {target_start})"
    else:
        # Check if dates are in July 2024 at least
        if '2024-07' in start_date or '2024-07' in end_date:
            return 0.25, f"Dates in correct month but wrong days: {start_date} to {end_date}"
        return 0.0, f"Wrong dates: {start_date} to {end_date} (expected {target_start} to {target_end})"


def check_all_day(all_day_flag):
    """Check if event is marked as all-day."""
    if all_day_flag is True:
        return 1.0, "Marked as all-day event"
    elif all_day_flag is False:
        return 0.0, "Not marked as all-day"
    else:
        return 0.0, f"Unknown all-day status: {all_day_flag}"


def check_location(location, target="sunnyvale"):
    """Check if location includes Sunnyvale."""
    location_norm = normalize_text(location)
    
    if not location_norm:
        return 0.0, "Location is empty"
    
    if target in location_norm:
        return 1.0, f"Correct location: '{location}'"
    
    # Partial credit for California locations
    ca_keywords = ['california', 'ca', 'bay area', 'silicon valley', 'san jose', 'palo alto']
    if any(kw in location_norm for kw in ca_keywords):
        return 0.3, f"Related location: '{location}' (but not Sunnyvale specifically)"
    
    return 0.0, f"Wrong location: '{location}'"


def evaluate_task(data_path, output_format="json"):
    """Main evaluation function."""
    evaluator = PartialCreditEvaluator(task_name="v2.gocalendar-11", output_format=output_format)
    
    # Define criteria
    evaluator.add_criterion(
        "event_created",
        weight=0.30,
        description="Calendar event was created"
    )
    evaluator.add_criterion(
        "correct_title",
        weight=0.20,
        description="Title indicates 'Math Camp'"
    )
    evaluator.add_criterion(
        "correct_dates",
        weight=0.25,
        description="Dates are July 21-27, 2024"
    )
    evaluator.add_criterion(
        "all_day_event",
        weight=0.10,
        description="Event is marked as all-day"
    )
    evaluator.add_criterion(
        "correct_location",
        weight=0.15,
        description="Location includes Sunnyvale"
    )
    
    # Load data
    data = load_json(data_path)
    if not data:
        for criterion in evaluator.criteria:
            evaluator.score(criterion, 0.0, "Failed to load data")
        evaluator.print_results()
        return
    
    # Get added events
    diffs = data.get('differences', {})
    events = diffs.get('events', {})
    added = events.get('added', {})
    
    if not isinstance(added, dict):
        added = {}
    
    if not added:
        evaluator.score("event_created", 0.0, "No events created")
        evaluator.score("correct_title", 0.0, "No events to check")
        evaluator.score("correct_dates", 0.0, "No events to check")
        evaluator.score("all_day_event", 0.0, "No events to check")
        evaluator.score("correct_location", 0.0, "No events to check")
        evaluator.print_results()
        return
    
    # Event exists
    evaluator.score("event_created", 1.0, f"Found {len(added)} event(s)")
    
    # Find best matching event
    best_score = 0.0
    best_event_scores = {}
    
    for event_id, event in added.items():
        if not isinstance(event, dict):
            continue
        
        title = event.get('title', '')
        start = event.get('start', '')
        end = event.get('end', '')
        all_day = event.get('allDay')
        location = event.get('location', '')
        
        # Score this event
        title_score, title_details = check_title(title)
        dates_score, dates_details = check_dates(start, end)
        all_day_score, all_day_details = check_all_day(all_day)
        location_score, location_details = check_location(location)
        
        # Calculate total
        total = (title_score * 0.20 + dates_score * 0.25 + 
                 all_day_score * 0.10 + location_score * 0.15) / 0.70
        
        if total > best_score:
            best_score = total
            best_event_scores = {
                'title': (title_score, title_details),
                'dates': (dates_score, dates_details),
                'all_day': (all_day_score, all_day_details),
                'location': (location_score, location_details),
                'event_id': event_id
            }
    
    # Score based on best event
    if best_event_scores:
        evaluator.score("correct_title", *best_event_scores['title'])
        evaluator.score("correct_dates", *best_event_scores['dates'])
        evaluator.score("all_day_event", *best_event_scores['all_day'])
        evaluator.score("correct_location", *best_event_scores['location'])
    else:
        evaluator.score("correct_title", 0.0, "No valid events")
        evaluator.score("correct_dates", 0.0, "No valid events")
        evaluator.score("all_day_event", 0.0, "No valid events")
        evaluator.score("correct_location", 0.0, "No valid events")
    
    evaluator.print_results()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("FAILURE")
        sys.exit(1)
    
    output_fmt = "json"
    if len(sys.argv) >= 3:
        output_fmt = sys.argv[2]
    
    evaluate_task(sys.argv[1], output_format=output_fmt)

