"""
IMPROVED Evaluation Script: gomail-13 (with Partial Credit)
Task: "Write an email to alexa richardson and ask to let me know when the files come in."

This version breaks down the task into 5 weighted criteria:
1. Email draft created (25%)
2. Correct recipient (25%) 
3. Valid subject (15%)
4. Correct content (25%)
5. Email sent (10%)

Usage:
    python eval_gomail_13_v2.py <path_to_final_state_diff.json>
    
Output formats supported:
    - JSON (default): Detailed breakdown with scores
    - Legacy: Just "SUCCESS" or "FAILURE" for backward compatibility
"""

import json
import sys
import os

# Import the partial credit framework
sys.path.insert(0, os.path.dirname(__file__))
from eval_framework_partial_credit import PartialCreditEvaluator, load_json, normalize_text


def gather_added_emails(data):
    """Gather all added emails from various locations in the data structure."""
    added = []
    
    # From differences.emails.added
    diff = data.get('differences') or {}
    emails_section = (diff.get('emails') or {}) if isinstance(diff, dict) else {}
    diff_added = emails_section.get('added') or []
    if isinstance(diff_added, list):
        added.extend(diff_added)
    
    # From initialfinaldiff.added.email.emails
    if isinstance(data.get('initialfinaldiff'), dict):
        init_add = data['initialfinaldiff'].get('added') or {}
        email_block = init_add.get('email') or {}
        emails_dict = email_block.get('emails') or {}
        if isinstance(emails_dict, dict):
            added.extend(list(emails_dict.values()))
    
    # Deduplicate by id
    seen = set()
    deduped = []
    for e in added:
        if not isinstance(e, dict):
            continue
        eid = e.get('id')
        key = ('id', eid) if eid is not None else ('obj', json.dumps(e, sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)
    
    return deduped


def check_recipient(email):
    """Check if email is addressed to alexa.richardson."""
    to_list = email.get('to')
    if not isinstance(to_list, list):
        return 0.0, "No recipients found"
    
    for addr in to_list:
        if not isinstance(addr, str):
            continue
        addr_norm = addr.strip().lower()
        if 'alexa.richardson' in addr_norm:
            return 1.0, f"Correct recipient: {addr}"
        # Partial credit for similar names
        if 'alexa' in addr_norm or 'richardson' in addr_norm:
            return 0.5, f"Partial match: {addr} (contains part of target name)"
    
    return 0.0, f"Wrong recipient(s): {', '.join(to_list)}"


def check_subject(email):
    """Check if subject is valid and not generic."""
    subject = email.get('subject', '')
    if not isinstance(subject, str):
        return 0.0, "No subject field"
    
    subject_stripped = subject.strip()
    if not subject_stripped:
        return 0.0, "Subject is empty"
    
    subject_lower = subject_stripped.lower()
    if subject_lower == 'no subject':
        return 0.0, "Subject is generic 'No Subject'"
    
    # Give partial credit if subject is very short (probably auto-generated)
    if len(subject_stripped) < 3:
        return 0.3, f"Subject too short: '{subject_stripped}'"
    
    # Check if subject is somewhat relevant to the task
    relevant_keywords = ['file', 'files', 'document', 'notification', 'notify', 'update']
    if any(kw in subject_lower for kw in relevant_keywords):
        return 1.0, f"Valid and relevant subject: '{subject_stripped}'"
    
    return 0.7, f"Valid but generic subject: '{subject_stripped}'"


def check_content(email):
    """Check if content mentions files and requests notification."""
    content = email.get('content', '')
    if not isinstance(content, str):
        return 0.0, "No content field"
    
    content_lower = content.strip().lower()
    if not content_lower:
        return 0.0, "Content is empty"
    
    # Required elements with variations
    notification_phrases = ['let me know', 'notify me', 'tell me', 'inform me', 'update me', 'alert me']
    file_keywords = ['file', 'files', 'document', 'documents']
    arrival_keywords = ['come in', 'arrive', 'received', 'ready', 'available']
    
    has_notification = any(phrase in content_lower for phrase in notification_phrases)
    has_files = any(kw in content_lower for kw in file_keywords)
    has_arrival = any(kw in content_lower for kw in arrival_keywords)
    
    score = 0.0
    details_parts = []
    
    if has_notification:
        score += 0.4
        details_parts.append("✓ Contains notification request")
    else:
        details_parts.append("✗ Missing notification request")
    
    if has_files:
        score += 0.4
        details_parts.append("✓ Mentions files")
    else:
        details_parts.append("✗ Doesn't mention files")
    
    if has_arrival:
        score += 0.2
        details_parts.append("✓ Mentions arrival/coming in")
    else:
        details_parts.append("~ Doesn't specify timing")
    
    details = "; ".join(details_parts)
    return score, details


def check_sent_status(email):
    """Check if email was actually sent."""
    sent = email.get('sent', False)
    if sent is True:
        return 1.0, "Email marked as sent"
    elif sent is False:
        return 0.0, "Email is draft (not sent)"
    else:
        return 0.0, f"Unknown sent status: {sent}"


def evaluate_task(data_path, output_format="json"):
    print(f"some random text in evaluate_task")
    """Main evaluation function."""
    # Initialize evaluator
    evaluator = PartialCreditEvaluator(task_name="v2.gomail-13", output_format=output_format)
    
    # Define criteria with weights
    evaluator.add_criterion(
        "email_exists",
        weight=0.25,
        description="Email draft created or composed"
    )
    evaluator.add_criterion(
        "correct_recipient",
        weight=0.25,
        description="Email addressed to alexa.richardson@*"
    )
    evaluator.add_criterion(
        "valid_subject",
        weight=0.15,
        description="Subject is present and not generic"
    )
    evaluator.add_criterion(
        "correct_content",
        weight=0.25,
        description="Body requests notification about files coming in"
    )
    evaluator.add_criterion(
        "email_sent",
        weight=0.10,
        description="Email was sent (not just drafted)"
    )
    
    # Load data
    data = load_json(data_path)
    if not data:
        # Score all as 0
        for criterion in evaluator.criteria:
            evaluator.score(criterion, 0.0, "Failed to load data")
        evaluator.print_results()
        return
    
    # Gather emails
    added_emails = gather_added_emails(data)
    
    if not added_emails:
        evaluator.score("email_exists", 0.0, "No emails found")
        evaluator.score("correct_recipient", 0.0, "No emails to check")
        evaluator.score("valid_subject", 0.0, "No emails to check")
        evaluator.score("correct_content", 0.0, "No emails to check")
        evaluator.score("email_sent", 0.0, "No emails to check")
        evaluator.print_results()
        return
    
    # Email exists
    evaluator.score("email_exists", 1.0, f"Found {len(added_emails)} email(s)")
    
    # Find best matching email and score it
    best_score = 0.0
    best_email_scores = {}
    
    for idx, email in enumerate(added_emails):
        if not isinstance(email, dict):
            continue
        
        # Check each criterion
        recipient_score, recipient_details = check_recipient(email)
        subject_score, subject_details = check_subject(email)
        content_score, content_details = check_content(email)
        sent_score, sent_details = check_sent_status(email)
        
        # Calculate total for this email
        total = (recipient_score * 0.25 + subject_score * 0.15 + 
                 content_score * 0.25 + sent_score * 0.10) / 0.75
        
        if total > best_score:
            best_score = total
            best_email_scores = {
                'recipient': (recipient_score, recipient_details),
                'subject': (subject_score, subject_details),
                'content': (content_score, content_details),
                'sent': (sent_score, sent_details),
                'index': idx
            }
    
    # Score based on best email
    if best_email_scores:
        evaluator.score("correct_recipient", *best_email_scores['recipient'])
        evaluator.score("valid_subject", *best_email_scores['subject'])
        evaluator.score("correct_content", *best_email_scores['content'])
        evaluator.score("email_sent", *best_email_scores['sent'])
    else:
        evaluator.score("correct_recipient", 0.0, "No valid emails")
        evaluator.score("valid_subject", 0.0, "No valid emails")
        evaluator.score("correct_content", 0.0, "No valid emails")
        evaluator.score("email_sent", 0.0, "No valid emails")
    
    evaluator.print_results()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("FAILURE")
        sys.exit(1)
    
    # Support optional output format argument
    output_fmt = "json"
    if len(sys.argv) >= 3:
        output_fmt = sys.argv[2]
    
    evaluate_task(sys.argv[1], output_format=output_fmt)

