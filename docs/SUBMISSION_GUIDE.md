# AGI SDK Submission Guide

This comprehensive guide covers everything you need to know about submitting your AI agents to the REAL Bench leaderboard and running local evaluations.

## Table of Contents

1. [Leaderboard Submission](#leaderboard-submission)
2. [Local Evaluation](#local-evaluation)
3. [Configuration Options](#configuration-options)
4. [Troubleshooting](#troubleshooting)

## Leaderboard Submission

### Prerequisites

1. **Get API Credentials**: Visit [realevals.xyz](https://realevals.xyz) to get your REAL API key
2. **Choose a Model**: Decide which LLM model you want to evaluate
3. **Pick a Run Name**: Choose a descriptive name for your submission

### Method 1: Automatic Run ID Generation (Recommended)

```python
from agisdk import REAL

# The harness will automatically get a run ID from the API
harness = REAL.harness(
    # Model configuration
    model="gpt-4o",                    # or "sonnet-3.7", "openrouter/deepseek/deepseek-r1:free"
    
    # Leaderboard submission
    api_key="your-real-api-key",       # Your REAL API key
    run_name="My GPT-4o Submission",   # Descriptive name for your run
    model_id_name="gpt-4o",           # Model identifier for the leaderboard
    leaderboard=True,                  # Enable leaderboard submission
    
    # Task configuration (optional - defaults to all tasks)
    task_type="omnizon",              # Run specific task type
    # task_name="webclones.omnizon-1", # Or run specific task
    
    # Execution options
    num_workers=4,                    # Parallel execution
    headless=True,                    # Run without browser GUI
    max_steps=25                      # Maximum steps per task
)

results = harness.run()
```

### Method 2: Manual Run ID

If you already have a run ID:

```python
harness = REAL.harness(
    model="gpt-4o",
    run_id="your-existing-run-id",
    leaderboard=True,
    # ... other options
)
```

### Method 3: Environment Variables

Set your API key as an environment variable:

```bash
export REAL_API_KEY="your-real-api-key"
```

```python
harness = REAL.harness(
    model="gpt-4o",
    run_name="My Submission",
    model_id_name="gpt-4o", 
    leaderboard=True,
    # API key will be read from REAL_API_KEY environment variable
)
```

### Submission Process

1. **Configure your harness** with leaderboard submission enabled
2. **Run the evaluation** - results are automatically submitted
3. **Check the leaderboard** at [realevals.xyz](https://realevals.xyz) to see your results

The submission happens automatically during task execution. Each completed task sends:
- Agent's final answer
- Task completion status
- Performance metrics

## Local Evaluation

For development and testing without leaderboard submission:

### Basic Local Evaluation

```python
from agisdk import REAL

harness = REAL.harness(
    model="gpt-4o",
    task_type="omnizon",
    headless=False,        # Show browser for debugging
    leaderboard=False,     # Disable leaderboard submission
    max_steps=25,
    results_dir="./my_results"  # Local results directory
)

results = harness.run()
```

### Custom Agent Evaluation

```python
from agisdk import REAL

class MyAgent(REAL.Agent):
    def __init__(self, agent_args):
        super().__init__(agent_args)
        # Initialize your agent
    
    def get_action(self, obs, action_set):
        # Your agent logic here
        return "click('some_element')"

class MyAgentArgs(REAL.AbstractAgentArgs):
    def __init__(self):
        super().__init__()
        self.agent_name = "my_custom_agent"

# Use your custom agent
harness = REAL.harness(
    agentargs=MyAgentArgs(),
    task_type="omnizon",
    leaderboard=False
)

results = harness.run()
```

### Parallel Local Evaluation

```python
harness = REAL.harness(
    model="gpt-4o",
    num_workers=4,        # Run 4 tasks in parallel
    use_cache=True,       # Cache results for faster re-runs
    results_dir="./results"
)
```

## Configuration Options

### Model Configuration

```python
# OpenAI models
model="gpt-4o"
model="gpt-4o-mini"

# Anthropic models  
model="sonnet-3.7"
model="sonnet-3.5"

# OpenRouter models
model="openrouter/deepseek/deepseek-r1:free"
model="openrouter/anthropic/claude-3.5-sonnet"
```

### Task Selection

```python
# Run all tasks (default)
# No task parameters needed

# Run specific task type
task_type="omnizon"        # Amazon-like tasks
task_type="dashdish"       # DoorDash-like tasks  
task_type="fly-unified"    # Flight booking tasks

# Run specific task
task_name="webclones.omnizon-1"

# Run specific task ID within type
task_type="omnizon"
task_id=1
```

### Browser Configuration

```python
headless=True,                    # Run without GUI (default: True)
browser_dimensions=(1280, 720),   # Browser window size
max_steps=25,                     # Maximum actions per task (default: 25)
```

### Observation Configuration

```python
use_html=False,          # Include HTML in observations (default: False)
use_axtree=True,         # Include accessibility tree (default: True)  
use_screenshot=True,     # Include screenshots (default: True)
```

### Execution Options

```python
num_workers=1,           # Number of parallel workers (default: 1)
use_cache=True,          # Cache results (default: True)
cache_only=False,        # Only use cached results (default: False)
force_refresh=False,     # Force re-run cached tasks (default: False)
results_dir="./results", # Results directory (default: "./results")
```

## Available Tasks

The REAL Bench includes realistic web applications across different domains:

| App Type | Task Prefix | Example Tasks |
|----------|-------------|---------------|
| 🛒 E-commerce (Amazon-like) | `omnizon` | Buy a laptop, find gifts |
| 🍔 Food Delivery (DoorDash-like) | `dashdish` | Order dinner, find restaurants |
| ✈️ Travel (United Airlines-like) | `fly-unified` | Book flights, check schedules |
| 🏡 Accommodation (Airbnb-like) | `staynb` | Reserve rooms, browse properties |
| 📅 Calendar (Google Calendar-like) | `gocalendar` | Schedule meetings, set reminders |
| 📬 Email (Gmail-like) | `gomail` | Compose emails, manage inbox |
| 🍽️ Dining (OpenTable-like) | `opendining` | Book restaurants, find dining |
| 👔 Professional (LinkedIn-like) | `networkin` | Accept connections, browse profiles |
| 🚗 Rideshare (Uber-like) | `udriver` | Book rides, check prices |
| 💼 Freelance (UpWork-like) | `topwork` | Find gigs, browse jobs |
| 🏠 Real Estate (Zillow-like) | `zilloft` | Browse houses, search properties |

Each task type has multiple numbered variants (e.g., `omnizon-1`, `omnizon-2`, etc.) with different scenarios and difficulty levels.

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```bash
# Make sure your API keys are set
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key" 
export REAL_API_KEY="your-key"
```

**2. Playwright Installation Issues**
```bash
# Force reinstall Playwright browsers
playwright install --force

# On Apple Silicon, install Playwright first
brew install --cask playwright
```

**3. Ray Parallel Execution Issues**
```bash
# Install Ray for parallel execution
pip install ray

# If Ray fails to initialize, run sequentially
num_workers=1
```

**4. Task Loading Errors**
- Check that `task_name` follows the format `webclones.{task-type}-{id}`
- Verify the task exists in the available task list
- Check for typos in task type names

**5. Leaderboard Submission Failures**
- Verify your REAL API key is correct
- Check that `model_id_name` matches your model
- Ensure `run_name` is unique for your submissions
- Check network connectivity to realevals.xyz

### Performance Optimization

**1. Use Caching**
```python
use_cache=True,      # Enable result caching
cache_only=True,     # Only use cached results (for testing)
```

**2. Parallel Execution**
```python
num_workers=4,       # Run multiple tasks in parallel
```

**3. Reduce Observation Size**
```python
use_html=False,      # Disable HTML observations
use_screenshot=False, # Disable screenshots if not needed
```

### Getting Help

- **Documentation**: Check the main [README.md](../README.md)
- **Examples**: Browse the [example/](../example/) directory
- **Issues**: Report bugs on [GitHub Issues](https://github.com/agi-inc/agisdk/issues)
- **Community**: Join the AGI Inc. community discussions

## Examples

See the [example/](../example/) directory for complete working examples:

- **`starter.py`**: Simplest possible implementation
- **`custom.py`**: Template for custom agents  
- **`hackable.py`**: Advanced agent with full configuration
- **`nova.py`**: Direct browser control example

Each example includes detailed comments and configuration options to help you get started quickly.