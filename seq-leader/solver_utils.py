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
                    strategy):

    print("Making partitons")
    # Build the partition command
    partition_command = (
        f"{partitioner} --compute-partitions={number_of_partitions} "
        f"--lang=smt2 --partition-strategy={strategy} "
        f"--checks-before-partition={checks_before_partition} "
        f"--checks-between-partitions={checks_between_partitions} "
        f"{partitioner_options} {smt_file}"
    )

    output = subprocess.check_output(
        partition_command, shell=True)
    print("partitioning at least terminated")
    partitions = output.decode("utf-8").strip().split('\n')
    psize = len(partitions)
    if partitions[-1] == "sat":
        return "sat"
    elif len(partitions) == 1 and partitions[-1] == "unsat":
        return "unsat"
    elif len(partitions) == 1 and partitions[-1] == "unknown":
        return "unknown"
    else:
        return partitions[0: len(partitions) - 1]


def get_partitions(partitioner, partitioner_options, number_of_partitions,
                   smt_file, checks_before_partition, checks_between_partitions,
                   strategy):

    partitions = make_partitions(partitioner, partitioner_options, number_of_partitions,
                                 smt_file, checks_before_partition, checks_between_partitions,
                                 strategy)

    if partitions == "sat" or partitions == "unsat":
        return partitions 

    if not len(partitions) > 1:
        alternate_partitioning_configurations = (
            get_alternate_partitioning_configurations(int(checks_before_partition), int(checks_between_partitions),
                                                      strategy, 3000)
        )
        for apc in alternate_partitioning_configurations:
            partitions = make_partitions(partitioner, partitioner_options,
                                         number_of_partitions, smt_file, *apc)
            if partitions == "sat" or partitions == "unsat":
                return partitions 
            if partitions == "unknown":
                continue
            if len(partitions) > 1:
                break
    return partitions


def get_alternate_partitioning_configurations(prepart_checks, btwpart_checks,
                                              strategy, backup_prepart_checks):
  return [
      [prepart_checks // 2, btwpart_checks // 2, strategy],
      [prepart_checks // 4, btwpart_checks // 4, strategy],
      [prepart_checks // 8, btwpart_checks // 8, strategy],
      [prepart_checks // 16, btwpart_checks // 16, strategy],
      [prepart_checks // 32, btwpart_checks // 32, strategy],
      [prepart_checks // 64, btwpart_checks // 64, strategy],
      [prepart_checks // 128, btwpart_checks // 128, strategy],
      [prepart_checks // 256, btwpart_checks // 256, strategy],
      [prepart_checks // 512, btwpart_checks // 512, strategy],
      [backup_prepart_checks, 1, "decision-trail"],
      [backup_prepart_checks // 2, 1, "decision-trail"],
      [backup_prepart_checks // 4, 1, "decision-trail"],
      [backup_prepart_checks // 8, 1, "decision-trail"],
      [backup_prepart_checks // 16, 1, "decision-trail"],
      [backup_prepart_checks // 32, 1, "decision-trail"],
      [backup_prepart_checks // 64, 1, "decision-trail"],
      [1, 1, "decision-trail"]  # last resort
  ]

"""
Make a copy of the partitioned problem and append a cube to it for each cube
that is in the list of partitions.
  partitions : The list of cubes to be appended to copies of the partitioned
               problem. 
  stitched_directory : The directory in which the stitched files will be 
                       written.  
  parent_file : The file that was partitioned. 
  debug : flag that indicates whether debug information should be printed
  returns : void
"""


def stitch_partition(partition: list, parent_file):

    # Read the original contents in
    with open(parent_file) as bench_file:
        bench_contents = bench_file.readlines()

        # Append the cube to the contents before check-sat
        check_sat_index = bench_contents.index("(check-sat)\n")
        bench_contents[check_sat_index:check_sat_index] = \
            [f"(assert {cube})\n" for cube in partition]
    with tempfile.NamedTemporaryFile(delete=False) as new_bench_file:
        new_bench_file.write("".join(bench_contents).encode('utf-8'))
        return new_bench_file.name


def run_solver(solver_executable, stitched_path, solver_opts: list, timeout):

    solve_command = [
        solver_executable,
        stitched_path,
        "--lang=smt2",
        f"--tlimit={timeout}",
    ] + solver_opts
    output = subprocess.run(
        solve_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT).stdout.decode("utf-8").strip()
    print(f"the output is {output}")
    if "unsat" in output:
        return "unsat"
    elif "sat" in output:
        return "sat"
    elif "timeout" in output:
        return "timeout"
    elif "unknown" in output:
        return "unknown"
    else:
        return "error"
