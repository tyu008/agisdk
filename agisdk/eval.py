import jmespath
from openai import OpenAI

def openai_evaluator(model_response, rubric, model="gpt-4o-mini"):
    """Uses OpenAI API to evaluate a response against a rubric."""
    client = OpenAI()
    prompt = f"""
        Given a student's answer and a rubric, grade the answer.
        Student's answer: {model_response}
        Rubric: {rubric}
        Grade the answer on a scale of 0 to 1, where 1 means it matches the rubric.
        Please answer only with a floating point number and nothing else.
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    
    try:
        score = float(response.choices[0].message.content.strip())
        passed = score >= 0.8
        return passed, score
    except ValueError:
        return False, 0.0
        
def check_evals(evals, env_state, model_response=None, llm_evaluator=openai_evaluator):
    results = []
    for eval in evals:
        if eval["type"] == "jmespath":
            try:
                actual = jmespath.search(eval["query"], env_state)
                passed = actual == eval["expected_value"]
                results.append({"passed": passed, "actual": actual, "expected": eval["expected_value"]})
            except Exception as e:
                results.append({"passed": False, "error": str(e)})
        elif eval["type"] == "llm_boolean" and llm_evaluator:
            try:
                passed, score = llm_evaluator(model_response, eval["rubric"])
                results.append({"passed": passed, "score": score, "response": model_response})
            except Exception as e:
                results.append({"passed": False, "error": str(e)})
    passed_all = all(r.get("passed", False) for r in results)
    return [passed_all, results]