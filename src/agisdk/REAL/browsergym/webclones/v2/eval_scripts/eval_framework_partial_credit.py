"""
Evaluation Framework with Partial Credit Support
=================================================

This framework enables evaluation scripts to award partial credit for incomplete tasks,
providing better insight into agent progress and capabilities.

Key Features:
1. Weighted sub-tasks/criteria
2. Detailed scoring breakdown
3. JSON output format for analysis
4. Backward compatibility with binary SUCCESS/FAILURE

Usage:
    from eval_framework_partial_credit import PartialCreditEvaluator, Criterion
    
    evaluator = PartialCreditEvaluator(task_name="gomail-13")
    
    # Define criteria with weights
    evaluator.add_criterion("email_composed", weight=0.25, description="Email draft created")
    evaluator.add_criterion("correct_recipient", weight=0.25, description="Sent to alexa.richardson@*")
    evaluator.add_criterion("valid_subject", weight=0.15, description="Subject is not empty/generic")
    evaluator.add_criterion("correct_content", weight=0.25, description="Body mentions files and notification")
    evaluator.add_criterion("email_sent", weight=0.10, description="Email was sent")
    
    # Score each criterion
    evaluator.score("email_composed", 1.0, "Found email draft")
    evaluator.score("correct_recipient", 1.0, "Recipient: alexa.richardson@example.com")
    evaluator.score("valid_subject", 0.0, "Subject: No Subject")
    evaluator.score("correct_content", 1.0, "Body contains required phrases")
    evaluator.score("email_sent", 1.0, "Email marked as sent")
    
    # Output results
    evaluator.print_results()  # Prints JSON with score and breakdown
"""

import json
import sys
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Criterion:
    """Represents a single evaluation criterion."""
    name: str
    weight: float
    description: str
    score: float = 0.0
    achieved: bool = False
    details: str = ""
    
    def to_dict(self):
        return {
            "name": self.name,
            "weight": self.weight,
            "description": self.description,
            "score": self.score,
            "achieved": self.achieved,
            "details": self.details
        }


class PartialCreditEvaluator:
    """
    Main evaluator class that manages criteria and computes weighted scores.
    """
    
    def __init__(self, task_name: str, output_format: str = "json"):
        """
        Initialize evaluator.
        
        Args:
            task_name: Name/ID of the task being evaluated
            output_format: "json" (detailed) or "legacy" (SUCCESS/FAILURE only)
        """
        self.task_name = task_name
        self.output_format = output_format
        self.criteria: Dict[str, Criterion] = {}
        self._total_weight = 0.0
        
    def add_criterion(self, name: str, weight: float, description: str) -> None:
        """
        Add an evaluation criterion.
        
        Args:
            name: Unique identifier for this criterion
            weight: Weight/importance (will be normalized)
            description: Human-readable description
        """
        if name in self.criteria:
            raise ValueError(f"Criterion '{name}' already exists")
        
        self.criteria[name] = Criterion(
            name=name,
            weight=weight,
            description=description
        )
        self._total_weight += weight
    
    def score(self, name: str, score: float, details: str = "") -> None:
        """
        Score a specific criterion.
        
        Args:
            name: Criterion identifier
            score: Score value (0.0 to 1.0)
            details: Optional details about the scoring
        """
        if name not in self.criteria:
            raise ValueError(f"Unknown criterion: '{name}'")
        
        criterion = self.criteria[name]
        criterion.score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
        criterion.achieved = criterion.score >= 0.99  # Consider achieved if >= 0.99
        criterion.details = details
    
    def get_total_score(self) -> float:
        """
        Calculate weighted total score.
        
        Returns:
            Total score between 0.0 and 1.0
        """
        if self._total_weight == 0:
            return 0.0
        
        weighted_sum = sum(
            c.score * c.weight for c in self.criteria.values()
        )
        return weighted_sum / self._total_weight
    
    def get_completion_percentage(self) -> float:
        """Get percentage of criteria fully achieved."""
        if not self.criteria:
            return 0.0
        achieved = sum(1 for c in self.criteria.values() if c.achieved)
        return (achieved / len(self.criteria)) * 100
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get detailed results as dictionary.
        
        Returns:
            Dictionary with score, breakdown, and metadata
        """
        total_score = self.get_total_score()
        
        return {
            "task_name": self.task_name,
            "total_score": round(total_score, 4),
            "binary_success": total_score >= 0.99,
            "legacy_output": "SUCCESS" if total_score >= 0.99 else "FAILURE",
            "completion_percentage": round(self.get_completion_percentage(), 2),
            "criteria_breakdown": [c.to_dict() for c in self.criteria.values()],
            "summary": {
                "criteria_total": len(self.criteria),
                "criteria_achieved": sum(1 for c in self.criteria.values() if c.achieved),
                "criteria_partial": sum(1 for c in self.criteria.values() if 0 < c.score < 0.99),
                "criteria_failed": sum(1 for c in self.criteria.values() if c.score == 0)
            }
        }
    
    def print_results(self) -> None:
        print(f"some random text")
        """Print results based on output format."""
        if self.output_format == "legacy":
            # Legacy format: just SUCCESS or FAILURE
            total_score = self.get_total_score()
            print("SUCCESS" if total_score >= 0.99 else "FAILURE")
        else:
            # JSON format with full details
            results = self.get_results()
            print(json.dumps(results, indent=2))
    
    def print_legacy_with_score(self) -> None:
        """Print legacy format on first line, JSON details on subsequent lines."""
        total_score = self.get_total_score()
        print("SUCCESS" if total_score >= 0.99 else "FAILURE")
        print(json.dumps(self.get_results(), indent=2))


# Utility functions for common checks

def load_json(path: str) -> Dict[str, Any]:
    """Load JSON file safely."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}", file=sys.stderr)
        return {}


