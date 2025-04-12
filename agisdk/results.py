from typing import Dict, Any
import json

class Results:
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize results object.
        
        Args:
            data: Dictionary containing evaluation results data
        """
        self.data = data
        
    def show(self):
        """
        Display the evaluation results.
        """
        print("\n=== Evaluation Results ===")
        print(f"Tasks completed: {self.data.get('tasks_completed', 0)}")
        print(f"Tasks failed: {self.data.get('tasks_failed', 0)}")
        print(f"Average score: {self.data.get('average_score', 0.0):.2f}")
        print("=======================\n")
        
    def save(self, path: str):
        """
        Save results to a JSON file.
        
        Args:
            path: Path to save the results
        """
        with open(path, 'w') as f:
            json.dump(self.data, f, indent=2)
        print(f"Results saved to {path}")
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert results to a dictionary.
        
        Returns:
            Dictionary containing evaluation results data
        """
        return self.data
