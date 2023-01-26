################### Build Mallob
FROM satcomp-common-base-image
USER root
#  Install required softwares
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt install -y cmake build-essential m4 bison flex zlib1g-dev libopenmpi-dev wget unzip build-essential zlib1g-dev cmake python3.8 build-essential gfortran wget curl default-jre python3.8-tk

# Build cvc5
RUN /usr/bin/python3.8 -m pip install toml
RUN /usr/bin/python3.8 -m pip install mpi4py

COPY ./gmp-6.2.1.tar.xz /gmp-6.2.1.tar.xz
RUN ls
RUN tar -xf gmp-6.2.1.tar.xz 
WORKDIR /gmp-6.2.1
RUN ./configure --enable-cxx
RUN make -j4
RUN make install


WORKDIR /
RUN git clone https://github.com/usi-verification-and-security/opensmt.git
WORKDIR /opensmt
RUN git fetch
RUN git pull
RUN mkdir build
RUN cd build
WORKDIR /opensmt/build
RUN cmake -DPARALLEL=true ..
RUN make -j2

WORKDIR /
RUN git clone https://github.com/amaleewilson/cvc5.git
WORKDIR /cvc5
RUN git fetch
RUN git checkout new-partitioning
RUN git pull
# Checkout the latest partitioning branch? 
RUN ./configure.sh --auto-download --static --static-binary
RUN cd build && make -j4 && cd ..
