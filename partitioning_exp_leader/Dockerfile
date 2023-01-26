################### Use Mallob
FROM cvc5_base AS builder
USER root

################### Extract cvc5 in run stage
FROM satcomp-base:leader5 AS cvc5_liaison
WORKDIR /

RUN /usr/bin/python3.8 -m pip install mpi4py

# Copy mallob and solver scripts
COPY --from=builder /cvc5/build/bin/cvc5 cvc5
COPY --from=builder /cvc5/build/bin/cvc5 /competition/cvc5
# COPY --chown=ecs-user ./test.smt2 test.smt2
COPY --chown=ecs-user ./run_cvc5.sh /competition/
COPY --chown=ecs-user ./replace_solver.py /competition/
COPY --chown=ecs-user ./solver_utils.py /competition/
COPY --chown=ecs-user /solver /competition
COPY --chown=ecs-user /cleanup /competition
USER ecs-user
RUN chmod +x /competition/run_cvc5.sh
RUN chmod +x /competition/solver
RUN chmod +x /competition/solver_utils.py
RUN chmod +x /competition/replace_solver.py
COPY --chown=ecs-user /cleanup /competition
RUN chmod +x /competition/cleanup
# RUN ./cvc5 --compute-partitions=32 --lang=smt2 --partition-strategy=heap-trail --checks-before-partition=5000 --checks-between-partitions=0 --append-learned-literals-to-cubes --produce-learned-literals test.smt2
