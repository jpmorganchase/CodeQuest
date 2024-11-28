"""
SPDX-License-Identifier: Apache-2.0
Copyright : JPMorganChase

CodeQUEST 
(
    Code Quality Understanding and 
    Enhancement System Toolkit
)
"""

import re
from textwrap import dedent
from typing import Dict, List
import json_repair

CODE_QUALITY_DIMENSIONS = {
    "Readability": {
        "0": "Both, variable and function names are descriptive and meaningful.",
        "1": "The code consistently follows a single specific code style guide.",
        "2": "There are comments that clearly explain complex or non-obvious parts of the code provided, without assuming prior knowledge.",
        "3": "The code provided is free of unexplained constants or magic numbers.",
        "4": "Each existing function is dedicated to a single task.",
    },
    "Maintainability": {
        "0": "The code provided is organized in a logical and understandable manner, allowing for easy comprehension.",
        "1": "The code provided strictly adheres to the DRY (Do not Repeat Yourself) principle, avoiding unnecessary repetition.",
        "2": "Code features can be added or modified without affecting existing functionality.",
        "3": "The code provided is effectively free of duplication, promoting efficiency and maintainability.",
        "4": "There are clear interfaces between different parts of the code provided, facilitating seamless interaction.",
    },
    "Testability": {
        "0": "The structure of the code provided facilitates easy mocking of dependencies.",
        "1": "The code provided produces consistent and predictable outputs for specific inputs.",
        "2": "The code provided is free of global states and variables.",
        "3": "The code provided is free from deep nesting or complex control flow, that could complicate testing.",
        "4": "The code provided is organized in a way that allows the straightforward measurement of code coverage.",
    },
    "Efficiency": {
        "0": "The code provided makes efficient use of data structures.",
        "1": "The code provided avoids creating unnecessary objects or data.",
        "2": "The code provided avoids suboptimal computations, such as unnecessary loops or repeated operations that could be optimized.",
        "3": "The code provided promotes the efficient use of system resources.",
        "4": "The code provided addresses any existing bottlenecks that could slow down the code.",
    },
    "Robustness": {
        "0": "Does the code provided validate and sanitize inputs in all relevant scenarios?",
        "1": "Does the code provided handle edge cases and unexpected inputs gracefully in all relevant scenarios?",
        "2": "Are there appropriate error handling and exception handling mechanisms in place for all relevant scenarios?",
        "3": "Does the code provided handle errors and exceptions gracefully in all relevant scenarios?",
        "4": "Does the code provided accounts for any potential race conditions, concurrency issues, or deadlock situations in all relevant scenarios?",
    },
    "Security": {
        "0": "The code provided consistently sanitizes user inputs to prevent injection attacks.",
        "1": "The code provided is completely free of hardcoded sensitive data, such as passwords and API keys.",
        "2": "The code provided adheres to established best practices for secure coding.",
        "3": "The code provided implements comprehensive error handling to prevent leakage of sensitive information.",
        "4": "The code provided utilizes secure communication protocols when performing network operations.",
    },
    "Documentation": {
        "0": "Comments are provided to explain non-obvious parts of the code.",
        "1": "There is a concise and clear description of the code's functionality.",
        "2": "Input parameters are documented.",
        "3": "Output values are documented.",
        "4": "Side effects are documented.",
    },
    "Modularity": {
        "0": "The code provided is divided into small, independent functions that perform specific tasks.",
        "1": "Individual parts of the code provided can be used, modified, and tested independently without affecting other parts.",
        "2": "The code provided avoids deep nesting and complex control flow structures.",
        "3": "The code provided adheres to the principles of high cohesion (related functionality within a single unit) and low coupling (minimal dependencies between units).",
        "4": "Different parts of the code are separated by well-defined interfaces to facilitate communication and maintainability.",
    },
    "Scalability": {
        "0": "The code provided is designed to handle increased data loads efficiently, or can it be easily adapted to do so.",
        "1": "The code provided is designed to handle an increased number of users efficiently, or can it be easily adapted to do so.",
        "2": "The code provided makes efficient use of resources, such as CPU and memory.",
        "3": "The code provided is free of bottlenecks that could potential limit scalability.",
        "4": "The code provided is designed to work in a distributed environment efficiently, or can it be easily adapted to do so.",
    },
    "Portability": {
        "0": "The code provided avoids relying on any platform-specific features or behavior.",
        "1": "The code provided can run in different environments without requiring major changes.",
        "2": "The code provided is free of hardcoded file paths or URLs that would limit portability.",
        "3": "The code provided uses standard libraries and APIs as much as possible.",
        "4": "All dependencies are clearly specified and easy to install.",
    },
}


class CodeQuestTemplate:
    role: str = "You are a helpful nad harmless AI software engineer. You must provide an answer to the following request. Be brief and precise."

    instruct: str = ""

    @classmethod
    def get_system(
        cls,
    ):
        return cls.role + "\n"

    @classmethod
    def get_human(
        cls,
    ):
        if not cls.instruct:
            raise NotImplementedError(
                f"You must implement your own instruct template | curr: {cls.instruct}"
            )
        return cls.instruct

    @classmethod
    def parse_response(cls, text: str) -> Dict[str, str]:
        pattern = r"``json(.*?)```"
        regex = re.compile(pattern, re.DOTALL)
        texts = regex.findall(text)
        if not texts:
            raise ValueError(f"Ill-formed LLM output: {text}")

        return json_repair.loads(texts[0])


