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

    print(partitioner)
    split_dir = ""
    try:
        test_command = f"mktemp -d"
        testing = subprocess.check_output(
            test_command, shell=True, stderr=subprocess.STDOUT)
        test_output = testing.decode("utf-8").strip()
        split_dir = test_output
    except Exception as e:
        print(e)

    # Here we add the OpenSMT splitting options to the original file.
    split_command = (r"sed -i '1s;^;"
                         r"(set-option :lookahead-split) \n"
                         r"(set-option :split-num 16) \n"
                         r"(set-option :output-dir \""
                         f"{split_dir}\") "
                         r"\n"
                         r"(set-option :split-format-length \"brief\") \n"
                         r"(set-option :split-format smt2)\n;' "
                         f"{smt_file}"
        )

    try:
       output = subprocess.run(
       split_command, shell=True,
       stdout=subprocess.PIPE,
       stderr=subprocess.STDOUT).stdout.decode("utf-8").strip()
    except Exception as e:
        print(e)

    partition_command = (
        f"{partitioner}  {smt_file}"
    )
    partitions = []
    # Now we run the opensmt-splitter to create the partitions.
    try:
        output = subprocess.check_output(
            partition_command, shell=True, stderr=subprocess.STDOUT, timeout=time_limit)
        the_output = output.decode("utf-8").strip()
        output_list = output.decode("utf-8").strip().split('\n')

        # Now undo that prefix we added.
        remove_split_command = f"sed -i '1,5d' {smt_file}"
        try:
           output = subprocess.run(
           remove_split_command, shell=True,
           stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT).stdout.decode("utf-8").strip()
        except Exception as e:
            print(e)
        if not "Outputing an instance" in the_output:
            print("no splits made!!!!")
            if output_list[-1] == "sat":
                return "sat"
            elif output_list[-1] == "unsat":
                return "unsat" 
            elif output_list[-1] == "unknown":
                return "unknown"
            else:
                print(the_output)
                return "error"

        # If not solved, then return the partitions
        else:
            for filename in os.listdir(split_dir):
                f = os.path.join(split_dir, filename)
                cat_command = f"cat {f}"
                partition = subprocess.check_output(cat_command,
                      shell=True, stderr=subprocess.STDOUT)
                p = ' '.join(partition.decode("utf-8").strip().split('\n'))
                partitions.append(p)
            return partitions
    except Exception as e:
        # Undo that prefix we added.
        remove_split_command = f"sed -i '1,5d' {smt_file}"
        try:
           output = subprocess.run(
           remove_split_command, shell=True,
           stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT).stdout.decode("utf-8").strip()
        except Exception as e:
            print(e)
        # If the partitioning timed out, good to know.
        if "timed out" in str(e):
            return "timeout"
        # Any other error is just an error.
        else:
            print(e)
            print(e.output)
            return "error"



def get_partitions(partitioner, partitioner_options, number_of_partitions,
                   smt_file, checks_before_partition, checks_between_partitions,
                   strategy, time_limit):

    partitions = make_partitions(partitioner, partitioner_options, number_of_partitions,
                                 smt_file, checks_before_partition, checks_between_partitions,
                                 strategy, time_limit)

    return partitions


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


def stitch_partition(partition, parent_file):
    # print("PARTITION INFO : " + partition)

    # Read the original contents in
    with open(parent_file) as bench_file:
        bench_contents = bench_file.readlines()

        # Append the cube to the contents before check-sat
        check_sat_index = bench_contents.index("(check-sat)\n")
        bench_contents[check_sat_index:check_sat_index] = \
            f"{partition}\n"
    with tempfile.NamedTemporaryFile(delete=False) as new_bench_file:
        new_bench_file.write("".join(bench_contents).encode('utf-8'))
        return new_bench_file.name


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
