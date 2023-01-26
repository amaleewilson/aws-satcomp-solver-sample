#!/usr/bin/env python3.8
import concurrent.futures
import json
import logging
import os
import re
import subprocess
import sys
from mpi4py import MPI
from solver_utils import *
from mpi4py.futures import MPICommExecutor
from collections import defaultdict

'''
NOTE: Need to make the solver script call this one, I think.
'''

comm_world = MPI.COMM_WORLD
my_rank = comm_world.Get_rank()
num_procs = comm_world.Get_size()

partitioner = sys.argv[1]
problem_path = sys.argv[2]

# The timeout used for the first generation of paritions
initial_timeout = 30000
# The factor to scale the timeout by
timeout_scale_factor = 2

partitioner_options = ("--append-learned-literals-to-cubes "
                       "--produce-learned-literals")
number_of_partitions = 8
checks_before_partition = "625"
checks_between_partitions = "625"
strategy = "strict-cube"

def run_a_partition(partition: list, solver_opts: list, timeout):
    smt_partition = stitch_partition(partition, problem_path)
    result = run_solver(partitioner, smt_partition, solver_opts, timeout)
    os.remove(smt_partition)
    return (partition, timeout, result)

def print_result(result):
    if result == "sat":
        print("found result SAT")
        comm_world.Abort()
    elif result == "unsat":
        print("found result UNSAT")
        comm_world.Abort()
    elif result == "unknown":
        print("found result UNKNOWN")
        comm_world.Abort()

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
        result = ["--full-saturate-quant", "--cegqi-nested-qe", "--decision=internal"]
    elif not logic.startswith("QF_"):
        result = ["--full-saturate-quant", "--fp-exp"]
    elif logic == "QF_AUFBV":
        result = ["--decision=stoponly"]
    elif logic == "QF_ABV":
        result = ["--arrays-weak-equiv"]
    elif logic in ["QF_AUFLIA", "QF_AUFNIA"]:
        result = ["--no-arrays-eager-index", "--arrays-eager-lemmas", "--decision=justification"]
    elif logic == "QF_AX":
        result = ["--no-arrays-eager-index", "--arrays-eager-lemmas", "--decision=internal"]
    elif logic == "QF_ALIA":
        result = ["--no-arrays-eager-index", "--arrays-eager-lemmas", "--decision=stoponly"]
    elif logic in ["QF_S", "QF_SLIA"]:
        result = ["--strings-exp"]
    elif "FP" in logic:
        result = ["--fp-exp"]

    print(f"  Solver options for logic: {result}")
    return result

with MPICommExecutor(MPI.COMM_WORLD, root=0) as executor:
    if executor is not None:
        print(f"Solving problem {problem_path}...")
        print(f"  Partitioner: {partitioner}")
        print(f"  Options: {partitioner_options}")
        print(f"  Number of partitions: {number_of_partitions}")
        print(f"  Checks before: {checks_before_partition}")
        print(f"  Checks between: {checks_between_partitions}")
        print(f"  Strategy: {strategy}")

        logic = get_logic(problem_path)
        print(f"  Logic: {logic}")
        solver_opts = get_options_for_logic(logic)

        # Create initial partitions
        partitions = get_partitions(partitioner, partitioner_options, number_of_partitions,
                                    problem_path, checks_before_partition, checks_between_partitions,
                                    strategy)
        if partitions in ["sat", "unsat", "unknown"]:
            print_result(partitions)
        print(f" {len(partitions)} partitions successfully made!")

        not_done = set(executor.submit(run_a_partition, [partition], solver_opts, initial_timeout) for partition in partitions)
        generations = defaultdict(lambda: 0)
        generations[1] = len(not_done)
        while not_done:
            print(f"Waiting for {len(not_done)} tasks to finish...")
            for gen, num_tasks in generations.items():
                print(f"  Generation {gen}: {num_tasks}")
            done, not_done = concurrent.futures.wait(
                not_done, return_when=concurrent.futures.FIRST_COMPLETED)
            for task in done:
                partition, timeout, answer = task.result()
                generations[len(partition)] -= 1
                if answer == "sat":
                    print("found result SAT")
                    comm_world.Abort()
                    break
                elif answer in ["timeout", "unknown"]:
                    print(f"Timeout with {timeout}, repartitioning and rescheduling")

                    # Create subpartitions
                    smt_partition = stitch_partition(partition, problem_path)
                    subpartitions = get_partitions(partitioner, partitioner_options, number_of_partitions,
                                                   smt_partition, checks_before_partition, checks_between_partitions,
                                                   strategy)
                    os.remove(smt_partition)
                    if subpartitions == "unsat":
                        print(f"Partitioner found unsat, skipping subpartitions")
                        continue
                    elif subpartitions in ["sat", "unknown"]:
                        print_result(subpartitions)

                    subpartitions = [partition + [subpartition] for subpartition in subpartitions]
                    print(f"  {len(subpartitions)} subpartitions successfully made!")

                    for subpartition in subpartitions:
                        task = executor.submit(run_a_partition, subpartition, solver_opts, timeout * timeout_scale_factor)
                        not_done.add(task)
                    print(f"  Subparitions submitted")

                    if len(subpartitions) > 0:
                        generations[len(subpartitions[0])] += len(subpartitions)

        print("found result UNSAT")
