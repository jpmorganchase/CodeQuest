# CodeQUEST
CodeQUEST (Code Quality Understanding and Enhancement System Toolkit)

CodeQUEST is a novel framework utilizing Large Language Models (LLMs) to assess and improve code across various quality dimensions, such as readability, security, maintainability, and efficiency. Inspired by the Actor-Critic method from Reinforcement Learning, our framework has two components:

- An Evaluator (Critic) that examines ten dimensions of code quality to provide both quantitative and qualitative evaluations.
- An Optimizer (Actor) that improves the code based on these evaluations.
In the code improvement cycle, the Optimizer grounds its improvement on the Evaluator's feedback, seeking higher code quality across multiple code quality dimensions jointly.

# Prerequisites
Ensure you have Python version 3.10 or higher installed on your system.

# Usage 

## Clone 
```bash
git clone <url>
```

## Installation 
```bash
python -m venv .venv
source .venv/bin/activate 
pip install -r requirements.txt
```

## Environment Variables
Ensure that you export OPENAI_API_KEY as part of your environment variables:
```bash
export OPENAI_API_KEY=<your key here>
```

## Tutorial 
Refer to **main.ipynb** for a detailed tutorial on how to use the framework, covering *Evaluation*, *Optimization* and the *Actor-Critic Loop* 

# License
CodeQUEST is licensed under the Apache-2.0 License. See the [LICENSE](LICENSE) file for details.


Open Source @ JPMorganChase