def normalize_text(text: Any) -> str:
    """Normalize text for comparison."""
    if text is None:
        return ""
    return str(text).strip().lower()


def check_contains_all(text: str, keywords: List[str]) -> Tuple[bool, str]:
    """
    Check if text contains all keywords.
    
    Returns:
        (success, details_string)
    """
    text_norm = normalize_text(text)
    missing = [kw for kw in keywords if kw.lower() not in text_norm]
    
    if not missing:
        return True, f"Contains all required: {', '.join(keywords)}"
    else:
        return False, f"Missing keywords: {', '.join(missing)}"


def check_contains_any(text: str, keywords: List[str]) -> Tuple[bool, str]:
    """
    Check if text contains any keyword.
    
    Returns:
        (success, details_string)
    """
    text_norm = normalize_text(text)
    found = [kw for kw in keywords if kw.lower() in text_norm]
    
    if found:
        return True, f"Found: {', '.join(found)}"
    else:
        return False, f"None of the keywords found: {', '.join(keywords)}"


def calculate_text_similarity_score(text: str, required_keywords: List[str]) -> Tuple[float, str]:
    """
    Calculate partial score based on keyword presence.
    
    Returns:
        (score, details_string)
    """
    if not required_keywords:
        return 1.0, "No keywords required"
    
    text_norm = normalize_text(text)
    found = [kw for kw in required_keywords if kw.lower() in text_norm]
    score = len(found) / len(required_keywords)
    
    details = f"Found {len(found)}/{len(required_keywords)} keywords: {', '.join(found)}"
    if len(found) < len(required_keywords):
        missing = [kw for kw in required_keywords if kw not in found]
        details += f" (missing: {', '.join(missing)})"
    
    return score, details


# Example usage
if __name__ == "__main__":
    # Demo: evaluate a hypothetical task
    evaluator = PartialCreditEvaluator(task_name="demo-task")
    
    evaluator.add_criterion("navigation", weight=0.20, description="Navigated to correct page")
    evaluator.add_criterion("form_filled", weight=0.30, description="Form fields completed")
    evaluator.add_criterion("submission", weight=0.30, description="Form submitted")
    evaluator.add_criterion("confirmation", weight=0.20, description="Confirmation received")
    
    # Simulate partial completion
    evaluator.score("navigation", 1.0, "Successfully navigated to /form")
    evaluator.score("form_filled", 0.75, "Filled 3/4 required fields")
    evaluator.score("submission", 0.0, "Form not submitted")
    evaluator.score("confirmation", 0.0, "No confirmation page")
    
    evaluator.print_results()
    
    print("\n--- Alternative: Legacy Format ---")
    evaluator2 = PartialCreditEvaluator(task_name="demo-task", output_format="legacy")
    evaluator2.add_criterion("test", weight=1.0, description="Test")
    evaluator2.score("test", 0.5, "Partial")
    evaluator2.print_results()  # Prints: FAILURE