class CodeQUESTBaselineEvalPrompt(CodeQuestTemplate):
    instruct = dedent(
        """
    ### CODE:
    ```
    {code}
    ```

    ### TASK:
    Think step by step to produce both a quantitative and qualitative assessment of the CODE provided. 
    * Your qualitative assessment must be a short summary about the quality of the CODE.
    * Your quantitative assessment must be an integer on a scale from -5 to 5, which respectively represent the low and high-quality ends of the scale. 
    Both types of evaluations must agree with each other.
        
    ### OUTPUT:
    Return your answer in a valid JSON as shown below:
    ```json
    {{
        "insight": <qualitative assessment:str>,
        "score": <quantitative assessment:int>
    }}
    ```
    """
    ).strip()


class CodeQUESTDimensionEvalPrompt(CodeQuestTemplate):
    instruct = dedent(
        """
    ### CODE: 
    ```
    {code}
    ```

    ### STATEMENTS: 
    {dimension_statements} 

    ### TASK:
    Think step by step to assess the veracity of each STATEMENT in light of the CODE provided. 
    Your answer to each statement must come from one of the following: 
        * -1 if the statement is false, 
        * 1 if the statement is true, 
        * 0 if the statement is not applicable or there is not enough evidence in the CODE to address it. 
        
    You must also provide a short summary about the quality of the code from a {quality_dimension} perspective, justifying your answers across the various statements. 
    
    ### OUTPUT:
    Return your answer in valid JSON as shown below:
    ```json
    {{   
        "insight": <code quality summary:str>,
        "scores": [<score_to_statement1:int>, <score_to_statement2:int>, ...]
    }}
    """
    ).strip()


class CodeQUESTAggPrompt(CodeQuestTemplate):
    instruct = dedent(
        """
    ### CODE:
    ```
    {code}
    ```

    ### List of individual comments: 
    {insights} 

    ### Task: 
    You are given a list of individual comments about the same code script. 
    Think step by step to build a comprehensive summary based on the individual comments. 

    ### OUTPUT:
    Return your answer in valid JSON as shown below:
    ```json
    {{   
        "summary": <code quality summary across comments:str>
    }}
    """
    ).strip()


class CodeQUESTOptimizerPrompt(CodeQuestTemplate):
    instruct = dedent(
        """
    ### Code: 
    {code}  
    
    ### Quality Dimensions Feedback: 
    {quality_insight}  
    
    ### TASK: 
    You are provided with a code script and detailed feedback for each quality dimension.
    For each quality dimension, you are provided with:
        * A score from -5 to 5. The higher the score, the better the quality.
        * Dimension insights, highlighting potential areas of improvement.

    Think step by step to complete the following:
        1) For each dimension, reflect on the score and insights.
        2) Condense a list of improvement points, so that the code would be evaluated at a higher score for each dimension.
        3) Improve the code script according to the improvement points, prioritizing dimensions with lower scores.
        4) Return:
            * the improvement points identified
            * the improved version of the code script 
            * explanations for each of the changes you've made
    Note: 
    * ALL improvement points MUST be addressed via meaningful changes to the code.
    
    ### OUTPUT: 
    Your final output contains two parts:
    Return your answer in a valid JSON as shown below:
    ```json
    {{   
        "improvement_points": List[str],
        "explanation_report": List[str]
    }}

    Then quote your code in the following section
    ```improved_code
    {{improved_code_here}}
    ```
    """
    ).strip()

    @classmethod
    def parse_response(cls, text: str) -> Dict[str, str|List[str]]:
        res = super().parse_response(text)

        pattern = r"``improved_code(.*?)```"
        regex = re.compile(pattern, re.DOTALL)
        codes = regex.findall(text)
        if not codes:
            raise ValueError(f"Improvement attempted failed to output code: {text}")

        res.update(dict(code=codes[0]))
        return res


class CoTOptimizerPrompt(CodeQUESTOptimizerPrompt):
    instruct = dedent(
        """
    ### Code: 
    {code}  
    
    ### Feedback: 
    {quality_insight}  
    
    ### TASK: 
    You are provided with a code script and feedback about its quality.
    Specifically, the feedback includes:
        * A qualitative assessment, which is a short summary about the quality of the CODE.
        * A quantitative assessment, which is an integer on a scale from -5 to 5, respectively representing the low and high-quality ends of the scale. 

    Think step by step to complete the following:
        1) Reflect on the feedback provided.
        2) Condense a list of improvement points, so that the code would be evaluated at a higher score.
        3) Improve the code script according to the improvement points.
        4) Return:
            * the improvement points identified
            * the improved version of the code script 
            * explanations for each of the changes you've made
    Note: 
    * ALL improvement points MUST be addressed via meaningful changes to the code.
    
    ### OUTPUT: 
    Your final output contains two parts:
    Return your answer in a valid JSON as shown below:
    ```json
    {{   
        "improvement_points": List[str],
        "explanation_report": List[str]
    }}

    Then quote your code in the following section
    ```improved_code
    {{improved_code_here}}
    ```
    """
    ).strip()
