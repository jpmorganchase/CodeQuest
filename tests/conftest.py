"""
SPDX-License-Identifier: Apache-2.0
Copyright : JPMorganChase

CodeQUEST 
(
    Code Quality Understanding and 
    Enhancement System Toolkit
)
"""

def pytest_addoption(parser):
    parser.addoption(
        "--func_path",
        action="store",
        default="",
        help="Path of the function to be tested",
    )
