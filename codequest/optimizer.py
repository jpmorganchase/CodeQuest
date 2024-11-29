"""
SPDX-License-Identifier: Apache-2.0
Copyright : JPMorganChase

CodeQUEST 
(
    Code Quality Understanding and 
    Enhancement System Toolkit
)
"""
from typing import Dict, List
from codequest.base import CoTOptLLM, CodeQUESTOptLLM


class Optimizer:
    """Baseline Optimizer for Code Quality"""

    def __init__(
        self,
        model_name: str = "gpt-4o",
        temperature: float = 0.2,
        max_toknes: int = 2048,
    ) -> None:
        """Instentiate an optimizer object

        :param model_name: name of the LLM, defaults to "gpt-4o"
        :type model_name: str, optional
        :param temperature: sampling temperature, defaults to 0.2
        :type temperature: float, optional
        :param max_toknes: maximum number of the output tokens 
            defaults to 2048
        :type max_toknes: int, optional
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_toknes

        self.model_args = (model_name, temperature, max_toknes)
        self._set_up()

    def _set_up(
        self,
    ) -> None:
        """
        Define the llm components within the Optimizer Class
        """
        self.opt_llm = CoTOptLLM(*self.model_args)

    def __call__(self, code: str, insight: str) -> Dict[str, str | float | List[str]]:
        """Invoke the underlying LLM

        :param code: code to be optimized
        :type code: str
        :param insight: qualitative assessment provided by the evaluator
        :type insight: str
        :return: Dictionary containing new code, cost and time expensed
        :rtype: Dict[str, str | float]
        """
        chain_out, runcost, runtime = self.opt_llm(
            {"code": code, "quality_insight": insight}
        )
        chain_out.update({"runcost": runcost, "runtime": runtime})
        return chain_out


class CodeQUESTOptimizer(Optimizer):
    """CodeQUEST Code Quality Optimizer"""

    def _set_up(self) -> None:
        self.opt_llm = CodeQUESTOptLLM(*self.model_args)
