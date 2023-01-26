#!/usr/bin/env python3.8
import json
import logging
import os
import re
import sys
from solver_utils import *
from collections import defaultdict

'''
NOTE: Need to make the solver script call this one, I think.
'''

partitioner = sys.argv[1]
problem_path = sys.argv[2]

# The timeout used for the first generation of paritions
initial_timeout = 1200000


def run_a_partition(partition, solver_opts: list, timeout):
    result = run_solver(partitioner, partition, solver_opts, timeout)
    return (partition, timeout, result)


def print_result(result):
    if result == "sat":
        print("found result SAT")
    elif result == "unsat":
        print("found result UNSAT")
    elif result == "unknown":
        print("found result UNKNOWN")


def get_logic(file):
    with open(file, "r") as f:
        content = f.read()
        m = re.search("set-logic ([A-Z_]+)", content)
        if m:
            return m[1]
    return None


def get_options_for_logic(logic: str):
    result = []
    if logic == "QF_LRA":
        result = ["--no-restrict-pivots", "--use-soi", "--new-prop"]
    elif logic == "QF_NIA":
        result = ["--nl-ext-tplanes"]
    elif logic == "UFBV":
        result = ["--finite-model-find"]
    elif logic == "BV":
        result = ["--full-saturate-quant", "--decision=internal"]
    elif logic in ["LIA", "LRA", "NIA", "NRA"]:
        result = ["--full-saturate-quant",
                  "--cegqi-nested-qe", "--decision=internal"]
    elif not logic.startswith("QF_"):
        result = ["--full-saturate-quant", "--fp-exp"]
    elif logic == "QF_AUFBV":
        result = ["--decision=stoponly"]
    elif logic == "QF_ABV":
        result = ["--arrays-weak-equiv"]
    elif logic in ["QF_AUFLIA", "QF_AUFNIA"]:
        result = ["--no-arrays-eager-index",
                  "--arrays-eager-lemmas", "--decision=justification"]
    elif logic == "QF_AX":
        result = ["--no-arrays-eager-index",
                  "--arrays-eager-lemmas", "--decision=internal"]
    elif logic == "QF_ALIA":
        result = ["--no-arrays-eager-index",
                  "--arrays-eager-lemmas", "--decision=stoponly"]
    elif logic in ["QF_S", "QF_SLIA"]:
        result = ["--strings-exp"]
    elif "FP" in logic:
        result = ["--fp-exp"]

    print(f"  Solver options for logic: {result}")
    return result


print(f"Solving problem {problem_path}...")
print(f"  Partitioner: {partitioner}")
logic = get_logic(problem_path)
print(f"  Logic: {logic}")
solver_opts = get_options_for_logic(logic)
partition, timeout, answer = run_a_partition(
    problem_path, solver_opts, initial_timeout)
if answer == "sat":
    print("found result SAT")
elif answer in ["timeout"]:
    print("found result TIMEOUT")
elif answer in ["unknown"]:
    print("found result UNKNOWN")
elif answer in ["unsat"]:
    print("found result UNSAT")
print("ERROR")
