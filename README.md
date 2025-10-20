<p align="center">
  <h1 align="center">🚀 AGI SDK</h1>
</p>


<p align="center">
  <a href="https://arxiv.org/abs/2504.11543">📄 Paper</a> •
  <a href="https://www.theagi.company/blog/introducing-real-bench">📝 Blog</a> •
  <a href="https://www.theagi.company">🏢 AGI Inc</a> •
  <a href="https://www.realevals.ai">🏆 Leaderboard</a>
</p>


<p align="center">
  <a href="https://pypi.org/project/agisdk"><img src="https://img.shields.io/pypi/v/agisdk?color=brightgreen" alt="PyPI version"></a>
  <a href="https://pypi.org/project/agisdk"><img src="https://img.shields.io/pypi/pyversions/agisdk" alt="Python versions"></a>
  <a href="https://static.pepy.tech/badge/agisdk"><img src="https://static.pepy.tech/badge/agisdk" alt="Downloads"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/agi-inc/agisdk" alt="License"></a>
</p>

<p align="center">
  <b>Build, evaluate, and level up your AI agents for the real web.</b>
</p>

<p align="center">
  <img src="docs/images/real.gif" alt="REAL benchmark demo" width="600">
</p>




# ✨ What is AGI SDK?

**AGI SDK** is a toolkit for **building** and **evaluating** AI browser agents in real-world environments.

It powers [REAL Bench](https://realevals.xyz): the first high-fidelity benchmark for AI agents navigating modern websites like Amazon, DoorDash, Airbnb, and more.

🔹 **Train agents** to browse and interact with real apps
🔹 **Benchmark agents** with robust, standardized tasks
🔹 **Submit to the leaderboard** and see how your agents stack up!

> **TL;DR**: Go from “idea” to “benchmarked agent” in <60 seconds

## 🛠️ Installation (30 s)

```bash
# Install the SDK using local source codes
pip install .

# Install Playwright browser dependencies
playwright install --force

# Set your LLM API key (for evaluation)
export XAI_API_KEY="your-api-key"   # any supported provider key works
```

✅ Supports Grok models! <br>

On Apple Silicon run `brew install --cask playwright` first.


## ⏱️ 10-second Quick-Start

Here's a minimal example to get you started for benchmarking an AI agent on the REAL Bench environment using grok models:

```bash
python example/hackable.py --model grok-4-fast-reasoning --headless True \
--workers 8 --results_dir all_results
```


## 📊 Evaluation Accuracy

### Overall Performance For the Improved Benchmark

| Metric | Value |
|--------|-------|
| **Total Tasks** | 102 |
| **Success Rate** | 59.8% (61/102) |

### Performance by Task Type

| Website | Tasks | Success | Success Rate |
|---------|-------|---------|--------------|
| **networkin** | 15 | 13 | 86.67% |
| **omnizon** | 14 | 10 | 71.43% |
| **dashdish** | 12 | 9 | 75.00% | 
| **topwork** | 11 | 5 | 45.45% | 
| **gocalendar** | 2 | 1 | 50.00% | 
| **gomail** | 13 | 5 | 38.46% | 
| **opendining** | 9 | 5 | 55.56% | 
| **staynb** | 7 | 2 | 28.57% | 
| **zilloft** | 8 | 5 | 62.50% | 
| **udriver** | 8 | 4 | 50.00% | 
| **marrisuite** | 3 | 2 | 66.67% |

> **Note**: Results based on evaluation with `grok-4-fast-reasoning` model. Performance may vary with different models and configurations.

📁 **[Access detailed results logs on Google Drive](https://drive.google.com/file/d/1IawGFUvwedsRseJAaYXZJWsBjI-L7I3Q/view?usp=sharing)**

## 🤝 Contributing

We welcome contributions of all kinds:
- 📢 Feature requests? [Open an Issue](https://github.com/agi-inc/agisdk/issues)
- 🐛 Bug reports? [Create a ticket](https://github.com/agi-inc/agisdk/issues)
- 📈 Improve REAL tasks? Join our [Project Board](https://github.com/orgs/agi-inc/projects/2)
- 🛠️ Submit code? Fork + PR - we love clean commits!

Let's build the future of agents together. 🔥

## 💬 Community
- [Join our Discord](https://discord.gg/c95EJDfXzx) (_coming soon!_)
- [Follow AGI Inc. on LinkedIn](https://www.linkedin.com/company/the-agi-company/)

## ⭐️ Why AGI SDK?

Because **your agents deserve better** than toy environments. <br>
Because **the real web is messy** and that's where the magic happens. <br>
Because **the future is agentic** and it starts here.
