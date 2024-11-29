"""
SPDX-License-Identifier: Apache-2.0
Copyright : JPMorganChase

CodeQUEST 
(
    Code Quality Understanding and 
    Enhancement System Toolkit
)
"""
import os
import time
from typing import Dict, Type, Tuple

from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import ChatPromptTemplate

from codequest.prompts import (
    CodeQuestTemplate,
    CodeQUESTBaselineEvalPrompt,
    CodeQUESTDimensionEvalPrompt,
    CodeQUESTAggPrompt,
    CodeQUESTOptimizerPrompt,
    CoTOptimizerPrompt,
)

class CodeQUESTParser(BaseOutputParser[str]):
    """LLM Output Parser, defined by the prompt template"""

    prompt_template: Type[CodeQuestTemplate]

    class Config:
        arbitrary_types_allowed = True

    def parse(self, text: str) -> Dict[str, str]:
        """Parse the text based on the
        parse_response method defined in the prompt_template

        :param text: LLM output tokens
        :type text: str
        :return: parsed dictionary
        :rtype: Dict[str, str]
        """
        return self.prompt_template.parse_response(text)


class CodeQUESTBaseLLM:
    """
    Constructor defining the interface with OpenAI models
    """

    prompt_template: CodeQuestTemplate

    def __init__(
        self,
        model_name: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        *args,
        **kwargs,
    ) -> None:
        """Base LLM Constructor, define the model, chat prompt template,
        and the LLM chain

        :param model_name: name of the OpenAI model
        :type model_name: str
        :param temperature: LLM Sampling Temperature, defaults to 0.2
        :type temperature: float, optional
        :param max_tokens: Maximum number of output tokens, defaults to 2048
        :type max_tokens: int, optional
        """
        self.model_name = model_name
        self.chat_prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompt_template.get_system()),
                ("human", self.prompt_template.get_human()),
            ]
        )

        self.temperature = temperature
        self.max_tokens = max_tokens

        if 'OPENAI_API_KEY' not in os.environ: 
            raise ValueError("env variable OPENAI_API_KEY must be specified")
        
        self.model = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            *args,
            **kwargs,
        )

        self.parser = CodeQUESTParser(prompt_template=self.prompt_template)
        self.chain = self.chat_prompt_template | self.model | self.parser

    def __call__(self, input_args: Dict[str, str]) -> Tuple[str, float, float]:
        """Invoke the Chain defined and call back the total cost

        :param input_args: input arguments for the chain
        :type input_args: Dict[str, str]
        :return: parsed output, total cost and runtime
        :rtype: Tuple[str, float, float]
        """
        with get_openai_callback() as cb:
            start_time = time.time()
            chain_out: str = self.chain.invoke(input_args)
            runtime = round(time.time() - start_time, 4)

        return chain_out, cb.total_cost, runtime


class CoTEvalLLM(CodeQUESTBaseLLM):
    """Define Baseline Code Eval LLM using CoT"""

    prompt_template = CodeQUESTBaselineEvalPrompt


class DimEvalLLM(CodeQUESTBaseLLM):
    """Define Dimension-wise Code Eval"""

    prompt_template = CodeQUESTDimensionEvalPrompt


class AggLLM(CodeQUESTBaseLLM):
    """Define Aggregation LLM summarising findings
    across multiple retries across the same dimension
    """

    prompt_template = CodeQUESTAggPrompt


class CoTOptLLM(CodeQUESTBaseLLM):
    """Dfine the Baseline Optimizer LLM improving
    the code quality based on the feedback
    """

    prompt_template = CoTOptimizerPrompt


class CodeQUESTOptLLM(CodeQUESTBaseLLM):
    """Define Optimization LLM improving the code
    quality based on the feedback
    """

    prompt_template = CodeQUESTOptimizerPrompt
