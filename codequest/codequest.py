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
from typing import List, Any, Dict, Type

import json
import pandas as pd
import ast
import subprocess

from codequest.evaluator import Evaluator
from codequest.optimizer import Optimizer

import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def format_dimwise_feedback_for_improver(report: pd.DataFrame) -> str:
    return json.dumps(report.to_dict(orient="records"), indent=2)


def script_to_module_conversion(script_dir_path: str, script_name: str) -> str:
    return script_dir_path.replace("/", ".") + f".{script_name}"


def load_script(script_path: str) -> str:
    with open(script_path, "r") as file:
        return file.read()


def check_syntax(code: str):
    try:
        ast.parse(code)
    except SyntaxError as e:
        logger.info("Syntax error detected:\n")
        logger.info(f"Line {e.lineno}: {e.msg}")
        raise e


def code_tester(
    script_path: str,
    test_cases_path: str,
):
    return subprocess.run(
        [
            "pytest",
            test_cases_path,
            "--tb",
            "short",
            "--func_path",
            script_path,
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )


class QUESTer:
    """Main Class for CodeQUEST Improvement Cycles"""

    def __init__(
        self,
        evaluator: Type[Evaluator],
        optimizer: Type[Optimizer],
        max_iterations: int = 5,
        target_quality_score: int = 5,
    ) -> None:
        """Instantiate a QUESTer Object

        :param evaluator: Evaluator or its inheritance
        :type evaluator: Type[Evaluator]
        :param optimizer: Optimizer or its inheritance
        :type optimizer: Type[Optimizer]
        :param max_iterations: maximum number of code improvement cycles, 
            defaults to 5
        :type max_iterations: int, optional
        :param target_quality_score: targted code quality score, 
            defaults to 5
        :type target_quality_score: int, optional
        """
        self.evaluator = evaluator
        self.optimizer = optimizer

        self.max_iterations = max_iterations
        self.target_quality_score = target_quality_score

    def __call__(
        self, script_path: str, testcases_path: str | None = None
    ) -> Dict[str, str | List[Any]]:
        """Invoke Actor-Critic Improvement Cycle

        :param script_path: path to the script to be evaluate & optimized
        :type script_path: str
        :param testcases_path: path to which the testcases are stored
            defaults to None
        :type testcases_path: str | None, optional
        :return: results for the full improvement cycle
        :rtype: Dict[str, str | List[Any]]
        """
        res = {}
        res["script_path"] = script_path
        trajects = []

        script_dir = os.path.dirname(script_path)
        script_name = os.path.basename(script_path)

        script_info = script_name.rsplit(".", 1)
        script_name_without_ext, ext = script_info[0], script_info[1]

        code = load_script(script_path)

        # initial eval
        eval_res = self.evaluator(code)
        quest_cost = eval_res["runcost"]
        quest_time = eval_res["runtime"]
        score = eval_res["score"]
        logger.info(f"Iteration:0 | Score: {score}")
        if "dimension_reports" in eval_res:
            insight = format_dimwise_feedback_for_improver(eval_res["report"])
        else:
            insight = eval_res["insight"]

        trajects.append(
            {
                "iteration": 0,
                "code": code,
                "score": score,
                "eval_res": eval_res,
                "accepted": False,
            }
        )
        # skip cycle for high-quality code
        if score > self.target_quality_score:
            res["cost"] = quest_cost
            res["time"] = quest_time
            res["trajectories"] = trajects
            return res

        for iteration in range(1, self.max_iterations + 1):
            # opt attempt
            optout = self.optimizer(code, insight)
            candidate = optout["code"]
            quest_cost += optout["runcost"]
            quest_time += optout["runtime"]

            # validation
            ## syntax check
            if ext == "py":
                try:
                    check_syntax(candidate)
                except SyntaxError:
                    trajects.append(
                        {
                            "iteration": iteration,
                            "code": candidate,
                            "eval_res": "SynTaxError",
                            "accepted": False,
                        }
                    )
                    continue

                ## test candidate
                if testcases_path:
                    candidate_file_name_without_ext = (
                        script_name_without_ext + f"_iteration_{iteration}_candid"
                    )
                    candidate_file_name = candidate_file_name_without_ext + f".{ext}"
                    candidate_tmp_path = os.path.join(script_dir, candidate_file_name)

                    with open(candidate_tmp_path, "w") as file:
                        file.write(candidate)
                    file.close()

                    test_out = code_tester(
                        script_to_module_conversion(
                            script_dir, candidate_file_name_without_ext
                        ),
                        testcases_path,
                    )
                    os.remove(candidate_tmp_path)

                    if test_out.returncode != 0:
                        logger.info(
                            f"""Found Test error for {candidate_tmp_path} at iteration {iteration}: 
                            \n {test_out.returncode} \n {test_out.stdout}"""
                        )
                        trajects.append(
                            {
                                "iteration": iteration,
                                "code": candidate,
                                "eval_res": "TestError",
                                "accepted": False,
                            }
                        )
                        continue

            # re-evaluation
            re_eval_res = self.evaluator(candidate)
            quest_cost += re_eval_res["runcost"]
            quest_time += re_eval_res["runtime"]
            curr_score = re_eval_res["score"]

            if curr_score > score:
                # update the candidate
                code = candidate
                score = curr_score
                logger.info(f"Iteration {iteration} | New high score achieved {score}")
                if "dimension_reports" in eval_res:
                    insight = format_dimwise_feedback_for_improver(
                        re_eval_res["report"]
                    )
                else:
                    insight = re_eval_res["insight"]

                new_version_path = os.path.join(
                    script_dir,
                    script_name_without_ext + f"_iteration_{iteration}" + f".{ext}",
                )
                logger.info(
                    f"Iteration {iteration} | Improved version -> {new_version_path}"
                )
                with open(new_version_path, "w") as file:
                    file.write(code)
                file.close()
                trajects.append(
                    {
                        "iteration": iteration,
                        "code": code,
                        "score": score,
                        "eval_res": re_eval_res,
                        "accepted": True,
                    }
                )
                # early-termination
                if score > self.target_quality_score:
                    res["cost"] = quest_cost
                    res["time"] = quest_time
                    res["trajectories"] = trajects
                    return res
            else:
                trajects.append(
                    {
                        "iteration": iteration,
                        "code": candidate,
                        "score": curr_score,
                        "eval_res": re_eval_res,
                        "accepted": False,
                    }
                )
                continue

        res["cost"] = quest_cost
        res["time"] = quest_time
        res["trajectories"] = trajects
        return res
