#!/bin/bash

echo $1
echo $2
# mpirun --mca btl_tcp_if_include eth0 --allow-run-as-root -np 2 \
#   --hostfile $1 --use-hwthread-cpus --map-by node:PE=2 --bind-to none --report-bindings \
# 
mpirun --mca btl_tcp_if_include eth0  --allow-run-as-root -np $2 \
  --hostfile $1  --use-hwthread-cpus --bind-to none --report-bindings \
  python3.8 /competition/replace_solver.py /competition/cvc5 $3


echo "cleaning up leader"
/competition/cleanup
