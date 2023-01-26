################### Build Mallob
FROM satcomp-common-base-image
USER root
#  Install required softwares
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt install -y cmake build-essential bison flex zlib1g-dev libopenmpi-dev wget unzip build-essential zlib1g-dev cmake python3.8 build-essential gfortran wget curl default-jre python3.8-tk

RUN git clone https://github.com/SMT-COMP/scrambler.git
WORKDIR /scrambler
RUN make -j2

WORKDIR /

# Build cvc5
RUN /usr/bin/python3.8 -m pip install toml
RUN /usr/bin/python3.8 -m pip install mpi4py
# RUN git clone https://github.com/cvc5/cvc5.git
RUN git clone https://github.com/amaleewilson/cvc5.git
WORKDIR cvc5
RUN git fetch
#RUN git checkout 61828785f9a0212ac4e437b191e418ad1946a4dc
RUN git checkout new-partitioning
RUN git pull
# Checkout the latest partitioning branch? 
RUN ./configure.sh --auto-download --static --static-binary
RUN cd build && make -j4 && cd ..

