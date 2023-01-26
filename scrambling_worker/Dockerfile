################### Use cvc5
FROM scrambling_base AS builder
USER root

################### Extract Mallob in run stage
FROM satcomp-base:worker9 AS cvc5_liaison
WORKDIR /

RUN /usr/bin/python3.8 -m pip install mpi4py

COPY --from=builder /cvc5/build/bin/cvc5 cvc5
COPY --from=builder /scrambler/scrambler /competition/scrambler
COPY --from=builder /cvc5/build/bin/cvc5 /competition/cvc5
COPY --from=scram:partitioning-leader9 /competition/run_cvc5.sh /competition/
COPY --from=scram:partitioning-leader9 /competition/replace_solver.py /competition/
COPY --from=scram:partitioning-leader9 /competition/solver_utils.py /competition/

RUN chown ecs-user /competition/replace_solver.py 
RUN chown ecs-user /competition/solver_utils.py
RUN chown ecs-user /competition/replace_solver.py 
COPY --chown=ecs-user /worker /competition

COPY --chown=ecs-user /cleanup /competition
RUN chmod +x /competition/cleanup
RUN chmod +x /competition/worker
USER ecs-user