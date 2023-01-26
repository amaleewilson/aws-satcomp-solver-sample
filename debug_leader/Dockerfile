################### Use Mallob
FROM cvc5_debug AS builder
USER root

################### Extract cvc5 in run stage
FROM satcomp-base:leader6 AS cvc5_seq_liaison
WORKDIR /

# Copy mallob and solver scripts
COPY --from=builder /cvc5/build/bin/cvc5 cvc5
COPY --from=builder /cvc5/build/bin/cvc5 /competition/cvc5
COPY --chown=ecs-user ./run_seq_cvc5.sh /competition/
COPY --chown=ecs-user ./replace_solver.py /competition/
COPY --chown=ecs-user ./solver_utils.py /competition/
COPY --chown=ecs-user /solver /competition
USER ecs-user
RUN chmod +x /competition/run_seq_cvc5.sh
RUN chmod +x /competition/solver
RUN chmod +x /competition/solver_utils.py
RUN chmod +x /competition/replace_solver.py
