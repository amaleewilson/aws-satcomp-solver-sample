import sys
import subprocess
import os
import re
import pandas

# # Remove all the existing docker images.
# subprocess.run("docker rmi -f $(docker images -aq)", shell=True)
#
# # Create the base image in the infrastructure repo
# subprocess.run("docker build -t satcomp-common-base-image .", shell=True,
#                cwd="/Users/amaleewilson/aws-batch-comp-infrastructure-sample/src/satcomp-common-base-image/")
#
# # Now create ten versions of the leader docker image.
# leader_docker_file_name = "/Users/amaleewilson/aws-batch-comp-infrastructure-sample/src/satcomp-leader-image/Dockerfile"
# for i in range(1, 11):
#     with open(leader_docker_file_name, "r") as leader_docker_file:
#         leader_docker_contents = leader_docker_file.readlines()
#
#     for line in leader_docker_contents:
#         if line.startswith("ENTRYPOINT"):
#             entry_line = line
#
#     fixed_entry_line = re.sub(
#         "cvc5-seq-[\d]*", "cvc5-seq-" + str(i), entry_line)
#
#     leader_docker_contents[leader_docker_contents.index(
#         entry_line)] = fixed_entry_line
#
#     with open(leader_docker_file_name, "w") as leader_docker_file:
#         leader_docker_contents = leader_docker_file.write(
#             "".join(leader_docker_contents))
#     subprocess.run(f"docker build -f satcomp-leader-image/Dockerfile -t satcomp-base:leader{i} .",
#                    shell=True, cwd="/Users/amaleewilson/aws-batch-comp-infrastructure-sample/src")

# # Now make the base cvc5 image
# subprocess.run("docker build -t cvc5_base .", shell=True,
#                cwd="/Users/amaleewilson/aws-satcomp-solver-sample/base")
#
#
# # Now make 10 versions of the cvc5 leader image.
# cvc5_leader_docker_file_name = "/Users/amaleewilson/aws-satcomp-solver-sample/seq-leader/Dockerfile"
# for i in range(1, 11):
#     with open(cvc5_leader_docker_file_name, "r") as cvc5_leader_docker_file:
#         cvc5_leader_docker_contents = cvc5_leader_docker_file.readlines()
#
#     for line in cvc5_leader_docker_contents:
#         if line.startswith("FROM satcomp-base"):
#             entry_line = line
#
#     fixed_entry_line = re.sub(
#         "satcomp-base:leader[\d]*", "satcomp-base:leader" + str(i), entry_line)
#
#     cvc5_leader_docker_contents[cvc5_leader_docker_contents.index(
#         entry_line)] = fixed_entry_line
#
#     with open(cvc5_leader_docker_file_name, "w") as cvc5_leader_docker_file:
#         cvc5_leader_docker_contents = cvc5_leader_docker_file.write(
#             "".join(cvc5_leader_docker_contents))
#     subprocess.run(f"docker build -t cvc5:seq-leader-{i} .",
#                    shell=True, cwd="/Users/amaleewilson/aws-satcomp-solver-sample/seq-leader")
#
# # Now login to AWS
# subprocess.run("aws --profile blab ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 127312632904.dkr.ecr.us-west-1.amazonaws.com", shell=True)
#
# # Now tag all the dockers and push them.
# for i in range(1, 11):
#     subprocess.run(
#         f"docker tag cvc5:seq-leader-{i} 127312632904.dkr.ecr.us-west-1.amazonaws.com/cvc5-seq-{i}-leader", shell=True)
#     subprocess.run(
#         f"docker push 127312632904.dkr.ecr.us-west-1.amazonaws.com/cvc5-seq-{i}-leader", shell=True)
#
# # Now start all the instances
# for i in range(1, 11):
#     subprocess.run(f"./update_instances --profile blab --option setup --project cvc5-seq-{i} --workers 0",
#                    shell=True, cwd="/Users/amaleewilson/aws-batch-comp-infrastructure-sample")

# Now send all the messages for the solvers
smtcomp_data = pandas.read_csv(
    "/Users/amaleewilson/aws-batch-comp-infrastructure-sample/cloud-map.csv")
comp = list(smtcomp_data["competition_name"])

for i in range(1, 11):
    proj = "cvc5-seq-" + str(i)
    for j in range(40):
        print(
            f"./send_message --profile blab --location s3://127312632904-us-west-1-{proj}-satcompbucket/{comp[(i-1)*40 + j]} --project {proj} --workers 0")
        subprocess.run(
            f"./send_message --profile blab --location s3://127312632904-us-west-1-{proj}-satcompbucket/{comp[(i-1)*40 + j]} --project {proj} --workers 0",
            shell=True, cwd="/Users/amaleewilson/aws-batch-comp-infrastructure-sample")
