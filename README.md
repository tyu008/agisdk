# AGI SDK

A simple SDK for benchmarking AI agents.

## Installation

```bash
pip install agisdk
```

## Usage

```python
from agisdk import EvalHarness

def myagentfn(prompt, playwright_object):
    # your agent implementation here
    return "Task completed successfully"

harness = EvalHarness(myagentfn, type="playwright", max_steps=25) # types of haranesses: url, playwright, cdp

results = harness.run(
    local=True,
    use_cache=True,
    dir="./results",
    tasks="all",
    paralel=True,
    num_workers=4
)

results.show()
```