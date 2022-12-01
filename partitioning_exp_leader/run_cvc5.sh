#!/bin/bash

echo $1
echo $2
# mpirun --mca btl_tcp_if_include eth0 --allow-run-as-root -np 2 \
#   --hostfile $1 --use-hwthread-cpus --map-by node:PE=2 --bind-to none --report-bindings \
# 

# I think we really want np to be the number of partitions (plus one?) in the case 
# of a single layer of partitioning. Additionally, bind to socket so that
# each instance gets full memory usage. 
mpiexec -n 9 --mca btl_tcp_if_include eth0  --allow-run-as-root \
  --hostfile $1  --report-bindings \
  python3.8 /competition/replace_solver.py /competition/cvc5 $2 $1

# 11/9 : this one kind of works. 
# mpiexec -n 9 --mca btl_tcp_if_include eth0  --allow-run-as-root \
#   --hostfile $1   --report-bindings \
#   python3.8 -m mpi4py.futures /competition/replace_solver.py /competition/cvc5 $2 $1

echo "cleaning up leader"
/competition/cleanup
