"""
SPDX-License-Identifier: Apache-2.0
Copyright : JPMorganChase

CodeQUEST 
(
    Code Quality Understanding and 
    Enhancement System Toolkit
)
"""
from typing import List, Dict, Union, Tuple

from concurrent.futures import Future, ThreadPoolExecutor
from multiprocessing import cpu_count

import numpy as np
import pandas as pd

from codequest.base import (
    CoTEvalLLM,
    DimEvalLLM,
    AggLLM,
)
from codequest.prompts import CODE_QUALITY_DIMENSIONS


class Evaluator:
    """Baseline code Evaluator powered by Zero-shot CoT"""

    def __init__(
        self,
        model_name: str = "gpt-4o",
        temperature: float = 0.2,
        max_toknes: int = 2048,
        num_retries: int = 1,
    ) -> None:
        """Instantiate an Evaluator object

        :param model_name: name of the evaluator model, defaults to "gpt-4o"
        :type model_name: str, optional
        :param temperature: default temperature, defaults to 0.2
        :type temperature: float, optional
        :param max_toknes: maximum number of generated tokens, defaults to 2048
        :type max_toknes: int, optional
        :param num_retries: number of retries per input for _eval(), defaults to 1
        :type num_retries: int, optional
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_toknes

        self.executor = ThreadPoolExecutor(max_workers=2 * cpu_count() - 1)
        self.num_retries = num_retries

        self.model_args = (model_name, temperature, max_toknes)
        self._set_up()

    def _set_up(
        self,
    ) -> None:
        """
        Define the llm components within the Evaluator Class
        """
        self.eval_llm = CoTEvalLLM(*self.model_args)
        self.agg_llm = AggLLM(*self.model_args)

    def _eval(self, code: str) -> Tuple[List[int], List[str], float, float]:
        """Perform parallel retry eval for a specified dimension

        :param code: code to be evaluated
        :type code: str
        :param dimension: dimension to be evaluated
        :type dimension: str
        :param dimension_statements: list of questions/statements
            for a dimension
        :type dimension_statements: List[str]
        :return: list of scroes for each dimension,
            list of qualitative evaluation for each dimension,
            total run cost and total run time
        :rtype: Tuple[List[int], List[str], float, float]
        """
        scores, insights = [], []
        total_run_cost = 0

        input_args = dict(code=code)

        futures = [
            self.executor.submit(
                self.eval_llm.__call__,
                input_args,
            )
            for _ in range(self.num_retries)
        ]

        tmp_run_times = []
        for future in futures:
            chain_out, run_cost, run_time = future.result()
            tmp_run_times.append(run_time)

            total_run_cost += run_cost

            scores.append(int(chain_out["score"]))
            insights.append(chain_out["insight"])

        return scores, insights, total_run_cost, max(tmp_run_times)

    def _agg_evals(
        self, code: str, scores: List[float], insights: List[str]
    ) -> Tuple[float, str, float, float]:
        """Aggregate the evaluation across a few number of retries

        :param code: code evaluated
        :type code: str
        :param scores: scores for the code across each retry
        :type scores: List[float]
        :param insights: list of qualitative assessment
        :type insights: List[str]
        :return: score, insight, cost and run time
        :rtype: Tuple[float, str, float, float]
        """
        run_cost, run_time = 0.0, 0.0
        score = float(np.mean(scores))

        if self.num_retries == 1:
            insight = insights[0]
            return score, insight, run_cost, run_time

        chain_out, run_cost, run_time = self.agg_llm(
            {"code": code, "insights": insights},
        )
        insight = chain_out["summary"]
        return score, insight, run_cost, run_time

    def __call__(self, code: str) -> Dict[str, Union[float, str, pd.DataFrame]]:
        """Perform evaluation, aggregation and report compilation

        :param code: code script to be evaluated
        :type code: str
        :return: result collections
        :rtype: Dict[str, Union[float, str, pd.DataFrame]]
        """
        scores, insights, eval_run_cost, eval_run_time = self._eval(code)
        score, insight, agg_run_cost, agg_run_time = self._agg_evals(
            code, scores, insights
        )

        total_run_cost = eval_run_cost + agg_run_cost
        total_run_time = eval_run_time + agg_run_time

        eval_report = pd.DataFrame(
            {
                "code_score": [score],
                "code_insight": [insight],
                "code_runtime": [int(total_run_time)],
                "code_runcost": [round(total_run_cost, 3)],
                "code_scores": [scores],
                "code_insights": [insights],
            }
        )
        return {
            "code": code,
            "score": score,
            "insight": insight,
            "report": eval_report,
            "runtime": total_run_time,
            "runcost": total_run_cost,
        }


class CodeQUESTEvaluator(Evaluator):
    """CodeQUEST code Evaluator"""

    def _set_up(
        self,
    ) -> None:
        self.eval_llm = DimEvalLLM(*self.model_args)
        self.agg_llm = AggLLM(*self.model_args)

    def _eval(
        self, code: str, dimension: str, dimension_statements: List[str]
    ) -> Tuple[List[int], List[str], float, float]:
        """Perform parallel retry eval for a specified dimension
        For the code quality score, we take the sum across each single
        dimension

        :param code: code to be evaluated
        :type code: str
        :param dimension: dimension to be evaluated
        :type dimension: str
        :param dimension_statements: list of questions/statements
            for a dimension
        :type dimension_statements: List[str]
        :return: list of scroes for each dimension,
            list of qualitative evaluation for each dimension,
            total run cost and total run time
        :rtype: Tuple[List[int], List[str], float, float]
        """
        dim_scores, dim_insights = [], []
        total_run_cost = 0

        input_args = dict(
            code=code,
            quality_dimension=dimension,
            dimension_statements=dimension_statements,
        )

        futures = [
            self.executor.submit(
                self.eval_llm.__call__,
                input_args,
            )
            for _ in range(self.num_retries)
        ]

        tmp_run_times = []
        for future in futures:
            chain_out, run_cost, run_time = future.result()
            tmp_run_times.append(run_time)

            total_run_cost += run_cost

            dim_scores.append(sum([int(num) for num in chain_out["scores"]]))
            dim_insights.append(chain_out["insight"])

        total_run_time = max(tmp_run_times)

        return dim_scores, dim_insights, total_run_cost, total_run_time

    def _agg_evals(
        self, code: str, dim_scores: List[float], dim_insights: List[str]
    ) -> Tuple[float, str, float, float]:
        """Aggregated the results across different evaluation retries

        :param code: code evaluated
        :type code: str
        :param dim_scores: scores for each retry
        :type dim_scores: List[float]
        :param dim_insights: dimensions insights for each retry
        :type dim_insights: List[str]
        :return: dimension score, insight, run cost and run time
        :rtype: Tuple[float, str, float, float]
        """
        if self.num_retries == 1:
            dimension_score = dim_scores[0]
            dimension_insights = dim_insights[0]
            run_cost = 0.0
            run_time = 0.0
        else:
            dimension_score = float(np.mean(dim_scores))
            dimension_out, run_cost, run_time = self.agg_llm(
                {"code": code, "insights": dim_insights},
            )
            dimension_insights = dimension_out["summary"]

        return dimension_score, dimension_insights, run_cost, run_time

    def _agg_dims(
        self, code: str, quality_reports: List[pd.DataFrame]
    ) -> Tuple[float, str, pd.DataFrame, float, float]:
        """Aggregate the evaluation across different dimensions

        :param code: code evaluated
        :type code: str
        :param quality_reports: list of code quality reports
        :type quality_reports: List[pd.DataFrame]
        :return: quality score, insights, section of code quality reposts,
            total run time and total run cost
        :rtype: Tuple[float, str, pd.DataFrame, float, float]
        """
        quality_report_df = pd.concat(quality_reports, axis=0).reset_index(drop=True)
        code_quality_score = round(quality_report_df["dimension_score"].mean(), 2)

        code_quality_out, agg_run_cost, agg_run_time = self.agg_llm(
            {
                "code": code,
                "insights": quality_report_df["dimension_insights"].values,
            },
        )
        code_quality_insights = code_quality_out["summary"]
        total_run_cost = quality_report_df["dimension_runcost"].sum() + agg_run_cost
        total_run_time = quality_report_df["dimension_runtime"].max() + agg_run_time

        return (
            code_quality_score,
            code_quality_insights,
            quality_report_df[
                ["quality_dimension", "dimension_score", "dimension_insights"]
            ],
            total_run_time,
            total_run_cost,
        )

    def _dim_eval(
        self,
        code: str,
        dimension: str,
        dimension_statements: List[str],
    ) -> pd.DataFrame:
        """Evaluate a particular code quality dimension

        :param code: code to be evaluated
        :type code: str
        :param dimension: code quality dimension
        :type dimension: str
        :param dimension_statements: list of questions
            or statements for a particular dimension
        :type dimension_statements: List[str]
        :return: A collection of code quality and run time
            information
        :rtype: pd.DataFrame
        """
        (
            dim_scores,
            dim_insights,
            total_run_cost,
            total_run_time,
        ) = self._eval(code, dimension, dimension_statements)

        (
            dimension_score,
            dimension_insights,
            agg_cost,
            agg_time,
        ) = self._agg_evals(code, dim_scores, dim_insights)
        total_run_cost += agg_cost
        total_run_time += agg_time

        return pd.DataFrame(
            {
                "quality_dimension": [dimension],
                "dimension_score": [dimension_score],
                "dimension_insight": [dimension_insights],
                "dimension_runtime": [int(total_run_time)],
                "dimension_runcost": [round(total_run_cost, 3)],
                "dimension_socres": [dim_scores],
                "dimension_insights": [dim_insights],
            }
        )

    def __call__(self, code: str) -> Dict[str, Union[float, str, pd.DataFrame]]:
        """Evaluate the code for each single dimension
        and aggregate the result

        :param code: code to be evaluated
        :type code: str
        :return: A collection of code quality information
        :rtype: Dict[str, Union[float, str, pd.DataFrame]]
        """
        futures: List[Future] = []
        for quality_dimension, dimension_statements in CODE_QUALITY_DIMENSIONS.items():
            futures.append(
                self.executor.submit(
                    self._dim_eval,
                    *(
                        code,
                        quality_dimension,
                        dimension_statements,
                    ),
                )
            )
        dimension_reports: List[pd.DataFrame] = [future.result() for future in futures]

        (
            code_quality_score,
            code_quality_insights,
            code_quality_report,
            total_run_time,
            total_run_cost,
        ) = self._agg_dims(code, dimension_reports)

        return {
            "code": code,
            "score": code_quality_score,
            "insight": code_quality_insights,
            "report": code_quality_report,
            "runtime": total_run_time,
            "runcost": total_run_cost,
            "dimension_reports": dimension_reports,
        }
