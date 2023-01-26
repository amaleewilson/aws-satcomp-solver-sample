################### Use Mallob
FROM osmt_base AS builder
USER root

################### Extract cvc5 in run stage
FROM satcomp-base:leader2 AS osmt_liaison
WORKDIR /

RUN /usr/bin/python3.8 -m pip install mpi4py

COPY --from=builder /usr/local/lib/libgmp* /usr/local/lib/

# Copy mallob and solver scripts
COPY --from=builder /cvc5/build/bin/cvc5 cvc5
COPY --from=builder /cvc5/build/bin/cvc5 /competition/cvc5
COPY --from=builder /opensmt/build/opensmt-splitter opensmt-splitter
COPY --from=builder --chown=ecs-user /opensmt/build/opensmt-splitter /competition/opensmt-splitter
# COPY --chown=ecs-user ./test.smt2 test.smt2
COPY --chown=ecs-user ./run_cvc5.sh /competition/
COPY --chown=ecs-user ./replace_solver.py /competition/
COPY --chown=ecs-user ./solver_utils.py /competition/
COPY --chown=ecs-user /solver /competition
COPY --chown=ecs-user /cleanup /competition
USER ecs-user
RUN chmod +x /competition/opensmt-splitter
RUN chmod +x /competition/run_cvc5.sh
RUN chmod +x /competition/solver
RUN chmod +x /competition/solver_utils.py
RUN chmod +x /competition/replace_solver.py
COPY --chown=ecs-user /cleanup /competition
RUN chmod +x /competition/cleanup
# RUN ./cvc5 --compute-partitions=32 --lang=smt2 --partition-strategy=heap-trail --checks-before-partition=5000 --checks-between-partitions=0 --append-learned-literals-to-cubes --produce-learned-literals test.smt2
