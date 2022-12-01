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
import time

# worker needs this


def run_a_partition(partition, solver_opts, timeout, problem_path, partitioner):
    # process_rank = comm_world.Get_rank()
    # process_count = comm_world.Get_size()
    # process_host = MPI.Get_processor_name()

    # print(', '.join(map(str, ('run_a_partition',
    #                           process_rank,
    #                           process_count,
    #                           process_host))))
    smt_partition = stitch_partition(partition, problem_path)
    result = run_solver(partitioner, smt_partition, solver_opts, timeout)
    os.remove(smt_partition)
    return (partition, timeout, result)

# Only leader needs this


def print_data_result(partitioning_time, partitioning_succeeded, solved_while_partitioning,
                      partitions_valid, number_of_partitions_made, final_result, solving_time):
    # Going for a json format.
    print("PARTITION_DATA {"
          f"\"partitioning_time\" : \"{partitioning_time}\", "
          f"\"partitioning_succeeded\" : \"{partitioning_succeeded}\", "
          f"\"solved_while_partitioning\" : \"{solved_while_partitioning}\", "
          f"\"partitions_valid\" : \"{partitions_valid}\", "
          f"\"number_of_partitions_made\" : \"{number_of_partitions_made}\", "
          f"\"final_result\" : \"{final_result}\", "
          f"\"solving_time\" : \"{solving_time}\" "
          "} END_PARTITION_DATA")
    comm_world.Abort()

# worker needs this


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

    # print(f"  Solver options for logic: {result}")
    return result


# MPI stuff
comm_world = MPI.COMM_WORLD
my_rank = comm_world.Get_rank()
num_procs = comm_world.Get_size()
process_host = MPI.Get_processor_name()
mpi_info = MPI.Info.Create()

# print(
#     f"mpi info: my_rank={my_rank}, num_procs={num_procs}, process_host={process_host}")

# BEGIN OPTIONS - these will be changed per partioning experiment
# partitioner_options = ("--append-learned-literals-to-cubes "
#                        "--produce-learned-literals")

# VERSION 1 lemma cubes with prioritization
# partitioner_options = " --partition-when tlimit --produce-learned-literals --partition-tlimit 30 --prioritize-literals  "
# number_of_partitions = 8
# checks_before_partition = "1"
# checks_between_partitions = "1"
# strategy = "lemma-cubes"

# #VERSION 2 lemma cubes without prioritization
# partitioner_options = " --partition-when tlimit --partition-tlimit 30 "
# number_of_partitions = 8
# checks_before_partition = "1"
# checks_between_partitions = "1"
# strategy = "lemma-cubes"

# #VERSION 3 heap cubes with prioritization
# partitioner_options = " --partition-when tlimit --produce-learned-literals --partition-tlimit 30 --prioritize-literals  "
# number_of_partitions = 8
# checks_before_partition = "1"
# checks_between_partitions = "1"
# strategy = "heap-cubes"

# #VERSION 4 heap cubes without prioritization
# partitioner_options = " --partition-when tlimit --partition-tlimit 30 "
# number_of_partitions = 8
# checks_before_partition = "1"
# checks_between_partitions = "1"
# strategy = "heap-cubes"

# #VERSION 5 decision cubes with prioritization
# partitioner_options = " --partition-when tlimit --produce-learned-literals --partition-tlimit 30 --prioritize-literals  "
# number_of_partitions = 8
# checks_before_partition = "1"
# checks_between_partitions = "1"
# strategy = "decision-cubes"

# #VERSION 6 decision cubes without prioritization
# partitioner_options = " --partition-when tlimit --partition-tlimit 30 "
# number_of_partitions = 8
# checks_before_partition = "1"
# checks_between_partitions = "1"
# strategy = "decision-cubes"


# #VERSION 2.2 lemma cubes without prioritization, WITH ZLL
# partitioner_options = " --append-learned-literals-to-cubes --partition-when tlimit --partition-tlimit 30 "
# number_of_partitions = 8
# checks_before_partition = "1"
# checks_between_partitions = "1"
# strategy = "lemma-cubes"

# #VERSION 4.2 heap cubes without prioritization, WITH ZLL
partitioner_options = " --append-learned-literals-to-cubes --partition-when tlimit --partition-tlimit 30 "
number_of_partitions = 8
checks_before_partition = "1"
checks_between_partitions = "1"
strategy = "heap-cubes"


# The timeout used for the partitioning itself
partitioning_timeout = 300000

# Solving timeout (total time)
solver_timeout = 1200000
# END OPTIONS


