import subprocess
import os
import json
import re
from pathlib import Path
import tempfile


def get_input_json(request_directory):
    input = os.path.join(request_directory, "input.json")
    with open(input) as f:
        return json.loads(f.read())


"""
Make partitions by executing the partitioner with the provided options. 

  partitioner : the executable to use for partitioning
  partitioner_options : extra cli arguments to pass to partitioner
  number_of_partitions : The desired number of partitions to be made. 
  output_file : The file that partitions are written to. 
  smt_file : The full path of the smt2 benchmark file being partitioned.
  checks_before_partition : number of checks before partitioner starts 
                            making partitions
  checks_between_partitions : number of checks between subsequent partitions
  strategy : the partitioning strategy to send to the partitioner
  debug : flag that indicates whether debug information should be printed
  returns : void

TODO: Probably want to check for errors and/or confirm that the 
partitions were actually made and return something like a bool.
"""


def make_partitions(partitioner, partitioner_options, number_of_partitions,
                    smt_file, checks_before_partition, checks_between_partitions,
                    strategy, time_limit):

    # print("Making partitons")
    # Build the partition command
    partition_command = (
        f"{partitioner} --compute-partitions={number_of_partitions} "
        f" --tlimit={time_limit} "
        f"--lang=smt2 --partition-strategy={strategy} "
        f"--checks-before-partition={checks_before_partition} "
        f"--checks-between-partitions={checks_between_partitions} "
        f"{partitioner_options} {smt_file}"
    )

    try:
        output = subprocess.check_output(
            partition_command, shell=True, stderr=subprocess.STDOUT)
        # print("partitioning at least terminated")
        partitions = output.decode("utf-8").strip().split('\n')

        # Handle case where problem is solved while partitioning.
        if partitions[-1] == "sat":
            return "sat"
        elif len(partitions) == 1 and partitions[-1] == "unsat":
            return "unsat"
        elif len(partitions) == 1 and partitions[-1] == "unknown":
            return "unknown"
        # If not solved, then return the partitions
        else:
            return partitions[0: len(partitions) - 1]
    except Exception as e:
        # If the partitioning timed out, good to know.
        if "timeout" in str(e.output):
            return "timeout"
        # Any other error is just an error.
        else:
            return "error"
            print(e)


def get_partitions(partitioner, partitioner_options, number_of_partitions,
                   smt_file, checks_before_partition, checks_between_partitions,
                   strategy, time_limit):

    partitions = make_partitions(partitioner, partitioner_options, number_of_partitions,
                                 smt_file, checks_before_partition, checks_between_partitions,
                                 strategy, time_limit)

    return partitions

def scramble_partitions(seed, benchmark):
    subprocess.run("ulimit -s 1048576", shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    scramble_output_file = tempfile.NamedTemporaryFile(delete=False)
    scramble_command = (f"/competition/scrambler -seed {seed} " 
        f" < {benchmark} > {scramble_output_file.name} "
    )
    subprocess.run(scramble_command, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT) 
    return scramble_output_file.name


def run_solver(solver_executable, stitched_path, solver_opts, timeout):

    options = ""
    for o in solver_opts:
        options = options + " " + o + " "

    solve_command = (
        f"{solver_executable} "
        f"{options} "
        "--lang=smt2 "
        f"--tlimit={timeout} "
        f"{stitched_path} "
    )
    # print("SOLVE COMMAND " + solve_command)
    output = subprocess.run(
        solve_command, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT).stdout.decode("utf-8").strip()
    if "unsat" in output:
        return "unsat"
    elif "sat" in output:
        return "sat"
    elif "timeout" in output:
        return "timeout"
    elif "unknown" in output:
        return "unknown"
    else:
        print(f"the error output is {output}")

        return "error"