# If this is the leader process, partition and spawn workers with partitions
if (my_rank == 0):
    # BEGIN DATA
    partitioning_time = 0
    partitioning_succeeded = True
    solved_while_partitioning = False
    partitions_valid = True
    number_of_partitions_made = 0
    final_result = "unsolved"
    solving_time = 0
    # END DATA
    print("strategy: ", strategy)

    partitioner = sys.argv[1]
    problem_path = sys.argv[2]
    host_fl = sys.argv[3]
    mpi_info.Set("add-hostfile", host_fl)

    logic = get_logic(problem_path)
    solver_opts = get_options_for_logic(logic)

    # Now make the partitions.
    # print(f"Solving problem {problem_path}...")
    # print(f"  Partitioner: {partitioner}")
    # print(f"  Logic: {logic}")
    # print(f"  Options: {partitioner_options}")
    # print(f"  Number of partitions: {number_of_partitions}")
    # print(f"  Checks before: {checks_before_partition}")
    # print(f"  Checks between: {checks_between_partitions}")
    # print(f"  Strategy: {strategy}")

    # Create partitions
    start_time = time.time()
    partitions = get_partitions(partitioner, partitioner_options, number_of_partitions,
                                problem_path, checks_before_partition, checks_between_partitions,
                                strategy, partitioning_timeout)
    partitioning_time = time.time() - start_time

    # In this case we solved during partitioning
    if partitions in ["sat", "unsat", "unknown"]:
        solved_while_partitioning = True
        final_result = partitions
        partitions_valid = "unknown"
        partitioning_succeeded = "unknown"
        print_data_result(partitioning_time, partitioning_succeeded, solved_while_partitioning,
                          partitions_valid, number_of_partitions_made, final_result, solving_time)
    # Partitioning timed out
    elif partitions in ["timeout"]:
        partitioning_time = "timeout"
        partitions_valid = "unknown"
        partitioning_succeeded = False
        print_data_result(partitioning_time, partitioning_succeeded, solved_while_partitioning,
                          partitions_valid, number_of_partitions_made, final_result, solving_time)
    # An error occurred
    elif partitions in ["error"]:
        partitioning_time = "error"
        partitions_valid = "unknown"
        partitioning_succeeded = False
        print_data_result(partitioning_time, partitioning_succeeded, solved_while_partitioning,
                          partitions_valid, number_of_partitions_made, final_result, solving_time)

    partitioning_succeeded = True
    # print(f" {len(partitions)} partitions successfully made!")
    number_of_partitions_made = len(partitions)

    print("begin_number_of_partitions_made{", number_of_partitions_made, "}end_number_of_partitions_made")

    # Must make this list the size of the number of nodes. 
    for i in range(number_of_partitions_made, number_of_partitions):
        partitions.append("NULL PARTITION")
    partitions = ["NULL ROOT PARTITION"] + partitions

else:
    partitions = None
    partitioner = None
    problem_path = None
    solver_opts = None
    partitioning_time = None

# Scatter the partitions
partitions = comm_world.scatter(partitions, root=0)

# if my_rank == 0:
#     print("root got this partition : " + partitions)

# Broadcast other data
partitioner = comm_world.bcast(partitioner, root=0)
problem_path = comm_world.bcast(problem_path, root=0)
solver_opts = comm_world.bcast(solver_opts, root=0)
partitioning_time = comm_world.bcast(partitioning_time, root=0)

# leader waits for result messages to come in from the workers
if my_rank == 0:
    unknown_result_partition = False
    timeout_result_partition = False
    messages_received = 0
    start_solving_time = time.time()
    # 8 is number of partitions, should un-hardcode this.
    while messages_received < number_of_partitions:
        worker_result = comm_world.recv(
            source=MPI.ANY_SOURCE, status=MPI.Status())
        # print(worker_result)
        messages_received = messages_received + 1

        if worker_result in ["sat"]:
            final_result = "sat"
            solving_time = time.time() - start_solving_time
            print_data_result(partitioning_time, partitioning_succeeded, solved_while_partitioning,
                              partitions_valid, number_of_partitions_made, final_result, solving_time)
        elif worker_result in ["unknown"]:
            # Could still find a sat partition, maybe
            unknown_result_partition = True
        elif worker_result in ["timeout"]:
            # Could still find a sat partition, maybe
            timeout_result_partition = True
        elif worker_result in ["error"]:
            print(f"invalid partition occurred")
            partitions_valid = False
            final_result = "error"
            solving_time = time.time() - start_solving_time
            print_data_result(partitioning_time, partitioning_succeeded, solved_while_partitioning,
                              partitions_valid, number_of_partitions_made, final_result, solving_time)
        # If none of the above conditions are met, then it was a null result because the worker 
        # did not receive a partition. 
    if (final_result == "unsolved"):
        if unknown_result_partition:
            final_result = "unknown"
        elif timeout_result_partition:
            final_result = "timeout"
        elif partitions_valid:
            final_result = "unsat"
    solving_time = time.time() - start_solving_time
    print_data_result(partitioning_time, partitioning_succeeded, solved_while_partitioning,
                      partitions_valid, number_of_partitions_made, final_result, solving_time)

# this is the worker part
else:
    # solver timeout is solver_timeout (20 minutes) - time to partition - a 60 second buffer.
    # The buffer is to allow for the communication etc etc and is in place so that we
    # can be guaranteed to get the data that this process exiting normally will give us.
    # In particular, we would like to know the partitioning time, regardless of whether we time out.
    # solving_solver_timeout = int(solver_timeout -
    #                              (partitioning_time * 1000) - (60000))
    solving_solver_timeout = 1200000 # Just let it die since we're using partitioning tlimit
    if not partitions == "NULL PARTITION":
        partition, timout, worker_result = run_a_partition(
            partitions, solver_opts, solving_solver_timeout, problem_path, partitioner)
        comm_world.send(worker_result, dest=0)
    else:
        comm_world.send("null result", dest=0)

